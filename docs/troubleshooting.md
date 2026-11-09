# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker is not running | Windows: start Docker Desktop and wait until it says running. Ubuntu: `sudo systemctl start docker` |
| `permission denied ... /var/run/docker.sock` (Ubuntu) | user not in the `docker` group | `sudo usermod -aG docker "$USER"`, then log out and in |
| `SECRET_KEY: required` or the backend container exits at start | `.env` missing or `SECRET_KEY` empty or shorter than 32 characters | `make env` creates `.env` with a random key; or set a long random value yourself |
| `port is already allocated` / `address already in use` on 8080 | another program uses the port | set `INFRADESK_PORT=8090` in `.env` and run `make up` again |
| Page loads but sign-in says the session expired or is refused | opened through a different host name than the one the server expects, or a stale cookie | use `http://localhost:8080`; clear the site cookies |
| `403 Origin not allowed` on writes | the browser Origin does not match `CORS_ORIGINS` / allowed origins | add the exact URL you use (scheme, host, port) to `CORS_ORIGINS` in `.env`, then `make up` |
| `/ready` returns 503 | database file not writable or not migrated | `make logs`; check the `infradesk-data` volume is mounted; restart with `make up` |
| Seed command refuses to run | `ENVIRONMENT=production` or `--yes` missing | set `ENVIRONMENT=development` in `.env`, restart, then `make seed-demo` |
| Windows: scripts `.sh` do not run | PowerShell has no bash | use WSL 2 (Ubuntu) or Git Bash, or run the `docker compose` commands from `installation-windows.md` directly |
| VM cannot be reached from the host browser | NAT network mode | use bridged mode or add a port forward for 8080 |
| Terraform: image not found | Terraform uses locally built `:latest` images | run `make build` first |
| Terraform and Compose both want a port | both stacks running | stop one; Compose uses 8080, Terraform 8081 |
| Ansible: `.env` and Puppet env differ | two files, one secret | export the same `SECRET_KEY` for both tools |
| Nagios shows UNKNOWN | the plugin was called with bad arguments | run `check_infradesk_http.sh` by hand and read its usage line |
| Blank page after an update | cached old bundle | hard refresh (Ctrl+Shift+R) |

Still stuck: `docker compose ps`, `make logs`, and `curl -i localhost:8080/ready` give the three most useful facts. Never paste the contents of `.env` into a chat or an issue.
