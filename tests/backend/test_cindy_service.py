from datetime import UTC, datetime

from api.services.cindy import (
    CindyAttempt,
    change_from_previous,
    completed_as_prescribed,
    estimate_calories,
    personal_best,
    total_reps,
)


def test_total_reps_formula() -> None:
    assert total_reps(full_rounds=10, extra_pullups=3, extra_pushups=2, extra_squats=1) == 306


def test_total_reps_with_no_partials() -> None:
    assert total_reps(5, 0, 0, 0) == 150


def test_completed_as_prescribed_requires_full_twenty_minutes() -> None:
    assert completed_as_prescribed(1200) is True
    assert completed_as_prescribed(1199) is False


def test_estimate_calories_uses_bodyweight_when_available() -> None:
    heavier = estimate_calories(1200, 100.0)
    lighter = estimate_calories(1200, 60.0)
    assert heavier > lighter


def test_estimate_calories_falls_back_to_default_bodyweight() -> None:
    assert estimate_calories(1200, None) > 0
    assert estimate_calories(1200, None) == estimate_calories(1200, 0)


def test_personal_best_prefers_higher_reps_then_faster_time() -> None:
    attempts = [
        CindyAttempt(datetime(2026, 1, 1, tzinfo=UTC), 8, 240, 1200),
        CindyAttempt(datetime(2026, 2, 1, tzinfo=UTC), 9, 270, 1100),
        CindyAttempt(datetime(2026, 3, 1, tzinfo=UTC), 9, 270, 1200),
    ]
    best = personal_best(attempts)
    assert best is not None
    assert best.total_reps == 270
    assert best.total_seconds == 1100


def test_personal_best_is_none_without_attempts() -> None:
    assert personal_best([]) is None


def test_change_from_previous_compares_latest_two() -> None:
    attempts = [
        CindyAttempt(datetime(2026, 1, 1, tzinfo=UTC), 8, 240, 1200),
        CindyAttempt(datetime(2026, 2, 1, tzinfo=UTC), 9, 270, 1150),
    ]
    change = change_from_previous(attempts)
    assert change is not None
    assert change.total_reps_change == 30
    assert change.total_seconds_change == -50
    assert change.full_rounds_change == 1


def test_change_from_previous_needs_two_attempts() -> None:
    attempts = [CindyAttempt(datetime(2026, 1, 1, tzinfo=UTC), 8, 240, 1200)]
    assert change_from_previous(attempts) is None
