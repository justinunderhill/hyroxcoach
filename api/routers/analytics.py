from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import (
    AthleteProfile,
    ExercisePerformance,
    TeamMembership,
    Workout,
    WorkoutCategory,
    WorkoutCategoryLink,
)
from api.schemas.analytics import (
    AthleteAnalyticsResponse,
    ConsistencyResponse,
    ExercisePointResponse,
    ExerciseProgressionResponse,
    PersonalBestResponse,
    RunningAnalyticsResponse,
    RunningSampleResponse,
    TeamAnalyticsResponse,
    TeamAthleteSummary,
)
from api.services.analytics import (
    ExercisePerformanceSample,
    ExerciseProgression,
    WorkoutSample,
    active_days_in_window,
    category_coverage,
    exercise_progression,
    personal_bests,
    running_summary,
    sessions_in_window,
    station_metric_history,
)
from api.services.teams import team_roster_user_ids

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


def load_exercise_samples(
    session: Session, user_ids: list[str], since: datetime
) -> list[ExercisePerformanceSample]:
    rows = session.execute(
        select(
            ExercisePerformance.id,
            ExercisePerformance.exercise_name,
            ExercisePerformance.normalized_exercise_key,
            ExercisePerformance.load_kg,
            ExercisePerformance.reps,
            ExercisePerformance.duration_seconds,
            ExercisePerformance.distance_m,
            Workout.occurred_at,
        )
        .join(Workout, Workout.id == ExercisePerformance.workout_id)
        .where(Workout.user_id.in_(user_ids), Workout.occurred_at >= since)
    ).all()

    return [
        ExercisePerformanceSample(
            id=str(row.id),
            occurred_at=(
                row.occurred_at
                if row.occurred_at.tzinfo is not None
                else row.occurred_at.replace(tzinfo=UTC)
            ),
            exercise_key=(row.normalized_exercise_key or row.exercise_name).strip().lower(),
            exercise_name=row.exercise_name,
            load_kg=float(row.load_kg) if row.load_kg is not None else None,
            reps=row.reps,
            duration_seconds=row.duration_seconds,
            distance_m=float(row.distance_m) if row.distance_m is not None else None,
        )
        for row in rows
    ]


def progression_response(
    progressions: list[ExerciseProgression],
) -> list[ExerciseProgressionResponse]:
    return [
        ExerciseProgressionResponse(
            exercise_key=progression.exercise_key,
            exercise_name=progression.exercise_name,
            primary_metric=progression.primary_metric,
            trend=progression.trend,
            points=[
                ExercisePointResponse(
                    id=point.id,
                    occurred_at=point.occurred_at,
                    load_kg=point.load_kg,
                    reps=point.reps,
                    duration_seconds=point.duration_seconds,
                    distance_m=point.distance_m,
                )
                for point in progression.points
            ],
        )
        for progression in progressions
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

    exercise_samples = load_exercise_samples(session, [user.id], since)
    progressions = exercise_progression(exercise_samples)
    stations = station_metric_history(exercise_samples)
    bests = personal_bests(exercise_samples)

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
        exercise_progression=progression_response(progressions),
        station_history=progression_response(stations),
        personal_bests=[
            PersonalBestResponse(
                exercise_key=best.exercise_key,
                exercise_name=best.exercise_name,
                metric=best.metric,
                best_value=best.best_value,
                achieved_at=best.achieved_at,
                is_current=best.is_current,
            )
            for best in bests
        ],
        data_note=data_note,
    )


def load_team_samples(
    session: Session, team_id: UUID, requester_id: str, since: datetime
) -> dict[str, list[WorkoutSample]]:
    rows = session.execute(
        select(
            Workout.id,
            Workout.user_id,
            Workout.occurred_at,
            Workout.distance_km,
            Workout.duration_minutes,
        )
        .where(
            Workout.team_id == team_id,
            Workout.occurred_at >= since,
            (Workout.user_id == requester_id) | (Workout.visibility == "team"),
        )
        .order_by(Workout.occurred_at.desc())
    ).all()
    workout_ids = [row.id for row in rows]

    category_rows = (
        session.execute(
            select(WorkoutCategoryLink.workout_id, WorkoutCategory.slug)
            .join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id)
            .where(WorkoutCategoryLink.workout_id.in_(workout_ids))
        ).all()
        if workout_ids
        else []
    )
    categories_by_workout: dict[str, list[str]] = {}
    for category_row in category_rows:
        categories_by_workout.setdefault(str(category_row.workout_id), []).append(category_row.slug)

    by_user: dict[str, list[WorkoutSample]] = {}
    for row in rows:
        by_user.setdefault(row.user_id, []).append(
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
        )
    return by_user


@router.get("/team/{team_id}", response_model=TeamAnalyticsResponse)
def get_team_analytics(
    team_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
    range_days: Annotated[int, Query(alias="range", ge=7, le=365)] = DEFAULT_RANGE_DAYS,
) -> TeamAnalyticsResponse:
    set_request_user(session, user.id)
    now = datetime.now(UTC)
    since = now - timedelta(days=range_days)

    membership = session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    active_slugs = list(
        session.scalars(
            select(WorkoutCategory.slug)
            .where(WorkoutCategory.active.is_(True))
            .order_by(WorkoutCategory.category_group, WorkoutCategory.name)
        )
    )

    samples_by_user = load_team_samples(session, team_id, user.id, since)

    member_ids = team_roster_user_ids(session, team_id)
    display_names = dict(
        session.execute(
            select(AthleteProfile.user_id, AthleteProfile.display_name).where(
                AthleteProfile.user_id.in_(member_ids)
            )
        ).all()
    )

    athletes: list[TeamAthleteSummary] = []
    combined_coverage: dict[str, int] = dict.fromkeys(active_slugs, 0)
    all_samples: list[WorkoutSample] = []

    for member_id in member_ids:
        member_samples = samples_by_user.get(member_id, [])
        all_samples.extend(member_samples)
        member_coverage = category_coverage(member_samples, active_slugs, now, range_days)
        running = running_summary(member_samples, now, range_days)
        athletes.append(
            TeamAthleteSummary(
                user_id=member_id,
                display_name=display_names.get(member_id) or "Athlete",
                consistency=ConsistencyResponse(
                    sessions_last_7_days=sessions_in_window(member_samples, now),
                    active_days_last_7_days=active_days_in_window(member_samples, now),
                ),
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
                category_coverage=member_coverage,
            )
        )

    combined_coverage = category_coverage(all_samples, active_slugs, now, range_days)
    neglected = [slug for slug, count in combined_coverage.items() if count == 0]

    data_note = None
    if not all_samples:
        data_note = "Not enough shared team data yet to show reliable trends."

    return TeamAnalyticsResponse(
        team_id=str(team_id),
        range_days=range_days,
        generated_at=now,
        athletes=athletes,
        combined_category_coverage=combined_coverage,
        neglected_categories=neglected,
        data_note=data_note,
    )
