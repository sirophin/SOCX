"""
Small shared helpers used across multiple parsers.
"""
from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Iterator, Optional


def safe_ip(value: Optional[str]) -> Optional[str]:
    """
    Returns `value` if it's a syntactically valid IPv4/IPv6 address,
    otherwise None. Postgres's INET column rejects invalid values outright,
    and one bad IP shouldn't fail an entire batch insert — the original
    string is preserved by the caller in `raw_fields` regardless.
    """
    if not value or value in ("-", "", "unknown"):
        return None
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        return None


def clean_str(value: Optional[str]) -> Optional[str]:
    """Normalizes empty/placeholder strings to None."""
    if value is None:
        return None
    value = value.strip()
    if not value or value in ("-", "N/A", "null", "NULL"):
        return None
    return value


def iter_raw_lines(file_path: Path) -> Iterator[bytes]:
    """
    Yields each line as raw bytes (newline stripped), reading in binary
    mode so a single line with invalid encoding can't derail the whole
    file — decoding is left to the caller, per line, so it can be handled
    as a per-record failure rather than a whole-file one.

    Opens the file eagerly (before returning), not lazily on first
    iteration — so a missing/unreadable file raises OSError immediately
    from the call site, where callers wrap this in try/except OSError to
    produce a clean ParserError rather than an ambiguous failure surfacing
    mid-iteration.
    """
    handle = open(file_path, "rb")

    def _generator() -> Iterator[bytes]:
        try:
            for raw_line in handle:
                yield raw_line.rstrip(b"\r\n")
        finally:
            handle.close()

    return _generator()
