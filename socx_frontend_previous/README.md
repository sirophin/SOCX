# SOCX Frontend

React + Vite + Tailwind frontend for the SOCX SOC Monitoring & Incident
Response Platform, built against the existing FastAPI backend.

## Setup

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if not proxying in dev
npm run dev
```

Dev server runs on `http://localhost:5173` and proxies `/api/*` to
`http://localhost:8000` (your FastAPI backend) — see `vite.config.js`. Set
`VITE_API_PROXY_TARGET` if your backend runs elsewhere.

```bash
npm run build     # production build to dist/
npm run preview   # serve the production build locally
```

There's no backend user-creation endpoint — create your first user
directly in Postgres (see the backend README) before logging in.

## Architecture

```
src/
├── api/            Axios client + one module per backend resource
│   ├── client.js        axios instance, auth header injection, 401 refresh-and-retry
│   ├── tokenStore.js     token storage (see "Auth" below)
│   ├── authApi.js, logsApi.js, investigationApi.js,
│   │   detectionRulesApi.js, alertsApi.js, usersApi.js
├── auth/
│   ├── AuthContext.jsx   session state, login/logout, session restore on load
│   ├── ProtectedRoute.jsx    redirects to /login if not authenticated
│   └── RoleRoute.jsx         gates a route to specific roles (e.g. Users -> Admin)
├── components/
│   ├── layout/       Sidebar, Topbar, AppShell
│   └── common/       Badge, Button, Card, Table, Modal, Field (Input/Select/
│                      Textarea/Checkbox), Pagination, EmptyState, ErrorBanner,
│                      LoadingSpinner, StatCard
├── pages/            One file per route (see below)
├── hooks/useAuth.js
└── utils/            formatters.js, constants.js (enum values matching the backend exactly)
```

## Pages ↔ backend endpoints

| Page | Endpoints used |
|---|---|
| Login | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Dashboard | Composed client-side from `GET /alerts`, `/detection-rules`, `/investigation/entries`, `/logs` (the backend has no `/dashboard` aggregation endpoint yet — see note below) |
| Upload Logs | `POST /logs/upload`, `GET /logs`, `POST /logs/{id}/parse` |
| Investigation | `GET /investigation/entries`, `GET /investigation/entries/{id}` |
| Detection Rules | `GET/POST /detection-rules`, `GET/PATCH/DELETE /detection-rules/{id}` |
| Alerts | `GET /alerts`, `GET /alerts/{id}`, `PATCH /alerts/{id}/acknowledge`, `PATCH /alerts/{id}/close` |
| Users (Admin only) | `GET /users`, `PATCH /users/{id}/deactivate` |
| Settings | `GET /auth/me` (read-only — see note below) |

**Two things intentionally match backend gaps rather than inventing UI for
endpoints that don't exist:**
- **Dashboard** has no dedicated backend aggregation endpoint, so it's
  built from existing list endpoints' `total` counts, fetched in
  parallel. Real data, just assembled client-side.
- **Settings** is read-only and **Users** has no "create user" form —
  the backend only supports listing/deactivating users and reading your
  own profile; there's no profile-edit, password-change, or user-creation
  endpoint yet. Adding forms for those would 404.

## Auth flow

- **Access token**: kept in memory only (a module variable in
  `tokenStore.js`), never written to any storage — reduces the XSS
  exposure window, at the cost of not surviving a page reload on its own.
- **Refresh token**: the backend returns it directly in the JSON body
  (there's no httpOnly cookie in this API), so the frontend has no choice
  but to hold it somewhere JS-accessible to use it at all — stored in
  `localStorage` so a page reload doesn't force a fresh login.
- On load, `AuthContext` tries to turn a stored refresh token into a
  fresh access token + profile before deciding if you're logged in.
- The Axios response interceptor catches a `401`, transparently calls
  `/auth/refresh`, retries the original request once, and — if the
  refresh itself fails (expired/revoked token) — clears everything and
  routes back to `/login`. Concurrent 401s share a single in-flight
  refresh call rather than each independently rotating the refresh token
  and invalidating each other.
- `ProtectedRoute` gates all authenticated pages; `RoleRoute` additionally
  gates `/users` to `Admin`. Detection Rule create/edit/delete buttons are
  hidden (not just disabled) for roles without `can_manage_rules`
  (Admin, Tier 2 Analyst) — but this is a UX convenience, not a security
  boundary; the backend enforces the real permission check regardless.

## Design

Dark theme, blue/black/gray, built for a data-dense operational console
rather than a marketing page — per the platform's original design brief.
Token system in `tailwind.config.js`: `base` (surfaces), `ink` (text),
`accent` (blue, actions), plus dedicated `severity` and `statuscolor`
scales used consistently everywhere a severity or status appears.
Display type is Space Grotesk, body is Inter, data (IPs, event IDs,
hashes, command lines) renders in IBM Plex Mono. The signature element is
the `[SOCX]` bracket wordmark — a nod to log/terminal bracket notation —
echoed in the left-accent bar on the active nav item and the severity dot
inside each badge. Animation is deliberately minimal: color/background
transitions on hover and one loading spinner, nothing more, per the
platform's "no unnecessary animations" requirement.

## Verified

- `npm run build` completes cleanly (123 modules, no errors/warnings).
- No unused imports (checked programmatically across every page file).
- Every API call's request shape (query params, body, multipart fields)
  and every response shape it reads (`LogOut`, `AlertOut`,
  `DetectionRuleOut`, `NormalizedLogEntryOut`, etc.) were checked directly
  against the backend's actual Pydantic schemas and enum values — not
  assumed. In particular, `AlertStatus` values are Title Case
  (`"Open"`, `"Investigating"`, …) while severities are lowercase
  (`"low"`, `"high"`, …); `src/utils/constants.js` centralizes these
  exact-case value lists specifically so this isn't reproduced
  inconsistently across pages.

**Not verified**: full browser runtime behavior (this sandbox couldn't
keep a dev server alive across tool calls to test interactively) or an
actual end-to-end run against a live backend. Recommend `npm run dev`
against your running FastAPI instance and a manual click-through before
deploying.

## Known backend issue this frontend will surface

`AlertStatus`, `AlertSeverity`, `AlertSource`, `IncidentSeverity`,
`IncidentStatus`, `IOCType`, and `RoleName` are missing the
`values_callable` fix applied earlier to `LogSourceType`/`LogSeverity`/
`ParseStatus` — inserting/updating any of these columns will currently
fail against a real Postgres database with "invalid input value for
enum". This breaks Alert creation (including the Detection Engine) at
the database layer. It's a backend fix, out of scope for this frontend
change — flagging it here since the Alerts and Detection Rules pages
will be the first place it's visible.
