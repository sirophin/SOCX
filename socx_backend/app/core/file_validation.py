"""
File validation for log uploads.

Two layers of validation, per the "don't trust the extension alone"
security practice from the architecture doc:
  1. Extension allow-list per source type.
  2. Lightweight content sniffing (magic bytes / decodability) — this is
     NOT log parsing (no field extraction), just a sanity check that the
     bytes plausibly match the claimed format.
"""
from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from app.models.log import LogSourceType


class UnsupportedFileTypeError(Exception):
    pass


class InvalidFileContentError(Exception):
    pass


# ---------------------------------------------------------------------------
# Extension allow-list per source type
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: dict[LogSourceType, set[str]] = {
    LogSourceType.EVTX: {".evtx"},
    LogSourceType.WINDOWS_SECURITY: {".evtx"},
    LogSourceType.LINUX_AUTH: {".log", ".txt"},
    LogSourceType.APACHE: {".log", ".txt"},
    LogSourceType.NGINX: {".log", ".txt"},
    LogSourceType.APPLICATION: {".log", ".txt"},
    LogSourceType.JSON: {".json"},
    LogSourceType.CSV: {".csv"},
}

# Source types this upload module actively accepts today, per the current
# requirements (Windows EVTX, Linux auth.log, Apache/Nginx, JSON, CSV).
# WINDOWS_SECURITY and APPLICATION remain in the schema/model for future
# modules (live monitoring / app-log ingestion) but are not yet exposed here.
ACCEPTED_SOURCE_TYPES: set[LogSourceType] = {
    LogSourceType.EVTX,
    LogSourceType.LINUX_AUTH,
    LogSourceType.APACHE,
    LogSourceType.NGINX,
    LogSourceType.JSON,
    LogSourceType.CSV,
}

_EVTX_MAGIC = b"ElfFile\x00"

# Filenames must not contain path separators or null bytes after sanitization.
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str) -> str:
    """
    Strips any directory components and unsafe characters, preventing
    path traversal (e.g. '../../etc/passwd') and null-byte injection.
    """
    name = PurePosixPath(filename.replace("\\", "/")).name
    name = name.replace("\x00", "")
    if not name or name in {".", ".."}:
        raise UnsupportedFileTypeError("Invalid filename")
    stem, dot, ext = name.rpartition(".")
    if dot:
        safe_stem = _UNSAFE_FILENAME_CHARS.sub("_", stem)[:200] or "file"
        safe_ext = _UNSAFE_FILENAME_CHARS.sub("", ext)[:10]
        return f"{safe_stem}.{safe_ext}"
    return _UNSAFE_FILENAME_CHARS.sub("_", name)[:200] or "file"


def validate_source_type_supported(source_type: LogSourceType) -> None:
    if source_type not in ACCEPTED_SOURCE_TYPES:
        raise UnsupportedFileTypeError(
            f"Source type '{source_type.value}' is not yet supported by the upload module"
        )


def validate_extension(filename: str, source_type: LogSourceType) -> None:
    allowed = ALLOWED_EXTENSIONS.get(source_type)
    if not allowed:
        raise UnsupportedFileTypeError(f"No allowed extensions configured for '{source_type.value}'")

    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in allowed:
        raise UnsupportedFileTypeError(
            f"File extension '{suffix or '(none)'}' is not allowed for source type "
            f"'{source_type.value}'. Allowed: {', '.join(sorted(allowed))}"
        )


def sniff_content(sample: bytes, source_type: LogSourceType) -> None:
    """
    Lightweight structural sanity check on the first chunk of the file.
    Deliberately shallow — full parsing is out of scope for this module.
    """
    if not sample:
        raise InvalidFileContentError("Uploaded file is empty")

    if source_type in (LogSourceType.EVTX, LogSourceType.WINDOWS_SECURITY):
        if not sample.startswith(_EVTX_MAGIC):
            raise InvalidFileContentError(
                "File does not have a valid EVTX header signature"
            )
        return

    if source_type == LogSourceType.JSON:
        try:
            text_start = sample.decode("utf-8", errors="strict").lstrip()
        except UnicodeDecodeError as exc:
            raise InvalidFileContentError("JSON file is not valid UTF-8 text") from exc
        if not text_start or text_start[0] not in "{[":
            raise InvalidFileContentError("File does not look like JSON (expected '{' or '[')")
        return

    # CSV, Linux auth.log, Apache, Nginx, application logs: plain text formats.
    try:
        sample.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidFileContentError(
            f"File does not appear to be valid UTF-8 text, required for '{source_type.value}'"
        ) from exc


def try_validate_json_fully(sample_is_full_file: bool, full_bytes: bytes) -> None:
    """
    Optional stricter check used only when the whole file fits in memory
    comfortably (small files) — attempts a full json.loads(). Not called
    for large files to avoid doing parsing-equivalent work here.
    """
    if not sample_is_full_file:
        return
    try:
        json.loads(full_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidFileContentError(f"File is not valid JSON: {exc}") from exc
