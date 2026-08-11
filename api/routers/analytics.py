from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import Workout, WorkoutCategory, WorkoutCategoryLink
from api.schemas.analytics import (
    AthleteAnalyticsResponse,
    ConsistencyResponse,
    RunningAnalyticsResponse,
    RunningSampleResponse,
)
from api.services.analytics import (
    WorkoutSample,
    active_days_in_window,
    category_coverage,
    running_summary,
    sessions_in_window,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]

DEFAULT_RANGE_DAYS = 28
MIN_SAMPLES_FOR_TRENDS = 2


def load_samples(session: Session, user_id: str, since: datetime) -> list[WorkoutSample]:
    rows = session.execute(
        select(Workout.id, Workout.occurred_at, Workout.distance_km, Workout.duration_minutes)
        .where(Workout.user_id == user_id, Workout.occurred_at >= since)
        .order_by(Workout.occurred_at.desc())
    ).all()
    workout_ids = [str(row.id) for row in rows]

    category_rows = session.execute(
        select(WorkoutCategoryLink.workout_id, WorkoutCategory.slug)
        .join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id)
        .where(WorkoutCategoryLink.workout_id.in_([row.id for row in rows]))
    ).all()
    categories_by_workout: dict[str, list[str]] = {workout_id: [] for workout_id in workout_ids}
    for category_row in category_rows:
        categories_by_workout[str(category_row.workout_id)].append(category_row.slug)

    return [
        WorkoutSample(
            id=str(row.id),
            occurred_at=(
                row.occurred_at
                if row.occurred_at.tzinfo is not None
                else row.occurred_at.replace(tzinfo=UTC)
            ),
            distance_km=float(row.distance_km) if row.distance_km is not None else None,
            duration_minutes=row.duration_minutes,
            category_slugs=tuple(categories_by_workout.get(str(row.id), [])),
        )
        for row in rows
    ]


@router.get("/me", response_model=AthleteAnalyticsResponse)
def get_my_analytics(
    user: CurrentUser,
    session: DatabaseSession,
    range_days: Annotated[int, Query(alias="range", ge=7, le=365)] = DEFAULT_RANGE_DAYS,
) -> AthleteAnalyticsResponse:
    set_request_user(session, user.id)
    now = datetime.now(UTC)
    since = now - timedelta(days=range_days)

    samples = load_samples(session, user.id, since)

    active_slugs = list(
        session.scalars(
            select(WorkoutCategory.slug)
            .where(WorkoutCategory.active.is_(True))
            .order_by(WorkoutCategory.category_group, WorkoutCategory.name)
        )
    )

    coverage = category_coverage(samples, active_slugs, now, range_days)
    running = running_summary(samples, now, range_days)

    data_note = None
    if len(samples) < MIN_SAMPLES_FOR_TRENDS:
        data_note = "Not enough logged workouts yet to show reliable trends."

    return AthleteAnalyticsResponse(
        range_days=range_days,
        generated_at=now,
        consistency=ConsistencyResponse(
            sessions_last_7_days=sessions_in_window(samples, now),
            active_days_last_7_days=active_days_in_window(samples, now),
        ),
        category_coverage=coverage,
        running=RunningAnalyticsResponse(
            weekly_distance_km=running.weekly_distance_km,
            avg_pace_seconds_per_km=running.avg_pace_seconds_per_km,
            best_5k_seconds=running.best_5k_seconds,
            recent=[
                RunningSampleResponse(
                    id=sample.id,
                    occurred_at=sample.occurred_at,
                    distance_km=sample.distance_km,
                    pace_seconds_per_km=sample.pace_seconds_per_km,
                )
                for sample in running.recent
            ],
        ),
        data_note=data_note,
    )
