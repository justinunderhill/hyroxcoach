from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Visibility = Literal["team", "private"]
CalorieSource = Literal["external", "estimated"]


class CindyStartResponse(BaseModel):
    started_at: datetime


class CindyCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    total_seconds: int = Field(gt=0, le=1_200)
    full_rounds: int = Field(ge=0, le=100)
    extra_pullups: int = Field(default=0, ge=0, le=200)
    extra_pushups: int = Field(default=0, ge=0, le=200)
    extra_squats: int = Field(default=0, ge=0, le=200)
    rpe: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = Field(default=None, max_length=2_000)
    visibility: Visibility = "team"
    calories_burned: int | None = Field(default=None, ge=0, le=5_000)
    estimate_calories: bool = False


class CindyResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workout_id: UUID
    full_rounds: int
    extra_pullups: int
    extra_pushups: int
    extra_squats: int
    total_reps: int
    total_seconds: int
    completed_as_prescribed: bool
    calories_burned: int | None
    calorie_source: CalorieSource | None
    calorie_estimation_version: str | None
    created_at: datetime


class CindyAttemptSummary(BaseModel):
    completed_at: datetime
    full_rounds: int
    total_reps: int
    total_seconds: int
    completed_as_prescribed: bool


class CindyChangeResponse(BaseModel):
    total_reps_change: int
    total_seconds_change: int
    full_rounds_change: int


class CindyAnalyticsResponse(BaseModel):
    latest: CindyAttemptSummary | None
    personal_best: CindyAttemptSummary | None
    change_from_previous: CindyChangeResponse | None
    history: list[CindyAttemptSummary]
