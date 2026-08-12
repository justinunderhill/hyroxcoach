import os

MEDIA_MIME_EXTENSIONS: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
}
MEDIA_MAX_SIZE_BYTES = 15 * 1024 * 1024
MEDIA_UPLOAD_URL_TTL_SECONDS = 300
MEDIA_DOWNLOAD_URL_TTL_SECONDS = 300

DEFAULT_EXTRACTION_MODEL = "gpt-4o-mini"
EXTRACTION_IMAGE_URL_TTL_SECONDS = 120


def extraction_model_name() -> str:
    return os.getenv("OPENAI_EXTRACTION_MODEL", DEFAULT_EXTRACTION_MODEL)


def frontend_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def media_bucket_name() -> str:
    bucket = os.getenv("R2_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("R2_BUCKET_NAME is required for media storage.")
    return bucket
