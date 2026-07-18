"""
AuditLog model — immutable trail of privileged/mutating user actions.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(UUIDPKMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_entries")

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "alert.status_update"
    target_entity: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Alert"
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.target_entity}:{self.target_id}>"
