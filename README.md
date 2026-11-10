# InfraDesk

**Offline IT asset management and problem reporting, with DevOps automation.**

InfraDesk is a locally hosted web application for small labs, student teams and local IT support
groups. An administrator manages users, assets and tickets; workers report problems, receive
assignments, add work notes and resolve tickets. Everything is stored in a local SQLite database and
nothing needs the internet once the dependencies are downloaded. The application is packaged with
Docker and surrounded by four DevOps tools with separate jobs:

| Tool | Job in this project |
|---|---|
| Docker Compose | Simple run for development and demos |
| Terraform | Declares its **own** set of Docker resources (separate deployment mode, port 8081) |
| Puppet | Configures an Ubuntu host (packages, user, folders, config file, Docker service, backup timer) with `puppet apply` |
| Ansible | Preflight checks, deployment, validation and rollback of the application |
| Nagios Core | Monitors `/health` and `/ready` and the host; **detects and reports, it does not repair** |

> InfraDesk is a student prototype and a local support tool. It is not a production ITSM product and
> it must not be exposed directly to the public internet without a security review.

## What has actually been verified

This table is the honest state of the project. "Verified" means it was run and passed in the build
environment (a Linux container with Python, Node and Chromium, but **no Docker daemon**, no Terraform,
Puppet or Nagios). Everything marked **Run it yourself** has complete files and exact commands, but
nobody has executed it yet. Run those steps on your Ubuntu VM and keep the real output as evidence.

| Area | Status |
|---|---|
| Backend: 116 automated tests (auth, roles, workflow, notifications, assets, users, reports, CSV, migrations, backup/restore, offline docs) and `ruff` | Verified |
| Frontend: typecheck, ESLint, 43 tests, production build | Verified |
| Real browser end-to-end test (headless Chromium, 21 checks, two roles, full ticket lifecycle, phone layout) | Verified (`e2e/`) |
| Backup and restore of a disposable SQLite database | Verified (tests) |
| Nagios check plugin against a fake server: OK, WARNING, CRITICAL, UNKNOWN | Verified |
| Shell scripts: `bash -n` and `shellcheck`; YAML: `yamllint`; Ansible: `--syntax-check` and `ansible-lint` | Verified |
| `docker compose config` | Verified |
| Docker image build, `docker compose up`, data survives restart, nginx proxy in a container | **Run it yourself** |
| Terraform `fmt`/`init`/`validate`/`plan`/`apply` | **Run it yourself** (no `.terraform.lock.hcl` yet; `terraform init` creates it, commit it) |
| Puppet `parser validate`, idempotence and drift-correction demo | **Run it yourself** |
| Ansible deploy/validate/rollback against a live Docker host | **Run it yourself** |
| Nagios `nagios -v` and the OK, CRITICAL, OK demonstration | **Run it yourself** |
| Offline operation with the network disconnected | **Run it yourself** |

## Quick start (simplest path: Docker Compose)

Requirements: Docker Desktop (Windows 11 with WSL2) or Docker Engine with the Compose plugin (Ubuntu).

```bash
git clone <your-repository-url> InfraDesk && cd InfraDesk
make env                       # creates .env with a freshly generated SECRET_KEY
make up                        # builds both images and starts the stack
```

Open <http://localhost:8080>. API documentation is at <http://localhost:8080/docs>, the health
endpoint at <http://localhost:8080/health>.

There are no default accounts. Create the first administrator, or load fictional demo data:

```bash
make create-admin ADMIN_USER=admin ADMIN_NAME="Lab Admin"     # asks for a password

# or, for a demo (needs ENVIRONMENT=development in .env):
make seed-demo        # demo_admin, worker_asha, worker_ravi, password printed on screen
```

The demo password is for a local demo only. Change it (or set `DEMO_PASSWORD`) before sharing a machine.

Stop and start: `make down` (data is kept in the Docker volume `infradesk-data`), `make up`.
No `make` on Windows? Use `docker compose up -d --build` after copying `.env.example` to `.env` and
replacing `SECRET_KEY` with a long random value (see [docs/installation-windows.md](docs/installation-windows.md)).

## Local development without Docker

```bash
# backend (Python 3.11+)
cd backend && python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
export SECRET_KEY=dev-only-secret-key-change-me-0123456789abcdef  # PowerShell: $env:SECRET_KEY="..."
python scripts/seed_demo_data.py --yes && uvicorn app.main:app --port 8000

# frontend (Node 20+), in another terminal
cd frontend && npm ci && npm run dev          # http://localhost:5173, proxies /api to port 8000
```

