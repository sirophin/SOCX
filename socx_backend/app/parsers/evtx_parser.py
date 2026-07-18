"""
Parser for Windows EVTX files, using the `evtx` library (Rust-backed,
via omerbenamram/evtx) rather than pure-Python XML parsing — it's
significantly faster and handles chunk-level corruption without pulling
down the whole file.

Corruption handling note: empirically (tested against both a real sample
EVTX and deliberately corrupted copies), `PyEvtxParser.records_json()`
does NOT yield RuntimeError objects for bad records — it *raises*
RuntimeError from the iterator itself, which would silently truncate a
plain for-loop. We drive the iterator manually with `next()` inside a
try/except so a single corrupt record/chunk is skipped and counted as
`failed`, and iteration continues through the rest of the file.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from evtx import PyEvtxParser

from app.models.log import LogSeverity, LogSourceType
from app.parsers.base_parser import BaseParser, ParserError, ParserRegistry
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats
from app.parsers.utils import clean_str, safe_ip

_LEVEL_SEVERITY_MAP = {
    0: LogSeverity.INFO,      # LogAlways
    1: LogSeverity.CRITICAL,  # Critical
    2: LogSeverity.HIGH,      # Error
    3: LogSeverity.MEDIUM,    # Warning
    4: LogSeverity.INFO,      # Information
    5: LogSeverity.INFO,      # Verbose
}

# Well-known auth-relevant event IDs get an explicit success/failure status.
_STATUS_BY_EVENT_ID = {
    "4624": "success",  # successful logon
    "4625": "failure",  # failed logon
    "4634": "success",  # logoff
    "4648": "success",  # explicit credential logon
    "4720": "success",  # user account created
    "4672": "success",  # special privileges assigned
}

# Fields worth promoting to top-level normalized columns, in priority order
# per target column (e.g. process name may appear under different names
# depending on the event type — process creation vs. service install).
_USERNAME_FIELDS = ("TargetUserName", "SubjectUserName", "AccountName")
_PROCESS_FIELDS = ("ProcessName", "NewProcessName", "ParentProcessName", "ServiceFileName")
_COMMAND_LINE_FIELDS = ("CommandLine",)
_IP_FIELDS = ("IpAddress",)


def _unwrap(value: Any) -> Any:
    """python-evtx-style JSON sometimes wraps attribute values as {'#text': ...}."""
    if isinstance(value, dict) and "#text" in value:
        return value["#text"]
    return value


def _first_present(data: dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        if key in data:
            value = clean_str(str(_unwrap(data[key])))
            if value:
                return value
    return None


@ParserRegistry.register
class EvtxParser(BaseParser):
    source_type = LogSourceType.EVTX

    def parse(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []

        try:
            parser = PyEvtxParser(str(file_path))
            record_iter = parser.records_json()
        except Exception as exc:  # noqa: BLE001 - whole-file open failure
            raise ParserError(f"Could not open EVTX file: {exc}") from exc

        while True:
            try:
                item = next(record_iter)
            except StopIteration:
                break
            except RuntimeError as exc:
                # A corrupt record/chunk — the underlying parser has already
                # advanced past it internally; counted and skipped.
                stats.record_error(f"corrupt record: {exc}")
                continue

            # Defensive: handle the documented (if unobserved) case where an
            # error is yielded rather than raised.
            if isinstance(item, Exception):
                stats.record_error(f"corrupt record: {item}")
                continue

            stats.total_records += 1
            try:
                entries.append(self._build_entry(item))
                stats.parsed += 1
            except Exception as exc:  # noqa: BLE001 - per-record failure only
                record_id = item.get("event_record_id", "unknown") if isinstance(item, dict) else "unknown"
                stats.record_error(f"record {record_id}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    def _build_entry(self, item: dict[str, Any]) -> ParsedLogEntry:
        try:
            event = json.loads(item["data"])
        except (KeyError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not parse record JSON: {exc}") from exc

        root = event.get("Event", {})
        system = root.get("System") or {}
        event_data = root.get("EventData") or root.get("UserData") or {}
        if not isinstance(event_data, dict):
            event_data = {}

        event_id_raw = _unwrap(system.get("EventID"))
        event_id = str(event_id_raw) if event_id_raw is not None else None

        time_created = system.get("TimeCreated") or {}
        system_time = None
        if isinstance(time_created, dict):
            system_time = (time_created.get("#attributes") or {}).get("SystemTime")
        if not system_time:
            raise ValueError("record has no System/TimeCreated/SystemTime")

        try:
            timestamp = datetime.fromisoformat(system_time.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"unparseable TimeCreated '{system_time}': {exc}") from exc

        level_raw = system.get("Level")
        severity = _LEVEL_SEVERITY_MAP.get(level_raw, LogSeverity.INFO) if isinstance(level_raw, int) else LogSeverity.INFO

        # Escalate: certain security-relevant event IDs are notable
        # regardless of the log's own Level field (e.g. 4625 failed logon
        # is only "Level 0" in the raw log but matters to a SOC).
        if event_id in ("4625",):
            severity = LogSeverity.MEDIUM
        elif event_id in ("4672", "4720", "1102", "7045"):
            severity = LogSeverity.HIGH if event_id == "1102" else LogSeverity.MEDIUM

        hostname = clean_str(system.get("Computer"))
        provider = (system.get("Provider") or {}).get("#attributes", {}).get("Name")
        channel = system.get("Channel")

        username = _first_present(event_data, _USERNAME_FIELDS)
        process_name = _first_present(event_data, _PROCESS_FIELDS)
        command_line = _first_present(event_data, _COMMAND_LINE_FIELDS)
        source_ip = safe_ip(_first_present(event_data, _IP_FIELDS))
        status = _STATUS_BY_EVENT_ID.get(event_id)

        raw_fields = {
            "provider": provider,
            "channel": channel,
            "event_record_id": system.get("EventRecordID"),
            "keywords": system.get("Keywords"),
            **event_data,
        }

        return ParsedLogEntry(
            timestamp=timestamp,
            event_id=event_id,
            hostname=hostname,
            username=username,
            process_name=process_name,
            source_ip=source_ip,
            destination_ip=None,
            command_line=command_line,
            status=status,
            severity=severity,
            raw_fields=raw_fields,
        )
