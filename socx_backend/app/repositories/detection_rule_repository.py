"""
Detection rule repository — CRUD data access for `detection_rules`.
No rule-matching/execution logic here — that's a future Detection Engine
module built on top of this.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection_rule import DetectionRule, RuleSeverity


class DetectionRuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **fields) -> DetectionRule:
        rule = DetectionRule(**fields)
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_by_id(self, rule_id: uuid.UUID) -> DetectionRule | None:
        stmt = select(DetectionRule).where(DetectionRule.id == rule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> DetectionRule | None:
        stmt = select(DetectionRule).where(DetectionRule.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        enabled: Optional[bool] = None,
        severity: Optional[RuleSeverity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DetectionRule], int]:
        filters = []
        if enabled is not None:
            filters.append(DetectionRule.enabled == enabled)
        if severity is not None:
            filters.append(DetectionRule.severity == severity)

        base_stmt = select(DetectionRule)
        count_stmt = select(func.count()).select_from(DetectionRule)
        for f in filters:
            base_stmt = base_stmt.where(f)
            count_stmt = count_stmt.where(f)

        base_stmt = base_stmt.order_by(DetectionRule.name.asc()).limit(limit).offset(offset)

        results = await self.db.execute(base_stmt)
        total = await self.db.execute(count_stmt)
        return list(results.scalars().all()), total.scalar_one()

    async def list_enabled(self) -> list[DetectionRule]:
        """
        Returns every enabled rule, unpaginated. Used by the Detection
        Engine, which must evaluate the complete active rule set on every
        call — not a page of it, unlike the CRUD list() above.
        """
        stmt = select(DetectionRule).where(DetectionRule.enabled.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, rule: DetectionRule, **fields) -> DetectionRule:
        for key, value in fields.items():
            setattr(rule, key, value)
        await self.db.flush()
        return rule

    async def delete(self, rule: DetectionRule) -> None:
        await self.db.delete(rule)
        await self.db.flush()
