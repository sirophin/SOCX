"""
Report model — generated PDF incident reports.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.user import User


class Report(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    incident: Mapped["Incident"] = relationship(back_populates="reports")

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    generated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_by: Mapped[Optional["User"]] = relationship(back_populates="generated_reports")

    generated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Report incident={self.incident_id} generated_at={self.generated_at}>"
