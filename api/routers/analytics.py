from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import AthleteProfile, TeamMembership, WorkoutCategory
from api.schemas.analytics import (
    AthleteAnalyticsResponse,
    ConsistencyResponse,
    ExercisePointResponse,
    ExerciseProgressionResponse,
    PersonalBestResponse,
    RaceDemandCoverageResponse,
    RunningAnalyticsResponse,
    RunningContextResponse,
    RunningSampleResponse,
    SimulationRecordResponse,
    StationComparisonResponse,
    StationSplitResponse,
    TeamAnalyticsResponse,
    TeamAthleteSummary,
)
from api.services.analytics import (
    ExerciseProgression,
    PersonalBest,
    RunningSummary,
    WorkoutSample,
    active_days_in_window,
    category_coverage,
    exercise_progression,
    joint_session_count,
    load_exercise_samples,
    load_samples,
    load_team_exercise_samples,
    load_team_samples,
    personal_bests,
    race_demand_coverage,
    running_summary,
    running_summary_by_context,
    sessions_in_window,
    simulation_history,
    station_metric_history,
    team_station_comparison,
)
from api.services.teams import team_roster_user_ids

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]

DEFAULT_RANGE_DAYS = 28
MIN_SAMPLES_FOR_TRENDS = 2


def running_response(running: RunningSummary) -> RunningAnalyticsResponse:
    return RunningAnalyticsResponse(
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
    )


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
    demand_coverage = race_demand_coverage(coverage)
    running = running_summary(samples, now, range_days)
    running_context = running_summary_by_context(samples, now, range_days)

    exercise_samples = load_exercise_samples(session, [user.id], since)
    progressions = exercise_progression(exercise_samples)
    stations = station_metric_history(exercise_samples)
    bests = personal_bests(exercise_samples)
    simulations = simulation_history(samples, exercise_samples)

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
        race_demand_coverage=RaceDemandCoverageResponse(
            trained_weight_pct=demand_coverage.trained_weight_pct,
            untrained_categories=demand_coverage.untrained_categories,
        ),
        running=running_response(running),
        running_by_context=RunningContextResponse(
            fresh=running_response(running_context.fresh),
            compromised=running_response(running_context.compromised),
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
        simulation_history=[
            SimulationRecordResponse(
                workout_id=record.workout_id,
                occurred_at=record.occurred_at,
                total_duration_minutes=record.total_duration_minutes,
                station_splits=[
                    StationSplitResponse(
                        exercise_key=split.exercise_key,
                        exercise_name=split.exercise_name,
                        duration_seconds=split.duration_seconds,
                        distance_m=split.distance_m,
                        notes=split.notes,
                    )
                    for split in record.station_splits
                ],
            )
            for record in simulations
        ],
        data_note=data_note,
    )


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
    exercise_samples_by_user = load_team_exercise_samples(session, team_id, user.id, since)

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
                running=running_response(running),
                category_coverage=member_coverage,
            )
        )

    combined_coverage = category_coverage(all_samples, active_slugs, now, range_days)
    neglected = [slug for slug, count in combined_coverage.items() if count == 0]

    bests_by_user: dict[str, list[PersonalBest]] = {
        member_id: personal_bests(exercise_samples_by_user.get(member_id, []))
        for member_id in member_ids
    }
    station_comparison, shared_station_gaps = team_station_comparison(bests_by_user)
    joint_sessions = joint_session_count(samples_by_user, now, range_days)

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
        station_comparison=[
            StationComparisonResponse(
                exercise_key=comparison.exercise_key,
                exercise_name=comparison.exercise_name,
                metric=comparison.metric,
                athlete_bests=comparison.athlete_bests,
                stronger_user_id=comparison.stronger_user_id,
            )
            for comparison in station_comparison
        ],
        shared_station_gaps=shared_station_gaps,
        joint_session_count=joint_sessions,
        data_note=data_note,
    )
