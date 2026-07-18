"""
Pydantic schemas for the Attack Simulator APIs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SimulatorStatusOut(BaseModel):
    running: bool
    started_at: Optional[datetime] = None
    events_generated: int
    alerts_generated: int
    last_event_at: Optional[datetime] = None
    last_error: Optional[str] = None
    interval_seconds: int


class SimulatorActionResponse(BaseModel):
    running: bool
    message: str
