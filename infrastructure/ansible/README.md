# Ansible: deploy, validate, roll back InfraDesk

Ansible owns the **application deployment**: the files in `/opt/infradesk/app`, the Docker Compose
project `infradesk`, image tags, and the post-deploy checks. It does not install packages or users
(Puppet) and does not touch the `infradesk-tf-*` resources (Terraform).

## What is here

| Path | Purpose |
|---|---|
| `ansible.cfg`, `inventory/hosts.ini` | settings; inventory with `localhost` (connection=local) and a commented VM example |
| `group_vars/all.yml` | all variables (paths, port, thresholds). Loaded by each playbook through `vars_files` |
| `playbooks/preflight.yml` | read-only checks: ping, secret set, docker + compose, disk space, port free or ours |
| `playbooks/deploy.yml` | runs preflight, then role `infradesk` |
| `playbooks/validate.yml` | `/health`, `/ready`, `/login`, `/docs`, `/openapi.json`, data volume `infradesk-data` |
| `playbooks/rollback.yml` | play 1 (tag `rollback`): previous image tag; play 2 (tag `recover`, only on request): restart |
| `roles/docker` | checks Docker and the Compose plugin (does not install them) |
| `roles/infradesk` | pack sources, release id, state file, copy files, render `.env`, compose build/up, wait for `/ready` |

## The secret is never in the repository

```bash
export INFRADESK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
# optional: choose the port (default 8080)
export INFRADESK_PORT=8080
```

Alternative with Ansible Vault (the file lives OUTSIDE the repo):

```bash
ansible-vault create ~/.infradesk-secrets.yml          # content:  infradesk_secret_key: "<generated value>"
ansible-playbook playbooks/deploy.yml -K -e @$HOME/.infradesk-secrets.yml --ask-vault-pass
```

`.env` on the target is written with mode 0600 and the task uses `no_log`, so the value is not printed.
Use the same secret on later deployments: a different SECRET_KEY logs every user out.

## Commands (run from `infrastructure/ansible`)

```bash
ansible-playbook --syntax-check playbooks/deploy.yml        # also: preflight, validate, rollback
ansible-playbook playbooks/preflight.yml                    # read-only checks
ansible-playbook playbooks/deploy.yml --check               # dry run (skips the docker commands)
ansible-playbook playbooks/deploy.yml -K                    # deploy; -K = ask for the sudo password
ansible-playbook playbooks/deploy.yml -K                    # again: "changed=0" shows idempotence
ansible-playbook playbooks/validate.yml
ansible-playbook playbooks/rollback.yml -K                  # back to the previous release
ansible-playbook playbooks/rollback.yml -K --tags recover   # just restart the stack
ansible-playbook playbooks/deploy.yml -K --tags deploy      # only the deploy steps (skip preflight)
```

Without sudo (a test on your own machine): `-e infradesk_app_dir=$HOME/infradesk-app -e infradesk_become=false`
(your user must be allowed to run `docker`). Remote VM: uncomment the entry in `inventory/hosts.ini`, use
SSH keys through `ssh-agent`, never passwords or keys in the repo.

## How a release works

1. The repository files needed for the build are packed into a deterministic tar; its checksum gives the
   release id (for example `r35c71b9a590b`). Same sources give the same id, so a second deploy changes nothing.
   Choose your own id with `INFRADESK_RELEASE=2026-demo1`.
2. The state file `/opt/infradesk/app/.deploy-state.json` records `current_tag` and `previous_tag`
   **before** anything is built.
3. Files are unpacked and `.env` is rendered (it contains `INFRADESK_TAG=<release>`). Only when one of them
   changed, the handler runs `docker compose up -d --build`, which tags the images
   `infradesk-backend:<release>` and `infradesk-frontend:<release>`.
4. `wait_for` the port, then `/ready` is polled (30 tries, 4 s apart).

Rollback needs the old images, so do not run `docker image prune -a` between releases. Rollback does not undo
database migrations: take a backup (`make backup`) before deploying, and restore it if the schema changed.
Files deleted from the repository are not deleted on the target (the archive is only unpacked on top).

## Ownership boundaries

| Layer | Tool | Owns |
|---|---|---|
| Host baseline | Puppet | packages, `infradesk` user, `/opt/infradesk`, `/opt/infradesk/data`, `/opt/infradesk/backups`, `/etc/infradesk`, docker service, backup timer |
| Application | Ansible | `/opt/infradesk/app`, Compose project `infradesk`, images, `.deploy-state.json` |
| Docker objects with `infradesk-tf-` prefix | Terraform | only those |

## Verification status

Run where this was written: `--syntax-check` of all four playbooks (passed), `ansible-lint` (passed, production
profile), `yamllint` (passed), `preflight.yml` (correctly stops: no Docker daemon there), and the file steps of
`deploy.yml` against a temporary directory (changed on the first run, `changed=0` on the second). NOT RUN: the
Docker steps (build, up, wait for `/ready`), `validate.yml` and `rollback.yml`, because no Docker daemon was
available. On your machine a good result is `failed=0` in each PLAY RECAP, and `validate.yml` ending with
"All checks passed".
