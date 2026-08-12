"""Deterministic step aggregators.

Pure functions over plain samples so weekly total, 7-day average and
week-over-week trend are unit testable without a database.
"""

from dataclasses import dataclass
from datetime import date, timedelta

WINDOW_DAYS = 7


@dataclass(frozen=True)
class StepSample:
    date: date
    steps: int


def _window_total(samples: list[StepSample], window_end: date, days: int) -> int:
    window_start = window_end - timedelta(days=days - 1)
    return sum(sample.steps for sample in samples if window_start <= sample.date <= window_end)


def weekly_total(samples: list[StepSample], on_date: date) -> int:
    return _window_total(samples, on_date, WINDOW_DAYS)


def seven_day_average(samples: list[StepSample], on_date: date) -> float:
    return round(weekly_total(samples, on_date) / WINDOW_DAYS, 1)


def week_over_week_trend(samples: list[StepSample], on_date: date) -> int:
    current = _window_total(samples, on_date, WINDOW_DAYS)
    prior_window_end = on_date - timedelta(days=WINDOW_DAYS)
    prior = _window_total(samples, prior_window_end, WINDOW_DAYS)
    return current - prior
