import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def jwks_client() -> PyJWKClient:
    jwks_url = os.getenv("NEON_AUTH_JWKS_URL")
    if not jwks_url:
        raise RuntimeError("NEON_AUTH_JWKS_URL is required.")
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=300)


def decode_access_token(token: str) -> dict[str, Any]:
    signing_key = jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["EdDSA"],
        # Small leeway absorbs ordinary clock skew between this host and the
        # token issuer; without it, iat/exp checks intermittently reject
        # freshly issued tokens as "not yet valid".
        leeway=10,
        options={"verify_aud": False, "require": ["sub", "exp"]},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        claims = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        ) from None

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    email = claims.get("email")
    return AuthenticatedUser(id=subject, email=email if isinstance(email, str) else None)
