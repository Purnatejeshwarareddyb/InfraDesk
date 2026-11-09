# Installation on Ubuntu 22.04 / 24.04

## 1. Prerequisites

```bash
git clone <your-repository-url> InfraDesk && cd InfraDesk
scripts/verify_environment.sh        # read-only: shows which tools exist
scripts/setup_ubuntu.sh              # installs missing packages (asks before using sudo), creates .env
```

`setup_ubuntu.sh` is safe to repeat and never overwrites an existing `.env`. If Docker Compose is missing on 22.04, install the
plugin from Docker's own repository (see <https://docs.docker.com/engine/install/ubuntu/>); the plugin has no package in Ubuntu 22.04's own sources.

Allow your user to use Docker without sudo, then log out and in again:

```bash
sudo usermod -aG docker "$USER"
```

## 2. Run the application

```bash
make env            # only if setup_ubuntu.sh did not create .env
make up             # docker compose -f docker-compose.yml up -d --build
curl -s localhost:8080/health          # {"status":"ok","app":"InfraDesk","version":"1.0.0"}
make create-admin ADMIN_USER=admin ADMIN_NAME="Lab Admin"
# or demo data (ENVIRONMENT=development in .env):
make seed-demo
```

Open `http://localhost:8080` (from another machine: `http://<server-ip>:8080`; open the port with `sudo ufw allow 8080/tcp` if ufw is on).
Stop with `make down`; data is kept in the Docker volume `infradesk-data`. Logs: `make logs`.

## 3. The DevOps demonstration (Ubuntu VM)

First create one secret and keep it for every tool: `export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"`
(Ansible reads `INFRADESK_SECRET_KEY`, Terraform `TF_VAR_secret_key`; export the same value under those names too.)

Use **one deployment mode** at a time. The suggested order for a demonstration:

| Step | Command (from the repository) | Details |
|---|---|---|
| Puppet: host baseline | `sudo env FACTER_infradesk_secret_key="$SECRET_KEY" puppet apply --modulepath=infrastructure/puppet/modules infrastructure/puppet/manifests/site.pp` | [puppet-guide.md](puppet-guide.md) |
| Ansible: deploy and validate | `cd infrastructure/ansible && ansible-playbook playbooks/deploy.yml -K && ansible-playbook playbooks/validate.yml` | [ansible-guide.md](ansible-guide.md) |
| Nagios: monitor | `infrastructure/nagios/scripts/install_or_validate.sh <nagios-config-dir>` | [nagios-guide.md](nagios-guide.md) |
| Terraform: alternative stack on port 8081 | `make tf-init tf-validate tf-plan` | [terraform-guide.md](terraform-guide.md) |

Install the tools with `sudo apt install ansible puppet-agent` (or `puppet`) and Nagios (`nagios4` and `monitoring-plugins`);
Terraform from HashiCorp's repository. Package names differ slightly between releases, check with `apt search`.
**The Puppet, Terraform and Nagios steps and the Docker steps of Ansible have not been run on a real host by the author of this code; run them,
keep the real output, and fix the small environment differences you find.**

## 4. Local development without Docker

```bash
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
python scripts/seed_demo_data.py --yes && uvicorn app.main:app --port 8000 &
cd ../frontend && npm ci && npm run dev
```

Or use `scripts/dev_start.sh` and `scripts/dev_stop.sh`, which start and stop both with PID files.

## 5. Updating

```bash
git pull && make up          # rebuilds changed layers; the migration runs automatically at start
make backup                  # before upgrading anything important
```
