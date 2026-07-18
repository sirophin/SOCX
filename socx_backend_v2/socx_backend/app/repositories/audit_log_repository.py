"""
Audit log repository — append-only writes for the security audit trail.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def write(
        self,
        action: str,
        target_entity: str,
        user_id: Optional[uuid.UUID] = None,
        target_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            target_entity=target_entity,
            target_id=target_id,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
