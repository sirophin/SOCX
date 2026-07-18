# SOCX Backend — Models + Auth/RBAC Module

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file (or export env vars) — see `app/core/config.py` for all
available settings:

```
DATABASE_URL=postgresql+asyncpg://socx:socx@localhost:5432/socx
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
FRONTEND_ORIGIN=http://localhost:5173
```

Apply `schema.sql` and `migration_refresh_tokens.sql` to your Postgres
instance (or wire up Alembic using `app/models/__init__.py` as the
autogenerate target — see previous deliverable).

Create at least one user manually to log in with, e.g.:

```python
from app.core.security import hash_password
print(hash_password("your-password"))
# then INSERT INTO users (username, email, password_hash, is_active, role_id)
# VALUES ('admin', 'admin@socx.local', '<hash above>', true,
#         (SELECT id FROM roles WHERE name = 'Admin'));
```

## Run

```bash
uvicorn app.main:app --reload
```

Docs at `http://localhost:8000/docs`.

## Auth flow implemented

- `POST /api/v1/auth/login` — username/password → access token (15 min) +
  refresh token (7 days). Refresh token's `jti` is persisted in
  `refresh_tokens` for revocation.
- `POST /api/v1/auth/refresh` — rotates the refresh token: old one is marked
  revoked, a new one is issued and linked via `replaced_by_jti`. Reuse of an
  already-revoked refresh token revokes the entire token family for that
  user (stolen-token defense).
- `POST /api/v1/auth/logout` — revokes the given refresh token.
- `GET /api/v1/auth/me` — returns the current user, resolved from the
  access token via the `get_current_user` dependency.
- `GET /api/v1/users` and `/users/{id}/deactivate` — example Admin-only
  routes using `require_roles(RoleName.ADMIN)`.
- `GET /api/v1/users/tier2-and-admin-example` — example multi-role route
  using `require_roles(RoleName.ADMIN, RoleName.TIER2_ANALYST)`.

## RBAC usage pattern

```python
from app.api.v1.deps import require_roles, require_permission
from app.models.role import RoleName

@router.post("/incidents/{id}/close",
             dependencies=[Depends(require_permission("can_close_incident"))])
async def close_incident(...): ...

@router.get("/admin-only", dependencies=[Depends(require_roles(RoleName.ADMIN))])
async def admin_only(...): ...
```

## What was tested in the sandbox (no live Postgres available)

- All modules syntax-checked and the full FastAPI app imported cleanly;
  all 8 routes resolve correctly in the OpenAPI schema.
- `core/security.py` functionally tested: password hash/verify round-trip,
  access/refresh token issuance and decoding, rejection of wrong-token-type
  and tampered tokens.
- `require_roles` RBAC guard functionally tested: allows the correct role,
  rejects others with 403.
- **Not tested**: the full DB-backed login → refresh → logout flow, since
  no Postgres instance was available in this environment. Recommend
  running `pytest` against a real (or `testcontainers`) Postgres before
  relying on this in production.
