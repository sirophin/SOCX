"""
Refresh token repository — supports issuance, lookup, and revocation
(used for logout and refresh-token rotation).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: uuid.UUID, jti: str, issued_at: datetime, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            issued_at=issued_at,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, jti: str, replaced_by_jti: str | None = None) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(
                revoked=True,
                revoked_at=datetime.now(timezone.utc),
                replaced_by_jti=replaced_by_jti,
            )
        )
        await self.db.execute(stmt)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Used for 'log out everywhere' / password-change security response."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
