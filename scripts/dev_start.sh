#!/usr/bin/env bash
# dev_start.sh - run InfraDesk WITHOUT Docker: backend (uvicorn) and frontend (Vite dev server).
# Usage: scripts/dev_start.sh
# Needs python3 (with venv), node 22 and npm. Creates backend/.venv and frontend/node_modules on first run.
# Backend: http://localhost:8000 (docs at /docs)   Frontend: http://localhost:5173
# PID files and logs live in .run/ ; stop everything with scripts/dev_stop.sh
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN="$ROOT/.run"
mkdir -p "$RUN"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "No .env found. Run 'make env' first (it generates a SECRET_KEY)." >&2
  exit 1
fi

# Already running? (PID file exists and the process is alive)
for name in backend frontend; do
  if [[ -f "$RUN/$name.pid" ]] && kill -0 "$(cat "$RUN/$name.pid")" 2>/dev/null; then
    echo "$name is already running (PID $(cat "$RUN/$name.pid")). Use scripts/dev_stop.sh first." >&2
    exit 1
  fi
done

# Load .env for the backend process (SECRET_KEY, DATABASE_URL, ...).
set -a
# shellcheck disable=SC1091
. "$ROOT/.env"
set +a

# --- backend ---
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet -r requirements.txt
.venv/bin/alembic upgrade head
nohup .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > "$RUN/backend.log" 2>&1 &
echo $! > "$RUN/backend.pid"
echo "backend started (PID $(cat "$RUN/backend.pid")), log: .run/backend.log"

# --- frontend ---
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi
nohup npm run dev > "$RUN/frontend.log" 2>&1 &
echo $! > "$RUN/frontend.pid"
echo "frontend started (PID $(cat "$RUN/frontend.pid")), log: .run/frontend.log"
echo "Open http://localhost:5173"
