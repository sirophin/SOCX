"""
Normalized log entry repository — read-side data access for the
Investigation APIs. Queries `normalized_log_entries` (the output of the
Log Parser module) with filtering and pagination; no write path here since
entries are only ever created by LogParsingService's bulk insert.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import LogSeverity, NormalizedLogEntry


class NormalizedLogEntryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, entry_id: uuid.UUID) -> NormalizedLogEntry | None:
        stmt = select(NormalizedLogEntry).where(NormalizedLogEntry.id == entry_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        username: Optional[str] = None,
        source_ip: Optional[str] = None,
        hostname: Optional[str] = None,
        event_id: Optional[str] = None,
        severity: Optional[LogSeverity] = None,
        timestamp_from: Optional[datetime] = None,
        timestamp_to: Optional[datetime] = None,
        log_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[NormalizedLogEntry], int]:
        """
        Filtering notes:
          - username / hostname: case-insensitive partial match (ILIKE) —
            free-text fields, analysts rarely know the exact stored casing
            or full value.
          - source_ip / event_id: exact match — these are structured,
            coded values (an IP or an event code), not free text.
          - severity: exact match against the LogSeverity enum.
          - timestamp_from / timestamp_to: inclusive range bounds, either
            or both may be supplied, for filtering by a time window.
          - log_id: optional extra filter (beyond what was asked) to scope
            results to entries parsed from one specific uploaded log —
            useful for "show me everything from this file" during
            investigation.
        """
        filters = []
        if username:
            filters.append(NormalizedLogEntry.username.ilike(f"%{username}%"))
        if hostname:
            filters.append(NormalizedLogEntry.hostname.ilike(f"%{hostname}%"))
        if source_ip:
            filters.append(NormalizedLogEntry.source_ip == source_ip)
        if event_id:
            filters.append(NormalizedLogEntry.event_id == event_id)
        if severity is not None:
            filters.append(NormalizedLogEntry.severity == severity)
        if timestamp_from is not None:
            filters.append(NormalizedLogEntry.timestamp >= timestamp_from)
        if timestamp_to is not None:
            filters.append(NormalizedLogEntry.timestamp <= timestamp_to)
        if log_id is not None:
            filters.append(NormalizedLogEntry.log_id == log_id)

        base_stmt = select(NormalizedLogEntry)
        count_stmt = select(func.count()).select_from(NormalizedLogEntry)
        for f in filters:
            base_stmt = base_stmt.where(f)
            count_stmt = count_stmt.where(f)

        base_stmt = base_stmt.order_by(NormalizedLogEntry.timestamp.desc()).limit(limit).offset(offset)

        results = await self.db.execute(base_stmt)
        total = await self.db.execute(count_stmt)
        return list(results.scalars().all()), total.scalar_one()
