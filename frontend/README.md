# InfraDesk frontend

React 18 + TypeScript (strict) + Vite single-page app for the InfraDesk offline IT ticketing and asset system.
It talks only to the FastAPI backend in `../backend` over relative URLs. No data is mocked in the app.

## Run

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies to the backend
```

Start the backend first (default `http://localhost:8000`). The dev server proxies `/api`, `/health`, `/ready`,
`/docs` and `/openapi.json` to it, so the browser sees one origin and the HttpOnly session cookie just works.
To point at another backend: `VITE_BACKEND_URL=http://host:port npm run dev`.
Sign in with an account created by your administrator (demo data: `backend/scripts/seed_demo_data.py`).

## Scripts

| Command | What it does |
| --- | --- |
| `npm run dev` | Vite dev server with the API proxy |
| `npm run build` | `tsc -b` then production build into `dist/` |
| `npm run preview` | Serve `dist/` locally (same proxy) |
| `npm test` | Vitest + React Testing Library (jsdom), `vitest run` |
| `npm run lint` | ESLint |
| `npm run typecheck` | TypeScript project check, no output files |

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_BASE` | empty | Prefix for API calls. Leave empty: production nginx serves the app and proxies the API on the same origin. |
| `VITE_BACKEND_URL` | `http://localhost:8000` | Dev/preview proxy target only. |

## Structure

```
src/
  api/          client.ts (single fetch wrapper, ApiError, 401 handling), endpoints.ts, types.ts
  auth/         AuthProvider, authContext (useAuth), ProtectedRoute (sign-in + role gate)
  components/   AppShell, nav, Badges, DataTable, Pagination, FormField, ConfirmDialog, Modal, Toast,
                StateViews (loading/error/empty), BarList (CSS bar charts), NotificationBell, EventList
  hooks/        useAsync, useDebounced, useQueryState (filters kept in the URL), useDocumentTitle
  pages/        Login, NotFound, admin/*, worker/*, shared/* (dashboard, tickets, notifications, password)
  styles/       global.css (CSS variables, responsive layout)
  utils/        date.ts (UTC ISO to local time), labels.ts, validation.ts, events.ts
  tests/        Vitest suites; fetch is mocked only here
```

Routes: `/login`; administrators use `/admin/...` (dashboard, tickets, users, assets, reports, activity,
notifications, settings); workers use `/worker/...` (dashboard, tickets, create ticket, notifications, account).
Route guards are a convenience; the backend enforces every permission.

## Behaviour notes

- Session: HttpOnly cookie set by `POST /api/v1/auth/login`. No token is stored in JavaScript or localStorage.
- Any 401 (except from login and the start-up `/auth/me` probe) clears auth state and returns to `/login` with
  "Your session has expired".
- Ticket status buttons come from the ticket's `allowed_transitions`. The resolution note field appears only
  for Resolve. Assigning uses the assign action, never the transition endpoint.
- Success messages appear only after the API call succeeded; failures show the backend message.
- CSV download is a plain link to `/api/v1/tickets/export.csv` carrying the current filters. If the session
  has expired the browser receives the JSON error instead of a file.
- The unread notification count is polled every 30 seconds while the tab is visible.
- The dev proxy keeps the original Host header (`changeOrigin: false`) because the backend's CSRF check
  compares the browser's Origin with Host. Keep that in any reverse proxy (nginx: `proxy_set_header Host $http_host`).

## Rules for contributors

- No icons and no emoji anywhere in the UI. Use text labels, status chips and CSS shapes.
- No CDNs, web fonts or third-party network calls. System font stack only; everything is bundled.
- No mock data outside `src/tests`.
- Keep all HTTP in `src/api/client.ts`; parse errors there, not in components.
- This folder intentionally has no Dockerfile or nginx config; those are maintained separately.
