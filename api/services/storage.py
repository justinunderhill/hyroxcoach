import os
from functools import lru_cache
from uuid import UUID

import boto3
from botocore.client import Config as BotoConfig

from api.config import media_bucket_name


@lru_cache
def _client():
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    if not (account_id and access_key and secret_key):
        raise RuntimeError(
            "R2_ACCOUNT_ID, R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY are required "
            "for media storage."
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def build_storage_key(user_id: str, media_asset_id: UUID, extension: str) -> str:
    return f"{user_id}/{media_asset_id}.{extension}"


def create_upload_url(storage_path: str, mime_type: str, ttl_seconds: int) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": media_bucket_name(), "Key": storage_path, "ContentType": mime_type},
        ExpiresIn=ttl_seconds,
    )


def create_download_url(storage_path: str, ttl_seconds: int) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": media_bucket_name(), "Key": storage_path},
        ExpiresIn=ttl_seconds,
    )


def delete_object(storage_path: str) -> None:
    _client().delete_object(Bucket=media_bucket_name(), Key=storage_path)
