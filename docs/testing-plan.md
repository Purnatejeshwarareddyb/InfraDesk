# Testing plan

## Strategy

| Level | Tool | Where | What it proves |
|---|---|---|---|
| Backend unit and API | pytest, FastAPI TestClient, a throw-away SQLite file per test | `backend/app/tests/` | rules, permissions, persistence, validation, error shapes |
| Migrations, scripts, backup/restore | pytest (subprocess against temporary databases) | `test_scripts_and_migrations.py` | schema creation, seed safety, backup integrity, restore confirmation |
| Static checks | `ruff`, `tsc`, ESLint, `shellcheck`, `yamllint`, `ansible-lint` | repository | style, type and obvious defects |
| Frontend component | Vitest, React Testing Library, jsdom, mocked `fetch` (tests only) | `frontend/src/tests/` | validation, protected routes, role-aware navigation, states, error handling |
| Browser end-to-end | Playwright, headless Chromium, real backend and real database | `e2e/browser_flow.py` | the whole workflow through the real UI |
| Plugin test | shell against a local fake HTTP server | `infrastructure/nagios/scripts/` | OK, WARNING, CRITICAL, UNKNOWN behaviour |
| Infrastructure | Docker, Terraform, Puppet, Ansible, Nagios commands | your Ubuntu VM | the DevOps layer works on a real host (**you run these**) |

## Requirement coverage (backend)

| Requirement from the specification | Test file and examples |
|---|---|
| Health and readiness, database unavailable | `test_health.py` (503 without leaking details) |
| Valid login, invalid login does not reveal the cause, inactive user blocked | `test_auth.py` |
| Cookie flags, expiry, wrong signature, immediate deactivation, CSRF origin check, hashing | `test_auth.py` |
| Worker blocked from admin routes, cannot see another worker's ticket, cannot promote self, extra JSON fields ignored | `test_permissions.py` |
| Ticket creation persists, validation errors, retired or unknown asset | `test_tickets.py` |
| Status transitions valid and invalid (eight illegal pairs, table vs specification), cancel, reopen, close | `test_tickets.py` |
| Assignment rules and history, comments in history, filters, search, sort, pagination, date range | `test_tickets.py` |
| CSV headers, escaping, formula injection, filters | `test_tickets.py` |
| Notifications created by real actions, read state persists, read all, actor not notified, readable status text | `test_notifications.py` |
| Asset create, list, update, duplicate tag, retire, search | `test_assets.py` |
| User create, validation, last-admin protection, password reset, activity log | `test_users.py` |
| Reports derived from actual records, worker scope, date range | `test_reports.py` |
| Migration creates every table, runs twice; seed guarded; create-admin; backup and restore | `test_scripts_and_migrations.py` |
| API docs served without CDN | `test_health.py` |

## Frontend tests (43)

Login validation and server error, redirects by role, protected routes (signed out, wrong role), 401 session-expired flow, role-aware navigation,
unread bell, ticket form validation, **API failure shows no success message**, loading, error and empty states, status and priority badges, pagination,
confirm dialog, API client error parsing.

## How to run everything

```bash
cd backend && ruff check . && pytest
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
python e2e/browser_flow.py ./shots        # see e2e/README.md for the setup
scripts/lint_all.sh                       # ruff, ESLint, shellcheck and yamllint if installed
```

## Infrastructure checks you must run (record real output in `reports/evidence/`)

`docker compose build`, `docker compose up -d` and `curl localhost:8080/ready`; create a ticket, `docker compose restart`, confirm it is still there; `make backup` then
`make restore FILE=...` on a disposable database; `terraform fmt -check`, `validate`, `plan`, `apply`, `destroy`; `puppet parser validate`, two applies, a drift correction;
`ansible-playbook --syntax-check`, `deploy.yml` twice, `validate.yml`, `rollback.yml`; `nagios -v` and the OK, CRITICAL, OK demonstration; the offline procedure.
Use [test-results-template.md](test-results-template.md) to record them. Anything you could not run is **NOT RUN**, with the reason.
