from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Visibility = Literal["team", "private"]
Source = Literal["manual", "image"]


class MealCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime
    meal_type: str | None = Field(default=None, max_length=30)
    description: str = Field(min_length=1, max_length=500)
    calories: int | None = Field(default=None, ge=0, le=10_000)
    protein_g: float | None = Field(default=None, ge=0, le=1_000)
    carbs_g: float | None = Field(default=None, ge=0, le=1_000)
    fat_g: float | None = Field(default=None, ge=0, le=1_000)
    nutrition_is_estimated: bool = False
    visibility: Visibility = "private"
    source: Source = "manual"
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("meal_type", "description", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class MealUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    meal_type: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    calories: int | None = Field(default=None, ge=0, le=10_000)
    protein_g: float | None = Field(default=None, ge=0, le=1_000)
    carbs_g: float | None = Field(default=None, ge=0, le=1_000)
    fat_g: float | None = Field(default=None, ge=0, le=1_000)
    nutrition_is_estimated: bool | None = None
    visibility: Visibility | None = None
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("meal_type", "description", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class MealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    team_id: UUID
    occurred_at: datetime
    meal_type: str | None
    description: str
    calories: int | None
    protein_g: Decimal | None
    carbs_g: Decimal | None
    fat_g: Decimal | None
    nutrition_is_estimated: bool
    notes: str | None
    visibility: Visibility
    source: Source
    created_at: datetime
    updated_at: datetime
