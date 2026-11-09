#!/bin/sh
# Managed by Puppet (module infradesk_host). Daily InfraDesk backup, started by infradesk-backup.timer.
# Variables come from /etc/infradesk/infradesk.env through the systemd EnvironmentFile.
# Steps: 1) consistent SQLite backup inside the container, 2) copy it to the host, 3) prune old files.
set -eu

APP_DIR="${INFRADESK_APP_DIR:-/opt/infradesk/app}"
DEST="${INFRADESK_BACKUP_DIR:-/opt/infradesk/backups}"
DAYS="${INFRADESK_RETENTION_DAYS:-14}"

if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
  echo "infradesk-backup: $APP_DIR/docker-compose.yml not found (deploy the app with Ansible first)" >&2
  exit 1
fi
cd "$APP_DIR"

# -T: no terminal (we run from systemd). -f: ignore compose.override.yml.
docker compose -f docker-compose.yml exec -T backend \
  python scripts/backup_database.py --db /data/infradesk.db --out /data/backups
docker compose -f docker-compose.yml cp backend:/data/backups/. "$DEST/"

# Keep the volume and the host copy from growing forever.
docker compose -f docker-compose.yml exec -T backend \
  find /data/backups -name 'infradesk-*.db' -mtime "+$DAYS" -delete
find "$DEST" -name 'infradesk-*.db' -mtime "+$DAYS" -delete
chmod 0640 "$DEST"/infradesk-*.db 2>/dev/null || true
echo "infradesk-backup: done, copies are in $DEST"
