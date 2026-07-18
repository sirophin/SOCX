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
| Dashboard | Composed from six independent widgets, each polling its own endpoint every 10s — see "Dashboard widgets" below (the backend has no `/dashboard` aggregation endpoint yet) |
| Upload Logs | `POST /logs/upload`, `GET /logs`, `POST /logs/{id}/parse` |
| Investigation | `GET /investigation/entries`, `GET /investigation/entries/{id}` |
| Detection Rules | `GET/POST /detection-rules`, `GET/PATCH/DELETE /detection-rules/{id}` |
| Alerts | `GET /alerts`, `GET /alerts/{id}`, `PATCH /alerts/{id}/acknowledge`, `PATCH /alerts/{id}/close` |
| Users (Admin only) | `GET /users`, `PATCH /users/{id}/deactivate` |
| Sample Datasets | None — static catalog + static files, see below |
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

## Dashboard widgets

Six independent widgets (`src/components/dashboard/`), each owning its own
fetch, auto-refresh, skeleton, and error handling — one slow or failing
widget never blocks or blanks the others:

| Widget | Data source | Chart |
|---|---|---|
| KPI row | `GET /alerts` (×3, filtered), `/detection-rules?enabled=true`, `/investigation/entries` — all `limit=1`, reading `.total` | — |
| Alerts by Severity | `GET /alerts?severity=X&limit=1` × 4 | Horizontal bar |
| Alerts by Status | `GET /alerts?status=X&limit=1` × 5 | Horizontal bar |
| Alert Volume (7 days) | `GET /alerts?limit=100`, bucketed by day client-side | Area |
| Recent Alerts | `GET /alerts?limit=5` | — |
| Recent Log Uploads | `GET /logs?limit=5` | — |

**Auto-refresh** (`src/hooks/useAutoRefresh.js`): polls every 10 seconds.
Distinguishes the *first* load (shows a skeleton) from every load after
that (background refresh — existing data stays on screen, a small
pulsing dot next to the widget title indicates a refresh is in flight).
If a background poll fails, the widget keeps showing its last good data
with a small inline "last refresh failed" banner, rather than blanking —
only a failure on the very first load shows a full error state. Polling
pauses while the browser tab is hidden (`visibilitychange`) and refreshes
immediately when it becomes visible again, rather than polling a tab
nobody's looking at.

**Alert Volume's honesty caveat**: the backend has no time-bucketed
aggregation endpoint, so this chart buckets the most recent 100 alerts by
day client-side. If there are more than 100 alerts within the 7-day
window, the widget says so explicitly in its subtitle ("Based on the most
recent N of M alerts") rather than silently under-reporting.

Charts use `recharts`, colored from `src/utils/chartColors.js` (kept in
sync with the Tailwind `severity`/`statuscolor` token scales — SVG chart
libraries need real hex values, not Tailwind classes). Given `recharts`
pulls in `d3` internals and is by far the heaviest dependency, it's
split into its own build chunk (`vite.config.js` → `manualChunks`) so it
caches independently from app code that changes far more often.



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

## Sample Datasets

Browse/download curated sample log files for testing SOCX itself (Upload
Logs, Detection Rules) — grouped by category (Windows, Linux, Apache,
Nginx, Firewall, IDS, VPN), with search and a category filter.

**Frontend-only, as requested** — no backend endpoint exists for this
yet:
- The catalog (`src/data/sampleDatasets.js`) is static data, not fetched
  from an API.
- **Download** works today anyway, with zero backend involvement: every
  file is real, sitting in `public/sample-datasets/`, served as a static
  asset. The Windows sample is an actual captured Windows Security event
  log (the same real fixture used earlier to build and test the
  backend's EVTX parser — not synthesized). The Linux/Apache/Nginx
  samples are synthetic but were verified by running them through the
  *actual* backend parsers before being added here (100% parsed, 0
  failures each) — genuinely realistic, immediately usable as real
  Upload-Logs test data, not just cosmetic mockups. Firewall/IDS/VPN
  don't have a backend parser yet, so those three are illustrative only.
- **Import is disabled everywhere**, labeled "Import (Coming Soon)" with
  a tooltip — there's no import endpoint yet, so it's honestly marked
  rather than wired to silently do nothing.
- `expectedAlerts` on each card is a curated training figure (how many
  distinct suspicious indicators that dataset was designed to contain),
  not a live Detection Engine count — there's no default rule set
  pre-seeded, so that can't be computed automatically yet.

Reusable components (`src/components/datasets/`): `DatasetCard`,
`CategorySection`, `DatasetFilters`. `Badge` (shared, `src/components/
common/Badge.jsx`) gained a third `kind="difficulty"` style map,
additive only — reuses the existing severity color scale rather than
inventing new tokens, since difficulty and severity both express "how
much this demands your attention."

**Scope discipline**: per the request, this feature did not touch
authentication, the dashboard, alerts, investigation, or any existing
API module. The only pre-existing files touched at all are `Badge.jsx`
(additive), `Sidebar.jsx` (one nav entry + one icon), and `App.jsx` (one
route registration) — the same minimal wiring pattern used every time a
new page was added earlier in this project.

## Verified

- `npm run build` completes cleanly (932 modules — recharts adds a lot —
  no errors/warnings; three chunks: app 62KB, vendor 211KB, charts 383KB,
  all gzip well under typical size budgets).
- No unused imports (checked programmatically across every page and
  dashboard widget file).
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
keep a dev server alive across tool calls to test interactively, or
observe actual 10-second refresh cycles firing in a live browser) or an
actual end-to-end run against a live backend. The `useAutoRefresh` hook
follows standard, well-understood React patterns (interval + ref to avoid
stale closures + visibilitychange), and every file compiles and bundles
correctly, but recommend `npm run dev` against your running FastAPI
instance and watching the Network tab for a few refresh cycles before
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
