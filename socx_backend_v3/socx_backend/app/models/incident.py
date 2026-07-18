"""
Incident model — bundles one or more related alerts into a formal case.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.alert import Alert
    from app.models.report import Report
    from app.models.investigation_note import InvestigationNote
    from app.models.ioc import IOC


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    OPEN = "Open"
    INVESTIGATING = "Investigating"
    CONTAINED = "Contained"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class Incident(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity, name="incident_severity_enum", native_enum=True), nullable=False
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incident_status_enum", native_enum=True),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
    )

    created_from_alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True
    )

    assigned_analyst_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_analyst: Mapped[Optional["User"]] = relationship(
        back_populates="assigned_incidents", foreign_keys=[assigned_analyst_id]
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    alert_links: Mapped[List["IncidentAlert"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(back_populates="incident")
    notes: Mapped[List["InvestigationNote"]] = relationship(back_populates="incident")
    iocs: Mapped[List["IOC"]] = relationship(back_populates="related_incident")

    def __repr__(self) -> str:
        return f"<Incident {self.title} status={self.status}>"


class IncidentAlert(Base):
    """Join table: which alerts are bundled into which incident."""
    __tablename__ = "incident_alerts"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True
    )

    incident: Mapped["Incident"] = relationship(back_populates="alert_links")
    alert: Mapped["Alert"] = relationship(back_populates="incident_links")
