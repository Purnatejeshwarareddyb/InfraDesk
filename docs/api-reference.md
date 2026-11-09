# API reference

The authoritative, always-current reference is the interactive documentation served by the application
itself at **`/docs`** (works offline, Swagger UI is bundled) and the machine-readable
`/openapi.json`. A snapshot of the contract is kept in [openapi.json](openapi.json). This page is a
short guide.

## Conventions

- Base path `/api/v1`. Health endpoints are at the root: `GET /health`, `GET /ready`.
- Authentication: `POST /api/v1/auth/login` sets an **HttpOnly, SameSite=Lax** cookie. Browsers send it automatically.
  With curl keep a cookie jar: `curl -c jar -b jar ...`.
- Requests that change data from a browser must come from the same origin (or a configured `CORS_ORIGINS` entry); otherwise `403 csrf_check_failed`.
- Lists are paginated: `?page=1&page_size=20` (max 100) and return `{items, total, page, page_size, pages}`.
- Errors always have one shape and never contain stack traces:

```json
{"error": {"code": "validation_error", "message": "The request contains invalid data.",
           "details": [{"field": "title", "message": "String should have at least 5 characters"}]}}
```

| Status | Meaning |
|---|---|
| 401 | not signed in or session expired (`not_authenticated`, `session_expired`, `invalid_credentials`) |
| 403 | signed in but not allowed (`admin_required`, `csrf_check_failed`) |
| 404 | does not exist **or you may not see it** (a worker asking for someone else's ticket gets 404) |
| 409 | conflict (`username_taken`, `asset_tag_taken`) |
| 422 | invalid input (`validation_error`) or a broken business rule (`invalid_transition`, `resolution_required`, `last_admin`, ...) |

## Endpoints

| Method and path | Who | Purpose |
|---|---|---|
| `GET /health` | anyone | liveness and version |
| `GET /ready` | anyone | database reachable (503 `{"status":"not_ready"}` otherwise) |
| `POST /auth/login` | anyone | start a session |
| `POST /auth/logout` | anyone | end the session |
| `GET /auth/me` | signed in | current user |
| `POST /auth/change-password` | signed in | change own password (needs current password) |
| `GET /users`, `POST /users` | admin | list (search, role, active filters) / create |
| `GET /users/{id}`, `PATCH /users/{id}` | admin | read / change name, role, reset password |
| `POST /users/{id}/deactivate`, `/activate` | admin | block or allow sign-in |
| `GET /tickets` | signed in | list **visible** tickets: `q`, `status`, `priority`, `category`, `assignee_id`, `reporter_id`, `mine`, `created_from`, `created_to`, `sort` |
| `POST /tickets` | signed in | report a ticket |
| `GET /tickets/{id}` | visible | ticket with comments, history and `allowed_transitions` |
| `PATCH /tickets/{id}` | admin | edit title, description, category, priority, related asset |
| `POST /tickets/{id}/assign` | admin | assign to an active user |
| `POST /tickets/{id}/transition` | per rules | change status (`resolution_note` required for `RESOLVED`) |
| `POST /tickets/{id}/comments` | visible | add a comment or work note |
| `GET /tickets/{id}/history` | visible | event history |
| `GET /tickets/export.csv` | admin | CSV of the (filtered) tickets, formula-injection safe |
| `GET /assets`, `GET /assets/{id}` | signed in | list / read (`q`, `status`, `asset_type`, `include_retired`) |
| `POST /assets`, `PATCH /assets/{id}`, `POST /assets/{id}/retire` | admin | manage the register |
| `GET /notifications` | signed in | own notifications and `unread_count` |
| `POST /notifications/{id}/read`, `POST /notifications/read-all` | signed in | mark read |
| `GET /reports/summary` | signed in | dashboard counts (all tickets for admins, own for workers) and recent activity |
| `GET /reports/tickets` | admin | counts by status, category, priority, assignee; optional `date_from`, `date_to` |
| `GET /activity` | admin | audit trail (ticket, user and asset events) |

## Example with curl

```bash
curl -s -c jar -H 'Content-Type: application/json' \
     -d '{"username":"demo_admin","password":"Demo-Passw0rd!"}' http://localhost:8080/api/v1/auth/login
curl -s -b jar 'http://localhost:8080/api/v1/tickets?status=OPEN&sort=priority'
curl -s -b jar -o tickets.csv http://localhost:8080/api/v1/tickets/export.csv
```
