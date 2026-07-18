"""
Log model (raw uploaded file) and NormalizedLogEntry (parsed/normalized common schema).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.alert import AlertLogEntry
    from app.models.ioc import IOC


class LogSourceType(str, enum.Enum):
    EVTX = "evtx"
    WINDOWS_SECURITY = "windows_security"
    LINUX_AUTH = "linux_auth_log"
    APACHE = "apache_access"
    NGINX = "nginx"
    APPLICATION = "application_log"
    JSON = "json"
    CSV = "csv"


class LogSeverity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    PARTIAL = "partial"    # completed with some failed/skipped records
    FAILED = "failed"      # whole-file failure, no entries persisted


class Log(UUIDPKMixin, TimestampMixin, Base):
    """Represents one uploaded raw log file/batch."""
    __tablename__ = "logs"

    source_type: Mapped[LogSourceType] = mapped_column(
        SAEnum(LogSourceType, name="log_source_type_enum", native_enum=True), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_reference: Mapped[str] = mapped_column(String(1000), nullable=False)  # storage path/URI
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_by: Mapped[Optional["User"]] = relationship(back_populates="uploaded_logs")

    # --- Parsing tracking (added for the Log Parser module) ---
    # Not part of the original Section-5 schema; see migration_log_parsing_fields.sql.
    parse_status: Mapped[ParseStatus] = mapped_column(
        SAEnum(ParseStatus, name="parse_status_enum", native_enum=True),
        default=ParseStatus.PENDING,
        nullable=False,
        index=True,
    )
    parsed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    parse_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    entries: Mapped[List["NormalizedLogEntry"]] = relationship(
        back_populates="log", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Log {self.original_filename} ({self.source_type})>"


class NormalizedLogEntry(UUIDPKMixin, Base):
    """
    Common normalized schema that ALL parsers (EVTX, auth.log, Apache,
    Nginx, app logs, JSON, CSV) map into. This is what the Detection
    Engine and Investigation Workspace query against.
    """
    __tablename__ = "normalized_log_entries"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logs.id", ondelete="CASCADE"), nullable=False
    )
    log: Mapped["Log"] = relationship(back_populates="entries")

    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    process_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True, index=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True, index=True)
    command_line: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g. success/failure/200/404
    severity: Mapped[LogSeverity] = mapped_column(
        SAEnum(LogSeverity, name="log_severity_enum", native_enum=True),
        default=LogSeverity.INFO,
        nullable=False,
    )
    # Catch-all for source-specific fields that don't fit the common schema
    raw_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    alert_links: Mapped[List["AlertLogEntry"]] = relationship(back_populates="log_entry")
    iocs: Mapped[List["IOC"]] = relationship(back_populates="source_log_entry")

    __table_args__ = (
        Index("ix_normalized_entries_ts_srcip", "timestamp", "source_ip"),
        Index("ix_normalized_entries_ts_user", "timestamp", "username"),
        Index("ix_normalized_entries_ts_host", "timestamp", "hostname"),
    )

    def __repr__(self) -> str:
        return f"<NormalizedLogEntry {self.event_id} @ {self.timestamp}>"
