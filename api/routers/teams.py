from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_invite_token_lookup, set_request_user
from api.models import AthleteProfile, GoalEvent, Team, TeamInvite, TeamMembership
from api.schemas.goal_events import GoalEventResponse, GoalEventUpsert
from api.schemas.invites import (
    TeamInviteAcceptResponse,
    TeamInviteCreate,
    TeamInviteCreateResponse,
    TeamInviteResponse,
    TeamMemberResponse,
    TeamResponse,
)
from api.services.invites import (
    MAX_ACTIVE_TEAM_MEMBERS,
    default_expiry,
    generate_token,
    hash_token,
)
from api.services.teams import team_roster, team_roster_user_ids

router = APIRouter(prefix="/api/teams", tags=["teams"])
invite_router = APIRouter(prefix="/api/team-invites", tags=["teams"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def _require_membership(session: Session, team_id: UUID, user: AuthenticatedUser) -> None:
    membership = session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user.id,
            TeamMembership.status == "active",
        )
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")


# Race-week/taper mode: the final 7 days before the event, inclusive of race
# day itself (PLAN.md Phase 8 "taper/race-week mode"). A fixed, documented
# window rather than a training-load-derived heuristic.
TAPER_WINDOW_DAYS = 7


def goal_event_response(goal_event: GoalEvent) -> GoalEventResponse:
    days_until_event = (goal_event.event_date - date.today()).days
    return GoalEventResponse(
        id=goal_event.id,
        team_id=goal_event.team_id,
        name=goal_event.name,
        event_type=goal_event.event_type,  # type: ignore[arg-type]
        event_date=goal_event.event_date,
        division=goal_event.division,
        location=goal_event.location,
        preparation_start_date=goal_event.preparation_start_date,
        days_until_event=days_until_event,
        is_taper_week=0 <= days_until_event <= TAPER_WINDOW_DAYS,
        created_at=goal_event.created_at,
        updated_at=goal_event.updated_at,
    )


@router.get("/{team_id}/goal-event", response_model=GoalEventResponse | None)
def get_goal_event(
    team_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> GoalEventResponse | None:
    set_request_user(session, user.id)
    _require_membership(session, team_id, user)
    goal_event = session.scalar(select(GoalEvent).where(GoalEvent.team_id == team_id))
    return goal_event_response(goal_event) if goal_event is not None else None


@router.put("/{team_id}/goal-event", response_model=GoalEventResponse)
def upsert_goal_event(
    team_id: UUID,
    payload: GoalEventUpsert,
    user: CurrentUser,
    session: DatabaseSession,
) -> GoalEventResponse:
    set_request_user(session, user.id)
    _require_membership(session, team_id, user)

    goal_event = session.scalar(select(GoalEvent).where(GoalEvent.team_id == team_id))
    if goal_event is None:
        goal_event = GoalEvent(team_id=team_id, name=payload.name, event_date=payload.event_date)
        session.add(goal_event)

    goal_event.name = payload.name
    goal_event.event_type = payload.event_type
    goal_event.event_date = payload.event_date
    goal_event.division = payload.division
    goal_event.location = payload.location
    goal_event.preparation_start_date = payload.preparation_start_date

    session.commit()
    session.refresh(goal_event)
    return goal_event_response(goal_event)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> TeamResponse:
    set_request_user(session, user.id)
    _require_membership(session, team_id, user)

    team = session.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")

    member_rows = team_roster(session, team_id)
    display_names = dict(
        session.execute(
            select(AthleteProfile.user_id, AthleteProfile.display_name).where(
                AthleteProfile.user_id.in_([row.user_id for row in member_rows])
            )
        ).all()
    )

    return TeamResponse(
        id=team.id,
        name=team.name,
        created_by=team.created_by,
        created_at=team.created_at,
        members=[
            TeamMemberResponse(
                user_id=row.user_id,
                display_name=display_names.get(row.user_id) or "Athlete",
                role=row.role,
                status=row.status,
            )
            for row in member_rows
        ],
    )


@router.post(
    "/{team_id}/invites",
    response_model=TeamInviteCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_team_invite(
    team_id: UUID,
    payload: TeamInviteCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> TeamInviteCreateResponse:
    set_request_user(session, user.id)
    _require_membership(session, team_id, user)

    roster = team_roster_user_ids(session, team_id)
    if len(roster) >= MAX_ACTIVE_TEAM_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This team already has two athletes.",
        )

    token = generate_token()
    invite = TeamInvite(
        team_id=team_id,
        invited_email=payload.invited_email,
        token_hash=hash_token(token),
        expires_at=default_expiry(),
        created_by=user.id,
    )
    session.add(invite)
    session.commit()
    session.refresh(invite)

    return TeamInviteCreateResponse(
        id=invite.id,
        team_id=invite.team_id,
        invited_email=invite.invited_email,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        created_by=invite.created_by,
        created_at=invite.created_at,
        token=token,
    )


@router.get("/{team_id}/invites", response_model=list[TeamInviteResponse])
def list_team_invites(
    team_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> list[TeamInviteResponse]:
    set_request_user(session, user.id)
    _require_membership(session, team_id, user)

    invites = session.scalars(
        select(TeamInvite)
        .where(TeamInvite.team_id == team_id)
        .order_by(TeamInvite.created_at.desc())
    ).all()
    return [TeamInviteResponse.model_validate(invite) for invite in invites]


@invite_router.post("/{token}/accept", response_model=TeamInviteAcceptResponse)
def accept_team_invite(
    token: str,
    user: CurrentUser,
    session: DatabaseSession,
) -> TeamInviteAcceptResponse:
    set_request_user(session, user.id)
    set_invite_token_lookup(session, hash_token(token))

    invite = session.scalar(select(TeamInvite).where(TeamInvite.token_hash == hash_token(token)))
    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found or already used."
        )
    if invite.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="This invite has already been accepted."
        )
    now = datetime.now(UTC)
    expires_at = (
        invite.expires_at
        if invite.expires_at.tzinfo
        else invite.expires_at.replace(tzinfo=UTC)
    )
    if expires_at < now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This invite has expired.")

    roster = team_roster_user_ids(session, invite.team_id)
    if user.id not in roster and len(roster) >= MAX_ACTIVE_TEAM_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This team already has two athletes.",
        )

    existing_membership = session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == invite.team_id, TeamMembership.user_id == user.id
        )
    )
    if existing_membership is None:
        session.add(
            TeamMembership(
                team_id=invite.team_id, user_id=user.id, role="athlete", status="active"
            )
        )
    elif existing_membership.status != "active":
        existing_membership.status = "active"

    # HYROX Doubles is a single-team-at-a-time model: joining a new team via
    # invite supersedes any other team the athlete was previously active on
    # (typically their own auto-provisioned solo team). Past records keep
    # their original team_id -- only future activity resolves to the new team.
    other_memberships = session.scalars(
        select(TeamMembership).where(
            TeamMembership.user_id == user.id,
            TeamMembership.team_id != invite.team_id,
            TeamMembership.status == "active",
        )
    ).all()
    for membership in other_memberships:
        membership.status = "left"

    invite.accepted_at = now

    try:
        session.flush()
    except IntegrityError:
        # A concurrent duplicate accept (double-click, retry, or a dev-mode
        # double-effect) already inserted this exact membership between our
        # SELECT above and this flush. Treat it as the idempotent success it
        # actually is rather than 500ing.
        session.rollback()
        # Rollback also discards this transaction's SET LOCAL RLS context.
        set_request_user(session, user.id)

    team = session.get(Team, invite.team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    membership = session.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == invite.team_id, TeamMembership.user_id == user.id
        )
    )
    session.commit()

    return TeamInviteAcceptResponse(
        team_id=team.id,
        team_name=team.name,
        role=membership.role if membership else "athlete",
        status=membership.status if membership else "active",
    )
