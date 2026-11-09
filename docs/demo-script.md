# Demonstration script (8 to 12 minutes)

Prepare beforehand: stack running (`make up`), `make seed-demo` done (development only), two browser windows (one normal, one private), Nagios and Ansible ready if you demonstrate DevOps.
Demo accounts exist only after the seed command; password `Demo-Passw0rd!` is for a local demonstration. Never expose this stack to the internet.

| # | Minutes | Action | What to say / show |
|---|---|---|---|
| 1 | 0.5 | Problem and goal | Reports of faulty equipment get lost; InfraDesk keeps assets, tickets and history in one offline system |
| 2 | 0.5 | Architecture slide / `docs/architecture.md` | browser, nginx, FastAPI, SQLite; the four DevOps tools and what each owns |
| 3 | 0.5 | `curl localhost:8080/health` and `/ready` | liveness and readiness are different |
| 4 | 1 | Sign in as `worker_asha` with a wrong password | one generic error; then correct sign-in |
| 5 | 1 | Worker reports a ticket (title, asset, priority) | validation messages, asset link, status Open |
| 6 | 0.5 | Worker tries `/admin/users` | blocked by the frontend and by the backend (403) |
| 7 | 1 | Private window: sign in as `demo_admin`; bell shows a notification | roles, notifications |
| 8 | 1 | Admin assigns the ticket to `worker_ravi` | status Assigned, history entry |
| 9 | 1.5 | Worker ravi: start work, add note, resolve with resolution note | only legal transitions are offered |
| 10 | 0.5 | Admin closes the ticket (confirmation dialog) | history shows every step with actor and time |
| 11 | 0.5 | Reports page and CSV export | numbers come from real records; CSV guards against formula injection |
| 12 | 0.5 | Activity log | administrative audit trail |
| 13 | 1 | `make backup`, then show the file; explain restore | data protection |
| 14 | 1.5 | DevOps: `puppet apply` (baseline), `ansible-playbook playbooks/deploy.yml` and `validate.yml`, Terraform plan/apply on 8081 | each tool's role; run beforehand if time is short and show the saved output |
| 15 | 1 | Nagios: OK, `make down`, CRITICAL, `make up`, OK | Nagios reports; it does not repair |
| 16 | 0.5 | Limitations | single node, SQLite, no e-mail, no HTTPS by default, Chromium-only E2E |

Rules: show only what you have really run. If a DevOps step was not run on your machine, say so rather than showing someone else's output.
