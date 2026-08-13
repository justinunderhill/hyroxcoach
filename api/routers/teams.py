from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import GoalEvent, TeamMembership
from api.schemas.goal_events import GoalEventResponse, GoalEventUpsert

router = APIRouter(prefix="/api/teams", tags=["teams"])
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
