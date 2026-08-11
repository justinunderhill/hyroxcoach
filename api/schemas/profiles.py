from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

TrainingDay = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    baseline_5k_seconds: int | None = Field(default=None, gt=0, le=86_400)
    training_days: list[TrainingDay] | None = Field(default=None, max_length=7)
    training_notes: str | None = Field(default=None, max_length=500)
    weight_kg: float | None = Field(default=None, gt=20, le=400)
    waist_cm: float | None = Field(default=None, gt=30, le=250)

    @field_validator("display_name", "timezone", "training_notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("training_days")
    @classmethod
    def unique_training_days(cls, value: list[TrainingDay] | None):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("Training days must be unique.")
        return value


class AthleteProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    timezone: str
    baseline_5k_seconds: int | None
    training_days: list[TrainingDay]
    training_notes: str | None
    created_at: datetime
    updated_at: datetime


class CurrentUserResponse(BaseModel):
    id: str
    email: EmailStr | None


class MeTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    role: Literal["owner", "athlete"]


class MeResponse(BaseModel):
    user: CurrentUserResponse
    profile: AthleteProfileResponse | None
    active_teams: list[MeTeamResponse] = Field(default_factory=list)
