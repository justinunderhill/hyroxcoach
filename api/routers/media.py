from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth import AuthenticatedUser, get_current_user
from api.config import (
    MEDIA_DOWNLOAD_URL_TTL_SECONDS,
    MEDIA_MIME_EXTENSIONS,
    MEDIA_UPLOAD_URL_TTL_SECONDS,
)
from api.database import get_session, set_request_user
from api.models import Meal, Measurement, MediaAsset, MediaLink, Workout
from api.schemas.media import (
    EntityType,
    MediaAssetResponse,
    MediaItemResponse,
    MediaUploadIntentRequest,
    MediaUploadIntentResponse,
)
from api.services import storage
from api.services.teams import active_team_ids, resolve_primary_team_id, teammate_user_ids

router = APIRouter(prefix="/api/media", tags=["media"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
DatabaseSession = Annotated[Session, Depends(get_session)]

_ENTITY_MODELS: dict[str, type[Workout] | type[Meal] | type[Measurement]] = {
    "workout": Workout,
    "meal": Meal,
    "measurement": Measurement,
}


def _require_owned_entity(
    session: Session, entity_type: EntityType, entity_id: UUID, user: AuthenticatedUser
) -> None:
    entity = session.get(_ENTITY_MODELS[entity_type], entity_id)
    if entity is None or entity.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_type.capitalize()} not found."
        )


def _can_view_entity(
    session: Session,
    entity_type: EntityType,
    entity_id: UUID,
    user: AuthenticatedUser,
    team_ids: list[UUID],
) -> bool:
    entity = session.get(_ENTITY_MODELS[entity_type], entity_id)
    if entity is None:
        return False
    if entity.user_id == user.id:
        return True
    if entity_type == "measurement":
        return entity.visibility == "team" and entity.user_id in teammate_user_ids(
            session, user.id
        )
    return entity.visibility == "team" and entity.team_id in team_ids


@router.post(
    "/upload-intent",
    response_model=MediaUploadIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_upload_intent(
    payload: MediaUploadIntentRequest,
    user: CurrentUser,
    session: DatabaseSession,
) -> MediaUploadIntentResponse:
    set_request_user(session, user.id)

    if payload.entity_type is not None and payload.entity_id is not None:
        _require_owned_entity(session, payload.entity_type, payload.entity_id, user)

    team_id = resolve_primary_team_id(session, user.id)
    media_id = uuid4()
    extension = MEDIA_MIME_EXTENSIONS[payload.mime_type]
    storage_path = storage.build_storage_key(user.id, media_id, extension)

    media_asset = MediaAsset(
        id=media_id,
        user_id=user.id,
        team_id=team_id,
        storage_path=storage_path,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        purpose=payload.purpose,
        visibility=payload.visibility,
    )
    session.add(media_asset)
    session.flush()

    if payload.entity_type is not None and payload.entity_id is not None:
        session.add(
            MediaLink(
                media_asset_id=media_id,
                entity_type=payload.entity_type,
                entity_id=payload.entity_id,
            )
        )

    session.commit()
    session.refresh(media_asset)

    upload_url = storage.create_upload_url(
        storage_path, payload.mime_type, MEDIA_UPLOAD_URL_TTL_SECONDS
    )

    return MediaUploadIntentResponse(
        media_asset=MediaAssetResponse.model_validate(media_asset),
        upload_url=upload_url,
        upload_headers={"Content-Type": payload.mime_type},
        expires_in=MEDIA_UPLOAD_URL_TTL_SECONDS,
    )


@router.get("", response_model=list[MediaItemResponse])
def list_media(
    user: CurrentUser,
    session: DatabaseSession,
    entity_type: Literal["workout", "meal", "measurement"] = Query(...),
    entity_ids: str = Query(..., description="Comma-separated entity UUIDs"),
) -> list[MediaItemResponse]:
    set_request_user(session, user.id)
    team_ids = active_team_ids(session, user.id)

    try:
        requested_ids = [UUID(part) for part in entity_ids.split(",") if part.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid entity id."
        ) from None

    viewable_ids = [
        entity_id
        for entity_id in requested_ids
        if _can_view_entity(session, entity_type, entity_id, user, team_ids)
    ]
    if not viewable_ids:
        return []

    links = session.scalars(
        select(MediaLink).where(
            MediaLink.entity_type == entity_type, MediaLink.entity_id.in_(viewable_ids)
        )
    ).all()
    if not links:
        return []

    asset_ids = [link.media_asset_id for link in links]
    assets = {
        asset.id: asset
        for asset in session.scalars(
            select(MediaAsset).where(MediaAsset.id.in_(asset_ids))
        ).all()
    }

    items: list[MediaItemResponse] = []
    for link in links:
        asset = assets.get(link.media_asset_id)
        if asset is None:
            continue
        view_url = storage.create_download_url(asset.storage_path, MEDIA_DOWNLOAD_URL_TTL_SECONDS)
        items.append(
            MediaItemResponse(
                media_asset=MediaAssetResponse.model_validate(asset),
                entity_type=link.entity_type,  # type: ignore[arg-type]
                entity_id=link.entity_id,
                view_url=view_url,
                expires_in=MEDIA_DOWNLOAD_URL_TTL_SECONDS,
            )
        )
    return items


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: UUID,
    user: CurrentUser,
    session: DatabaseSession,
) -> None:
    set_request_user(session, user.id)
    asset = session.get(MediaAsset, media_id)
    if asset is None or asset.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")

    storage_path = asset.storage_path
    session.delete(asset)
    session.commit()
    storage.delete_object(storage_path)
