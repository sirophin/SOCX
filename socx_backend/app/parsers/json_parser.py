"""
Parser for JSON log files. Supports two shapes:
  1. NDJSON / JSON Lines — one JSON object per line (most common for logs).
  2. A single top-level JSON array of objects.

Field mapping is case-insensitive and tries a list of common aliases per
normalized field (e.g. "user", "username", "account" all map to username).
Unmapped keys are preserved in full in `raw_fields` — nothing is discarded.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.log import LogSourceType
from app.parsers.base_parser import BaseParser, ParserError, ParserRegistry
from app.parsers.field_mapping import find_field, map_severity, parse_timestamp
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats
from app.parsers.utils import clean_str, safe_ip


def _s(obj: dict[str, Any], field_name: str) -> str | None:
    value = find_field(obj, field_name)
    return clean_str(str(value)) if value is not None else None


def _ip(obj: dict[str, Any], field_name: str) -> str | None:
    value = find_field(obj, field_name)
    return safe_ip(str(value)) if value is not None else None


@ParserRegistry.register
class JsonParser(BaseParser):
    source_type = LogSourceType.JSON

    def parse(self, file_path: Path) -> ParseResult:
        try:
            with open(file_path, "rb") as f:
                head = f.read(4096).lstrip()
        except OSError as exc:
            raise ParserError(f"Could not open file: {exc}") from exc

        if head[:1] == b"[":
            return self._parse_json_array(file_path)
        return self._parse_ndjson(file_path)

    # -- NDJSON (one object per line) ----------------------------------

    def _parse_ndjson(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []

        with open(file_path, "rb") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                stats.total_records += 1
                try:
                    text = line.decode("utf-8", errors="strict")
                    obj = json.loads(text)
                    if not isinstance(obj, dict):
                        raise ValueError("JSON line is not an object")
                    entries.append(self._build_entry(obj))
                    stats.parsed += 1
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                    stats.record_error(f"line {line_no}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    # -- Single JSON array of objects -----------------------------------

    def _parse_json_array(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ParserError(f"Top-level JSON array is malformed and could not be read: {exc}") from exc

        if not isinstance(data, list):
            raise ParserError("Expected a top-level JSON array")

        for idx, obj in enumerate(data):
            stats.total_records += 1
            try:
                if not isinstance(obj, dict):
                    raise ValueError("array element is not an object")
                entries.append(self._build_entry(obj))
                stats.parsed += 1
            except ValueError as exc:
                stats.record_error(f"element {idx}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    # -- shared field mapping --------------------------------------------

    def _build_entry(self, obj: dict[str, Any]) -> ParsedLogEntry:
        ts_raw = find_field(obj, "timestamp")
        timestamp = parse_timestamp(ts_raw) if ts_raw is not None else datetime.now(timezone.utc)

        return ParsedLogEntry(
            timestamp=timestamp,
            event_id=_s(obj, "event_id"),
            hostname=_s(obj, "hostname"),
            username=_s(obj, "username"),
            process_name=_s(obj, "process_name"),
            source_ip=_ip(obj, "source_ip"),
            destination_ip=_ip(obj, "destination_ip"),
            command_line=_s(obj, "command_line"),
            status=_s(obj, "status"),
            severity=map_severity(find_field(obj, "severity")),
            raw_fields=obj,
        )
