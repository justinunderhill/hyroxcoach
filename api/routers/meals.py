from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import Meal
from api.schemas.meals import MealCreate, MealResponse, MealUpdate
from api.services.teams import active_team_ids, resolve_primary_team_id

router = APIRouter(prefix="/api/meals", tags=["meals"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def require_ownership(meal: Meal, user: AuthenticatedUser) -> None:
    if meal.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found.")


def load_owned_meal_or_404(session: Session, meal_id: UUID, user: AuthenticatedUser) -> Meal:
    meal = session.get(Meal, meal_id)
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found.")
    require_ownership(meal, user)
    return meal


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    payload: MealCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> Meal:
    set_request_user(session, user.id)
    team_id = resolve_primary_team_id(session, user.id)

    meal = Meal(
        user_id=user.id,
        team_id=team_id,
        occurred_at=payload.occurred_at,
        meal_type=payload.meal_type,
        description=payload.description,
        calories=payload.calories,
        protein_g=Decimal(str(payload.protein_g)) if payload.protein_g is not None else None,
        carbs_g=Decimal(str(payload.carbs_g)) if payload.carbs_g is not None else None,
        fat_g=Decimal(str(payload.fat_g)) if payload.fat_g is not None else None,
        nutrition_is_estimated=payload.nutrition_is_estimated,
        notes=payload.notes,
        visibility=payload.visibility,
        source=payload.source,
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return meal


@router.get("", response_model=list[MealResponse])
def list_meals(
    user: CurrentUser,
    session: DatabaseSession,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[Meal]:
    set_request_user(session, user.id)
    team_ids = active_team_ids(session, user.id)

    conditions = [
        (Meal.user_id == user.id) | ((Meal.visibility == "team") & Meal.team_id.in_(team_ids))
    ]
    if from_date is not None:
        conditions.append(Meal.occurred_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date is not None:
        conditions.append(Meal.occurred_at <= datetime.combine(to_date, datetime.max.time()))

    query = select(Meal).where(*conditions).order_by(Meal.occurred_at.desc()).limit(limit)
    return list(session.scalars(query).all())


@router.patch("/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: UUID,
    payload: MealUpdate,
    user: CurrentUser,
    session: DatabaseSession,
) -> Meal:
    set_request_user(session, user.id)
    meal = load_owned_meal_or_404(session, meal_id, user)

    if payload.occurred_at is not None:
        meal.occurred_at = payload.occurred_at
    if payload.meal_type is not None:
        meal.meal_type = payload.meal_type
    if payload.description is not None:
        meal.description = payload.description
    if payload.calories is not None:
        meal.calories = payload.calories
    if payload.protein_g is not None:
        meal.protein_g = Decimal(str(payload.protein_g))
    if payload.carbs_g is not None:
        meal.carbs_g = Decimal(str(payload.carbs_g))
    if payload.fat_g is not None:
        meal.fat_g = Decimal(str(payload.fat_g))
    if payload.nutrition_is_estimated is not None:
        meal.nutrition_is_estimated = payload.nutrition_is_estimated
    if payload.notes is not None:
        meal.notes = payload.notes
    if payload.visibility is not None:
        meal.visibility = payload.visibility

    session.commit()
    session.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> None:
    set_request_user(session, user.id)
    meal = load_owned_meal_or_404(session, meal_id, user)
    session.delete(meal)
    session.commit()
