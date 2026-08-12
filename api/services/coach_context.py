"""Deterministic CoachContext assembly for Phase 7 (AI_COACH.md #3).

Pure functions over already-computed values so the shape sent to the model
is unit-testable without a database, mirroring api/services/analytics.py's
split between DB-loading (left to the router/coach service) and aggregation
(here). CLAUDE.md rule 2: the model interprets these numbers, it never
derives them.

Team-scope context is privacy-sensitive: a team_weekly insight has no single
owning user (user_id is null) and may be read by either teammate later, so
it must only ever aggregate visibility='team' records — never a caller's own
private data — even though this module trusts its caller to have already
filtered accordingly (see api/services/coach.py).
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from api.services.analytics import ExerciseProgression, PersonalBest, RunningSummary
from api.services.cindy import AttemptChange, CindyAttempt


@dataclass(frozen=True)
class PeriodInfo:
    scope: str
    start: date | None
    end: date | None


@dataclass(frozen=True)
class TargetEventInfo:
    name: str
    event_date: date
    days_until_event: int
    division: str | None


@dataclass(frozen=True)
class NutritionContextInputs:
    days_logged: int
    days_in_range: int
    avg_calories: float | None
    calories_target: int | None
    estimated_share: float | None


@dataclass(frozen=True)
class StepsContextInputs:
    seven_day_average: float | None
    trend_vs_prior_week: int | None


@dataclass(frozen=True)
class MeasurementContextInputs:
    latest_weight_kg: float | None
    weight_change_kg: float | None
    latest_waist_cm: float | None
    waist_change_cm: float | None


@dataclass(frozen=True)
class CindyContextInputs:
    latest: CindyAttempt | None
    personal_best: CindyAttempt | None
    change: AttemptChange | None
    attempts_count: int


def _period_dict(period: PeriodInfo) -> dict[str, Any]:
    return {
        "scope": period.scope,
        "start": period.start.isoformat() if period.start else None,
        "end": period.end.isoformat() if period.end else None,
    }


def _target_event_dict(target_event: TargetEventInfo | None) -> dict[str, Any] | None:
    if target_event is None:
        return None
    return {
        "name": target_event.name,
        "event_date": target_event.event_date.isoformat(),
        "days_until_event": target_event.days_until_event,
        "division": target_event.division,
    }


def _progression_dict(progression: ExerciseProgression) -> dict[str, Any]:
    latest = progression.points[0] if progression.points else None
    return {
        "exercise_key": progression.exercise_key,
        "exercise_name": progression.exercise_name,
        "primary_metric": progression.primary_metric,
        "trend": progression.trend,
        "sample_count": len(progression.points),
        "latest_value": getattr(latest, progression.primary_metric) if latest else None,
    }


def _personal_best_dict(best: PersonalBest) -> dict[str, Any]:
    return {
        "exercise_key": best.exercise_key,
        "exercise_name": best.exercise_name,
        "metric": best.metric,
        "best_value": best.best_value,
        "achieved_at": best.achieved_at.date().isoformat(),
        "is_current": best.is_current,
    }


def _running_dict(running: RunningSummary) -> dict[str, Any]:
    return {
        "weekly_distance_km": running.weekly_distance_km,
        "avg_pace_seconds_per_km": running.avg_pace_seconds_per_km,
        "best_5k_seconds": running.best_5k_seconds,
        "recent_session_count": len(running.recent),
    }


def _cindy_dict(cindy: CindyContextInputs) -> dict[str, Any]:
    return {
        "attempts_count": cindy.attempts_count,
        "latest_total_reps": cindy.latest.total_reps if cindy.latest else None,
        "latest_total_seconds": cindy.latest.total_seconds if cindy.latest else None,
        "personal_best_total_reps": cindy.personal_best.total_reps if cindy.personal_best else None,
        "change_total_reps": cindy.change.total_reps_change if cindy.change else None,
    }


def assemble_athlete_context(
    *,
    display_name: str,
    baseline_5k_seconds: int | None,
    period: PeriodInfo,
    target_event: TargetEventInfo | None,
    recent_workouts: list[dict[str, Any]],
    weekly_sessions: int,
    weekly_active_days: int,
    category_coverage_counts: dict[str, int],
    running: RunningSummary,
    station_progressions: list[ExerciseProgression],
    strength_progressions: list[ExerciseProgression],
    personal_bests: list[PersonalBest],
    nutrition: NutritionContextInputs | None = None,
    steps: StepsContextInputs | None = None,
    measurements: MeasurementContextInputs | None = None,
    cindy: CindyContextInputs | None = None,
) -> dict[str, Any]:
    """Builds the per-athlete CoachContext for workout/weekly scopes.

    nutrition/steps/measurements/cindy are optional: a workout-scope insight
    may omit them entirely (None) rather than passing a fabricated all-null
    reading as if it were a real query result — None means "not queried for
    this scope", not "queried and found nothing" (CLAUDE.md rule 1).
    """
    neglected = [slug for slug, count in category_coverage_counts.items() if count == 0]

    notes: list[str] = []
    if weekly_sessions == 0:
        notes.append("No workouts logged in the last 7 days.")
    if nutrition is not None:
        if nutrition.days_logged == 0:
            notes.append("No meals logged in the last 7 days.")
        elif nutrition.days_logged < nutrition.days_in_range:
            notes.append(
                f"Nutrition logged on {nutrition.days_logged} of "
                f"{nutrition.days_in_range} recent days — treat averages as partial."
            )
    if target_event is None:
        notes.append("No target event configured yet.")
    if not personal_bests:
        notes.append("Not enough exercise history yet to detect personal bests.")

    return {
        "target_event": _target_event_dict(target_event),
        "athlete": {
            "display_name": display_name,
            "baseline_5k_seconds": baseline_5k_seconds,
        },
        "period": _period_dict(period),
        "recent_workouts": recent_workouts,
        "weekly_metrics": {
            "sessions": weekly_sessions,
            "active_days": weekly_active_days,
            "category_coverage": category_coverage_counts,
            "neglected_categories": neglected,
        },
        "running_metrics": _running_dict(running),
        "station_metrics": {
            "progressions": [_progression_dict(item) for item in station_progressions]
        },
        "strength_metrics": {
            "progressions": [_progression_dict(item) for item in strength_progressions],
            "personal_bests": [_personal_best_dict(item) for item in personal_bests],
        },
        "meal_metrics": (
            {
                "days_logged": nutrition.days_logged,
                "days_in_range": nutrition.days_in_range,
                "avg_calories": nutrition.avg_calories,
                "calories_target": nutrition.calories_target,
                "estimated_share": nutrition.estimated_share,
            }
            if nutrition is not None
            else None
        ),
        "steps_metrics": (
            {
                "seven_day_average": steps.seven_day_average,
                "trend_vs_prior_week": steps.trend_vs_prior_week,
            }
            if steps is not None
            else None
        ),
        "measurement_trends": (
            {
                "latest_weight_kg": measurements.latest_weight_kg,
                "weight_change_kg": measurements.weight_change_kg,
                "latest_waist_cm": measurements.latest_waist_cm,
                "waist_change_cm": measurements.waist_change_cm,
            }
            if measurements is not None
            else None
        ),
        "cindy_metrics": _cindy_dict(cindy) if cindy is not None else None,
        "team_comparison": None,
        "data_quality": {"notes": notes},
    }


@dataclass(frozen=True)
class TeamAthleteSummaryInputs:
    display_name: str
    weekly_sessions: int
    running: RunningSummary
    category_coverage_counts: dict[str, int]


@dataclass(frozen=True)
class TeamContextInputs:
    period: PeriodInfo
    target_event: TargetEventInfo | None
    athletes: list[TeamAthleteSummaryInputs] = field(default_factory=list)
    combined_category_coverage: dict[str, int] = field(default_factory=dict)


def assemble_team_context(inputs: TeamContextInputs) -> dict[str, Any]:
    """Builds the team_weekly CoachContext. Only ever fed visibility='team'
    aggregates by the caller — see module docstring."""
    neglected = [
        slug for slug, count in inputs.combined_category_coverage.items() if count == 0
    ]

    notes: list[str] = []
    if not inputs.athletes:
        notes.append("No shared team-visible workouts logged yet.")
    if inputs.target_event is None:
        notes.append("No target event configured yet.")
    if len(inputs.athletes) < 2:
        notes.append("Only one athlete has team-visible activity this period.")

    return {
        "target_event": _target_event_dict(inputs.target_event),
        "period": _period_dict(inputs.period),
        "athletes": [
            {
                "display_name": athlete.display_name,
                "weekly_sessions": athlete.weekly_sessions,
                "running": _running_dict(athlete.running),
                "category_coverage": athlete.category_coverage_counts,
            }
            for athlete in inputs.athletes
        ],
        "combined_category_coverage": inputs.combined_category_coverage,
        "neglected_categories": neglected,
        "data_quality": {"notes": notes},
    }
