from datetime import UTC, date, datetime, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import (
    AthleteProfile,
    CindyResult,
    DailyStep,
    GoalEvent,
    Meal,
    Measurement,
    NutritionTarget,
    TeamMembership,
    Workout,
    WorkoutCategory,
    WorkoutCategoryLink,
)
from api.schemas.coach import CoachInsightData, CoachInsightResponse
from api.services import coach
from api.services.analytics import (
    active_days_in_window,
    category_coverage,
    exercise_progression,
    load_exercise_samples,
    load_samples,
    load_team_visible_samples,
    personal_bests,
    running_summary,
    sessions_in_window,
    station_metric_history,
)
from api.services.cindy import CindyAttempt
from api.services.cindy import change_from_previous as cindy_change_from_previous
from api.services.cindy import personal_best as cindy_personal_best
from api.services.coach_context import (
    CindyContextInputs,
    MeasurementContextInputs,
    NutritionContextInputs,
    PeriodInfo,
    StepsContextInputs,
    TargetEventInfo,
    TeamAthleteSummaryInputs,
    TeamContextInputs,
    assemble_athlete_context,
    assemble_team_context,
)
from api.services.nutrition import MealMacros, daily_totals
from api.services.steps import StepSample, seven_day_average, week_over_week_trend
from api.services.teams import resolve_primary_team_id, team_roster_user_ids

