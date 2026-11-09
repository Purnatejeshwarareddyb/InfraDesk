<#
InfraDesk one-step setup for Windows 11 (PowerShell). Run from the repository root:
    powershell -ExecutionPolicy Bypass -File scripts\windows\setup.ps1 [-Demo] [-Admin <username>]
-Demo   also loads fictional demo users and data (local demonstration only)
Safe to repeat. Never overwrites an existing .env.
#>
param([switch]$Demo, [string]$Admin = "")
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail "Docker is not installed. Install Docker Desktop (WSL2 backend) first: docs\installation-windows.md" }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Fail "Docker is installed but not running. Start Docker Desktop and wait for 'Engine running', then run this again." }

if (-not (Test-Path .env)) {
    $bytes = New-Object byte[] 48
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $key = [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_").TrimEnd("=")
    $text = (Get-Content .env.example -Raw) -replace "SECRET_KEY=change-me", "SECRET_KEY=$key"
    if (-not $Demo) { $text = $text -replace "ENVIRONMENT=development", "ENVIRONMENT=production" }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) ".env"), $text, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "Created .env with a new random SECRET_KEY (not shown, not committed)."
} else {
    Write-Host ".env already exists; leaving it unchanged."
    if ($Demo -and -not (Select-String -Path .env -Pattern '^ENVIRONMENT=development' -Quiet)) {
        Fail "-Demo needs ENVIRONMENT=development in .env (demo data is refused in production). Edit .env and run again."
    }
}

Write-Host "Building and starting (first build takes several minutes)..."
docker compose -f docker-compose.yml up -d --build
if ($LASTEXITCODE -ne 0) { Fail "docker compose failed; see the output above and docs\troubleshooting.md" }

$port = "8080"
$m = Select-String -Path .env -Pattern '^INFRADESK_PORT=(\d+)' | Select-Object -First 1
if ($m) { $port = $m.Matches[0].Groups[1].Value }

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try { $r = Invoke-WebRequest -UseBasicParsing "http://localhost:$port/ready" -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ready = $true; break } } catch { }
    Start-Sleep -Seconds 2
}
if (-not $ready) { Fail "The application did not become ready in 2 minutes. Run: docker compose -f docker-compose.yml logs" }
Write-Host "Application is ready: http://localhost:$port" -ForegroundColor Green

if ($Demo) {
    docker compose -f docker-compose.yml exec -T backend python scripts/seed_demo_data.py --yes
    Write-Host "Demo users: demo_admin, worker_asha, worker_ravi  (password Demo-Passw0rd!, local demonstration only)"
}
if ($Admin -ne "") {
    Write-Host "Creating administrator '$Admin' (you will be asked for a password)..."
    docker compose -f docker-compose.yml exec backend python scripts/create_admin.py --username $Admin --display-name $Admin
}
Write-Host "Stop with: powershell -File scripts\windows\stop.ps1"
