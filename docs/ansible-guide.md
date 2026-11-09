# Ansible guide

Full details: [`infrastructure/ansible/README.md`](../infrastructure/ansible/README.md).

## Role

Ansible automates the **operations** on the host: check that it is ready, deploy the application, validate it, roll back. It is agentless
(it connects over SSH, or locally with `connection=local`) and uses YAML playbooks.

| Term | Meaning here |
|---|---|
| Inventory | `inventory/hosts.ini`: `localhost` (local connection) plus a commented VM example |
| Playbook | `preflight.yml`, `deploy.yml`, `validate.yml`, `rollback.yml` |
| Role | reusable unit: `roles/docker` (check Docker), `roles/infradesk` (the deployment) |
| Variable | `group_vars/all.yml` and role defaults (paths, port, disk threshold) |
| Handler | a task that runs only when notified by a change, for example restarting the stack after the `.env` or the sources changed |

## What each playbook does

- **preflight**: read-only. Connectivity, the secret is set, Docker and Compose present, enough disk space, the port is free or already ours.
- **deploy**: preflight, then pack the sources, compute a release id from their checksum, record the previous image tag in a state file, write the `.env`
  (mode 0600, secret from the environment, never from the repository), `docker compose build/up`, wait for `/ready`.
- **validate**: `/health`, `/ready`, the login page, `/docs`, `/openapi.json`, and that the volume `infradesk-data` exists.
- **rollback**: puts the previously recorded image tag back and restarts; with `--tags recover` it only restarts the stack. It does **not** undo database
  migrations: restore a backup if the schema changed.

## Demonstration

```bash
cd infrastructure/ansible
export INFRADESK_SECRET_KEY="$SECRET_KEY"
ansible-playbook --syntax-check playbooks/deploy.yml
ansible-playbook playbooks/preflight.yml
ansible-playbook playbooks/deploy.yml -K          # first run: changed
ansible-playbook playbooks/deploy.yml -K          # second run: changed=0 for the file steps (idempotence)
ansible-playbook playbooks/validate.yml
```

## Status

Verified: `--syntax-check` on all four playbooks, `ansible-lint` (production profile), and the file-handling steps of `deploy.yml` against a temporary
directory (release id, state file, `.env` with mode 600, second run `changed=0`). `preflight.yml` correctly stopped with "Docker is not ready" when no Docker
daemon existed. **Not verified**: the Docker steps (build, up, validate, rollback) against a live Docker host. Run them and keep the output.
