"""
Detection Rule CRUD endpoints.

Reading rules (list/get) is open to any authenticated, active analyst.
Creating, updating, and deleting rules requires the `can_manage_rules`
permission on the caller's role (already seeded: Admin and Tier 2 Analyst
have it, Tier 1 Analyst does not — see schema.sql's role seed data) via
the existing `require_permission` RBAC dependency. No new auth/RBAC logic
is introduced here.

Rule *execution* (matching rules against normalized_log_entries and
generating alerts) is intentionally not implemented — this module is
CRUD only.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, require_permission
from app.db.session import get_db
from app.models.detection_rule import RuleSeverity
from app.models.user import User
from app.repositories.detection_rule_repository import DetectionRuleRepository
from app.schemas.detection_rule import (
    DetectionRuleCreate,
    DetectionRuleListResponse,
    DetectionRuleOut,
    DetectionRuleUpdate,
)

router = APIRouter(prefix="/detection-rules", tags=["Detection Rules"])


def _payload_to_fields(payload: DetectionRuleCreate | DetectionRuleUpdate) -> dict:
    """Converts a validated schema into DB-ready field values (source_ip
    needs to go from Pydantic's IPvAnyAddress back to a plain string for
    the INET column)."""
    data = payload.model_dump(exclude_unset=isinstance(payload, DetectionRuleUpdate))
    if "source_ip" in data and data["source_ip"] is not None:
        data["source_ip"] = str(data["source_ip"])
    return data


@router.post("", response_model=DetectionRuleOut, status_code=status.HTTP_201_CREATED)
async def create_detection_rule(
    payload: DetectionRuleCreate,
    current_user: User = Depends(require_permission("can_manage_rules")),
    db: AsyncSession = Depends(get_db),
) -> DetectionRuleOut:
    repo = DetectionRuleRepository(db)
    rule = await repo.create(**_payload_to_fields(payload))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A detection rule named '{payload.name}' already exists",
        )
    await db.refresh(rule)
    return DetectionRuleOut.model_validate(rule)


@router.get("", response_model=DetectionRuleListResponse)
async def list_detection_rules(
    enabled: Optional[bool] = Query(default=None),
    severity: Optional[RuleSeverity] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DetectionRuleListResponse:
    repo = DetectionRuleRepository(db)
    rules, total = await repo.list(enabled=enabled, severity=severity, limit=limit, offset=offset)
    return DetectionRuleListResponse(
        items=[DetectionRuleOut.model_validate(r) for r in rules],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{rule_id}", response_model=DetectionRuleOut)
async def get_detection_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DetectionRuleOut:
    repo = DetectionRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection rule not found")
    return DetectionRuleOut.model_validate(rule)


@router.patch("/{rule_id}", response_model=DetectionRuleOut)
async def update_detection_rule(
    rule_id: uuid.UUID,
    payload: DetectionRuleUpdate,
    current_user: User = Depends(require_permission("can_manage_rules")),
    db: AsyncSession = Depends(get_db),
) -> DetectionRuleOut:
    repo = DetectionRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection rule not found")

    fields = _payload_to_fields(payload)
    if not fields:
        return DetectionRuleOut.model_validate(rule)

    await repo.update(rule, **fields)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A detection rule named '{payload.name}' already exists",
        )
    await db.refresh(rule)
    return DetectionRuleOut.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection_rule(
    rule_id: uuid.UUID,
    current_user: User = Depends(require_permission("can_manage_rules")),
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = DetectionRuleRepository(db)
    rule = await repo.get_by_id(rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection rule not found")
    await repo.delete(rule)
    await db.commit()
