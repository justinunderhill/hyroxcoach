"""Deterministic analytics aggregators.

All functions here are pure and operate on plain in-memory samples so they
can be unit tested without a database. Canonical values (weekly counts,
pace, coverage) must be computed here rather than left to the LLM per
CLAUDE.md rule 2.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import ExercisePerformance, Workout, WorkoutCategory, WorkoutCategoryLink

WEEK_DAYS = 7
FIVE_K_MIN_KM = 4.9
FIVE_K_MAX_KM = 5.1

# Matches workout_categories.slug for category_group = 'hyrox_station' (see
# migrations/20260812_0004). An exercise_performance is treated as station work
# when its normalized_exercise_key matches one of these.
STATION_EXERCISE_KEYS = {
    "skierg",
    "sled_push",
    "sled_pull",
    "burpee_broad_jumps",
    "row",
    "farmers_carry",
    "sandbag_lunges",
    "wall_balls",
}

MetricType = Literal["load_kg", "duration_seconds", "distance_m", "reps"]
Trend = Literal["improving", "flat", "declining"]

# Lower values are better for time trials; higher is better for the rest.
LOWER_IS_BETTER: set[MetricType] = {"duration_seconds"}
TREND_THRESHOLD = 0.02


@dataclass(frozen=True)
class WorkoutSample:
    id: str
    occurred_at: datetime
    distance_km: float | None
    duration_minutes: int | None
    category_slugs: tuple[str, ...] = field(default_factory=tuple)


def pace_seconds_per_km(duration_minutes: int | None, distance_km: float | None) -> float | None:
    if not duration_minutes or not distance_km:
        return None
    return (duration_minutes * 60) / distance_km


def _within_window(sample: WorkoutSample, now: datetime, days: int) -> bool:
    window_start = now - timedelta(days=days)
    return window_start <= sample.occurred_at <= now


def sessions_in_window(samples: list[WorkoutSample], now: datetime, days: int = WEEK_DAYS) -> int:
    return sum(1 for sample in samples if _within_window(sample, now, days))


def active_days_in_window(
    samples: list[WorkoutSample], now: datetime, days: int = WEEK_DAYS
) -> int:
    distinct_dates = {
        sample.occurred_at.date() for sample in samples if _within_window(sample, now, days)
    }
    return len(distinct_dates)


def category_coverage(
    samples: list[WorkoutSample],
    active_slugs: list[str],
    now: datetime,
    days: int,
) -> dict[str, int]:
    coverage = dict.fromkeys(active_slugs, 0)
    for sample in samples:
        if not _within_window(sample, now, days):
            continue
        for slug in sample.category_slugs:
            if slug in coverage:
                coverage[slug] += 1
    return coverage


@dataclass(frozen=True)
class RunningSample:
    id: str
    occurred_at: datetime
    distance_km: float
    pace_seconds_per_km: float | None


@dataclass(frozen=True)
class RunningSummary:
    weekly_distance_km: float
    avg_pace_seconds_per_km: float | None
    recent: list[RunningSample]
    best_5k_seconds: int | None


def running_summary(
    samples: list[WorkoutSample],
    now: datetime,
    range_days: int,
    recent_limit: int = 10,
) -> RunningSummary:
    running_samples = [sample for sample in samples if sample.distance_km]

    weekly_distance_km = round(
        sum(
            sample.distance_km or 0
            for sample in running_samples
            if _within_window(sample, now, WEEK_DAYS)
        ),
        2,
    )

    paced = [
        (sample, pace_seconds_per_km(sample.duration_minutes, sample.distance_km))
        for sample in running_samples
        if _within_window(sample, now, range_days)
    ]
    known_paces = [pace for _, pace in paced if pace is not None]
    avg_pace = round(sum(known_paces) / len(known_paces), 1) if known_paces else None

    recent = sorted(
        (sample for sample in running_samples if _within_window(sample, now, range_days)),
        key=lambda sample: sample.occurred_at,
        reverse=True,
    )[:recent_limit]
    recent_out = [
        RunningSample(
            id=sample.id,
            occurred_at=sample.occurred_at,
            distance_km=sample.distance_km or 0,
            pace_seconds_per_km=pace_seconds_per_km(sample.duration_minutes, sample.distance_km),
        )
        for sample in recent
    ]

    five_k_candidates = [
        sample.duration_minutes * 60
        for sample in running_samples
        if _within_window(sample, now, range_days)
        and sample.duration_minutes
        and sample.distance_km is not None
        and FIVE_K_MIN_KM <= sample.distance_km <= FIVE_K_MAX_KM
    ]
    best_5k_seconds = min(five_k_candidates) if five_k_candidates else None

    return RunningSummary(
        weekly_distance_km=weekly_distance_km,
        avg_pace_seconds_per_km=avg_pace,
        recent=recent_out,
        best_5k_seconds=best_5k_seconds,
    )


@dataclass(frozen=True)
class ExercisePerformanceSample:
    id: str
    occurred_at: datetime
    exercise_key: str
    exercise_name: str
    load_kg: float | None
    reps: int | None
    duration_seconds: int | None
    distance_m: float | None


@dataclass(frozen=True)
class ExercisePoint:
    id: str
    occurred_at: datetime
    load_kg: float | None
    reps: int | None
    duration_seconds: int | None
    distance_m: float | None


@dataclass(frozen=True)
class ExerciseProgression:
    exercise_key: str
    exercise_name: str
    primary_metric: MetricType
    trend: Trend | None
    points: list[ExercisePoint]


def _primary_metric(points: list[ExercisePoint], min_count: int = 2) -> MetricType:
    for metric in ("load_kg", "duration_seconds", "distance_m", "reps"):
        if sum(1 for point in points if getattr(point, metric) is not None) >= min_count:
            return metric  # type: ignore[return-value]
    return "reps"


def _trend_for_metric(points: list[ExercisePoint], metric: MetricType) -> Trend | None:
    ordered = sorted(points, key=lambda point: point.occurred_at)
    values = [getattr(point, metric) for point in ordered if getattr(point, metric) is not None]
    if len(values) < 2:
        return None

    midpoint = len(values) // 2 or 1
    first_half = values[:midpoint]
    second_half = values[midpoint:] or values[-1:]
    first_avg = sum(first_half) / len(first_half)
    second_avg = sum(second_half) / len(second_half)
    if first_avg == 0:
        return None

    change = (second_avg - first_avg) / abs(first_avg)
    if metric in LOWER_IS_BETTER:
        change = -change

    if change > TREND_THRESHOLD:
        return "improving"
    if change < -TREND_THRESHOLD:
        return "declining"
    return "flat"


def exercise_progression(
    samples: list[ExercisePerformanceSample],
    recent_limit: int = 20,
) -> list[ExerciseProgression]:
    grouped: dict[str, list[ExercisePerformanceSample]] = {}
    for sample in samples:
        grouped.setdefault(sample.exercise_key, []).append(sample)

    results: list[ExerciseProgression] = []
    for exercise_key, exercise_samples in grouped.items():
        ordered = sorted(exercise_samples, key=lambda sample: sample.occurred_at, reverse=True)
        latest_name = ordered[0].exercise_name
        points = [
            ExercisePoint(
                id=sample.id,
                occurred_at=sample.occurred_at,
                load_kg=sample.load_kg,
                reps=sample.reps,
                duration_seconds=sample.duration_seconds,
                distance_m=sample.distance_m,
            )
            for sample in ordered[:recent_limit]
        ]
        metric = _primary_metric(points)
        results.append(
            ExerciseProgression(
                exercise_key=exercise_key,
                exercise_name=latest_name,
                primary_metric=metric,
                trend=_trend_for_metric(points, metric),
                points=points,
            )
        )

    results.sort(key=lambda progression: progression.points[0].occurred_at, reverse=True)
    return results


def station_metric_history(
    samples: list[ExercisePerformanceSample],
    recent_limit: int = 20,
) -> list[ExerciseProgression]:
    station_samples = [sample for sample in samples if sample.exercise_key in STATION_EXERCISE_KEYS]
    return exercise_progression(station_samples, recent_limit=recent_limit)


@dataclass(frozen=True)
class PersonalBest:
    exercise_key: str
    exercise_name: str
    metric: MetricType
    best_value: float
    achieved_at: datetime
    is_current: bool


def _best_value(metric: MetricType, values: list[tuple[datetime, float]]) -> tuple[datetime, float]:
    if metric in LOWER_IS_BETTER:
        return min(values, key=lambda entry: entry[1])
    return max(values, key=lambda entry: entry[1])


def personal_bests(samples: list[ExercisePerformanceSample]) -> list[PersonalBest]:
    grouped: dict[str, list[ExercisePerformanceSample]] = {}
    for sample in samples:
        grouped.setdefault(sample.exercise_key, []).append(sample)

    results: list[PersonalBest] = []
    for exercise_key, exercise_samples in grouped.items():
        points = [
            ExercisePoint(
                id=sample.id,
                occurred_at=sample.occurred_at,
                load_kg=sample.load_kg,
                reps=sample.reps,
                duration_seconds=sample.duration_seconds,
                distance_m=sample.distance_m,
            )
            for sample in exercise_samples
        ]
        metric = _primary_metric(points, min_count=1)
        values = [
            (sample.occurred_at, getattr(sample, metric))
            for sample in exercise_samples
            if getattr(sample, metric) is not None
        ]
        if not values:
            continue

        best_at, best_value = _best_value(metric, values)
        latest_at = max(sample.occurred_at for sample in exercise_samples)
        latest_name = max(exercise_samples, key=lambda sample: sample.occurred_at).exercise_name

        results.append(
            PersonalBest(
                exercise_key=exercise_key,
                exercise_name=latest_name,
                metric=metric,
                best_value=best_value,
                achieved_at=best_at,
                is_current=best_at == latest_at,
            )
        )

    results.sort(key=lambda best: best.achieved_at, reverse=True)
    return results


def _category_slugs_by_workout(
    session: Session, workout_ids: list[UUID]
) -> dict[str, list[str]]:
    if not workout_ids:
        return {}
    category_rows = session.execute(
        select(WorkoutCategoryLink.workout_id, WorkoutCategory.slug)
        .join(WorkoutCategory, WorkoutCategory.id == WorkoutCategoryLink.category_id)
        .where(WorkoutCategoryLink.workout_id.in_(workout_ids))
    ).all()
    grouped: dict[str, list[str]] = {}
    for row in category_rows:
        grouped.setdefault(str(row.workout_id), []).append(row.slug)
    return grouped


def _as_aware(occurred_at: datetime) -> datetime:
    return occurred_at if occurred_at.tzinfo is not None else occurred_at.replace(tzinfo=UTC)


def load_samples(session: Session, user_id: str, since: datetime) -> list[WorkoutSample]:
    rows = session.execute(
        select(Workout.id, Workout.occurred_at, Workout.distance_km, Workout.duration_minutes)
        .where(Workout.user_id == user_id, Workout.occurred_at >= since)
        .order_by(Workout.occurred_at.desc())
    ).all()
    categories_by_workout = _category_slugs_by_workout(session, [row.id for row in rows])

    return [
        WorkoutSample(
            id=str(row.id),
            occurred_at=_as_aware(row.occurred_at),
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
            occurred_at=_as_aware(row.occurred_at),
            exercise_key=(row.normalized_exercise_key or row.exercise_name).strip().lower(),
            exercise_name=row.exercise_name,
            load_kg=float(row.load_kg) if row.load_kg is not None else None,
            reps=row.reps,
            duration_seconds=row.duration_seconds,
            distance_m=float(row.distance_m) if row.distance_m is not None else None,
        )
        for row in rows
    ]


def load_team_samples(
    session: Session, team_id: UUID, requester_id: str, since: datetime
) -> dict[str, list[WorkoutSample]]:
    """Per-viewer team samples: the requester's own private workouts plus
    everyone's team-visible ones. Suitable for a dashboard the requester is
    looking at directly — NOT for content that might be persisted and read
    by a teammate later (use load_team_visible_samples for that)."""
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
    categories_by_workout = _category_slugs_by_workout(session, [row.id for row in rows])

    by_user: dict[str, list[WorkoutSample]] = {}
    for row in rows:
        by_user.setdefault(row.user_id, []).append(
            WorkoutSample(
                id=str(row.id),
                occurred_at=_as_aware(row.occurred_at),
                distance_km=float(row.distance_km) if row.distance_km is not None else None,
                duration_minutes=row.duration_minutes,
                category_slugs=tuple(categories_by_workout.get(str(row.id), [])),
            )
        )
    return by_user


def load_team_visible_samples(
    session: Session, team_id: UUID, since: datetime
) -> dict[str, list[WorkoutSample]]:
    """Only visibility='team' workouts, for every member, regardless of
    caller. Required for content persisted where any teammate might read it
    later (e.g. a team_weekly coach insight) — never mix in one caller's own
    private data there, or it would leak to the other athlete."""
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
            Workout.visibility == "team",
        )
        .order_by(Workout.occurred_at.desc())
    ).all()
    categories_by_workout = _category_slugs_by_workout(session, [row.id for row in rows])

    by_user: dict[str, list[WorkoutSample]] = {}
    for row in rows:
        by_user.setdefault(row.user_id, []).append(
            WorkoutSample(
                id=str(row.id),
                occurred_at=_as_aware(row.occurred_at),
                distance_km=float(row.distance_km) if row.distance_km is not None else None,
                duration_minutes=row.duration_minutes,
                category_slugs=tuple(categories_by_workout.get(str(row.id), [])),
            )
        )
    return by_user
