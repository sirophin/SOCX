"""
Pydantic schemas for the Log Upload module.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.log import LogSourceType


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
