from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.config import MEDIA_MAX_SIZE_BYTES, MEDIA_MIME_EXTENSIONS

Purpose = Literal["workout_evidence", "meal_photo", "measurement", "other"]
EntityType = Literal["workout", "meal", "measurement"]
Visibility = Literal["team", "private"]


class MediaUploadIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: Purpose
    mime_type: str = Field(min_length=3, max_length=100)
    size_bytes: int = Field(gt=0, le=MEDIA_MAX_SIZE_BYTES)
    visibility: Visibility = "private"
    entity_type: EntityType | None = None
    entity_id: UUID | None = None

    @model_validator(mode="after")
    def entity_fields_are_paired(self) -> "MediaUploadIntentRequest":
        if (self.entity_type is None) != (self.entity_id is None):
            raise ValueError("entity_type and entity_id must be provided together.")
        return self

    @model_validator(mode="after")
    def mime_type_is_supported(self) -> "MediaUploadIntentRequest":
        if self.mime_type not in MEDIA_MIME_EXTENSIONS:
            allowed = ", ".join(sorted(MEDIA_MIME_EXTENSIONS))
            raise ValueError(f"Unsupported mime type. Allowed: {allowed}.")
        return self


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    mime_type: str
    size_bytes: int
    purpose: Purpose
    visibility: Visibility
    created_at: datetime


class MediaUploadIntentResponse(BaseModel):
    media_asset: MediaAssetResponse
    upload_url: str
    upload_method: Literal["PUT"] = "PUT"
    upload_headers: dict[str, str]
    expires_in: int


class MediaItemResponse(BaseModel):
    media_asset: MediaAssetResponse
    entity_type: EntityType
    entity_id: UUID
    view_url: str
    expires_in: int


class MediaLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: EntityType
    entity_id: UUID
