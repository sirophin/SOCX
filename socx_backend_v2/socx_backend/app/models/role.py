"""
Role model — Admin, Tier1 Analyst, Tier2 Analyst.
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPKMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class RoleName(str, enum.Enum):
    ADMIN = "Admin"
    TIER1_ANALYST = "Tier 1 Analyst"
    TIER2_ANALYST = "Tier 2 Analyst"


class Role(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[RoleName] = mapped_column(
        SAEnum(RoleName, name="role_name_enum", native_enum=True),
        unique=True,
        nullable=False,
    )
    # Fine-grained permission flags, e.g. {"can_close_incident": true, "can_manage_users": true}
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    users: Mapped[List["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
