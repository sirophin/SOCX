"""
Pydantic schemas for the Detection Rule CRUD APIs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, IPvAnyAddress

from app.models.detection_rule import RuleSeverity


class DetectionRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    enabled: bool = True
    severity: RuleSeverity
    event_id: Optional[str] = Field(default=None, max_length=50)
    username: Optional[str] = Field(default=None, max_length=255)
    source_ip: Optional[IPvAnyAddress] = None
    process_name: Optional[str] = Field(default=None, max_length=500)
    command_contains: Optional[str] = None


class DetectionRuleCreate(DetectionRuleBase):
    pass


class DetectionRuleUpdate(BaseModel):
    """All fields optional — PATCH semantics, only supplied fields are changed."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    severity: Optional[RuleSeverity] = None
    event_id: Optional[str] = Field(default=None, max_length=50)
    username: Optional[str] = Field(default=None, max_length=255)
    source_ip: Optional[IPvAnyAddress] = None
    process_name: Optional[str] = Field(default=None, max_length=500)
    command_contains: Optional[str] = None


class DetectionRuleOut(DetectionRuleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DetectionRuleListResponse(BaseModel):
    items: list[DetectionRuleOut]
    total: int
    limit: int
    offset: int
