"""
Parser for CSV log files. Expects a header row; column names are matched
case-insensitively against the same alias lists used by the JSON parser
(see app.parsers.field_mapping). Extra/unmapped columns are preserved in
`raw_fields`.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.log import LogSourceType
from app.parsers.base_parser import BaseParser, ParserError, ParserRegistry
from app.parsers.field_mapping import find_field, map_severity, parse_timestamp
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats
from app.parsers.utils import clean_str, safe_ip


def _s(row: dict[str, Any], field_name: str) -> str | None:
    value = find_field(row, field_name)
    return clean_str(str(value)) if value is not None else None


def _ip(row: dict[str, Any], field_name: str) -> str | None:
    value = find_field(row, field_name)
    return safe_ip(str(value)) if value is not None else None


@ParserRegistry.register
class CsvParser(BaseParser):
    source_type = LogSourceType.CSV

    def parse(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []

        try:
            raw_bytes = file_path.read_bytes()
        except OSError as exc:
            raise ParserError(f"Could not open file: {exc}") from exc

        try:
            text = raw_bytes.decode("utf-8-sig")  # tolerate a BOM from Excel exports
        except UnicodeDecodeError as exc:
            raise ParserError(f"File is not valid UTF-8: {exc}") from exc

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise ParserError("CSV file has no header row")

        for row_no, row in enumerate(reader, start=2):  # header is row 1
            stats.total_records += 1
            try:
                if None in row and row[None]:
                    # DictReader puts overflow columns under key None when a
                    # row has more fields than the header — malformed row.
                    raise ValueError(
                        f"row has more columns than the header "
                        f"({len(reader.fieldnames) + len(row[None])} vs {len(reader.fieldnames)})"
                    )
                entries.append(self._build_entry(row))
                stats.parsed += 1
            except ValueError as exc:
                stats.record_error(f"row {row_no}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    def _build_entry(self, row: dict[str, Any]) -> ParsedLogEntry:
        ts_raw = find_field(row, "timestamp")
        timestamp = parse_timestamp(ts_raw) if ts_raw else datetime.now(timezone.utc)

        return ParsedLogEntry(
            timestamp=timestamp,
            event_id=_s(row, "event_id"),
            hostname=_s(row, "hostname"),
            username=_s(row, "username"),
            process_name=_s(row, "process_name"),
            source_ip=_ip(row, "source_ip"),
            destination_ip=_ip(row, "destination_ip"),
            command_line=_s(row, "command_line"),
            status=_s(row, "status"),
            severity=map_severity(find_field(row, "severity")),
            raw_fields={k: v for k, v in row.items() if k is not None},
        )
