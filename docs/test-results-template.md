# Test results template (fill in with your own real results)

Date: ____  Machine / OS: ____  Tester: ____  Commit: ____

Rules: paste real output or a screenshot reference for each row. If you did not run it, write **NOT RUN** and the reason. Never copy results from another machine or project.

| # | Check | Command | Expected | Actual result | Evidence file | Pass / Fail / NOT RUN |
|---|---|---|---|---|---|---|
| 1 | Backend tests | `cd backend && pytest -q` | all pass | | | |
| 2 | Frontend tests | `npm test` | all pass | | | |
| 3 | Browser end-to-end | `python e2e/browser_flow.py ./shots` | 21 of 21 | | | |
| 4 | Images build | `docker compose build` | success | | | |
| 5 | Stack starts | `docker compose up -d`; `curl localhost:8080/ready` | `{"status":"ready"}` | | | |
| 6 | Data survives restart | create a ticket; `docker compose restart`; list tickets | ticket still present | | | |
| 7 | Backup | `make backup` | file in `./backups` | | | |
| 8 | Restore (disposable DB only) | `make restore FILE=...` | asks to confirm; data back | | | |
| 9 | Terraform validate | `make tf-validate` | `Success! The configuration is valid.` | | | |
| 10 | Terraform apply and destroy | `make tf-apply`; `curl localhost:8081/health`; `make tf-destroy` | stack up, then removed, volume kept | | | |
| 11 | Puppet syntax | `puppet parser validate ...` | no output | | | |
| 12 | Puppet idempotence | apply twice | second run has no changes | | | |
| 13 | Puppet drift correction | edit managed file or stop Docker; apply | restored | | | |
| 14 | Ansible syntax | `ansible-playbook --syntax-check playbooks/deploy.yml` | OK | | | |
| 15 | Ansible deploy twice | `deploy.yml` x2 | second run `changed=0` for file steps | | | |
| 16 | Ansible validate | `validate.yml` | all checks pass | | | |
| 17 | Rollback or recover | `rollback.yml` (and `--tags recover`) | previous release or restart works | | | |
| 18 | Nagios config | `nagios -v nagios.cfg` | 0 errors | | | |
| 19 | Nagios OK, CRITICAL, OK | stop and start the app | states follow | | | |
| 20 | Offline run | disconnect the internet; use the app | works | | | |

Notes and problems found:
