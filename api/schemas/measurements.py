from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Visibility = Literal["team", "private"]


class MeasurementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    waist_cm: float | None = Field(default=None, gt=30, le=250)
    resting_hr: int | None = Field(default=None, gt=20, le=250)
    notes: str | None = Field(default=None, max_length=500)
    visibility: Visibility = "private"

    @field_validator("notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_a_value(self) -> "MeasurementCreate":
        if self.weight_kg is None and self.waist_cm is None and not self.notes:
            raise ValueError("Provide at least a weight, waist measurement or note.")
        return self


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    occurred_at: datetime
    weight_kg: Decimal | None
    waist_cm: Decimal | None
    resting_hr: int | None
    notes: str | None
    visibility: Visibility
    created_at: datetime
