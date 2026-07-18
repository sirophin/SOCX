"""
Auth service — orchestrates login, refresh-token rotation, and logout.
Contains no HTTP concerns; raises domain exceptions that the API layer maps
to HTTP status codes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DecodedTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


class AuthError(Exception):
    """Base class for auth failures the API layer maps to 401/403."""


class InvalidCredentialsError(AuthError):
    pass


class InactiveUserError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit = AuditLogRepository(db)

    async def authenticate(
        self, username: str, password: str, ip_address: Optional[str] = None
    ) -> tuple[str, str]:
        """Validates credentials and issues a (access_token, refresh_token) pair."""
        user = await self.users.get_by_username(username)

        # Constant-shape failure path: don't reveal whether the username exists.
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password")

        if not user.is_active:
            raise InactiveUserError("This account has been deactivated")

        access_token = create_access_token(user.id, user.role.name.value)
        refresh_token, jti = create_refresh_token(user.id, user.role.name.value)

        decoded = decode_token(refresh_token, TokenType.REFRESH)
        await self.refresh_tokens.create(
            user_id=user.id,
            jti=jti,
            issued_at=datetime.fromtimestamp(decoded.iat, tz=timezone.utc),
            expires_at=datetime.fromtimestamp(decoded.exp, tz=timezone.utc),
        )
        await self.audit.write(
            action="auth.login", target_entity="User", user_id=user.id,
            target_id=user.id, ip_address=ip_address,
        )
        await self.db.commit()
        return access_token, refresh_token

    async def refresh(self, refresh_token: str, ip_address: Optional[str] = None) -> tuple[str, str]:
        """Validates a refresh token, rotates it, and issues a new access+refresh pair."""
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except DecodedTokenError as exc:
            raise InvalidRefreshTokenError(str(exc)) from exc

        stored = await self.refresh_tokens.get_by_jti(payload.jti)
        if stored is None or stored.revoked:
            # Reuse of a revoked/rotated token is a strong signal of theft:
            # revoke the whole session family defensively.
            if stored is not None:
                await self.refresh_tokens.revoke_all_for_user(stored.user_id)
                await self.db.commit()
            raise InvalidRefreshTokenError("Refresh token is invalid or has been revoked")

        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("Refresh token has expired")

        user = await self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InactiveUserError("This account is no longer active")

        # Rotate: issue new refresh token, revoke the old one, link them.
        new_access_token = create_access_token(user.id, user.role.name.value)
        new_refresh_token, new_jti = create_refresh_token(user.id, user.role.name.value)
        new_decoded = decode_token(new_refresh_token, TokenType.REFRESH)

        await self.refresh_tokens.create(
            user_id=user.id,
            jti=new_jti,
            issued_at=datetime.fromtimestamp(new_decoded.iat, tz=timezone.utc),
            expires_at=datetime.fromtimestamp(new_decoded.exp, tz=timezone.utc),
        )
        await self.refresh_tokens.revoke(payload.jti, replaced_by_jti=new_jti)
        await self.audit.write(
            action="auth.token_refresh", target_entity="User", user_id=user.id,
            target_id=user.id, ip_address=ip_address,
        )
        await self.db.commit()
        return new_access_token, new_refresh_token

    async def logout(self, refresh_token: str, ip_address: Optional[str] = None) -> None:
        """Revokes the given refresh token so it can no longer be used."""
        try:
            payload = decode_token(refresh_token, TokenType.REFRESH)
        except DecodedTokenError:
            # Already invalid/expired — logout is idempotent, nothing to do.
            return

        await self.refresh_tokens.revoke(payload.jti)
        await self.audit.write(
            action="auth.logout", target_entity="User",
            user_id=uuid.UUID(payload.sub), target_id=uuid.UUID(payload.sub),
            ip_address=ip_address,
        )
        await self.db.commit()

    async def get_current_user_from_access_token(self, access_token: str) -> User:
        try:
            payload = decode_token(access_token, TokenType.ACCESS)
        except DecodedTokenError as exc:
            raise InvalidCredentialsError(str(exc)) from exc

        user = await self.users.get_by_id(uuid.UUID(payload.sub))
        if user is None or not user.is_active:
            raise InactiveUserError("User not found or inactive")
        return user
