from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import AthleteProfile, Measurement
from api.schemas.profiles import (
    AthleteProfileResponse,
    CurrentUserResponse,
    MeResponse,
    ProfileUpdate,
)

router = APIRouter(prefix="/api/me", tags=["profiles"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def profile_response(profile: AthleteProfile) -> AthleteProfileResponse:
    availability = profile.training_availability or {}
    return AthleteProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        timezone=profile.timezone,
        baseline_5k_seconds=profile.baseline_5k_seconds,
        training_days=availability.get("days", []),
        training_notes=availability.get("notes"),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def me_response(user: AuthenticatedUser, profile: AthleteProfile | None) -> MeResponse:
    return MeResponse(
        user=CurrentUserResponse(id=user.id, email=user.email),
        profile=profile_response(profile) if profile else None,
        active_teams=[],
    )


@router.get("", response_model=MeResponse)
def get_me(
    user: CurrentUser,
    session: DatabaseSession,
) -> MeResponse:
    set_request_user(session, user.id)
    profile = session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user.id))
    return me_response(user, profile)


@router.patch("", response_model=MeResponse)
def update_me(
    update: ProfileUpdate,
    user: CurrentUser,
    session: DatabaseSession,
) -> MeResponse:
    set_request_user(session, user.id)
    profile = session.scalar(select(AthleteProfile).where(AthleteProfile.user_id == user.id))

    if profile is None:
        if not update.display_name or not update.timezone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Display name and timezone are required to create a profile.",
            )
        profile = AthleteProfile(
            user_id=user.id,
            display_name=update.display_name,
            timezone=update.timezone,
        )
        session.add(profile)

    if update.display_name is not None:
        profile.display_name = update.display_name
    if update.timezone is not None:
        profile.timezone = update.timezone
    if update.baseline_5k_seconds is not None:
        profile.baseline_5k_seconds = update.baseline_5k_seconds

    if update.training_days is not None or update.training_notes is not None:
        availability = dict(profile.training_availability or {})
        if update.training_days is not None:
            availability["days"] = update.training_days
        if update.training_notes is not None:
            availability["notes"] = update.training_notes
        profile.training_availability = availability

    if update.weight_kg is not None or update.waist_cm is not None:
        session.add(
            Measurement(
                user_id=user.id,
                weight_kg=Decimal(str(update.weight_kg)) if update.weight_kg is not None else None,
                waist_cm=Decimal(str(update.waist_cm)) if update.waist_cm is not None else None,
                notes="Onboarding baseline",
                visibility="private",
            )
        )

    session.commit()
    session.refresh(profile)
    return me_response(user, profile)