router = APIRouter(prefix="/api/coach", tags=["coach"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]

WINDOW_DAYS = 7
RANGE_DAYS = 28


def _user_timezone(session: Session, user_id: str) -> ZoneInfo:
    timezone_name = session.scalar(
        select(AthleteProfile.timezone).where(AthleteProfile.user_id == user_id)
    )
    try:
        return ZoneInfo(timezone_name) if timezone_name else ZoneInfo("UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _goal_event_info(session: Session, team_id: UUID, today: date) -> TargetEventInfo | None:
    goal_event = session.scalar(select(GoalEvent).where(GoalEvent.team_id == team_id))
    if goal_event is None:
        return None
    return TargetEventInfo(
        name=goal_event.name,
        event_date=goal_event.event_date,
        days_until_event=(goal_event.event_date - today).days,
        division=goal_event.division,
    )


def _nutrition_context(
    session: Session, user_id: str, since_date: date, today: date
) -> NutritionContextInputs:
    since_utc = datetime.combine(since_date, datetime.min.time(), tzinfo=UTC)
    meals = list(
        session.scalars(select(Meal).where(Meal.user_id == user_id, Meal.occurred_at >= since_utc))
    )
    days_logged = len({meal.occurred_at.date() for meal in meals})
    days_in_range = (today - since_date).days + 1

    totals = daily_totals(
        [
            MealMacros(
                calories=meal.calories,
                protein_g=float(meal.protein_g) if meal.protein_g is not None else None,
                carbs_g=float(meal.carbs_g) if meal.carbs_g is not None else None,
                fat_g=float(meal.fat_g) if meal.fat_g is not None else None,
            )
            for meal in meals
        ]
    )
    avg_calories = round(totals.calories / days_logged, 0) if days_logged else None
    estimated_share = (
        round(sum(1 for meal in meals if meal.nutrition_is_estimated) / len(meals), 2)
        if meals
        else None
    )

    target_row = session.scalar(
        select(NutritionTarget)
        .where(NutritionTarget.user_id == user_id, NutritionTarget.effective_from <= today)
        .order_by(NutritionTarget.effective_from.desc())
    )

    return NutritionContextInputs(
        days_logged=days_logged,
        days_in_range=days_in_range,
        avg_calories=avg_calories,
        calories_target=target_row.calories_target if target_row else None,
        estimated_share=estimated_share,
    )


def _steps_context(
    session: Session, user_id: str, since_date: date, today: date
) -> StepsContextInputs:
    samples = [
        StepSample(date=row.date, steps=row.steps)
        for row in session.scalars(
            select(DailyStep).where(
                DailyStep.user_id == user_id, DailyStep.date >= since_date - timedelta(days=7)
            )
        )
    ]
    if not samples:
        return StepsContextInputs(seven_day_average=None, trend_vs_prior_week=None)
    return StepsContextInputs(
        seven_day_average=seven_day_average(samples, today),
        trend_vs_prior_week=week_over_week_trend(samples, today),
    )


def _measurement_context(
    session: Session, user_id: str, since_date: date
) -> MeasurementContextInputs:
    since_utc = datetime.combine(since_date, datetime.min.time(), tzinfo=UTC)
    latest = session.scalar(
        select(Measurement)
        .where(Measurement.user_id == user_id)
        .order_by(Measurement.occurred_at.desc())
        .limit(1)
    )
    baseline = session.scalar(
        select(Measurement)
        .where(Measurement.user_id == user_id, Measurement.occurred_at <= since_utc)
        .order_by(Measurement.occurred_at.desc())
        .limit(1)
    )
    latest_weight = float(latest.weight_kg) if latest and latest.weight_kg is not None else None
    baseline_weight = (
        float(baseline.weight_kg) if baseline and baseline.weight_kg is not None else None
    )
    latest_waist = float(latest.waist_cm) if latest and latest.waist_cm is not None else None
    baseline_waist = (
        float(baseline.waist_cm) if baseline and baseline.waist_cm is not None else None
    )

    return MeasurementContextInputs(
        latest_weight_kg=latest_weight,
        weight_change_kg=(
            round(latest_weight - baseline_weight, 1)
            if latest_weight is not None and baseline_weight is not None
            else None
        ),
        latest_waist_cm=latest_waist,
        waist_change_cm=(
            round(latest_waist - baseline_waist, 1)
            if latest_waist is not None and baseline_waist is not None
            else None
        ),
    )


def _cindy_context(session: Session, user_id: str) -> CindyContextInputs:
    rows = session.execute(
        select(
            Workout.occurred_at,
            CindyResult.full_rounds,
            CindyResult.total_reps,
            CindyResult.total_seconds,
        )
        .join(Workout, Workout.id == CindyResult.workout_id)
        .where(CindyResult.user_id == user_id)
        .order_by(Workout.occurred_at)
    ).all()
    attempts = [
        CindyAttempt(
            completed_at=row.occurred_at,
            full_rounds=row.full_rounds,
            total_reps=row.total_reps,
            total_seconds=row.total_seconds,
        )
        for row in rows
    ]
    return CindyContextInputs(
        latest=attempts[-1] if attempts else None,
        personal_best=cindy_personal_best(attempts),
        change=cindy_change_from_previous(attempts),
        attempts_count=len(attempts),
    )


def _recent_workouts_summary(
    session: Session, user_id: str, since: datetime, limit: int = 10
) -> list[dict]:
    rows = list(
        session.scalars(
            select(Workout)
            .where(Workout.user_id == user_id, Workout.occurred_at >= since)
            .order_by(Workout.occurred_at.desc())
            .limit(limit)
        )
    )
    workout_ids = [row.id for row in rows]
    categories: dict[UUID, list[str]] = {}
    if workout_ids:
        category_rows = session.execute(
            select(WorkoutCategoryLink.workout_id, WorkoutCategory.slug)
            .join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id)
            .where(WorkoutCategoryLink.workout_id.in_(workout_ids))
        ).all()
        for row in category_rows:
            categories.setdefault(row.workout_id, []).append(row.slug)

    return [
        {
            "id": str(workout.id),
            "occurred_at": workout.occurred_at.date().isoformat(),
            "title": workout.title,
            "activity_type": workout.activity_type,
            "category_slugs": categories.get(workout.id, []),
            "duration_minutes": workout.duration_minutes,
            "distance_km": (
                float(workout.distance_km) if workout.distance_km is not None else None
            ),
            "rpe": workout.rpe,
        }
        for workout in rows
    ]


def _active_category_slugs(session: Session) -> list[str]:
    return list(
        session.scalars(
            select(WorkoutCategory.slug)
            .where(WorkoutCategory.active.is_(True))
            .order_by(WorkoutCategory.category_group, WorkoutCategory.name)
        )
    )


def _build_weekly_context(session: Session, user_id: str, team_id: UUID) -> tuple[dict, date, date]:
    tz = _user_timezone(session, user_id)
    today = datetime.now(tz).date()
    since_date = today - timedelta(days=WINDOW_DAYS - 1)
    range_since_utc = datetime.now(UTC) - timedelta(days=RANGE_DAYS)
    now = datetime.now(UTC)

    profile = session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user_id))
    display_name = profile.display_name if profile else "Athlete"
    baseline_5k = profile.baseline_5k_seconds if profile else None

    samples = load_samples(session, user_id, range_since_utc)
    active_slugs = _active_category_slugs(session)
    coverage = category_coverage(samples, active_slugs, now, WINDOW_DAYS)
    running = running_summary(samples, now, RANGE_DAYS)

    exercise_samples = load_exercise_samples(session, [user_id], range_since_utc)
    stations = station_metric_history(exercise_samples)
    strength = exercise_progression(exercise_samples)
    bests = personal_bests(exercise_samples)

    context = assemble_athlete_context(
        display_name=display_name,
        baseline_5k_seconds=baseline_5k,
        period=PeriodInfo(scope="weekly", start=since_date, end=today),
        target_event=_goal_event_info(session, team_id, today),
        recent_workouts=_recent_workouts_summary(
            session, user_id, datetime.combine(since_date, datetime.min.time(), tzinfo=UTC)
        ),
        weekly_sessions=sessions_in_window(samples, now, WINDOW_DAYS),
        weekly_active_days=active_days_in_window(samples, now, WINDOW_DAYS),
        category_coverage_counts=coverage,
        running=running,
        station_progressions=stations,
        strength_progressions=strength,
        personal_bests=bests,
        nutrition=_nutrition_context(session, user_id, since_date, today),
        steps=_steps_context(session, user_id, since_date, today),
        measurements=_measurement_context(session, user_id, since_date),
        cindy=_cindy_context(session, user_id),
    )
    return context, since_date, today


