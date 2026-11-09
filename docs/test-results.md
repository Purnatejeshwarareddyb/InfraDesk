# Test results (actually obtained)

Run on 2026-10-19 in the build environment: Linux container, Python 3.13, Node 22, headless Chromium. No Docker daemon, no Terraform, Puppet or Nagios.
Re-run the commands on your own machine and replace these with your own output and screenshots before submitting.

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Backend lint | `cd backend && ruff check .` | All checks passed |
| 2 | Backend tests | `cd backend && pytest -q` | **116 passed** (about 55 s) |
| 3 | Frontend types | `npm run typecheck` | clean |
| 4 | Frontend lint | `npm run lint` | 0 errors, 0 warnings |
| 5 | Frontend tests | `npm test` | **5 files, 43 tests passed** |
| 6 | Frontend build | `npm run build` | success; JS 246.7 kB (76.8 kB gzip), CSS 16.8 kB |
| 7 | `npm audit` (at build time) | `npm audit` | 0 vulnerabilities |
| 8 | Browser end-to-end | `python e2e/browser_flow.py` | **21 of 21 checks passed** (see below) |
| 9 | Dev proxy and cookie flow | curl through the Vite proxy | login 200 with HttpOnly cookie, `/auth/me` 200, tickets total 5, CSV 200, worker `/users` 403 |
| 10 | Nagios plugin | against a local fake server | OK 0; slow with `-w` WARNING 1; slow with `-c`, HTTP 500, missing text, refused connection all CRITICAL 2; bad arguments UNKNOWN 3 |
| 11 | Shell scripts | `bash -n`, `shellcheck` | clean |
| 12 | YAML | `yamllint -s` | clean |
| 13 | Ansible | `ansible-playbook --syntax-check` (4 playbooks), `ansible-lint` | pass, 0 failures |
| 14 | Ansible file steps | `deploy.yml` against a temp directory | release id, state file, `.env` mode 600; second run `changed=0` |
| 15 | Ansible preflight without Docker | `preflight.yml` | stops with "Docker is not ready" (correct) |
| 16 | Compose file | `docker compose config` | valid (with and without the override); refuses to run when `SECRET_KEY` is unset |

## Browser end-to-end checks (item 8)

Wrong password shows the error; empty login shows validation; admin sign-in reaches the dashboard; admin creates a worker; admin creates an asset (tag upper-cased);
worker sign-in reaches the worker area; worker cannot open the admin users page; worker reports a ticket linked to the asset; admin is notified; admin assigns the
ticket (status becomes Assigned); the worker's bell shows 1 unread; worker starts work, adds a work note, resolves with a resolution note; the worker notifications
page loads; admin closes the ticket (confirmation dialog); CSV export contains the new ticket; the reports page shows real counts; the activity log shows administrative
actions; the phone layout (390 px wide) has no horizontal scroll and the Menu button opens the navigation.

Not covered by the browser test: keyboard-only use, screen readers, colour-contrast measurement, other browsers (only Chromium).

## NOT RUN (no suitable tool in the build environment)

| Check | Why | What to do |
|---|---|---|
| `docker build`, `docker compose up`, persistence across restart, the nginx proxy inside a container | no Docker daemon | run on Windows (Docker Desktop) or Ubuntu |
| Terraform `fmt`, `init`, `validate`, `plan`, `apply`, `destroy` | binary download refused | run on your machine, commit `.terraform.lock.hcl` |
| Puppet `parser validate`, `--noop`, idempotent second apply, drift correction | package not obtainable | run on the Ubuntu VM |
| Ansible deploy, validate and rollback against a live Docker host | no Docker daemon | run on the Ubuntu VM |
| Nagios `nagios -v` and the OK, CRITICAL, OK demonstration | no Nagios | run on the Ubuntu VM |
| Offline operation with the network disconnected | no Docker stack to test | follow `offline-operation.md` |
| GitHub Actions workflow | not pushed to GitHub | push and read the first run; the Terraform step is the likeliest to need a tweak |
| Load or concurrency testing | out of scope | SQLite and one worker are meant for a small group |

## Defects found and fixed during testing

- The Swagger documentation page loaded its scripts from a CDN, which breaks offline use: it is now bundled and served locally (test added).
- Assignment history showed the assignee's name twice, and status notifications showed raw names such as `IN_PROGRESS`: both reworded (test added).
- The sign-in error flag was overwritten by the redirect after a 401: fixed in the frontend, covered by a test.
- Ansible did not load `group_vars` for playbooks run from another folder, and a failed first build lost a handler notification: both fixed.
- The logo block and sidebar dots were decorative icon-like shapes: removed to respect the no-icons requirement.
