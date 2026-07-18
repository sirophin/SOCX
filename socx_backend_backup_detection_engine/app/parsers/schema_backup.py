"""
Common data structures shared by every log parser. Every parser, regardless
of source format, produces a ParseResult made of ParsedLogEntry objects in
this one common schema — this is what lets a single Detection Engine (built
later) run against any log source without source-specific code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.models.log import LogSeverity

# Cap on how many individual error messages we keep in memory/DB per parse
# run — files with thousands of malformed lines shouldn't blow up storage
# or the response payload. The counts themselves are never capped.
MAX_SAMPLE_ERRORS = 25


@dataclass
class ParsedLogEntry:
    """Mirrors the `normalized_log_entries` table, minus the DB-generated id/log_id."""

    timestamp: datetime
    event_id: Optional[str] = None
    hostname: Optional[str] = None
    username: Optional[str] = None
    process_name: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    command_line: Optional[str] = None
    status: Optional[str] = None
    severity: LogSeverity = LogSeverity.INFO
    raw_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseStats:
    """
    Parsing statistics for one file.

    - total_records: every record/line/row the parser attempted to process
      (blank/comment lines that are intentionally and silently ignored are
      NOT counted here — see `skipped` for records that were seen but
      deliberately not turned into entries).
    - parsed: successfully converted into a ParsedLogEntry.
    - skipped: recognized as not applicable (e.g. a log line type this
      parser doesn't extract fields from) — not an error.
    - failed: the record was malformed/corrupted and could not be parsed.
    """

    total_records: int = 0
    parsed: int = 0
    skipped: int = 0
    failed: int = 0
    sample_errors: list[str] = field(default_factory=list)

    def record_error(self, message: str) -> None:
        self.failed += 1
        if len(self.sample_errors) < MAX_SAMPLE_ERRORS:
            self.sample_errors.append(message)

    def merge(self, other: "ParseStats") -> None:
        self.total_records += other.total_records
        self.parsed += other.parsed
        self.skipped += other.skipped
        self.failed += other.failed
        remaining = MAX_SAMPLE_ERRORS - len(self.sample_errors)
        if remaining > 0:
            self.sample_errors.extend(other.sample_errors[:remaining])

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "parsed": self.parsed,
            "skipped": self.skipped,
            "failed": self.failed,
            "sample_errors": self.sample_errors,
        }


@dataclass
class ParseResult:
    entries: list[ParsedLogEntry]
    stats: ParseStats
