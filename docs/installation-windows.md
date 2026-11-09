# Installation on Windows 11

Two paths. Pick **A** to run and demonstrate the application quickly. Pick **B** (an Ubuntu virtual
machine) when you also want to demonstrate Puppet, Ansible and Nagios, which are Linux tools.

Laptop reference: Windows 11, 8 GB RAM, Ryzen 5 5500U, integrated graphics. No GPU is needed.

## Fastest route (one script)

After Docker Desktop shows "Engine running", open PowerShell in the project folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\setup.ps1 -Demo
```

It checks Docker, creates `.env` with a random `SECRET_KEY` (never overwritten), builds and starts the stack, waits for `/ready`, and with `-Demo` loads the fictional demo users.
Use `-Admin myname` instead of `-Demo` to create a real administrator (it asks for the password). Then `scripts\windows\stop.ps1` to stop and `scripts\windows\backup.ps1` to back up.
These PowerShell scripts were written but **not executed** in the build environment (no Windows); if one fails, the manual steps below do the same thing.

## Path A: Docker Desktop with WSL2 (application and Compose)

1. Turn on virtualization in the BIOS if it is off (Task Manager, Performance, CPU: "Virtualization: Enabled").
2. Open PowerShell as administrator: `wsl --install` and restart. Check with `wsl --status`.
3. Install **Docker Desktop** (WSL2 backend). Start it and wait until it says "Engine running".
4. Limit its memory so the laptop stays responsive: create `%UserProfile%\.wslconfig` containing

   ```
   [wsl2]
   memory=3GB
   processors=4
   ```

   then run `wsl --shutdown` and start Docker Desktop again. InfraDesk itself uses about 100 to 250 MB.
5. Install **Git for Windows**. Optionally install `make` (for example `winget install GnuWin32.Make`) or just use the plain
   commands below.
6. Get the project and start it (PowerShell):

   ```powershell
   git clone <your-repository-url> InfraDesk; cd InfraDesk
   Copy-Item .env.example .env
   # generate a secret and put it into .env as SECRET_KEY=...
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   notepad .env
   docker compose -f docker-compose.yml up -d --build
   ```

   (No Python on Windows? Use any random string of 40 or more characters, for example from a password manager.)
7. Open <http://localhost:8080>. Create an administrator:

   ```powershell
   docker compose -f docker-compose.yml exec backend python scripts/create_admin.py --username admin --display-name "Lab Admin"
   ```

   or load fictional demo data (`ENVIRONMENT=development` must be set in `.env` first, then `docker compose ... up -d` again):

   ```powershell
   docker compose -f docker-compose.yml exec backend python scripts/seed_demo_data.py --yes
   ```

8. Stop: `docker compose -f docker-compose.yml down` (data stays in the volume). Start again with `up -d`.

Reach it from another device on the same network: allow inbound TCP 8080 in Windows Defender Firewall, then browse to
`http://<this-pc-ip>:8080` (find the address with `ipconfig`). Add that address to `CORS_ORIGINS` only if you call the API directly
from another origin; the normal web interface is same-origin and needs nothing. It works only on the same local network, not from the internet.

## Local development without Docker (Windows)

```powershell
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SECRET_KEY = "dev-only-secret-key-change-me-0123456789abcdef"
python scripts/seed_demo_data.py --yes; uvicorn app.main:app --port 8000
# second terminal
cd frontend; npm ci; npm run dev          # http://localhost:5173
```

Needs Python 3.11+ and Node.js 20+. The shell scripts in `scripts/` are for Linux; on Windows use WSL or the commands above.

## Path B: Ubuntu virtual machine (for Puppet, Ansible, Nagios)

1. Install VirtualBox (or VMware Workstation Player) and download Ubuntu Server or Desktop 24.04 LTS.
2. Create a VM with **2 vCPUs, 3 GB RAM, 25 GB disk**. Do not run Docker Desktop at the same time (8 GB total is tight).
3. Network: **Bridged adapter** if you want other devices to reach it, otherwise NAT with a port forward (host 8080 to guest 8080,
   host 22 to guest 22). Host-only is enough for a demo from the same laptop.
4. Install Ubuntu, then continue with [installation-ubuntu.md](installation-ubuntu.md) inside the VM.

CPU and RAM tips: close the browser tabs you do not need, build the images once (`docker compose build`) and reuse them,
and do not run the Terraform stack and the Compose stack together unless you need to (each uses little, but Nagios and the VM add up).
