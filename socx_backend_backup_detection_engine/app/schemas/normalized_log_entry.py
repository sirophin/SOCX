"""
Pydantic schemas for the Investigation APIs (read-side of
normalized_log_entries).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, IPvAnyAddress

from app.models.log import LogSeverity


class NormalizedLogEntryOut(BaseModel):
    id: uuid.UUID
    log_id: uuid.UUID
    timestamp: datetime
    event_id: Optional[str] = None
    hostname: Optional[str] = None
    username: Optional[str] = None
    process_name: Optional[str] = None
    source_ip: Optional[IPvAnyAddress] = None
    destination_ip: Optional[IPvAnyAddress] = None
    command_line: Optional[str] = None
    status: Optional[str] = None
    severity: LogSeverity
    raw_fields: dict[str, Any]

    model_config = {"from_attributes": True}


class NormalizedLogEntryListResponse(BaseModel):
    items: list[NormalizedLogEntryOut]
    total: int
    limit: int
    offset: int
