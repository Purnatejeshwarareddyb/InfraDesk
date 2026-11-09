# Project plan (SPM / MS Project input)

All durations are **estimates** for planning; replace them with your real dates and actuals.

| ID | Task | Est. days | Depends on |
|---|---|---|---|
| 1 | Requirements and synopsis | 3 | none |
| 2 | Architecture and database design | 3 | 1 |
| 3 | Backend foundation (config, security, models, migrations) | 4 | 2 |
| 4 | Ticket, asset, user services and API | 6 | 3 |
| 5 | Notifications, reports, activity log, CSV | 3 | 4 |
| 6 | Backend tests | 4 | 4 |
| 7 | Frontend foundation (client, auth, routing) | 3 | 3 |
| 8 | Frontend pages (worker and admin) | 6 | 7, 4 |
| 9 | Frontend tests | 3 | 8 |
| 10 | Docker and Compose | 2 | 5, 8 |
| 11 | Terraform | 2 | 10 |
| 12 | Puppet | 2 | 10 |
| 13 | Ansible | 3 | 10 |
| 14 | Nagios | 2 | 10 |
| 15 | Browser end-to-end and integration testing | 2 | 8, 10 |
| 16 | Documentation, demo script, report | 4 | 15 |
| 17 | Final review and presentation | 2 | 16 |

## Milestones
M1 design approved (task 2); M2 backend complete (5, 6); M3 working application (8, 9); M4 DevOps complete (11 to 14); M5 verified and documented (15 to 17).

## Critical path
1, 2, 3, 4, 8, 10, (13), 15, 16, 17. Tasks 11, 12, 14 can run in parallel after 10.

## Resources
One student, one laptop (Windows 11), one Ubuntu VM, free tools only.

## Risks
| Risk | Mitigation |
|---|---|
| Docker or VM problems delay DevOps tasks | start Docker setup early; `troubleshooting.md` |
| Tool versions differ from the written configs | run each tool's validate command first and keep real output |
| Scope growth | keep the out-of-scope list in the synopsis |
| Lost data | `make backup` before changes; Git for code |
