"""Exercises the real OpenAI vision extraction path against R2 + a synthetic
test screenshot: generate image -> upload to R2 -> presigned GET -> real
model call -> schema validation. Not just the mocked pytest suite.
"""

import io
import json
import urllib.request
from uuid import uuid4

from dotenv import load_dotenv
from PIL import Image, ImageDraw

from api.schemas.extraction import WorkoutExtractionData
from api.services import ai_client, extraction, storage

load_dotenv(".env.local")

image = Image.new("RGB", (600, 300), color="white")
draw = ImageDraw.Draw(image)
draw.text(
    (20, 20),
    "Riverside Parkrun\n09/08/2026\n\nTime: 28:11\nDistance: 5.0 km\nPosition: 42",
    fill="black",
)
buffer = io.BytesIO()
image.save(buffer, format="JPEG")
image_bytes = buffer.getvalue()

test_key = storage.build_storage_key("extraction-smoke-test", uuid4(), "jpg")
upload_url = storage.create_upload_url(test_key, "image/jpeg", 300)
request = urllib.request.Request(
    upload_url, data=image_bytes, method="PUT", headers={"Content-Type": "image/jpeg"}
)
with urllib.request.urlopen(request) as response:
    if response.status not in (200, 201):
        raise SystemExit(f"Upload failed with status {response.status}")

try:
    download_url = storage.create_download_url(test_key, 120)
    raw = ai_client.call_vision_model(
        extraction.SYSTEM_PROMPT,
        extraction.WORKOUT_USER_PROMPT,
        download_url,
        WorkoutExtractionData.model_json_schema(),
    )
    parsed = WorkoutExtractionData.model_validate(json.loads(raw))
finally:
    storage.delete_object(test_key)

print(f"model: {ai_client.extraction_model_name()}")
print(f"event_name: {parsed.event_name}")
print(f"occurred_at: {parsed.occurred_at}")
print(f"distance_km: {parsed.distance_km}")
print(f"duration_seconds: {parsed.duration_seconds}")
print(f"position: {parsed.position}")
print(f"confidence: {parsed.confidence}")
print(f"uncertainty_notes: {parsed.uncertainty_notes}")

if parsed.distance_km != 5.0:
    raise SystemExit(
        f"Expected distance_km=5.0 to be read from the image, got {parsed.distance_km}"
    )

print(
    "\nExtraction verified: real OpenAI vision call returned schema-valid data "
    "with plausible values."
)
