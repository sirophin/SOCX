"""
Alert service — the acknowledge/close workflow actions, with domain-level
state guards and audit logging. List/Get are plain reads and go straight
from the API layer through AlertRepository without needing a service.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.repositories.alert_repository import AlertRepository
from app.repositories.audit_log_repository import AuditLogRepository

__all__ = ["AlertService", "AlertNotFoundError", "InvalidAlertStateError"]


class AlertNotFoundError(Exception):
    pass


class InvalidAlertStateError(Exception):
    """Raised when an action doesn't make sense for the alert's current status."""


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alerts = AlertRepository(db)
        self.audit = AuditLogRepository(db)

    async def acknowledge(
        self,
        alert_id: uuid.UUID,
        analyst_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Alert:
        """Claims the alert: status -> Investigating, and assigns the
        caller as its analyst."""
        alert = await self.alerts.get_by_id(alert_id)

        if alert is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")

        if alert.status == AlertStatus.CLOSED:
            raise InvalidAlertStateError("Cannot acknowledge a closed alert")

        await self.alerts.update_status(
            alert,
            AlertStatus.INVESTIGATING,
            analyst_id=analyst_id,
        )

        await self.audit.write(
            action="alert.acknowledge",
            target_entity="Alert",
            user_id=analyst_id,
            target_id=alert.id,
            ip_address=ip_address,
        )

        await self.db.commit()

        # Refresh all scalar fields (status, updated_at, etc.)
        await self.db.refresh(alert)

        # Refresh relationships used in AlertOut
        await self.db.refresh(
            alert,
            attribute_names=["rule", "analyst"],
        )

        return alert

    async def close(
        self,
        alert_id: uuid.UUID,
        analyst_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Alert:
        """Closes the alert: status -> Closed."""

        alert = await self.alerts.get_by_id(alert_id)

        if alert is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")

        if alert.status == AlertStatus.CLOSED:
            raise InvalidAlertStateError("Alert is already closed")

        await self.alerts.update_status(
            alert,
            AlertStatus.CLOSED,
        )

        await self.audit.write(
            action="alert.close",
            target_entity="Alert",
            user_id=analyst_id,
            target_id=alert.id,
            ip_address=ip_address,
        )

        await self.db.commit()

        # Refresh all scalar fields (status, updated_at, etc.)
        await self.db.refresh(alert)

        # Refresh relationships used in AlertOut
        await self.db.refresh(
            alert,
            attribute_names=["rule", "analyst"],
        )

        return alert
