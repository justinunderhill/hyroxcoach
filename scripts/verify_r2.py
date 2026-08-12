import urllib.error
import urllib.request
from uuid import uuid4

from dotenv import load_dotenv

from api.services import storage

load_dotenv(".env.local")

test_key = storage.build_storage_key("r2-smoke-test", uuid4(), "txt")
payload = b"hyrox-coach r2 smoke test"

upload_url = storage.create_upload_url(test_key, "text/plain", 300)
request = urllib.request.Request(
    upload_url, data=payload, method="PUT", headers={"Content-Type": "text/plain"}
)
with urllib.request.urlopen(request) as response:
    if response.status not in (200, 201):
        raise SystemExit(f"Upload failed with status {response.status}")

download_url = storage.create_download_url(test_key, 300)
with urllib.request.urlopen(download_url) as response:
    body = response.read()
    if body != payload:
        raise SystemExit("Downloaded content did not match uploaded content.")

storage.delete_object(test_key)

deleted_check_url = storage.create_download_url(test_key, 300)
try:
    urllib.request.urlopen(deleted_check_url)
except urllib.error.HTTPError as error:
    if error.code != 404:
        raise SystemExit(f"Expected 404 after delete, got {error.code}") from error
else:
    raise SystemExit("Object still downloadable after delete.")

print("R2 verified: upload, download (content matched), and delete all succeeded.")
