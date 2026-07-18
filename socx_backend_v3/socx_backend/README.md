# SOCX Backend — Models, Auth/RBAC, Log Upload, and Log Parser

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

## Log Parser Module

`POST /api/v1/logs/{log_id}/parse` — parses a previously uploaded file into
`normalized_log_entries`. Returns the updated `Log` record with
`parse_status`, `parsed_at`, and `parse_stats`.

```bash
curl -X POST http://localhost:8000/api/v1/logs/<log_id>/parse \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

`parse_stats` shape: `{"total_records": N, "parsed": N, "skipped": N,
"failed": N, "sample_errors": [...]}` — `sample_errors` is capped at 25
messages so a file with thousands of bad lines doesn't bloat the row; the
counts themselves are never capped.

**Modular parser design** (`app/parsers/`) — Strategy pattern, one class
per source, all registered against `LogSourceType` via `ParserRegistry`
(`@ParserRegistry.register`), so the parsing service never has an
if/elif chain and a new source is added by writing one new file:

| Source | File | Approach |
|---|---|---|
| EVTX | `evtx_parser.py` | `evtx` (Rust-backed) library, manual `next()`-driven iteration for per-record error recovery |
| Linux auth.log | `linux_auth_parser.py` | Regex on syslog format; extracts SSH auth attempts, sudo commands, new-user creation |
| Apache | `apache_parser.py` | Thin subclass of `common_log_format.py` (Combined Log Format regex) |
| Nginx | `nginx_parser.py` | Same base as Apache — default Nginx access log format is Combined Log Format |
| JSON | `json_parser.py` | NDJSON or top-level array; case-insensitive field-alias mapping (`app/parsers/field_mapping.py`) |
| CSV | `csv_parser.py` | Header-based `csv.DictReader`, same field-alias mapping as JSON |

All parsers return a common `ParseResult` (`app/parsers/schema.py`):
`entries: list[ParsedLogEntry]` in the shared normalized schema, plus
`stats: ParseStats`. This is what lets one pipeline/service handle every
source without source-specific code downstream.

**Malformed/corrupted file handling** — two tiers, matching the
`BaseParser` contract:
- **Per-record failures** (a bad line, a corrupt EVTX chunk, a malformed
  JSON object) are caught, counted in `stats.failed`, and parsing
  continues. The file ends up `parse_status = partial`.
- **Whole-file failures** (file can't be opened, top-level JSON array is
  malformed, empty CSV with no header) raise `ParserError`, caught by
  `LogParsingService`, which sets `parse_status = failed` with the error
  message in `parse_stats` — **not** a 5xx response; parsing is a
  best-effort operation on untrusted input by design.
- The EVTX case needed special handling: empirically, the `evtx` library's
  `records_json()` iterator *raises* `RuntimeError` for a corrupt
  record/chunk rather than yielding one (contrary to what its docstring
  suggests) — a plain `for` loop would silently truncate at the first
  corrupt chunk. The parser drives the iterator manually with `next()`
  inside a `try/except RuntimeError` so it recovers and keeps going. This
  was verified against a real sample EVTX file with random byte corruption
  injected (see testing notes below).

**Preserving the original file reference**: parsing never touches or moves
the raw uploaded file; every inserted `normalized_log_entries` row carries
`log_id` pointing back to the original `Log` row (and its `file_reference`
on disk), so the original evidence is always traceable from a normalized
entry.

**Re-parsing**: by default, parsing an already-`completed`/`partial` log
returns `409 Conflict`. Pass `{"force": true}` to re-parse — this deletes
the log's existing `normalized_log_entries` first, then re-inserts, so
results aren't duplicated.

**Performance note**: parsing runs via `asyncio.to_thread()` rather than
directly on the event loop, since regex/EVTX-binary/CSV/JSON parsing is
CPU-bound synchronous work — this keeps one large file from stalling other
requests. For very large files or many concurrent uploads, the natural
next step (per the architecture doc) is moving this to a Celery/RQ worker
queue instead of an in-request thread.

**New migration**: `parse_status`, `parsed_at`, `parse_stats` columns were
added to `logs` (not in the original Section-5 schema) — see
`migration_log_parsing_fields.sql`.

**Not implemented in this module** (by design, per current scope): the
Detection Engine. Parsing stops at producing `normalized_log_entries` rows.

---

## What was tested in the sandbox (no live Postgres available)

- All modules syntax-checked and the full FastAPI app imports cleanly; all
  12 routes resolve correctly in the OpenAPI schema, each with the expected
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
- **Parsers — all six tested against real/synthetic files with
  deliberately malformed records, not just imported:**
  - EVTX: parsed a real 2261-record sample file downloaded from the
    `evtx` library's own test fixtures (100% success). Then tested against
    a copy with 500 random byte flips injected — 1700 records still parsed
    correctly, 8 corrupt chunks caught and counted in `stats.failed`, zero
    crashes, confirming the manual `next()` error-recovery loop works
    against real corruption, not just a mocked scenario.
  - Linux auth.log: SSH failed/accepted logins, sudo commands, and new-user
    creation all correctly extracted from synthetic lines; a
    non-syslog-format line correctly counted as `skipped`.
  - Apache: Combined Log Format lines parsed correctly, including
    correctly elevating severity on SQLi/XSS/path-traversal signatures in
    the request path; one deliberately malformed line correctly counted
    as `failed`.
  - JSON: both NDJSON and top-level-array shapes tested, including a
    non-JSON line, a truncated object, and a non-object array element —
    all correctly caught as per-record failures without aborting the file.
  - CSV: header-based column mapping verified; a row with extra columns
    beyond the header correctly caught as `failed`.
  - In every test, `len(result.entries) == result.stats.parsed` was
    asserted to hold — the stats and the actual returned data never
    silently diverge.

**Not tested**: the full DB-backed flows end-to-end (login → refresh →
logout, log upload → metadata row → listing, and parse → bulk insert →
`normalized_log_entries` rows persisted), since no Postgres instance was
available in this environment. The storage→parser integration (file saved
by `FileStorageService`, then read and parsed by the correct
`ParserRegistry`-resolved parser) *was* verified end-to-end; only the final
DB-write step is unverified. Recommend running `pytest` against a real (or
`testcontainers`) Postgres before relying on this in production.
