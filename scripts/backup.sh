#!/usr/bin/env bash
# backup.sh - back up the database of the RUNNING Docker Compose stack into ./backups.
# Usage: scripts/backup.sh
# 1) the backend container makes a consistent SQLite backup in /data/backups (volume infradesk-data)
# 2) the files are copied to ./backups on the host. Nothing is deleted or overwritten.
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.yml)

if ! "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -qx backend; then
  echo "The backend container is not running. Start it with: make up" >&2
  exit 1
fi

"${COMPOSE[@]}" exec -T backend python scripts/backup_database.py --db /data/infradesk.db --out /data/backups
mkdir -p backups
"${COMPOSE[@]}" cp backend:/data/backups/. ./backups
echo "Backups on the host:"
find backups -maxdepth 1 -name 'infradesk-*.db' | sort -r | head -n 5