def _build_workout_context(session: Session, workout: Workout, team_id: UUID) -> dict:
    tz = _user_timezone(session, workout.user_id)
    today = datetime.now(tz).date()
    range_since_utc = datetime.now(UTC) - timedelta(days=RANGE_DAYS)
    now = datetime.now(UTC)

    profile = session.scalar(
        select(AthleteProfile).where(AthleteProfile.user_id == workout.user_id)
    )
    display_name = profile.display_name if profile else "Athlete"
    baseline_5k = profile.baseline_5k_seconds if profile else None

    focus_category_slugs = list(
        session.scalars(
            select(WorkoutCategory.slug)
            .join(WorkoutCategoryLink, WorkoutCategoryLink.category_id == WorkoutCategory.id)
            .where(WorkoutCategoryLink.workout_id == workout.id)
        )
    )
    focus_workout = {
        "id": str(workout.id),
        "occurred_at": workout.occurred_at.date().isoformat(),
        "title": workout.title,
        "activity_type": workout.activity_type,
        "category_slugs": focus_category_slugs,
        "duration_minutes": workout.duration_minutes,
        "distance_km": float(workout.distance_km) if workout.distance_km is not None else None,
        "rpe": workout.rpe,
        "source": workout.source,
        "is_focus_workout": True,
    }

    samples = load_samples(session, workout.user_id, range_since_utc)
    active_slugs = _active_category_slugs(session)
    coverage = category_coverage(samples, active_slugs, now, WINDOW_DAYS)
    running = running_summary(samples, now, RANGE_DAYS)

    exercise_samples = load_exercise_samples(session, [workout.user_id], range_since_utc)
    stations = station_metric_history(exercise_samples)
    strength = exercise_progression(exercise_samples)
    bests = personal_bests(exercise_samples)

    other_recent = [
        item
        for item in _recent_workouts_summary(session, workout.user_id, range_since_utc, limit=10)
        if item["id"] != str(workout.id)
    ]

    return assemble_athlete_context(
        display_name=display_name,
        baseline_5k_seconds=baseline_5k,
        period=PeriodInfo(scope="workout", start=None, end=None),
        target_event=_goal_event_info(session, team_id, today),
        recent_workouts=[focus_workout, *other_recent[:9]],
        weekly_sessions=sessions_in_window(samples, now, WINDOW_DAYS),
        weekly_active_days=active_days_in_window(samples, now, WINDOW_DAYS),
        category_coverage_counts=coverage,
        running=running,
        station_progressions=stations,
        strength_progressions=strength,
        personal_bests=bests,
    )


