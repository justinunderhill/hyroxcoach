from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class TeamInviteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invited_email: EmailStr | None = Field(default=None, max_length=255)


class TeamInviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    invited_email: str | None
    expires_at: datetime
    accepted_at: datetime | None
    created_by: str
    created_at: datetime


class TeamInviteCreateResponse(TeamInviteResponse):
    token: str = Field(description="Plaintext invite token — shown only in this response.")


class TeamInviteAcceptResponse(BaseModel):
    team_id: UUID
    team_name: str
    role: str
    status: str


class TeamMemberResponse(BaseModel):
    user_id: str
    display_name: str
    role: str
    status: str


class TeamResponse(BaseModel):
    id: UUID
    name: str
    created_by: str
    created_at: datetime
    members: list[TeamMemberResponse]

    @field_validator("members")
    @classmethod
    def sort_by_role(cls, value: list[TeamMemberResponse]) -> list[TeamMemberResponse]:
        return sorted(value, key=lambda member: (member.role != "owner", member.display_name))
