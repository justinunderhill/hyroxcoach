"""Deterministic analytics aggregators.

All functions here are pure and operate on plain in-memory samples so they
can be unit tested without a database. Canonical values (weekly counts,
pace, coverage) must be computed here rather than left to the LLM per
CLAUDE.md rule 2.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

WEEK_DAYS = 7
FIVE_K_MIN_KM = 4.9
FIVE_K_MAX_KM = 5.1


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
