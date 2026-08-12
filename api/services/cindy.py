"""Deterministic Cindy (20-minute AMRAP) calculations.

Pure functions so the reps formula, calorie estimate, personal-best
selection and attempt-over-attempt change are unit testable without a
database, per CLAUDE.md rule 2.
"""

from dataclasses import dataclass
from datetime import datetime

REPS_PER_ROUND = 30
FULL_DURATION_SECONDS = 1200

# Documented estimate formula: MET-based, using the ACSM metabolic
# equivalent for vigorous-effort calisthenics circuits (~8.0 METs).
# calories = MET * bodyweight_kg * duration_hours
# Falls back to a reference bodyweight when none is on file — this makes
# the estimate less personal, which is exactly why it must always be
# labelled "Estimated" and carry calorie_estimation_version.
CINDY_MET = 8.0
DEFAULT_BODYWEIGHT_KG = 75.0
CALORIE_ESTIMATION_VERSION = "met_v1"


def total_reps(full_rounds: int, extra_pullups: int, extra_pushups: int, extra_squats: int) -> int:
    return full_rounds * REPS_PER_ROUND + extra_pullups + extra_pushups + extra_squats


def completed_as_prescribed(total_seconds: int) -> bool:
    return total_seconds >= FULL_DURATION_SECONDS


def estimate_calories(total_seconds: int, bodyweight_kg: float | None) -> int:
    weight = bodyweight_kg if bodyweight_kg and bodyweight_kg > 0 else DEFAULT_BODYWEIGHT_KG
    hours = total_seconds / 3600
    return round(CINDY_MET * weight * hours)


@dataclass(frozen=True)
class CindyAttempt:
    completed_at: datetime
    full_rounds: int
    total_reps: int
    total_seconds: int


def personal_best(attempts: list[CindyAttempt]) -> CindyAttempt | None:
    if not attempts:
        return None
    return max(attempts, key=lambda attempt: (attempt.total_reps, -attempt.total_seconds))


@dataclass(frozen=True)
class AttemptChange:
    total_reps_change: int
    total_seconds_change: int
    full_rounds_change: int


def change_from_previous(attempts_by_date_asc: list[CindyAttempt]) -> AttemptChange | None:
    if len(attempts_by_date_asc) < 2:
        return None
    latest = attempts_by_date_asc[-1]
    previous = attempts_by_date_asc[-2]
    return AttemptChange(
        total_reps_change=latest.total_reps - previous.total_reps,
        total_seconds_change=latest.total_seconds - previous.total_seconds,
        full_rounds_change=latest.full_rounds - previous.full_rounds,
    )
