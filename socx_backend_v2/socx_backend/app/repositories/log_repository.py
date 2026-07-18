"""
Log repository — persistence for uploaded-file metadata (the `logs` table).
No parsing/normalized-entry access here; that belongs to a future
LogParsingModule working against `normalized_log_entries`.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log import Log, LogSourceType


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
