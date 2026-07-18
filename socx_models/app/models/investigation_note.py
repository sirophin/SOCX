"""
InvestigationNote model — analyst notes attached to an alert or an incident.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.incident import Incident
    from app.models.user import User


class InvestigationNote(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "investigation_notes"

    # A note belongs to EITHER an alert OR an incident (not both, not neither).
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True
    )

    analyst_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    analyst: Mapped[Optional["User"]] = relationship(back_populates="investigation_notes")

    note_text: Mapped[str] = mapped_column(Text, nullable=False)

    alert: Mapped[Optional["Alert"]] = relationship(back_populates="notes")
    incident: Mapped[Optional["Incident"]] = relationship(back_populates="notes")

    __table_args__ = (
        CheckConstraint(
            "(alert_id IS NOT NULL AND incident_id IS NULL) OR "
            "(alert_id IS NULL AND incident_id IS NOT NULL)",
            name="ck_note_belongs_to_one_parent",
        ),
    )

    def __repr__(self) -> str:
        return f"<InvestigationNote {self.id}>"
