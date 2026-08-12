from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import DailyStep
from api.schemas.steps import StepsHistoryResponse, StepsResponse, StepsUpsert
from api.services.steps import StepSample, seven_day_average, week_over_week_trend, weekly_total
from api.services.teams import teammate_user_ids

router = APIRouter(prefix="/api/steps", tags=["steps"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.put("/{on_date}", response_model=StepsResponse)
def upsert_steps(
    on_date: date,
    payload: StepsUpsert,
    user: CurrentUser,
    session: DatabaseSession,
) -> DailyStep:
    set_request_user(session, user.id)

    entry = session.scalar(
        select(DailyStep).where(DailyStep.user_id == user.id, DailyStep.date == on_date)
    )
    if entry is None:
        entry = DailyStep(user_id=user.id, date=on_date)
        session.add(entry)

    entry.steps = payload.steps
    entry.source = payload.source
    entry.visibility = payload.visibility

    session.commit()
    session.refresh(entry)
    return entry


@router.get("", response_model=StepsHistoryResponse)
def list_steps(
    user: CurrentUser,
    session: DatabaseSession,
    athlete: str | None = None,
    days: int = 28,
) -> StepsHistoryResponse:
    set_request_user(session, user.id)
    teammates = teammate_user_ids(session, user.id)

    since = datetime.now(UTC).date() - timedelta(days=max(days, 1) - 1)

    conditions = [
        (DailyStep.user_id == user.id)
        | ((DailyStep.visibility == "team") & DailyStep.user_id.in_(teammates)),
        DailyStep.date >= since,
    ]
    if athlete is not None:
        conditions.append(DailyStep.user_id == athlete)

    entries = list(
        session.scalars(select(DailyStep).where(*conditions).order_by(DailyStep.date.desc()))
    )

    own_samples = [
        StepSample(date=row.date, steps=row.steps)
        for row in session.scalars(
            select(DailyStep).where(
                DailyStep.user_id == user.id, DailyStep.date >= since - timedelta(days=7)
            )
        )
    ]
    today = datetime.now(UTC).date()

    return StepsHistoryResponse(
        entries=[StepsResponse.model_validate(entry) for entry in entries],
        weekly_total=weekly_total(own_samples, today),
        seven_day_average=seven_day_average(own_samples, today),
        trend_vs_prior_week=week_over_week_trend(own_samples, today),
    )
