"""
Shared FastAPI dependencies: DB session, current-user resolution, and
role/permission-based access control (RBAC) guards.
"""
from __future__ import annotations

from typing import Iterable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.services.auth_service import AuthError, AuthService

# HTTPBearer (rather than OAuth2PasswordBearer) since SOCX uses a JSON login
# body, not OAuth2 form-based password flow.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    try:
        user = await auth_service.get_current_user_from_access_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_roles(*allowed_roles: RoleName):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.post("/users", dependencies=[Depends(require_roles(RoleName.ADMIN))])
    or, to also use the resolved user in the handler:
        async def endpoint(user: User = Depends(require_roles(RoleName.ADMIN, RoleName.TIER2_ANALYST))):
    """
    async def _guard(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.name.value}' is not permitted to "
                    f"perform this action"
                ),
            )
        return current_user

    return _guard


def require_permission(permission_key: str):
    """
    Fine-grained RBAC based on the JSONB `permissions` map on the Role model
    (e.g. {"can_manage_users": true}), for cases where role name alone isn't
    granular enough (e.g. "can_close_incident").

    Usage:
        @router.patch("/incidents/{id}/status",
                       dependencies=[Depends(require_permission("can_close_incident"))])
    """
    async def _guard(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role.permissions.get(permission_key, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_key}",
            )
        return current_user

    return _guard


def get_client_ip(request: Request) -> str | None:
    """Best-effort client IP extraction, respecting a reverse proxy's X-Forwarded-For."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
