#!/usr/bin/env bash
# test_all.sh - run the backend (pytest) and frontend (vitest) test suites.
# Usage: scripts/test_all.sh      (installs dependencies into backend/.venv and frontend/node_modules if needed)
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,3p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)

echo "== backend tests =="
cd "$ROOT/backend"
[[ -d .venv ]] || python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements-dev.txt
# The tests set their own configuration; this value only satisfies the settings validator.
SECRET_KEY="${SECRET_KEY:-test-only-secret-key-0123456789abcdef0123456789}" .venv/bin/python -m pytest

echo "== frontend tests =="
cd "$ROOT/frontend"
[[ -d node_modules ]] || npm ci
npm test

echo "All tests finished."
