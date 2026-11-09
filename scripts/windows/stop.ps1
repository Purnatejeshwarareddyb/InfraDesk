# Stops InfraDesk. Data stays in the Docker volume. Add -Remove to also delete the volume (ALL DATA LOST).
param([switch]$Remove)
Set-Location (Join-Path $PSScriptRoot "..\..")
if ($Remove) {
    $a = Read-Host "This deletes the database volume. Type DELETE to continue"
    if ($a -ne "DELETE") { Write-Host "Cancelled."; exit 0 }
    docker compose -f docker-compose.yml down -v
} else { docker compose -f docker-compose.yml down }
