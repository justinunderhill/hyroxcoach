from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, text
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


def _is_postgres(session: Session) -> bool:
    return session.get_bind().dialect.name == "postgresql"


def team_roster_user_ids(session: Session, team_id: UUID) -> list[str]:
    """Active member user_ids for a team, including the caller.

    team_memberships' own SELECT policy only exposes the caller's row (see
    migrations/20260817_0009's docstring), so a plain ORM query against it
    only ever returns the caller under real RLS. On Postgres we go through
    the team_member_user_ids() SECURITY DEFINER function (migration
    20260818_0010), which checks caller membership itself and then reads
    with the table owner's privileges. SQLite (used in tests) has no RLS at
    all, so the plain query already returns the full roster there.
    """
    if _is_postgres(session):
        return list(
            session.scalars(
                text("SELECT user_id FROM team_member_user_ids(:team_id)"),
                {"team_id": str(team_id)},
            )
        )
    return list(
        session.scalars(
            select(TeamMembership.user_id).where(
                TeamMembership.team_id == team_id, TeamMembership.status == "active"
            )
        )
    )


def teammate_user_ids(session: Session, user_id: str) -> list[str]:
    team_ids = active_team_ids(session, user_id)
    if not team_ids:
        return []
    roster = {
        member_id
        for team_id in team_ids
        for member_id in team_roster_user_ids(session, team_id)
    }
    roster.discard(user_id)
    return list(roster)
