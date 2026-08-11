from datetime import datetime

from pydantic import BaseModel


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


class AthleteAnalyticsResponse(BaseModel):
    range_days: int
    generated_at: datetime
    consistency: ConsistencyResponse
    category_coverage: dict[str, int]
    running: RunningAnalyticsResponse
    data_note: str | None = None
