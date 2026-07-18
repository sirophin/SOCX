"""
Shared parsing logic for Apache/Nginx access logs in Combined Log Format
(the default for both servers):

  127.0.0.1 - frank [10/Oct/2023:13:55:36 -0700] "GET /path HTTP/1.1" 200 2326 "referrer" "user-agent"

Apache and Nginx subclass this with only `source_type` differing — the
line format is effectively identical, which is exactly the kind of
duplication the plugin/Strategy pattern is meant to avoid.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.models.log import LogSeverity
from app.parsers.base_parser import BaseParser, ParserError
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats
from app.parsers.utils import clean_str, iter_raw_lines, safe_ip

_COMBINED_LOG_RE = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+'
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)\s+(?P<protocol>[^"]+)"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)'
    r'(?:\s+"(?P<referrer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
)

# Signatures used for the web-attack detection rules (SQLi, XSS, dir enum) —
# extracted here at parse time so evidence is captured even before the
# Detection Engine exists; the engine will re-evaluate against normalized
# fields, this just avoids losing the raw path/query for later use.
_SQLI_PATTERN = re.compile(r"(\bunion\b.*\bselect\b|\bor\b\s+1=1|--|;--|/\*|\bdrop\b\s+\btable\b)", re.IGNORECASE)
_XSS_PATTERN = re.compile(r"(<script|%3cscript|onerror=|onload=|javascript:)", re.IGNORECASE)
_DIR_ENUM_PATTERN = re.compile(r"(\.\./|/etc/passwd|/wp-admin|/\.git/|/\.env)", re.IGNORECASE)


class CommonLogFormatParser(BaseParser):
    """Base class; subclasses only need to set `source_type`."""

    def parse(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []

        try:
            line_iter = iter_raw_lines(file_path)
        except OSError as exc:
            raise ParserError(f"Could not open file: {exc}") from exc

        for line_no, raw_line in enumerate(line_iter, start=1):
            if not raw_line.strip():
                continue

            stats.total_records += 1
            try:
                decoded = raw_line.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                stats.record_error(f"line {line_no}: invalid UTF-8 ({exc})")
                continue

            try:
                entry = self._parse_line(decoded)
                if entry is None:
                    stats.record_error(f"line {line_no}: does not match Combined Log Format")
                else:
                    entries.append(entry)
                    stats.parsed += 1
            except Exception as exc:  # noqa: BLE001
                stats.record_error(f"line {line_no}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    def _parse_line(self, line: str) -> ParsedLogEntry | None:
        match = _COMBINED_LOG_RE.match(line)
        if not match:
            return None

        try:
            # e.g. 10/Oct/2023:13:55:36 -0700
            timestamp = datetime.strptime(match["time"], "%d/%b/%Y:%H:%M:%S %z")
        except ValueError as exc:
            raise ValueError(f"unparseable timestamp '{match['time']}': {exc}") from exc

        status_code = match["status"]
        path = match["path"]
        method = match["method"]
        protocol = match["protocol"]
        request_target = f"{method} {path} {protocol}"

        severity = self._severity_for_status(status_code)
        # Escalate severity if the path matches a known web-attack signature,
        # regardless of HTTP status (an attack attempt is notable even if
        # the server returned a 404 or 403 for it).
        if _SQLI_PATTERN.search(path) or _XSS_PATTERN.search(path) or _DIR_ENUM_PATTERN.search(path):
            severity = LogSeverity.HIGH

        return ParsedLogEntry(
            timestamp=timestamp,
            event_id=None,
            hostname=None,
            username=clean_str(match["user"]),
            process_name=None,
            source_ip=safe_ip(match["ip"]),
            destination_ip=None,
            command_line=request_target,
            status=status_code,
            severity=severity,
            raw_fields={
                "method": method,
                "path": path,
                "protocol": protocol,
                "size": match["size"],
                "referrer": clean_str(match["referrer"]),
                "user_agent": clean_str(match["agent"]),
            },
        )

    @staticmethod
    def _severity_for_status(status_code: str) -> LogSeverity:
        try:
            code = int(status_code)
        except ValueError:
            return LogSeverity.INFO
        if code >= 500:
            return LogSeverity.HIGH
        if code in (401, 403):
            return LogSeverity.MEDIUM
        if code == 404 or 400 <= code < 500:
            return LogSeverity.LOW
        return LogSeverity.INFO
