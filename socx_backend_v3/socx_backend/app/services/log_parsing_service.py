"""
Log parsing service — orchestrates turning a previously-uploaded raw file
into `normalized_log_entries` rows.

Pipeline: fetch Log row -> resolve file on disk -> select parser via
ParserRegistry -> run parser (off the event loop, since parsing is CPU-bound
sync code) -> bulk insert entries -> persist parse status/stats on the Log
row -> audit log -> commit.

Explicitly out of scope here (per current requirements): the Detection
Engine. This module's job ends at normalized_log_entries.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log, NormalizedLogEntry, ParseStatus
import app.parsers  # noqa: F401 - triggers parser registration
from app.parsers.base_parser import ParserError, ParserRegistry
from app.parsers.schema import ParseResult
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.log_repository import LogRepository
from app.services.file_storage_service import FileStorageService

__all__ = [
    "LogParsingService",
    "LogNotFoundError",
    "AlreadyParsedError",
    "UnsupportedForParsingError",
]


class LogNotFoundError(Exception):
    pass


class AlreadyParsedError(Exception):
    """Raised when re-parsing is attempted without force=True on a log that's already done."""


class UnsupportedForParsingError(Exception):
    """No parser is registered for this log's source type."""


class LogParsingService:
    def __init__(self, db: AsyncSession, storage: Optional[FileStorageService] = None):
        self.db = db
        self.storage = storage or FileStorageService()
        self.logs = LogRepository(db)
        self.audit = AuditLogRepository(db)

    async def parse_log(
        self,
        log_id: uuid.UUID,
        triggered_by_id: Optional[uuid.UUID],
        ip_address: Optional[str] = None,
        force: bool = False,
    ) -> Log:
        log = await self.logs.get_by_id(log_id)
        if log is None:
            raise LogNotFoundError(f"Log {log_id} not found")

        if log.parse_status in (ParseStatus.COMPLETED, ParseStatus.PARTIAL) and not force:
            raise AlreadyParsedError(
                f"Log {log_id} has already been parsed (status={log.parse_status.value}). "
                f"Pass force=true to re-parse."
            )

        if log.source_type not in ParserRegistry.supported_source_types():
            raise UnsupportedForParsingError(
                f"No parser is registered for source type '{log.source_type.value}'"
            )

        await self.logs.set_parse_status(log, ParseStatus.PARSING)
        await self.db.commit()

        file_path = self.storage.resolve_absolute_path(log.file_reference)
        parser = ParserRegistry.get_parser(log.source_type)

        try:
            # Parsing is CPU-bound synchronous code (regex, EVTX binary
            # decode, csv/json parsing) — run off the event loop so one
            # large file doesn't stall every other request.
            result: ParseResult = await asyncio.to_thread(parser.parse, file_path)
        except ParserError as exc:
            stats_dict = {"error": str(exc), "total_records": 0, "parsed": 0, "skipped": 0, "failed": 0}
            await self.logs.set_parse_status(
                log, ParseStatus.FAILED, stats=stats_dict, mark_parsed_now=True
            )
            await self.audit.write(
                action="log.parse_failed", target_entity="Log",
                user_id=triggered_by_id, target_id=log.id, ip_address=ip_address,
            )
            await self.db.commit()
            return log
        except Exception as exc:  # noqa: BLE001 - defensive: never let parsing crash the request
            stats_dict = {
                "error": f"Unexpected parser failure: {exc}",
                "total_records": 0, "parsed": 0, "skipped": 0, "failed": 0,
            }
            await self.logs.set_parse_status(
                log, ParseStatus.FAILED, stats=stats_dict, mark_parsed_now=True
            )
            await self.audit.write(
                action="log.parse_failed", target_entity="Log",
                user_id=triggered_by_id, target_id=log.id, ip_address=ip_address,
            )
            await self.db.commit()
            return log

        if force:
            # Re-parse: drop previously normalized entries for this log
            # before inserting the fresh set, so results aren't duplicated.
            await self.db.execute(
                delete(NormalizedLogEntry).where(NormalizedLogEntry.log_id == log.id)
            )

        await self.logs.bulk_insert_normalized_entries(log.id, result.entries)

        final_status = ParseStatus.COMPLETED if result.stats.failed == 0 else ParseStatus.PARTIAL
        await self.logs.set_parse_status(
            log, final_status, stats=result.stats.as_dict(), mark_parsed_now=True
        )

        await self.audit.write(
            action="log.parse_completed", target_entity="Log",
            user_id=triggered_by_id, target_id=log.id, ip_address=ip_address,
        )
        await self.db.commit()
        await self.db.refresh(log, attribute_names=["uploaded_by"])
        return log
