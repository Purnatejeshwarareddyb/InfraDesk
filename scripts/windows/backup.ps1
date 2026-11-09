# Backs up the database of the RUNNING stack into .\backups (same method as scripts/backup.sh).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")
$running = docker compose -f docker-compose.yml ps --status running --services 2>$null
if ($running -notcontains "backend") { Write-Host "The backend is not running. Start it with scripts\windows\setup.ps1" -ForegroundColor Red; exit 1 }
docker compose -f docker-compose.yml exec -T backend python scripts/backup_database.py --db /data/infradesk.db --out /data/backups
if ($LASTEXITCODE -ne 0) { Write-Host "Backup failed." -ForegroundColor Red; exit 1 }
New-Item -ItemType Directory -Force backups | Out-Null
docker compose -f docker-compose.yml cp backend:/data/backups/. ./backups
Write-Host "Backups are in: $(Resolve-Path backups)"
Get-ChildItem backups -Filter "infradesk-*.db" | Sort-Object Name -Descending | Select-Object -First 5 Name
