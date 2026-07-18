"""
User management endpoints — demonstrates RBAC in practice.
Only Admins can list/create/deactivate users; any authenticated user can
read their own profile via /auth/me instead.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserOut],
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserOut]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        UserOut(id=u.id, username=u.username, email=u.email, role=u.role.name.value, is_active=u.is_active)
        for u in users
    ]


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserOut,
    dependencies=[Depends(require_roles(RoleName.ADMIN))],
)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id, username=user.username, email=user.email,
        role=user.role.name.value, is_active=user.is_active,
    )


@router.get(
    "/tier2-and-admin-example",
    response_model=list[UserOut],
    dependencies=[Depends(require_roles(RoleName.ADMIN, RoleName.TIER2_ANALYST))],
)
async def example_multi_role_route(db: AsyncSession = Depends(get_db)) -> list[UserOut]:
    """
    Example showing a route open to more than one role — Tier 2 Analysts
    and Admins, but not Tier 1 Analysts. Mirrors the "close incident"
    permission boundary from the architecture doc.
    """
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        UserOut(id=u.id, username=u.username, email=u.email, role=u.role.name.value, is_active=u.is_active)
        for u in users
    ]
