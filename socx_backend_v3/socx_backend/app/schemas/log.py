"""
Pydantic schemas for the Log Upload and Log Parser modules.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.log import LogSourceType, ParseStatus


class UploadedByOut(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class LogOut(BaseModel):
    id: uuid.UUID
    source_type: LogSourceType
    original_filename: str
    file_size_bytes: Optional[int]
    ingested_at: datetime
    uploaded_by: Optional[UploadedByOut] = None
    parse_status: ParseStatus
    parsed_at: Optional[datetime] = None
    parse_stats: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    items: list[LogOut]
    total: int
    limit: int
    offset: int


class LogListParams(BaseModel):
    source_type: Optional[LogSourceType] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ParseRequest(BaseModel):
    force: bool = Field(
        default=False,
        description="If true, re-parse and replace any previously normalized entries for this log.",
    )
