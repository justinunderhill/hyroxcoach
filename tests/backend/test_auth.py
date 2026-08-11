from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api import auth


class StaticJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token: str):
        return SimpleNamespace(key=self.key)


def test_valid_neon_token_resolves_authenticated_user(monkeypatch) -> None:
    private_key = Ed25519PrivateKey.generate()
    token = jwt.encode(
        {
            "sub": "user-123",
            "email": "athlete@example.com",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        private_key,
        algorithm="EdDSA",
    )
    monkeypatch.setattr(auth, "jwks_client", lambda: StaticJwksClient(private_key.public_key()))

    user = auth.get_current_user(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert user.id == "user-123"
    assert user.email == "athlete@example.com"


def test_missing_credentials_are_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        auth.get_current_user(None)

    assert error.value.status_code == 401
