from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import AthleteProfile, Meal, NutritionTarget
from api.schemas.nutrition import (
    DailyNutritionResponse,
    DailyTotalsResponse,
    NutritionTargetCreate,
    NutritionTargetResponse,
    RemainingResponse,
)
from api.services.nutrition import (
    MealMacros,
    daily_totals,
    remaining_vs_target,
    select_effective_target,
)
from api.services.nutrition import (
    NutritionTarget as NutritionTargetSample,
)

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def user_timezone(session: Session, user_id: str) -> ZoneInfo:
    timezone_name = session.scalar(
        select(AthleteProfile.timezone).where(AthleteProfile.user_id == user_id)
    )
    try:
        return ZoneInfo(timezone_name) if timezone_name else ZoneInfo("UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def local_day_bounds_utc(local_date: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(local_date, time.min, tzinfo=tz)
    end = datetime.combine(local_date, time.max, tzinfo=tz)
    return start, end


@router.post("/targets", response_model=NutritionTargetResponse, status_code=201)
def create_target(
    payload: NutritionTargetCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> NutritionTarget:
    set_request_user(session, user.id)
    tz = user_timezone(session, user.id)
    effective_from = payload.effective_from or datetime.now(tz).date()

    target = NutritionTarget(
        user_id=user.id,
        effective_from=effective_from,
        calories_target=payload.calories_target,
        protein_g_target=(
            Decimal(str(payload.protein_g_target)) if payload.protein_g_target is not None else None
        ),
        carbs_g_target=(
            Decimal(str(payload.carbs_g_target)) if payload.carbs_g_target is not None else None
        ),
        fat_g_target=(
            Decimal(str(payload.fat_g_target)) if payload.fat_g_target is not None else None
        ),
    )
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


@router.get("/targets", response_model=NutritionTargetResponse | None)
def get_active_target(
    user: CurrentUser,
    session: DatabaseSession,
) -> NutritionTarget | None:
    set_request_user(session, user.id)
    tz = user_timezone(session, user.id)
    today = datetime.now(tz).date()
    return _load_effective_target(session, user.id, today)


def _load_effective_target(
    session: Session, user_id: str, on_date: date
) -> NutritionTarget | None:
    rows = list(
        session.scalars(
            select(NutritionTarget).where(
                NutritionTarget.user_id == user_id, NutritionTarget.effective_from <= on_date
            )
        )
    )
    if not rows:
        return None
    samples = [
        NutritionTargetSample(
            effective_from=row.effective_from,
            calories_target=row.calories_target,
            protein_g_target=(
                float(row.protein_g_target) if row.protein_g_target is not None else None
            ),
            carbs_g_target=float(row.carbs_g_target) if row.carbs_g_target is not None else None,
            fat_g_target=float(row.fat_g_target) if row.fat_g_target is not None else None,
        )
        for row in rows
    ]
    effective = select_effective_target(samples, on_date)
    if effective is None:
        return None
    return next(row for row in rows if row.effective_from == effective.effective_from)


@router.get("/daily", response_model=DailyNutritionResponse)
def get_daily_nutrition(
    user: CurrentUser,
    session: DatabaseSession,
    on_date: Annotated[date | None, Query(alias="date")] = None,
) -> DailyNutritionResponse:
    set_request_user(session, user.id)
    tz = user_timezone(session, user.id)
    target_date = on_date or datetime.now(tz).date()
    start, end = local_day_bounds_utc(target_date, tz)

    meals = list(
        session.scalars(
            select(Meal)
            .where(Meal.user_id == user.id, Meal.occurred_at >= start, Meal.occurred_at <= end)
            .order_by(Meal.occurred_at)
        )
    )

    totals = daily_totals(
        [
            MealMacros(
                calories=meal.calories,
                protein_g=float(meal.protein_g) if meal.protein_g is not None else None,
                carbs_g=float(meal.carbs_g) if meal.carbs_g is not None else None,
                fat_g=float(meal.fat_g) if meal.fat_g is not None else None,
            )
            for meal in meals
        ]
    )

    target_row = _load_effective_target(session, user.id, target_date)
    target_sample = (
        NutritionTargetSample(
            effective_from=target_row.effective_from,
            calories_target=target_row.calories_target,
            protein_g_target=(
                float(target_row.protein_g_target)
                if target_row.protein_g_target is not None
                else None
            ),
            carbs_g_target=(
                float(target_row.carbs_g_target) if target_row.carbs_g_target is not None else None
            ),
            fat_g_target=(
                float(target_row.fat_g_target) if target_row.fat_g_target is not None else None
            ),
        )
        if target_row is not None
        else None
    )
    remaining = remaining_vs_target(totals, target_sample)

    return DailyNutritionResponse(
        date=target_date,
        target=NutritionTargetResponse.model_validate(target_row) if target_row else None,
        consumed=DailyTotalsResponse(
            calories=totals.calories,
            protein_g=totals.protein_g,
            carbs_g=totals.carbs_g,
            fat_g=totals.fat_g,
        ),
        remaining=RemainingResponse(
            calories=remaining.calories,
            protein_g=remaining.protein_g,
            carbs_g=remaining.carbs_g,
            fat_g=remaining.fat_g,
        ),
        meals=list(meals),
    )
