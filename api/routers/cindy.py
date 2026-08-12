from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import CindyResult, Measurement, Workout, WorkoutCategory, WorkoutCategoryLink
from api.schemas.cindy import (
    CindyAnalyticsResponse,
    CindyAttemptSummary,
    CindyChangeResponse,
    CindyCompleteRequest,
    CindyResultResponse,
    CindyStartResponse,
)
from api.services.cindy import (
    CALORIE_ESTIMATION_VERSION,
    CindyAttempt,
    change_from_previous,
    estimate_calories,
    personal_best,
)
from api.services.cindy import (
    completed_as_prescribed as compute_completed_as_prescribed,
)
from api.services.cindy import (
    total_reps as compute_total_reps,
)
from api.services.teams import resolve_primary_team_id

router = APIRouter(prefix="/api", tags=["cindy"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]

CINDY_CATEGORY_SLUGS = ("strength", "functional_conditioning")


@router.post("/workouts/cindy/start", response_model=CindyStartResponse)
def start_cindy(user: CurrentUser) -> CindyStartResponse:
    return CindyStartResponse(started_at=datetime.now(UTC))


def _latest_bodyweight_kg(session: Session, user_id: str) -> float | None:
    weight = session.scalar(
        select(Measurement.weight_kg)
        .where(Measurement.user_id == user_id, Measurement.weight_kg.is_not(None))
        .order_by(Measurement.occurred_at.desc())
        .limit(1)
    )
    return float(weight) if weight is not None else None


@router.post(
    "/workouts/cindy/complete", response_model=CindyResultResponse, status_code=201
)
def complete_cindy(
    payload: CindyCompleteRequest,
    user: CurrentUser,
    session: DatabaseSession,
) -> CindyResult:
    set_request_user(session, user.id)
    team_id = resolve_primary_team_id(session, user.id)

    reps = compute_total_reps(
        payload.full_rounds, payload.extra_pullups, payload.extra_pushups, payload.extra_squats
    )
    as_prescribed = compute_completed_as_prescribed(payload.total_seconds)

    calories_burned: int | None = None
    calorie_source: str | None = None
    calorie_estimation_version: str | None = None
    if payload.calories_burned is not None:
        calories_burned = payload.calories_burned
        calorie_source = "external"
    elif payload.estimate_calories:
        bodyweight = _latest_bodyweight_kg(session, user.id)
        calories_burned = estimate_calories(payload.total_seconds, bodyweight)
        calorie_source = "estimated"
        calorie_estimation_version = CALORIE_ESTIMATION_VERSION

    workout = Workout(
        user_id=user.id,
        team_id=team_id,
        occurred_at=payload.occurred_at or datetime.now(UTC),
        title="Cindy",
        activity_type="cindy",
        duration_minutes=max(1, round(payload.total_seconds / 60)),
        rpe=payload.rpe,
        notes=payload.notes,
        visibility=payload.visibility,
    )
    session.add(workout)
    session.flush()

    category_ids = session.scalars(
        select(WorkoutCategory.id).where(WorkoutCategory.slug.in_(CINDY_CATEGORY_SLUGS))
    )
    for category_id in category_ids:
        session.add(WorkoutCategoryLink(workout_id=workout.id, category_id=category_id))

    result = CindyResult(
        workout_id=workout.id,
        user_id=user.id,
        full_rounds=payload.full_rounds,
        extra_pullups=payload.extra_pullups,
        extra_pushups=payload.extra_pushups,
        extra_squats=payload.extra_squats,
        total_reps=reps,
        total_seconds=payload.total_seconds,
        completed_as_prescribed=as_prescribed,
        calories_burned=calories_burned,
        calorie_source=calorie_source,
        calorie_estimation_version=calorie_estimation_version,
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


@router.get("/analytics/cindy", response_model=CindyAnalyticsResponse)
def cindy_analytics(
    user: CurrentUser,
    session: DatabaseSession,
) -> CindyAnalyticsResponse:
    set_request_user(session, user.id)

    rows = session.execute(
        select(
            Workout.occurred_at,
            CindyResult.full_rounds,
            CindyResult.total_reps,
            CindyResult.total_seconds,
            CindyResult.completed_as_prescribed,
        )
        .join(Workout, Workout.id == CindyResult.workout_id)
        .where(CindyResult.user_id == user.id)
        .order_by(Workout.occurred_at)
    ).all()

    history = [
        CindyAttemptSummary(
            completed_at=row.occurred_at,
            full_rounds=row.full_rounds,
            total_reps=row.total_reps,
            total_seconds=row.total_seconds,
            completed_as_prescribed=row.completed_as_prescribed,
        )
        for row in rows
    ]
    attempts = [
        CindyAttempt(
            completed_at=item.completed_at,
            full_rounds=item.full_rounds,
            total_reps=item.total_reps,
            total_seconds=item.total_seconds,
        )
        for item in history
    ]

    best = personal_best(attempts)
    change = change_from_previous(attempts)

    return CindyAnalyticsResponse(
        latest=history[-1] if history else None,
        personal_best=(
            CindyAttemptSummary(
                completed_at=best.completed_at,
                full_rounds=best.full_rounds,
                total_reps=best.total_reps,
                total_seconds=best.total_seconds,
                completed_as_prescribed=compute_completed_as_prescribed(best.total_seconds),
            )
            if best
            else None
        ),
        change_from_previous=(
            CindyChangeResponse(
                total_reps_change=change.total_reps_change,
                total_seconds_change=change.total_seconds_change,
                full_rounds_change=change.full_rounds_change,
            )
            if change
            else None
        ),
        history=list(reversed(history)),
    )