def _build_team_weekly_context(session: Session, team_id: UUID) -> tuple[dict, date, date]:
    today = datetime.now(UTC).date()
    since_date = today - timedelta(days=WINDOW_DAYS - 1)
    range_since_utc = datetime.now(UTC) - timedelta(days=RANGE_DAYS)
    now = datetime.now(UTC)

    active_slugs = _active_category_slugs(session)
    samples_by_user = load_team_visible_samples(session, team_id, range_since_utc)
    member_ids = team_roster_user_ids(session, team_id)
    display_names = dict(
        session.execute(
            select(AthleteProfile.user_id, AthleteProfile.display_name).where(
                AthleteProfile.user_id.in_(member_ids)
            )
        ).all()
    )

    athlete_inputs: list[TeamAthleteSummaryInputs] = []
    all_samples = []
    for member_id in member_ids:
        member_samples = samples_by_user.get(member_id, [])
        if not member_samples:
            continue
        all_samples.extend(member_samples)
        athlete_inputs.append(
            TeamAthleteSummaryInputs(
                display_name=display_names.get(member_id) or "Athlete",
                weekly_sessions=sessions_in_window(member_samples, now, WINDOW_DAYS),
                running=running_summary(member_samples, now, RANGE_DAYS),
                category_coverage_counts=category_coverage(
                    member_samples, active_slugs, now, WINDOW_DAYS
                ),
            )
        )

    combined_coverage = category_coverage(all_samples, active_slugs, now, WINDOW_DAYS)

    context = assemble_team_context(
        TeamContextInputs(
            period=PeriodInfo(scope="team_weekly", start=since_date, end=today),
            target_event=_goal_event_info(session, team_id, today),
            athletes=athlete_inputs,
            combined_category_coverage=combined_coverage,
        )
    )
    return context, since_date, today


def _response(insight) -> CoachInsightResponse:  # noqa: ANN001
    return CoachInsightResponse(
        id=insight.id,
        scope=insight.scope,
        user_id=insight.user_id,
        team_id=insight.team_id,
        period_start=insight.period_start,
        period_end=insight.period_end,
        source_record_id=insight.source_record_id,
        coach_version=insight.coach_version,
        model_name=insight.model_name,
        insight=CoachInsightData.model_validate(insight.insight_json),
        created_at=insight.created_at,
    )


@router.post(
    "/workout/{workout_id}",
    response_model=CoachInsightResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_workout_insight(
    workout_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> CoachInsightResponse:
    set_request_user(session, user.id)
    workout = session.get(Workout, workout_id)
    if workout is None or workout.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found.")

    context = _build_workout_context(session, workout, workout.team_id)
    insight = coach.generate_insight(
        session,
        scope="workout",
        user_id=user.id,
        team_id=workout.team_id,
        period_start=None,
        period_end=None,
        source_record_id=workout.id,
        context=context,
        reuse_cached=False,
    )
    session.commit()
    return _response(insight)


@router.get("/weekly", response_model=CoachInsightResponse)
def get_weekly_review(
    user: CurrentUser,
    session: DatabaseSession,
) -> CoachInsightResponse:
    set_request_user(session, user.id)
    team_id = resolve_primary_team_id(session, user.id)

    context, period_start, period_end = _build_weekly_context(session, user.id, team_id)
    insight = coach.generate_insight(
        session,
        scope="weekly",
        user_id=user.id,
        team_id=team_id,
        period_start=period_start,
        period_end=period_end,
        source_record_id=None,
        context=context,
        reuse_cached=True,
    )
    session.commit()
    return _response(insight)


@router.get("/team/{team_id}/weekly", response_model=CoachInsightResponse)
def get_team_weekly_review(
    team_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> CoachInsightResponse:
    set_request_user(session, user.id)
    membership = session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    context, period_start, period_end = _build_team_weekly_context(session, team_id)
    insight = coach.generate_insight(
        session,
        scope="team_weekly",
        user_id=None,
        team_id=team_id,
        period_start=period_start,
        period_end=period_end,
        source_record_id=None,
        context=context,
        reuse_cached=True,
    )
    session.commit()
    return _response(insight)
