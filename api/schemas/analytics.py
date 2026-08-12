from datetime import datetime
from typing import Literal

from pydantic import BaseModel

MetricType = Literal["load_kg", "duration_seconds", "distance_m", "reps"]
TrendDirection = Literal["improving", "flat", "declining"]


class RunningSampleResponse(BaseModel):
    id: str
    occurred_at: datetime
    distance_km: float
    pace_seconds_per_km: float | None


class RunningAnalyticsResponse(BaseModel):
    weekly_distance_km: float
    avg_pace_seconds_per_km: float | None
    best_5k_seconds: int | None
    recent: list[RunningSampleResponse]


class ConsistencyResponse(BaseModel):
    sessions_last_7_days: int
    active_days_last_7_days: int


class ExercisePointResponse(BaseModel):
    id: str
    occurred_at: datetime
    load_kg: float | None
    reps: int | None
    duration_seconds: int | None
    distance_m: float | None


class ExerciseProgressionResponse(BaseModel):
    exercise_key: str
    exercise_name: str
    primary_metric: MetricType
    trend: TrendDirection | None
    points: list[ExercisePointResponse]


class PersonalBestResponse(BaseModel):
    exercise_key: str
    exercise_name: str
    metric: MetricType
    best_value: float
    achieved_at: datetime
    is_current: bool


class AthleteAnalyticsResponse(BaseModel):
    range_days: int
    generated_at: datetime
    consistency: ConsistencyResponse
    category_coverage: dict[str, int]
    running: RunningAnalyticsResponse
    exercise_progression: list[ExerciseProgressionResponse]
    station_history: list[ExerciseProgressionResponse]
    personal_bests: list[PersonalBestResponse]
    data_note: str | None = None


class TeamAthleteSummary(BaseModel):
    user_id: str
    display_name: str
    consistency: ConsistencyResponse
    running: RunningAnalyticsResponse
    category_coverage: dict[str, int]


class TeamAnalyticsResponse(BaseModel):
    team_id: str
    range_days: int
    generated_at: datetime
    athletes: list[TeamAthleteSummary]
    combined_category_coverage: dict[str, int]
    neglected_categories: list[str]
    data_note: str | None = None
