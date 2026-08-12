from datetime import date, timedelta

from api.services.steps import StepSample, seven_day_average, week_over_week_trend, weekly_total

TODAY = date(2026, 8, 15)


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_weekly_total_sums_trailing_seven_days_inclusive() -> None:
    samples = [StepSample(days_ago(i), 1000) for i in range(7)]
    assert weekly_total(samples, TODAY) == 7000


def test_weekly_total_excludes_older_entries() -> None:
    samples = [StepSample(days_ago(i), 1000) for i in range(10)]
    assert weekly_total(samples, TODAY) == 7000


def test_seven_day_average() -> None:
    samples = [StepSample(days_ago(i), 1400) for i in range(7)]
    assert seven_day_average(samples, TODAY) == 1400.0


def test_week_over_week_trend_positive_when_improving() -> None:
    samples = [StepSample(days_ago(i), 1000) for i in range(7)]
    samples += [StepSample(days_ago(i), 500) for i in range(7, 14)]
    assert week_over_week_trend(samples, TODAY) == 3500


def test_week_over_week_trend_is_zero_with_no_data() -> None:
    assert week_over_week_trend([], TODAY) == 0
