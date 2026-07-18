"""
IOC (Indicator of Compromise) model — extracted from log evidence during investigation.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.incident import Incident
    from app.models.log import NormalizedLogEntry


class IOCType(str, enum.Enum):
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    HOSTNAME = "hostname"
    URL = "url"
    USERNAME = "username"
    REGISTRY_PATH = "registry_path"
    HASH = "hash"
    FILE_PATH = "file_path"


class IOC(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "iocs"

    type: Mapped[IOCType] = mapped_column(
        SAEnum(IOCType, name="ioc_type_enum", native_enum=True), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)

    first_seen: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    related_alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True
    )
    related_alert: Mapped[Optional["Alert"]] = relationship(back_populates="iocs")

    related_incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True
    )
    related_incident: Mapped[Optional["Incident"]] = relationship(back_populates="iocs")

    source_log_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("normalized_log_entries.id", ondelete="SET NULL"), nullable=True
    )
    source_log_entry: Mapped[Optional["NormalizedLogEntry"]] = relationship(back_populates="iocs")

    __table_args__ = (
        UniqueConstraint("type", "value", "related_alert_id", name="uq_ioc_type_value_alert"),
    )

    def __repr__(self) -> str:
        return f"<IOC {self.type}:{self.value}>"