## Tests

```bash
make test                                   # backend (pytest) + frontend (vitest)
cd backend && ruff check . && pytest        # 116 tests
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
python e2e/browser_flow.py ./shots          # real browser test, see e2e/README.md
```

Results from the last run are in [docs/test-results.md](docs/test-results.md).

## Repository map

| Path | Content |
|---|---|
| `backend/` | FastAPI application, SQLAlchemy models, Alembic migration, services, tests, admin scripts |
| `frontend/` | React + TypeScript + Vite single-page application (no icon library, no CDN) |
| `docker/`, `docker-compose.yml` | Images (backend, nginx + frontend) and the Compose stack |
| `infrastructure/terraform` | Docker provider configuration, its own network, volume and containers |
| `infrastructure/puppet` | `infradesk_host` module and `site.pp` for `puppet apply` |
| `infrastructure/ansible` | Inventory, roles and the preflight, deploy, validate and rollback playbooks |
| `infrastructure/nagios` | Object definitions, the HTTP check plugin, install/validate script |
| `scripts/` | Ubuntu setup, dev start/stop, test, lint, backup, restore, offline preload, environment check |
| `e2e/` | Real browser end-to-end test |
| `docs/` | Architecture, workflow, database, API, security, installation, guides, testing, demo script, viva, report outline, SPM plan, synopsis |
| `reports/` | Place for **your** genuine screenshots and command output |

## Ownership boundaries (so the tools never fight)

| Resource | Owner |
|---|---|
| Ubuntu packages, the `infradesk` user, `/opt/infradesk` folders, `/etc/infradesk/infradesk.env`, Docker service, backup timer | Puppet |
| Application files in `/opt/infradesk/app`, image tags, the Compose project `infradesk`, post-deploy checks | Ansible |
| Containers and network named `infradesk-tf-*`, volume `infradesk-tf-data` | Terraform |
| Quick local Compose run (`infradesk-*`, port 8080) | Docker Compose |
| Watching the running service | Nagios |

Use **one** deployment mode at a time: Compose/Ansible (port 8080) **or** Terraform (port 8081).

## Offline operation

The first installation needs the internet (OS packages, Python and npm packages, Docker images,
Terraform provider). After that the application needs no internet at all: all fonts, scripts and the
API documentation page are bundled. Run `scripts/offline_preload.sh` while online to cache everything,
then follow [docs/offline-operation.md](docs/offline-operation.md) to prove it with the network off.
"Offline" means no internet; other devices can reach it only on the same local network.

## Security summary

Passwords are hashed with Argon2; sessions use an HttpOnly cookie with a short-lived signed token;
cross-site writes are blocked by an Origin check; every route is authorized on the **backend**
(a worker sees only own or assigned tickets); there is no public registration; secrets come from
environment variables and `.env` is git-ignored. Details and known limits: [docs/security.md](docs/security.md).

## Documentation index

[Synopsis](docs/synopsis/synopsis.pdf) · [Architecture](docs/architecture.md) · [Workflow](docs/workflow.md) ·
[Database](docs/database-design.md) · [API](docs/api-reference.md) · [Security](docs/security.md) ·
[Windows install](docs/installation-windows.md) · [Ubuntu install](docs/installation-ubuntu.md) ·
[Offline](docs/offline-operation.md) · [Terraform](docs/terraform-guide.md) · [Puppet](docs/puppet-guide.md) ·
[Ansible](docs/ansible-guide.md) · [Nagios](docs/nagios-guide.md) · [Testing plan](docs/testing-plan.md) ·
[Test results](docs/test-results.md) · [Troubleshooting](docs/troubleshooting.md), [User manual](docs/user-manual.md) · [Demo script](docs/demo-script.md) ·
[Viva questions](docs/viva-questions.md) · [Report outline](docs/report-outline.md) · [SPM plan](docs/spm-ms-project-plan.md)

## Flow
[![Architecture diagram](https://gitdiagram.com/diagram-badge.svg)](https://gitdiagram.com/purnatejeshwarareddyb/infradesk?utm_source=readme&utm_medium=badge)



## Licence

MIT, see [LICENSE](LICENSE). Bundled Swagger UI is Apache-2.0 (`backend/app/static/swagger/LICENSE`).
