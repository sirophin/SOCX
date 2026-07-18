"""
Core security primitives: password hashing and JWT issuance/verification.

Kept framework-agnostic (no FastAPI imports) so it can be unit-tested in
isolation and reused outside the request/response cycle if needed.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    sub: str            # user id (UUID as string)
    role: str            # role name, e.g. "Admin"
    type: TokenType
    jti: str             # unique token id (used for refresh-token revocation)
    iat: int
    exp: int
    iss: str


class DecodedTokenError(Exception):
    """Raised for any invalid/expired/malformed token. Caller maps this to 401."""


def _create_token(
    subject: uuid.UUID,
    role: str,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: Optional[str] = None,
) -> tuple[str, str]:
    """Returns (encoded_jwt, jti)."""
    now = datetime.now(timezone.utc)
    jti = jti or str(uuid.uuid4())
    payload = {
        "sub": str(subject),
        "role": role,
        "type": token_type.value,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "iss": settings.JWT_ISSUER,
    }
    encoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti


def create_access_token(subject: uuid.UUID, role: str) -> str:
    token, _ = _create_token(
        subject,
        role,
        TokenType.ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return token


def create_refresh_token(subject: uuid.UUID, role: str) -> tuple[str, str]:
    """Returns (encoded_jwt, jti) — the caller persists the jti for revocation."""
    return _create_token(
        subject,
        role,
        TokenType.REFRESH,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: TokenType) -> TokenPayload:
    try:
        raw = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise DecodedTokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise DecodedTokenError("Token is invalid") from exc

    if raw.get("type") != expected_type.value:
        raise DecodedTokenError(f"Expected a {expected_type.value} token")

    return TokenPayload(**raw)
