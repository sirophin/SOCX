"""
RefreshToken model — tracks issued refresh tokens by their JWT ID (jti) so
they can be revoked server-side on logout, without needing to store the
actual token value (only its unique identifier and a hash for lookup safety
are kept).

NOTE: this table is not part of the original architecture doc's schema
(Section 5). It's added specifically to support real logout/revocation,
since stateless JWTs can't otherwise be invalidated before they expire.
In production this belongs in Redis (fast TTL-based lookups) rather than
Postgres — see docs/architecture.md Section 18 (Scalability).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(UUIDPKMixin, Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    # timezone=True is required: application code consistently generates
    # timezone-aware UTC datetimes via datetime.now(timezone.utc). Without
    # it, Postgres stores/returns naive datetimes and any comparison or
    # arithmetic against an aware datetime (e.g. in AuthService.refresh())
    # raises TypeError: can't compare/subtract offset-naive and
    # offset-aware datetimes.
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Set on rotation: the jti of the new refresh token issued to replace this one.
    replaced_by_jti: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<RefreshToken jti={self.jti} user={self.user_id} revoked={self.revoked}>"
