# Viva questions and answers (based on what is implemented)

## Project
**Why InfraDesk?** Equipment faults are reported informally and forgotten. It gives one place for assets, tickets, assignment and history, usable offline in a lab.
**Who are the users?** Administrators (manage users, assets, assignment, close tickets, reports) and workers (report faults, work on assigned tickets).
**What is out of scope?** E-mail, HTTPS termination, multi-node deployment, PostgreSQL, load testing.

## Architecture
**Why FastAPI and SQLite?** Typed validation, automatic OpenAPI, small footprint; SQLite needs no server and suits a small offline group. WAL mode and foreign keys are enabled.
**Where are business rules?** In the service layer (`app/services`), not in routes. Status rules are one `TRANSITIONS` table in `ticket_service.py`.
**How does the frontend know which buttons to show?** The API returns `allowed_transitions` per ticket; the UI renders those only.
**Why nginx in front?** It serves the built SPA and proxies `/api`, so the browser sees one origin; no CORS wildcard is needed.

## Security
**How are passwords stored?** Argon2 hashes; never plaintext or logged.
**How is a session kept?** JWT in an HttpOnly, SameSite=Lax cookie. The user is reloaded from the database each request, so deactivation takes effect at once.
**CSRF?** SameSite plus an Origin-header check on write requests.
**Role enforcement?** On the backend (dependencies); the frontend hiding is only convenience. Workers see only their own or assigned tickets; others return 404.
**Login errors?** One generic message and a dummy hash comparison to reduce user enumeration by timing.
**CSV export risk?** Cells starting with `=`, `+`, `-`, `@` are neutralised.

## Database
**Tables?** users, assets, tickets, comments, notifications, audit_events (see `database-design.md`). Deletes are RESTRICT; assets are retired, not deleted.
**Migrations?** Alembic; `0001_initial_schema` creates everything and can run twice safely.
**Timestamps?** Stored as naive UTC by a custom type and returned timezone-aware.

## DevOps
**Docker Compose?** Two containers (backend, nginx frontend), non-root, `no-new-privileges`, all capabilities dropped, memory limits; only the frontend port is published.
**Terraform?** Provisions its own `infradesk-tf-*` network, volume and containers on port 8081 with the Docker provider. It is an alternative to Compose, not a second owner of the same containers.
**Puppet?** Host baseline with `puppet apply`: packages, service user, folders, env file, Docker service, backup timer. Idempotent by design; no master/agent.
**Ansible?** Deploy, validate and roll back the application under `/opt/infradesk/app`, with release records.
**Nagios?** Checks `/health`, `/ready`, port, disk, load, Docker every minute; HARD CRITICAL after 3 failures. **It does not auto-repair**; a person runs the recover play or `make up`.
**Which of these have you run?** Answer honestly from your own `test-results` record. In the build environment only the tests, linters, Ansible file steps, compose validation and the Nagios plugin were run.

## Testing
**What tests exist?** 116 backend tests, 43 frontend tests, a 21-check browser flow, plus static checks. Mention real numbers from your own run.
**What did testing find?** CDN-loaded API docs (fixed, now vendored), duplicated history wording, raw enum names in notifications, an Ansible variable-loading bug.

## Your contribution (fill in)
- What I designed myself: ____
- What I changed or extended: ____
- What I ran and verified on my machine: ____
- What I would improve next: ____
