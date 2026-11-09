#!/usr/bin/env bash
# lint_all.sh - ruff (backend), eslint (frontend), and shellcheck / yamllint when they are installed.
# Usage: scripts/lint_all.sh
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,3p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)

echo "== ruff (backend) =="
cd "$ROOT/backend"
[[ -d .venv ]] || python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements-dev.txt
.venv/bin/ruff check .

echo "== eslint (frontend) =="
cd "$ROOT/frontend"
[[ -d node_modules ]] || npm ci
npm run lint

cd "$ROOT"
if command -v shellcheck >/dev/null 2>&1; then
  echo "== shellcheck =="
  shellcheck scripts/*.sh infrastructure/nagios/scripts/*.sh infrastructure/puppet/modules/infradesk_host/files/*.sh
else
  echo "== shellcheck: not installed, skipped =="
fi
if command -v yamllint >/dev/null 2>&1; then
  echo "== yamllint =="
  yamllint -d relaxed docker-compose.yml compose.override.yml infrastructure/ansible .github
else
  echo "== yamllint: not installed, skipped =="
fi
echo "Lint finished."
