from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ExtractionType = Literal["workout", "meal"]
ExtractionStatus = Literal["succeeded", "failed"]


class ExtractionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_type: ExtractionType


class ExtractionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    media_asset_id: UUID
    extraction_type: ExtractionType
    model_name: str
    status: ExtractionStatus
    confidence: float | None
    extracted_data: dict
    user_confirmed: bool
    confirmed_data: dict | None
    error_message: str | None
    created_at: datetime
    confirmed_at: datetime | None


class ExtractionConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extraction_result_id: UUID
    confirmed_data: dict = Field(default_factory=dict)


class WorkoutExtractionData(BaseModel):
    """Structured output contract for the vision model on a workout screenshot."""

    model_config = ConfigDict(extra="forbid")

    event_name: str | None = None
    occurred_at: str | None = Field(default=None, description="ISO date, e.g. 2026-08-09")
    distance_km: float | None = None
    duration_seconds: int | None = None
    pace_seconds_per_km: float | None = None
    position: str | None = None
    source_label: str | None = None
    notes: str | None = None
    confidence: float = Field(ge=0, le=1)
    uncertainty_notes: list[str] = Field(default_factory=list)


class MealExtractionData(BaseModel):
    """Structured output contract for the vision model on a meal photo."""

    model_config = ConfigDict(extra="forbid")

    likely_foods: list[str] = Field(default_factory=list)
    meal_type: str | None = None
    estimated_calories_low: int | None = None
    estimated_calories_high: int | None = None
    notes: str | None = None
    confidence: float = Field(ge=0, le=1)
    uncertainty_notes: list[str] = Field(default_factory=list)
