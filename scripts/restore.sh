#!/usr/bin/env bash
# restore.sh - restore the database of the Docker Compose stack from a backup file. DESTRUCTIVE.
# Usage: scripts/restore.sh backups/infradesk-YYYYMMDDTHHMMSS...db
# Steps: ask for typed confirmation -> stop the app -> one-off container restores the file
#        (the old database is first saved as /data/infradesk.db.before-restore-*) -> start the app.
set -euo pipefail

if [[ $# -ne 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'
  [[ $# -eq 1 ]] && exit 0
  exit 2
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
FILE=$1
if [[ ! -f "$FILE" ]]; then
  echo "Backup file not found: $FILE" >&2
  exit 1
fi
DIR=$(cd "$(dirname "$FILE")" && pwd)
NAME=$(basename "$FILE")
COMPOSE=(docker compose -f docker-compose.yml)

echo "This will REPLACE the current InfraDesk database with: $FILE"
echo "The application will be stopped and started again. The old database is kept as a safety copy."
read -r -p "Type 'restore' to continue: " answer
if [[ "$answer" != "restore" ]]; then
  echo "Cancelled. Nothing was changed."
  exit 1
fi

"${COMPOSE[@]}" stop
# --no-deps: do not start the web container. The backup folder is mounted read-only.
if "${COMPOSE[@]}" run --rm --no-deps -v "$DIR:/restore:ro" backend \
     python scripts/restore_database.py "/restore/$NAME" --db /data/infradesk.db --yes; then
  "${COMPOSE[@]}" up -d
  echo "Restore finished and the application was started."
else
  echo "Restore FAILED. The application is still stopped; the data was not replaced." >&2
  echo "Start it again with: make up" >&2
  exit 1
fi
