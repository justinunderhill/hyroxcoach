from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.schemas.meals import MealResponse


class NutritionTargetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effective_from: date | None = None
    calories_target: int | None = Field(default=None, ge=0, le=10_000)
    protein_g_target: float | None = Field(default=None, ge=0, le=1_000)
    carbs_g_target: float | None = Field(default=None, ge=0, le=1_000)
    fat_g_target: float | None = Field(default=None, ge=0, le=1_000)

    @model_validator(mode="after")
    def require_a_value(self) -> "NutritionTargetCreate":
        if (
            self.calories_target is None
            and self.protein_g_target is None
            and self.carbs_g_target is None
            and self.fat_g_target is None
        ):
            raise ValueError("Provide at least one target value.")
        return self


class NutritionTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    effective_from: date
    calories_target: int | None
    protein_g_target: Decimal | None
    carbs_g_target: Decimal | None
    fat_g_target: Decimal | None
    created_at: datetime


class DailyTotalsResponse(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


class RemainingResponse(BaseModel):
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None


class DailyNutritionResponse(BaseModel):
    date: date
    target: NutritionTargetResponse | None
    consumed: DailyTotalsResponse
    remaining: RemainingResponse
    meals: list[MealResponse]
