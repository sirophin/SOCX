"""
Log repository — persistence for uploaded-file metadata (the `logs` table)
and, for the Log Parser module, bulk insertion of parsed
`normalized_log_entries` plus parse-status tracking on the parent Log.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log import Log, LogSourceType, NormalizedLogEntry, ParseStatus
from app.parsers.schema import ParsedLogEntry


class LogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        source_type: LogSourceType,
        original_filename: str,
        file_reference: str,
        file_size_bytes: int,
        uploaded_by_id: Optional[uuid.UUID],
    ) -> Log:
        log = Log(
            source_type=source_type,
            original_filename=original_filename,
            file_reference=file_reference,
            file_size_bytes=file_size_bytes,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> Log | None:
        stmt = (
            select(Log)
            .options(selectinload(Log.uploaded_by))
            .where(Log.id == log_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        source_type: Optional[LogSourceType] = None,
        uploaded_by_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Log], int]:
        filters = []
        if source_type is not None:
            filters.append(Log.source_type == source_type)
        if uploaded_by_id is not None:
            filters.append(Log.uploaded_by_id == uploaded_by_id)

        base_stmt = select(Log).options(selectinload(Log.uploaded_by))
        count_stmt = select(func.count()).select_from(Log)
        for f in filters:
            base_stmt = base_stmt.where(f)
            count_stmt = count_stmt.where(f)

        base_stmt = base_stmt.order_by(Log.ingested_at.desc()).limit(limit).offset(offset)

        results = await self.db.execute(base_stmt)
        total = await self.db.execute(count_stmt)
        return list(results.scalars().all()), total.scalar_one()

    # --- Parsing support -------------------------------------------------

    async def set_parse_status(
        self,
        log: Log,
        status: ParseStatus,
        stats: Optional[dict] = None,
        mark_parsed_now: bool = False,
    ) -> None:
        log.parse_status = status
        if stats is not None:
            log.parse_stats = stats
        if mark_parsed_now:
            log.parsed_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def bulk_insert_normalized_entries(
        self, log_id: uuid.UUID, entries: list[ParsedLogEntry]
    ) -> int:
        """
        Bulk-inserts parsed entries linked to `log_id` (preserving the
        original uploaded file reference via the FK). Uses SQLAlchemy Core
        bulk insert rather than one ORM object per row for efficiency on
        large files.
        """
        if not entries:
            return 0

        rows = [
            {
                "log_id": log_id,
                "timestamp": e.timestamp,
                "event_id": e.event_id,
                "hostname": e.hostname,
                "username": e.username,
                "process_name": e.process_name,
                "source_ip": e.source_ip,
                "destination_ip": e.destination_ip,
                "command_line": e.command_line,
                "status": e.status,
                "severity": e.severity,
                "raw_fields": e.raw_fields,
            }
            for e in entries
        ]

        await self.db.execute(NormalizedLogEntry.__table__.insert(), rows)
        return len(rows)
