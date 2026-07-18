"""
Pydantic schemas for the Alert Management APIs.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.alert import AlertSeverity, AlertSource, AlertStatus


class RuleRefOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class AnalystRefOut(BaseModel):
    id: uuid.UUID
    username: str

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: uuid.UUID
    rule: RuleRefOut
    severity: AlertSeverity
    status: AlertStatus
    source: AlertSource
    evidence: dict[str, Any]
    analyst: Optional[AnalystRefOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertOut]
    total: int
    limit: int
    offset: int
