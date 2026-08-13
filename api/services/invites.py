"""Team-invite token handling.

DATA_MODEL.md: never store a reusable plain-text invite token. The
plaintext token is generated here, returned to the caller exactly once by
the router, and only its hash is ever persisted.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

# HYROX Doubles is exactly two athletes per team (PRODUCT_REQUIREMENTS.md
# #2's "Team" concept) -- a documented cap, not an arbitrary limit.
MAX_ACTIVE_TEAM_MEMBERS = 2
INVITE_EXPIRY_DAYS = 14


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def default_expiry(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + timedelta(days=INVITE_EXPIRY_DAYS)
