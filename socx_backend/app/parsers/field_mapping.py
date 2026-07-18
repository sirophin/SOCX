"""
Shared field-alias mapping and timestamp/severity normalization, used by
both the JSON and CSV parsers (structurally similar problem: map
arbitrarily-named source fields onto the common schema).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.models.log import LogSeverity

FIELD_ALIASES: dict[str, list[str]] = {
    "timestamp": ["timestamp", "time", "@timestamp", "datetime", "date"],
    "event_id": ["event_id", "eventid", "event", "id"],
    "hostname": ["hostname", "host", "computer"],
    "username": ["username", "user", "account", "accountname"],
    "process_name": ["process_name", "process", "processname"],
    "source_ip": ["source_ip", "src_ip", "srcip", "client_ip", "ip"],
    "destination_ip": ["destination_ip", "dst_ip", "dstip", "dest_ip"],
    "command_line": ["command_line", "commandline", "message", "msg"],
    "status": ["status", "result"],
    "severity": ["severity", "level", "loglevel", "log_level"],
}

SEVERITY_MAP: dict[str, LogSeverity] = {
    "critical": LogSeverity.CRITICAL,
    "fatal": LogSeverity.CRITICAL,
    "error": LogSeverity.HIGH,
    "high": LogSeverity.HIGH,
    "warning": LogSeverity.MEDIUM,
    "warn": LogSeverity.MEDIUM,
    "medium": LogSeverity.MEDIUM,
    "low": LogSeverity.LOW,
    "info": LogSeverity.INFO,
    "information": LogSeverity.INFO,
    "debug": LogSeverity.INFO,
}


def find_field(obj: dict[str, Any], field_name: str) -> Optional[Any]:
    """Case-insensitive lookup of `field_name` against its alias list in `obj`."""
    lowered = {(k or "").strip().lower(): v for k, v in obj.items() if k is not None}
    for alias in FIELD_ALIASES[field_name]:
        if alias in lowered and lowered[alias] not in (None, ""):
            return lowered[alias]
    return None


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        ts = value / 1000 if value > 1e12 else value  # epoch ms vs seconds
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(value, str):
        candidate = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(candidate)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d/%b/%Y:%H:%M:%S %z"):
            try:
                dt = datetime.strptime(value.strip(), fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    raise ValueError(f"unrecognized timestamp value: {value!r}")


def map_severity(value: Any) -> LogSeverity:
    if isinstance(value, str):
        return SEVERITY_MAP.get(value.strip().lower(), LogSeverity.INFO)
    return LogSeverity.INFO
