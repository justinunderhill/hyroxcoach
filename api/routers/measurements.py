from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.database import get_session, set_request_user
from api.models import Measurement
from api.schemas.measurements import MeasurementCreate, MeasurementResponse, MeasurementUpdate
from api.services.teams import teammate_user_ids

router = APIRouter(prefix="/api/measurements", tags=["measurements"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]


def load_owned_measurement_or_404(
    session: Session, measurement_id: UUID, user: AuthenticatedUser
) -> Measurement:
    measurement = session.get(Measurement, measurement_id)
    if measurement is None or measurement.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found.")
    return measurement


@router.post("", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
def create_measurement(
    payload: MeasurementCreate,
    user: CurrentUser,
    session: DatabaseSession,
) -> Measurement:
    set_request_user(session, user.id)

    measurement = Measurement(
        user_id=user.id,
        occurred_at=payload.occurred_at or datetime.now(UTC),
        weight_kg=Decimal(str(payload.weight_kg)) if payload.weight_kg is not None else None,
        waist_cm=Decimal(str(payload.waist_cm)) if payload.waist_cm is not None else None,
        resting_hr=payload.resting_hr,
        notes=payload.notes,
        visibility=payload.visibility,
    )
    session.add(measurement)
    session.commit()
    session.refresh(measurement)
    return measurement


@router.get("", response_model=list[MeasurementResponse])
def list_measurements(
    user: CurrentUser,
    session: DatabaseSession,
    athlete: str | None = None,
) -> list[Measurement]:
    set_request_user(session, user.id)
    teammates = teammate_user_ids(session, user.id)

    conditions = [
        (Measurement.user_id == user.id)
        | ((Measurement.visibility == "team") & Measurement.user_id.in_(teammates))
    ]
    if athlete is not None:
        conditions.append(Measurement.user_id == athlete)

    query = select(Measurement).where(*conditions).order_by(Measurement.occurred_at.desc())
    return list(session.scalars(query).all())


@router.patch("/{measurement_id}", response_model=MeasurementResponse)
def update_measurement(
    measurement_id: UUID,
    payload: MeasurementUpdate,
    user: CurrentUser,
    session: DatabaseSession,
) -> Measurement:
    set_request_user(session, user.id)
    measurement = load_owned_measurement_or_404(session, measurement_id, user)

    if payload.occurred_at is not None:
        measurement.occurred_at = payload.occurred_at
    if payload.weight_kg is not None:
        measurement.weight_kg = Decimal(str(payload.weight_kg))
    if payload.waist_cm is not None:
        measurement.waist_cm = Decimal(str(payload.waist_cm))
    if payload.resting_hr is not None:
        measurement.resting_hr = payload.resting_hr
    if payload.notes is not None:
        measurement.notes = payload.notes
    if payload.visibility is not None:
        measurement.visibility = payload.visibility

    session.commit()
    session.refresh(measurement)
    return measurement


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    measurement_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> None:
    set_request_user(session, user.id)
    measurement = load_owned_measurement_or_404(session, measurement_id, user)
    session.delete(measurement)
    session.commit()
