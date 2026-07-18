"""
DetectionRule model — configurable detection logic definitions.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.mitre_technique import MitreTechnique
    from app.models.alert import Alert


class DetectionRule(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "detection_rules"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Brute Force", "Web Attack"
    description: Mapped[str] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # e.g. {"failed_login_threshold": 10, "window_minutes": 5}
    threshold_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    mitre_technique_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mitre_techniques.id", ondelete="SET NULL"), nullable=True
    )
    mitre_technique: Mapped[Optional["MitreTechnique"]] = relationship(back_populates="detection_rules")

    alerts: Mapped[List["Alert"]] = relationship(back_populates="rule")

    def __repr__(self) -> str:
        return f"<DetectionRule {self.name}>"
