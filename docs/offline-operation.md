# Offline operation

**Offline means no internet.** The application and its API documentation page make no request to any
external host: no CDN, no web fonts, no analytics, no third-party API. Other devices can use it only
if they are on the same local network as the host.

## What needs the internet, and when

| Item | Needed online once | Cached by |
|---|---|---|
| Ubuntu/Windows packages, Docker Engine or Docker Desktop | yes | OS package cache |
| Base images `python:3.13-slim`, `node:22-alpine`, `nginxinc/nginx-unprivileged:1.27-alpine` | yes | Docker image store (`scripts/offline_preload.sh --docker`) |
| Python packages | yes (image build) | `--pip` downloads wheels to `.offline/pip-wheels` |
| npm packages | yes (image build, `npm ci`) | `--npm` fills `.offline/npm-cache` and installs `frontend/node_modules` |
| Terraform Docker provider | yes (`terraform init`) | `--terraform` mirrors it to `.offline/provider-mirror` (needs Terraform) |
| Puppet, Ansible, Nagios packages | yes | OS package cache |

A **fresh installation on a clean computer is not possible offline.** Prepare while online, then disconnect.

## Prepare (online)

```bash
scripts/offline_preload.sh --all          # or choose --docker --npm --pip --terraform
docker images | grep -E "infradesk|python|nginx|node"      # the images are now local
```

Build the images once with `make build` so the final images exist locally; after that `docker compose up` does not pull or download anything.

## Prove it (offline)

1. Start the stack (`make up`) and confirm it works.
2. Disconnect the internet but keep the local network: turn off Wi-Fi or unplug the cable, or in a VM set the adapter to **Host-only**.
   (On Linux, `ip route` should show no default route.)
3. Restart the stack: `make down && make up` (this must not try to download anything; it builds from the local cache or reuses the images).
4. Check: <http://localhost:8080> loads and works; <http://localhost:8080/docs> renders the Swagger page; log in, create a ticket;
   `curl localhost:8080/ready` returns `{"status":"ready"}`.
5. Optional proof that nothing external is requested: open the browser developer tools, Network tab, reload, and confirm every request goes to
   `localhost`. The repository also contains a test that fails if the API docs page references a CDN.

Record the result (date, how the network was disconnected, what you checked) in `reports/evidence/`.

## If something tries to download

`docker compose up --build` after a source change rebuilds layers and needs the package registries **unless** the dependency layers
are cached; keep `requirements.txt` and `package-lock.json` unchanged while offline. Use `docker compose up -d` (no `--build`) to reuse existing images.
