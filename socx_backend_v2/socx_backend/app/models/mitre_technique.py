"""
MITRE ATT&CK technique reference table.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.detection_rule import DetectionRule


class MitreTechnique(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "mitre_techniques"

    technique_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # e.g. T1110
    tactic: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. Credential Access
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. Brute Force
    description: Mapped[str] = mapped_column(Text, nullable=True)
    reference_url: Mapped[str] = mapped_column(String(500), nullable=True)

    detection_rules: Mapped[List["DetectionRule"]] = relationship(back_populates="mitre_technique")

    def __repr__(self) -> str:
        return f"<MitreTechnique {self.technique_id} - {self.name}>"
