from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EventType = Literal["hyrox_doubles"]


class GoalEventUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    event_type: EventType = "hyrox_doubles"
    event_date: date
    division: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=120)
    preparation_start_date: date | None = None

    @field_validator("name", "division", "location")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class GoalEventResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    event_type: EventType
    event_date: date
    division: str | None
    location: str | None
    preparation_start_date: date | None
    days_until_event: int
    created_at: datetime
    updated_at: datetime
