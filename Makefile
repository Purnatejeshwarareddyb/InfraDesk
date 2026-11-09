# InfraDesk - common tasks. Run `make help` to list them. Recipes need GNU make and a POSIX shell (Linux, WSL, Git Bash).
COMPOSE   := docker compose -f docker-compose.yml
BACKEND   := backend
VENV      := $(BACKEND)/.venv
TF_DIR    := infrastructure/terraform
ANSIBLE   := infrastructure/ansible
PUPPET    := infrastructure/puppet
# Usage examples: make create-admin ADMIN_USER=admin ADMIN_NAME="Lab Admin"   make restore FILE=backups/infradesk-....db
ADMIN_USER ?= admin
ADMIN_NAME ?= Administrator
FILE ?=

.DEFAULT_GOAL := help
.PHONY: help env backend-install backend-test frontend-install frontend-test test lint up down logs build \
        seed-demo create-admin backup restore tf-init tf-validate tf-plan tf-apply tf-destroy \
        puppet-validate ansible-check nagios-validate clean

help: ## show this list
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{ printf "  %-18s %s\n", $$1, $$2 }'

env: ## create .env with a generated SECRET_KEY (never overwrites an existing .env)
	@if [ -f .env ]; then echo ".env already exists, not changed"; else \
	  secret=$$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))'); \
	  sed "s#^SECRET_KEY=.*#SECRET_KEY=$$secret#" .env.example > .env; chmod 600 .env; \
	  echo "created .env"; fi

backend-install: ## create backend/.venv and install dev requirements
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r $(BACKEND)/requirements-dev.txt

backend-test: ## run the backend tests (pytest)
	cd $(BACKEND) && SECRET_KEY="$${SECRET_KEY:-test-only-secret-key-0123456789abcdef0123456789}" .venv/bin/python -m pytest

frontend-install: ## install frontend dependencies (npm ci)
	cd frontend && npm ci

frontend-test: ## run the frontend tests (vitest)
	cd frontend && npm test

test: backend-test frontend-test ## run all tests

lint: ## ruff + eslint (+ shellcheck/yamllint if installed)
	scripts/lint_all.sh

up: ## build and start the Docker Compose stack in the background
	$(COMPOSE) up -d --build
	@echo "Open http://localhost:$${INFRADESK_PORT:-8080}"

down: ## stop the stack (the data volume is kept)
	$(COMPOSE) down

logs: ## follow the logs of both containers
	$(COMPOSE) logs -f --tail=100

build: ## build the images without starting them
	$(COMPOSE) build

seed-demo: ## load fictional demo data (needs ENVIRONMENT=development in .env)
	$(COMPOSE) exec backend python scripts/seed_demo_data.py --yes

create-admin: ## create an administrator (asks for the password): make create-admin ADMIN_USER=admin ADMIN_NAME="Lab Admin"
	$(COMPOSE) exec backend python scripts/create_admin.py --username "$(ADMIN_USER)" --display-name "$(ADMIN_NAME)"

backup: ## back up the database to ./backups
	scripts/backup.sh

restore: ## restore a backup (asks for confirmation): make restore FILE=backups/<file>.db
	@test -n "$(FILE)" || { echo "usage: make restore FILE=backups/<file>.db"; exit 2; }
	scripts/restore.sh "$(FILE)"

tf-init: ## terraform init (downloads the Docker provider once)
	cd $(TF_DIR) && terraform init

tf-validate: ## terraform fmt -check and validate
	cd $(TF_DIR) && terraform fmt -check -recursive && terraform validate

tf-plan: ## terraform plan (needs TF_VAR_secret_key)
	cd $(TF_DIR) && terraform plan

tf-apply: ## terraform apply (asks for confirmation)
	cd $(TF_DIR) && terraform apply

tf-destroy: ## destroy the Terraform containers and network, KEEP the data volume
	cd $(TF_DIR) && terraform destroy -target=docker_container.web -target=docker_container.backend -target=docker_network.net

puppet-validate: ## puppet parser validate (+ epp validate) of the module
	puppet parser validate $(PUPPET)/manifests/site.pp $(PUPPET)/modules/infradesk_host/manifests/init.pp
	puppet epp validate $(PUPPET)/modules/infradesk_host/templates/*.epp

ansible-check: ## ansible syntax-check of all playbooks
	cd $(ANSIBLE) && for p in preflight deploy validate rollback; do ansible-playbook --syntax-check playbooks/$$p.yml || exit 1; done

nagios-validate: ## shell-check the Nagios plugin; run `nagios -v` if a Nagios config is given: make nagios-validate NAGIOS_CFG=/etc/nagios4/nagios.cfg
	sh -n infrastructure/nagios/scripts/check_infradesk_http.sh
	sh -n infrastructure/nagios/scripts/install_or_validate.sh
	@if [ -n "$(NAGIOS_CFG)" ]; then nagios -v "$(NAGIOS_CFG)"; else echo "NAGIOS_CFG not set: configuration not validated"; fi

clean: ## remove caches and build output (NOT .env, NOT data, NOT backups)
	rm -rf frontend/dist .run $(BACKEND)/.pytest_cache $(BACKEND)/.ruff_cache
	find $(BACKEND) -name __pycache__ -type d -prune -exec rm -rf {} +
