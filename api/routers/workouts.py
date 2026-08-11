from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import (
    ExercisePerformance,
    Workout,
    WorkoutCategory,
    WorkoutCategoryLink,
)
from api.schemas.workouts import (
    ExercisePerformanceCreate,
    ExercisePerformanceResponse,
    WorkoutCategoryResponse,
    WorkoutCreate,
    WorkoutResponse,
    WorkoutUpdate,
)
from api.services.teams import active_team_ids, resolve_primary_team_id

router = APIRouter(prefix="/api", tags=["workouts"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def resolve_category_ids(session: Session, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    categories = session.execute(
        select(WorkoutCategory.id, WorkoutCategory.slug).where(
            WorkoutCategory.slug.in_(slugs), WorkoutCategory.active.is_(True)
        )
    ).all()
    found_slugs = {row.slug for row in categories}
    unknown = sorted(set(slugs) - found_slugs)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown workout category slugs: {', '.join(unknown)}.",
        )
    return [row.id for row in categories]


def category_slugs_by_workout(
    session: Session, workout_ids: list[UUID]
) -> dict[UUID, list[str]]:
    if not workout_ids:
        return {}
    rows = session.execute(
        select(WorkoutCategoryLink.workout_id, WorkoutCategory.slug)
        .join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id)
        .where(WorkoutCategoryLink.workout_id.in_(workout_ids))
    ).all()
    grouped: dict[UUID, list[str]] = {workout_id: [] for workout_id in workout_ids}
    for row in rows:
        grouped[row.workout_id].append(row.slug)
    return grouped


def workout_response(
    workout: Workout,
    category_slugs: list[str],
    performances: list[ExercisePerformance] | None = None,
) -> WorkoutResponse:
    return WorkoutResponse(
        id=workout.id,
        user_id=workout.user_id,
        team_id=workout.team_id,
        occurred_at=workout.occurred_at,
        title=workout.title,
        activity_type=workout.activity_type,
        category_slugs=category_slugs,
        duration_minutes=workout.duration_minutes,
        distance_km=workout.distance_km,
        rpe=workout.rpe,
        notes=workout.notes,
        visibility=workout.visibility,  # type: ignore[arg-type]
        source=workout.source,  # type: ignore[arg-type]
        performances=[
            ExercisePerformanceResponse.model_validate(performance)
            for performance in (performances or [])
        ],
        created_at=workout.created_at,
        updated_at=workout.updated_at,
    )


def require_ownership(workout: Workout, user: AuthenticatedUser) -> None:
    if workout.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")


def can_view(workout: Workout, user: AuthenticatedUser, team_ids: list[UUID]) -> bool:
    if workout.user_id == user.id:
        return True
    return workout.visibility == "team" and workout.team_id in team_ids


def load_workout_or_404(session: Session, workout_id: UUID) -> Workout:
    workout = session.get(Workout, workout_id, options=[selectinload(Workout.performances)])
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")
    return workout


def load_viewable_workout_or_404(
    session: Session, workout_id: UUID, user: AuthenticatedUser
) -> Workout:
    workout = load_workout_or_404(session, workout_id)
    if not can_view(workout, user, active_team_ids(session, user.id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")
    return workout


def load_owned_workout_or_404(
    session: Session, workout_id: UUID, user: AuthenticatedUser
) -> Workout:
    workout = load_workout_or_404(session, workout_id)
    require_ownership(workout, user)
    return workout


@router.get("/workout-categories", response_model=list[WorkoutCategoryResponse])
def list_workout_categories(
    user: CurrentUser,
    session: DatabaseSession,
) -> list[WorkoutCategoryResponse]:
    set_request_user(session, user.id)
    categories = session.scalars(
        select(WorkoutCategory)
        .where(WorkoutCategory.active.is_(True))
        .order_by(WorkoutCategory.category_group, WorkoutCategory.name)
    ).all()
    return [WorkoutCategoryResponse.model_validate(category) for category in categories]


@router.post("/workouts", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: WorkoutCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> WorkoutResponse:
    set_request_user(session, user.id)
    team_id = resolve_primary_team_id(session, user.id)
    category_ids = resolve_category_ids(session, payload.category_slugs)

    workout = Workout(
        user_id=user.id,
        team_id=team_id,
        occurred_at=payload.occurred_at,
        title=payload.title,
        activity_type=payload.activity_type,
        duration_minutes=payload.duration_minutes,
        distance_km=Decimal(str(payload.distance_km)) if payload.distance_km is not None else None,
        rpe=payload.rpe,
        notes=payload.notes,
        visibility=payload.visibility,
    )
    session.add(workout)
    session.flush()

    for category_id in category_ids:
        session.add(WorkoutCategoryLink(workout_id=workout.id, category_id=category_id))

    session.commit()
    session.refresh(workout)
    return workout_response(workout, payload.category_slugs)


@router.get("/workouts", response_model=list[WorkoutResponse])
def list_workouts(
    user: CurrentUser,
    session: DatabaseSession,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    category: str | None = None,
    athlete: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[WorkoutResponse]:
    set_request_user(session, user.id)
    team_ids = active_team_ids(session, user.id)

    conditions = [
        (Workout.user_id == user.id)
        | ((Workout.visibility == "team") & Workout.team_id.in_(team_ids))
    ]
    if from_date is not None:
        conditions.append(Workout.occurred_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date is not None:
        conditions.append(Workout.occurred_at <= datetime.combine(to_date, datetime.max.time()))
    if athlete is not None:
        conditions.append(Workout.user_id == athlete)

    query = select(Workout).where(*conditions)
    if category is not None:
        query = query.join(
            WorkoutCategoryLink, WorkoutCategoryLink.workout_id == Workout.id
        ).join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id).where(
            WorkoutCategory.slug == category
        )

    query = query.order_by(Workout.occurred_at.desc()).limit(limit)
    workouts = session.scalars(query).all()

    category_map = category_slugs_by_workout(session, [workout.id for workout in workouts])
    return [
        workout_response(workout, category_map.get(workout.id, []))
        for workout in workouts
    ]


@router.get("/workouts/{workout_id}", response_model=WorkoutResponse)
def get_workout(
    workout_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> WorkoutResponse:
    set_request_user(session, user.id)
    workout = load_viewable_workout_or_404(session, workout_id, user)
    category_map = category_slugs_by_workout(session, [workout.id])
    return workout_response(
        workout, category_map.get(workout.id, []), list(workout.performances)
    )


@router.patch("/workouts/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: UUID,
    payload: WorkoutUpdate,
    user: CurrentUser,
    session: DatabaseSession,
) -> WorkoutResponse:
    set_request_user(session, user.id)
    workout = load_owned_workout_or_404(session, workout_id, user)

    if payload.occurred_at is not None:
        workout.occurred_at = payload.occurred_at
    if payload.title is not None:
        workout.title = payload.title
    if payload.activity_type is not None:
        workout.activity_type = payload.activity_type
    if payload.duration_minutes is not None:
        workout.duration_minutes = payload.duration_minutes
    if payload.distance_km is not None:
        workout.distance_km = Decimal(str(payload.distance_km))
    if payload.rpe is not None:
        workout.rpe = payload.rpe
    if payload.notes is not None:
        workout.notes = payload.notes
    if payload.visibility is not None:
        workout.visibility = payload.visibility

    category_slugs: list[str] | None = None
    if payload.category_slugs is not None:
        category_ids = resolve_category_ids(session, payload.category_slugs)
        session.query(WorkoutCategoryLink).filter(
            WorkoutCategoryLink.workout_id == workout.id
        ).delete()
        for category_id in category_ids:
            session.add(WorkoutCategoryLink(workout_id=workout.id, category_id=category_id))
        category_slugs = payload.category_slugs

    session.commit()
    session.refresh(workout)

    if category_slugs is None:
        category_slugs = category_slugs_by_workout(session, [workout.id]).get(workout.id, [])

    return workout_response(workout, category_slugs, list(workout.performances))


@router.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> None:
    set_request_user(session, user.id)
    workout = load_owned_workout_or_404(session, workout_id, user)
    session.delete(workout)
    session.commit()


@router.post(
    "/workouts/{workout_id}/performances",
    response_model=ExercisePerformanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_exercise_performance(
    workout_id: UUID,
    payload: ExercisePerformanceCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> ExercisePerformanceResponse:
    set_request_user(session, user.id)
    workout = load_owned_workout_or_404(session, workout_id, user)

    performance = ExercisePerformance(
        workout_id=workout.id,
        exercise_name=payload.exercise_name,
        normalized_exercise_key=payload.normalized_exercise_key,
        sequence_no=payload.sequence_no,
        sets=payload.sets,
        reps=payload.reps,
        load_kg=Decimal(str(payload.load_kg)) if payload.load_kg is not None else None,
        distance_m=Decimal(str(payload.distance_m)) if payload.distance_m is not None else None,
        duration_seconds=payload.duration_seconds,
        pace_seconds_per_km=(
            Decimal(str(payload.pace_seconds_per_km))
            if payload.pace_seconds_per_km is not None
            else None
        ),
        calories=payload.calories,
        rpe=payload.rpe,
        performance_metadata=payload.metadata,
        notes=payload.notes,
    )
    session.add(performance)
    session.commit()
    session.refresh(performance)
    return ExercisePerformanceResponse.model_validate(performance)
