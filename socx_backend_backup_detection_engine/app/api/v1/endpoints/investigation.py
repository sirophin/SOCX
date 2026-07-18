"""
Investigation APIs — read-only querying of normalized_log_entries for SOC
analyst investigation workflows. This is the search/filter surface over
parsed log evidence produced by the Log Parser module; it has no write
path of its own (entries are only ever created by LogParsingService).
"""
from __future__ import annotations

import ipaddress
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.db.session import get_db
from app.models.log import LogSeverity
from app.models.user import User
from app.repositories.normalized_log_entry_repository import NormalizedLogEntryRepository
from app.schemas.normalized_log_entry import NormalizedLogEntryListResponse, NormalizedLogEntryOut

router = APIRouter(prefix="/investigation", tags=["Investigation"])


def _validate_ip(value: Optional[str]) -> Optional[str]:
    """Rejects a malformed source_ip filter with a clean 400 instead of
    letting an invalid value hit the database as a raw comparison error."""
    if value is None:
        return None
    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{value}' is not a valid IP address",
        )
    return value


@router.get("/entries", response_model=NormalizedLogEntryListResponse)
async def list_normalized_entries(
    username: Optional[str] = Query(default=None, description="Case-insensitive partial match"),
    source_ip: Optional[str] = Query(default=None, description="Exact IP match"),
    hostname: Optional[str] = Query(default=None, description="Case-insensitive partial match"),
    event_id: Optional[str] = Query(default=None, description="Exact match"),
    severity: Optional[LogSeverity] = Query(default=None),
    timestamp_from: Optional[datetime] = Query(default=None, description="Inclusive lower bound"),
    timestamp_to: Optional[datetime] = Query(default=None, description="Inclusive upper bound"),
    log_id: Optional[uuid.UUID] = Query(
        default=None, description="Restrict to entries parsed from one specific uploaded log"
    ),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NormalizedLogEntryListResponse:
    """
    Lists normalized log entries, most recent first, with optional filters.
    All filters are combined with AND when multiple are supplied.
    """
    validated_ip = _validate_ip(source_ip)

    repo = NormalizedLogEntryRepository(db)
    entries, total = await repo.list(
        username=username,
        source_ip=validated_ip,
        hostname=hostname,
        event_id=event_id,
        severity=severity,
        timestamp_from=timestamp_from,
        timestamp_to=timestamp_to,
        log_id=log_id,
        limit=limit,
        offset=offset,
    )
    return NormalizedLogEntryListResponse(
        items=[NormalizedLogEntryOut.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/entries/{entry_id}", response_model=NormalizedLogEntryOut)
async def get_normalized_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NormalizedLogEntryOut:
    repo = NormalizedLogEntryRepository(db)
    entry = await repo.get_by_id(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized log entry not found")
    return NormalizedLogEntryOut.model_validate(entry)
