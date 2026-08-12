from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Source = Literal["manual", "health_connect", "apple_health", "other_import"]
Visibility = Literal["team", "private"]


class StepsUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: int = Field(ge=0, le=200_000)
    source: Source = "manual"
    visibility: Visibility = "private"


class StepsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    date: date
    steps: int
    source: Source
    visibility: Visibility
    created_at: datetime
    updated_at: datetime


class StepsHistoryResponse(BaseModel):
    entries: list[StepsResponse]
    weekly_total: int
    seven_day_average: float
    trend_vs_prior_week: int
