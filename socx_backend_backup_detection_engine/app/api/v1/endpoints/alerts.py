"""
Alert APIs: list, get, acknowledge, close.

Acknowledging/closing alerts is routine first-line SOC work (Tier 1
territory), so these endpoints are open to any authenticated, active
analyst — no extra permission gate, consistent with the logs/investigation
endpoints. (Contrast with Detection Rule management, which is gated
behind `can_manage_rules` since editing detection logic itself is a
higher-privilege action than triaging the alerts it produces.)
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_client_ip, get_current_active_user
from app.db.session import get_db
from app.models.alert import AlertSeverity, AlertSource, AlertStatus
from app.models.user import User
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertListResponse, AlertOut
from app.services.alert_service import AlertNotFoundError, AlertService, InvalidAlertStateError

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    severity: Optional[AlertSeverity] = Query(default=None),
    status_: Optional[AlertStatus] = Query(default=None, alias="status"),
    source: Optional[AlertSource] = Query(default=None),
    rule_id: Optional[uuid.UUID] = Query(default=None),
    analyst_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertListResponse:
    repo = AlertRepository(db)
    alerts, total = await repo.list(
        severity=severity,
        status=status_,
        source=source,
        rule_id=rule_id,
        analyst_id=analyst_id,
        limit=limit,
        offset=offset,
    )
    return AlertListResponse(
        items=[AlertOut.model_validate(a) for a in alerts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    repo = AlertRepository(db)
    alert = await repo.get_by_id(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertOut.model_validate(alert)


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    """Claims the alert (status -> Investigating) and assigns the caller as its analyst."""
    service = AlertService(db)
    try:
        alert = await service.acknowledge(alert_id, current_user.id, get_client_ip(request))
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidAlertStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AlertOut.model_validate(alert)


@router.patch("/{alert_id}/close", response_model=AlertOut)
async def close_alert(
    alert_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    """Closes the alert (status -> Closed). Does not change who's assigned."""
    service = AlertService(db)
    try:
        alert = await service.close(alert_id, current_user.id, get_client_ip(request))
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidAlertStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AlertOut.model_validate(alert)
