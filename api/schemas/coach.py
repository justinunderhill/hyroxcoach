from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CoachScope = Literal["workout", "daily", "weekly", "team_weekly"]
CoachStatus = Literal["on_track", "mixed", "needs_attention", "insufficient_data"]
Priority = Literal["low", "medium", "high"]
TimeHorizon = Literal["next_session", "this_week", "next_2_weeks"]


class CoachWin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    evidence: str


class CoachGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    evidence: str
    priority: Priority


class CoachRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str
    reason: str
    time_horizon: TimeHorizon


class CoachInsightData(BaseModel):
    """Structured output contract for the coaching model (AI_COACH.md #4)."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    status: CoachStatus
    wins: list[CoachWin] = Field(default_factory=list)
    gaps: list[CoachGap] = Field(default_factory=list)
    recommendations: list[CoachRecommendation] = Field(default_factory=list)
    team_notes: list[str] = Field(default_factory=list)
    data_limits: list[str] = Field(default_factory=list)


class CoachInsightResponse(BaseModel):
    id: UUID
    scope: CoachScope
    user_id: str | None
    team_id: UUID
    period_start: date | None
    period_end: date | None
    source_record_id: UUID | None
    coach_version: str
    model_name: str
    insight: CoachInsightData
    created_at: datetime
