"""
Alert repository — creation of Alert rows (and their evidence link to the
originating normalized_log_entries row) from a Detection Engine match,
plus the read/status-update data access needed by the Alert Management
APIs (list, get, acknowledge, close).
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert, AlertLogEntry, AlertSeverity, AlertSource, AlertStatus
from app.models.detection_rule import DetectionRule
from app.models.log import NormalizedLogEntry


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_from_match(
        self,
        rule: DetectionRule,
        entry: NormalizedLogEntry,
        severity: AlertSeverity,
        source: AlertSource,
        matched_conditions: dict,
    ) -> Alert:
        """
        Creates an Alert for `rule` matching `entry`, with an evidence
        snapshot of what matched, and links the alert to the originating
        log entry via alert_log_entries so the evidence stays traceable.
        """
        evidence = {
            "rule_id": str(rule.id),
            "rule_name": rule.name,
            "matched_conditions": matched_conditions,
            "log_entry_id": str(entry.id),
            "log_entry_snapshot": {
                "timestamp": entry.timestamp.isoformat(),
                "event_id": entry.event_id,
                "hostname": entry.hostname,
                "username": entry.username,
                "process_name": entry.process_name,
                "source_ip": str(entry.source_ip) if entry.source_ip is not None else None,
                "destination_ip": str(entry.destination_ip) if entry.destination_ip is not None else None,
                "command_line": entry.command_line,
                "status": entry.status,
            },
        }

        alert = Alert(
            rule_id=rule.id,
            severity=severity,
            source=source,
            evidence=evidence,
        )
        self.db.add(alert)
        await self.db.flush()  # need alert.id before creating the evidence link

        self.db.add(AlertLogEntry(alert_id=alert.id, log_entry_id=entry.id))
        await self.db.flush()

        return alert

    # --- Alert Management support ----------------------------------------

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        stmt = (
            select(Alert)
            .options(selectinload(Alert.rule), selectinload(Alert.analyst))
            .where(Alert.id == alert_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        source: Optional[AlertSource] = None,
        rule_id: Optional[uuid.UUID] = None,
        analyst_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Alert], int]:
        filters = []
        if severity is not None:
            filters.append(Alert.severity == severity)
        if status is not None:
            filters.append(Alert.status == status)
        if source is not None:
            filters.append(Alert.source == source)
        if rule_id is not None:
            filters.append(Alert.rule_id == rule_id)
        if analyst_id is not None:
            filters.append(Alert.analyst_id == analyst_id)

        base_stmt = select(Alert).options(selectinload(Alert.rule), selectinload(Alert.analyst))
        count_stmt = select(func.count()).select_from(Alert)
        for f in filters:
            base_stmt = base_stmt.where(f)
            count_stmt = count_stmt.where(f)

        base_stmt = base_stmt.order_by(Alert.created_at.desc()).limit(limit).offset(offset)

        results = await self.db.execute(base_stmt)
        total = await self.db.execute(count_stmt)
        return list(results.scalars().all()), total.scalar_one()

    async def update_status(
        self,
        alert: Alert,
        status: AlertStatus,
        analyst_id: Optional[uuid.UUID] = None,
    ) -> Alert:
        """Updates alert.status, and alert.analyst_id only if `analyst_id`
        is explicitly provided (None means "leave it as-is", not "clear
        it") — acknowledge sets it, close leaves whoever's assigned
        untouched."""
        alert.status = status
        if analyst_id is not None:
            alert.analyst_id = analyst_id
        await self.db.flush()
        return alert
