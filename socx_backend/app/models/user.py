"""
User model — SOC analysts and administrators.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.alert import Alert
    from app.models.incident import Incident
    from app.models.log import Log
    from app.models.investigation_note import InvestigationNote
    from app.models.report import Report
    from app.models.audit_log import AuditLog
    from app.models.refresh_token import RefreshToken


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped["Role"] = relationship(back_populates="users")

    # Alerts assigned to this analyst
    assigned_alerts: Mapped[List["Alert"]] = relationship(
        back_populates="analyst", foreign_keys="Alert.analyst_id"
    )
    # Incidents assigned to this analyst
    assigned_incidents: Mapped[List["Incident"]] = relationship(
        back_populates="assigned_analyst", foreign_keys="Incident.assigned_analyst_id"
    )
    uploaded_logs: Mapped[List["Log"]] = relationship(back_populates="uploaded_by")
    investigation_notes: Mapped[List["InvestigationNote"]] = relationship(back_populates="analyst")
    generated_reports: Mapped[List["Report"]] = relationship(back_populates="generated_by")
    audit_entries: Mapped[List["AuditLog"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
