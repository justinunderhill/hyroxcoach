from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import TeamMembership


def active_team_ids(session: Session, user_id: str) -> list[UUID]:
    return list(
        session.scalars(
            select(TeamMembership.team_id).where(
                TeamMembership.user_id == user_id, TeamMembership.status == "active"
            )
        )
    )


def resolve_primary_team_id(session: Session, user_id: str) -> UUID:
    team_ids = active_team_ids(session, user_id)
    if not team_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Complete your athlete profile before logging.",
        )
    return team_ids[0]


def teammate_user_ids(session: Session, user_id: str) -> list[str]:
    team_ids = active_team_ids(session, user_id)
    if not team_ids:
        return []
    return list(
        session.scalars(
            select(TeamMembership.user_id).where(
                TeamMembership.team_id.in_(team_ids),
                TeamMembership.status == "active",
                TeamMembership.user_id != user_id,
            )
        )
    )
