from datetime import UTC, datetime, timedelta

from api.services.analytics import (
    WorkoutSample,
    active_days_in_window,
    category_coverage,
    pace_seconds_per_km,
    running_summary,
    sessions_in_window,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


def sample(
    days_ago: float,
    distance_km: float | None = None,
    duration_minutes: int | None = None,
    categories: tuple[str, ...] = (),
) -> WorkoutSample:
    return WorkoutSample(
        id=f"w-{days_ago}",
        occurred_at=NOW - timedelta(days=days_ago),
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        category_slugs=categories,
    )


def test_pace_seconds_per_km_handles_missing_values() -> None:
    assert pace_seconds_per_km(None, 5.0) is None
    assert pace_seconds_per_km(30, None) is None
    assert pace_seconds_per_km(30, 5.0) == 360.0


def test_sessions_in_window_excludes_older_workouts() -> None:
    samples = [sample(1), sample(6), sample(8), sample(14)]
    assert sessions_in_window(samples, NOW, days=7) == 2


def test_active_days_in_window_counts_distinct_dates() -> None:
    samples = [sample(1), sample(1.2), sample(2)]
    assert active_days_in_window(samples, NOW, days=7) == 2


def test_category_coverage_zero_fills_untouched_categories() -> None:
    samples = [sample(1, categories=("running",)), sample(2, categories=("running", "strength"))]
    coverage = category_coverage(samples, ["running", "strength", "mobility"], NOW, days=7)
    assert coverage == {"running": 2, "strength": 1, "mobility": 0}


def test_category_coverage_respects_window() -> None:
    samples = [sample(30, categories=("running",))]
    coverage = category_coverage(samples, ["running"], NOW, days=7)
    assert coverage == {"running": 0}


def test_running_summary_weekly_distance_and_average_pace() -> None:
    samples = [
        sample(1, distance_km=5.0, duration_minutes=30),
        sample(3, distance_km=10.0, duration_minutes=55),
        sample(10, distance_km=5.0, duration_minutes=25),
    ]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.weekly_distance_km == 15.0
    assert summary.avg_pace_seconds_per_km is not None
    assert len(summary.recent) == 3


def test_running_summary_detects_best_5k_within_tolerance() -> None:
    samples = [
        sample(1, distance_km=5.0, duration_minutes=25),
        sample(5, distance_km=4.95, duration_minutes=24),
        sample(10, distance_km=10.0, duration_minutes=50),
    ]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.best_5k_seconds == 24 * 60


def test_running_summary_best_5k_is_none_without_matching_distance() -> None:
    samples = [sample(1, distance_km=10.0, duration_minutes=50)]
    summary = running_summary(samples, NOW, range_days=28)
    assert summary.best_5k_seconds is None
