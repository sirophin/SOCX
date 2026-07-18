"""
Parser for Linux /var/log/auth.log (syslog format).

Handles the two record types the detection rules care about most:
  - sshd authentication attempts (Failed/Accepted password, invalid user)
  - sudo command execution

Any other syslog line is still captured as a generic entry (process +
message in raw_fields) rather than dropped, since it may still be useful
evidence even if this parser doesn't extract structured fields from it.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from app.models.log import LogSeverity, LogSourceType
from app.parsers.base_parser import BaseParser, ParserError, ParserRegistry
from app.parsers.schema import ParsedLogEntry, ParseResult, ParseStats
from app.parsers.utils import clean_str, iter_raw_lines, safe_ip

# Jul  8 10:15:23 hostname sshd[1234]: Failed password for invalid user admin from 203.0.113.5 port 51234 ssh2
_SYSLOG_LINE_RE = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>[\w.\-/]+)(\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$"
)

_SSH_AUTH_RE = re.compile(
    r"^(?P<result>Failed|Accepted)\s+(?P<method>\S+)\s+for\s+"
    r"(?:(?P<invalid>invalid user)\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)"
)

_SUDO_RE = re.compile(
    r"^\s*(?P<user>\S+)\s*:.*?\bUSER=(?P<target_user>\S+)\s*;\s*COMMAND=(?P<command>.*)$"
)

_NEW_USER_RE = re.compile(r"new user:\s*name=(?P<user>[^,\s]+)", re.IGNORECASE)


@ParserRegistry.register
class LinuxAuthParser(BaseParser):
    source_type = LogSourceType.LINUX_AUTH

    def parse(self, file_path: Path) -> ParseResult:
        stats = ParseStats()
        entries: list[ParsedLogEntry] = []
        current_year = datetime.now(timezone.utc).year

        try:
            line_iter = iter_raw_lines(file_path)
        except OSError as exc:
            raise ParserError(f"Could not open file: {exc}") from exc

        for line_no, raw_line in enumerate(line_iter, start=1):
            if not raw_line.strip():
                continue  # blank lines are silently ignored, not counted

            stats.total_records += 1
            try:
                decoded = raw_line.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                stats.record_error(f"line {line_no}: invalid UTF-8 ({exc})")
                continue

            try:
                entry = self._parse_line(decoded, current_year)
                if entry is None:
                    stats.skipped += 1
                else:
                    entries.append(entry)
                    stats.parsed += 1
            except Exception as exc:  # noqa: BLE001 - any parse failure is per-line
                stats.record_error(f"line {line_no}: {exc}")

        return ParseResult(entries=entries, stats=stats)

    def _parse_line(self, line: str, year: int) -> ParsedLogEntry | None:
        match = _SYSLOG_LINE_RE.match(line)
        if not match:
            return None  # doesn't look like a syslog line at all -> skipped

        month, day, time_str = match["month"], match["day"], match["time"]
        try:
            timestamp = datetime.strptime(
                f"{year} {month} {day} {time_str}", "%Y %b %d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError(f"unparseable timestamp '{month} {day} {time_str}': {exc}") from exc

        host = match["host"]
        process = match["process"]
        message = match["message"]

        username = None
        source_ip = None
        status = None
        command_line = None
        severity = LogSeverity.INFO
        event_id = None

        ssh_match = _SSH_AUTH_RE.match(message)
        sudo_match = _SUDO_RE.match(message)

        if ssh_match:
            result = ssh_match["result"]
            username = ssh_match["user"]
            source_ip = safe_ip(ssh_match["ip"])
            status = "success" if result == "Accepted" else "failure"
            severity = LogSeverity.INFO if result == "Accepted" else LogSeverity.MEDIUM
            event_id = "ssh_auth_failure" if result == "Failed" else "ssh_auth_success"
        elif sudo_match:
            username = sudo_match["user"]
            command_line = sudo_match["command"]
            status = "success"
            severity = LogSeverity.LOW
            event_id = "sudo_command"
        elif "new user" in message.lower():
            new_user_match = _NEW_USER_RE.search(message)
            username = new_user_match["user"] if new_user_match else None
            severity = LogSeverity.MEDIUM
            event_id = "new_user_created"

        return ParsedLogEntry(
            timestamp=timestamp,
            event_id=event_id,
            hostname=clean_str(host),
            username=clean_str(username),
            process_name=clean_str(process),
            source_ip=source_ip,
            destination_ip=None,
            command_line=clean_str(command_line),
            status=status,
            severity=severity,
            raw_fields={"process": process, "message": message},
        )
