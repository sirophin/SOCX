# SOCX Backend — Models, Auth/RBAC, and Log Upload

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
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=100
```

Apply `schema.sql` and `migration_refresh_tokens.sql` (from earlier
deliverables) to your Postgres instance, or wire up Alembic using
`app/models/__init__.py` as the autogenerate target.

Create at least one user manually to log in with:

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

---

## Auth flow (JWT + RBAC)

- `POST /api/v1/auth/login` — username/password → access token (15 min) +
  refresh token (7 days). Refresh token's `jti` is persisted in
  `refresh_tokens` for revocation.
- `POST /api/v1/auth/refresh` — rotates the refresh token: old one is marked
  revoked, a new one is issued and linked via `replaced_by_jti`. Reuse of an
  already-revoked refresh token revokes the entire token family for that
  user (stolen-token defense).
- `POST /api/v1/auth/logout` — revokes the given refresh token.
- `GET /api/v1/auth/me` — returns the current user, resolved from the
  access token.
- `GET /api/v1/users`, `/users/{id}/deactivate` — example Admin-only routes.
- `GET /api/v1/users/tier2-and-admin-example` — example multi-role route.

RBAC usage pattern:

```python
from app.api.v1.deps import require_roles, require_permission
from app.models.role import RoleName

@router.post("/incidents/{id}/close",
             dependencies=[Depends(require_permission("can_close_incident"))])
async def close_incident(...): ...

@router.get("/admin-only", dependencies=[Depends(require_roles(RoleName.ADMIN))])
async def admin_only(...): ...
```

---

## Log Upload Module

`POST /api/v1/logs/upload` — multipart form with `file` and `source_type`
(one of: `evtx`, `linux_auth_log`, `apache_access`, `nginx`, `json`, `csv`).
Any authenticated, active user (Admin/Tier 1/Tier 2) can upload — log
collection isn't a privileged action.

```bash
curl -X POST http://localhost:8000/api/v1/logs/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "source_type=linux_auth_log" \
  -F "file=@auth.log"
```

Validation performed (see `app/core/file_validation.py`):
- Extension allow-list per source type (e.g. `.evtx` only for EVTX, `.json`
  only for JSON).
- Filename sanitization — strips directory components and unsafe
  characters, blocking path traversal.
- Lightweight content sniffing on the first chunk (EVTX magic bytes, JSON
  structural check, UTF-8 decodability for text formats) — **not** full
  parsing, just a sanity check that bytes match the claimed format.
- Streamed to disk in 1MB chunks with a hard cap (`MAX_UPLOAD_SIZE_MB`,
  default 100MB); any partial file is deleted if validation or the size cap
  fails mid-stream.

Storage layout: `uploads/<source_type>/<yyyy>/<mm>/<uuid>_<filename>` —
avoids unbounded directory sizes and is easy to swap for object storage
(S3-compatible) later.

`GET /api/v1/logs` — paginated list, filterable by `source_type` and
`mine_only`. `GET /api/v1/logs/{id}` — single record.

**Not implemented in this module** (by design, per current scope): parsing
file contents into `normalized_log_entries`, and a download endpoint for
retrieving a previously uploaded raw file.

**Note on source types**: the `logs` table/enum also includes
`windows_security` and `application_log`, defined in the original schema
for future modules (live Windows monitoring, app-log ingestion). This
upload module deliberately only accepts the six source types listed above,
per current requirements — uploading those two returns `415`.

---

## What was tested in the sandbox (no live Postgres available)

- All modules syntax-checked and the full FastAPI app imports cleanly; all
  11 routes resolve correctly in the OpenAPI schema, each with the expected
  `HTTPBearer` security requirement.
- `core/security.py`: password hash/verify round-trip, access/refresh token
  issuance and decoding, rejection of wrong-token-type and tampered tokens.
- `require_roles` RBAC guard: allows the correct role, rejects others with
  403.
- `core/file_validation.py`: filename sanitization (path traversal
  blocked), extension allow-list enforcement, content sniffing for EVTX/
  JSON/text formats, empty-file rejection.
- `services/file_storage_service.py`, full round trip against a real temp
  directory: successful save + byte-for-byte integrity check, bad-content
  rejection with no partial file left behind, size-limit enforcement with
  cleanup, and path-traversal filename containment verified against the
  resolved upload directory.

**Not tested**: the full DB-backed flows (login → refresh → logout, and log
upload → metadata row → listing), since no Postgres instance was available
in this environment. Recommend running `pytest` against a real (or
`testcontainers`) Postgres before relying on this in production.
