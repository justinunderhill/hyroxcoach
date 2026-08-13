from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Visibility = Literal["team", "private"]
Source = Literal["manual", "image", "integration"]


class ExercisePerformanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_name: str = Field(min_length=1, max_length=120)
    normalized_exercise_key: str | None = Field(default=None, max_length=120)
    sequence_no: int = Field(default=1, ge=1, le=100)
    sets: int | None = Field(default=None, ge=1, le=100)
    reps: int | None = Field(default=None, ge=1, le=10_000)
    load_kg: float | None = Field(default=None, gt=0, le=1_000)
    distance_m: float | None = Field(default=None, gt=0, le=200_000)
    duration_seconds: int | None = Field(default=None, gt=0, le=86_400)
    pace_seconds_per_km: float | None = Field(default=None, gt=0, le=3_600)
    calories: int | None = Field(default=None, ge=0, le=10_000)
    rpe: int | None = Field(default=None, ge=1, le=10)
    metadata: dict = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=1_000)

    @field_validator("exercise_name", "normalized_exercise_key", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class ExercisePerformanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exercise_name: str
    normalized_exercise_key: str | None
    sequence_no: int
    sets: int | None
    reps: int | None
    load_kg: Decimal | None
    distance_m: Decimal | None
    duration_seconds: int | None
    pace_seconds_per_km: Decimal | None
    calories: int | None
    rpe: int | None
    notes: str | None


class WorkoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime
    title: str = Field(min_length=1, max_length=120)
    activity_type: str = Field(min_length=1, max_length=60)
    category_slugs: list[str] = Field(default_factory=list, max_length=15)
    duration_minutes: int | None = Field(default=None, gt=0, le=1_440)
    distance_km: float | None = Field(default=None, gt=0, le=1_000)
    rpe: int | None = Field(default=None, ge=1, le=10)
    visibility: Visibility = "private"
    source: Source = "manual"
    notes: str | None = Field(default=None, max_length=2_000)
    is_simulation: bool = False
    paired_workout_id: UUID | None = Field(
        default=None,
        description="A teammate's team-visible workout logged for the same joint session.",
    )

    @field_validator("title", "activity_type", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("category_slugs")
    @classmethod
    def unique_categories(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Category slugs must be unique.")
        return value


class WorkoutUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurred_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    activity_type: str | None = Field(default=None, min_length=1, max_length=60)
    category_slugs: list[str] | None = Field(default=None, max_length=15)
    duration_minutes: int | None = Field(default=None, gt=0, le=1_440)
    distance_km: float | None = Field(default=None, gt=0, le=1_000)
    rpe: int | None = Field(default=None, ge=1, le=10)
    visibility: Visibility | None = None
    notes: str | None = Field(default=None, max_length=2_000)
    is_simulation: bool | None = None
    paired_workout_id: UUID | None = None

    @field_validator("title", "activity_type", "notes")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    team_id: UUID
    occurred_at: datetime
    title: str
    activity_type: str
    category_slugs: list[str]
    duration_minutes: int | None
    distance_km: Decimal | None
    rpe: int | None
    notes: str | None
    visibility: Visibility
    source: Source
    is_simulation: bool
    paired_workout_id: UUID | None
    performances: list[ExercisePerformanceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkoutCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    category_group: str
