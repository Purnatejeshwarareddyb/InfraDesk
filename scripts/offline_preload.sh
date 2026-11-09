#!/usr/bin/env bash
# offline_preload.sh - download everything once (online) so a later demo works offline.
# Usage: scripts/offline_preload.sh [--docker] [--npm] [--pip] [--terraform] [--all]
#   --docker     pull base images and build the InfraDesk images
#   --npm        fill an npm cache in .offline/npm-cache (and install frontend/node_modules)
#   --pip        download Python wheels to .offline/pip-wheels
#   --terraform  mirror the Terraform provider to .offline/provider-mirror (needs terraform)
# With no option this help is shown and nothing is downloaded.
set -euo pipefail

if [[ $# -eq 0 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
do_docker=0; do_npm=0; do_pip=0; do_tf=0
for arg in "$@"; do
  case "$arg" in
    --docker) do_docker=1 ;;
    --npm) do_npm=1 ;;
    --pip) do_pip=1 ;;
    --terraform) do_tf=1 ;;
    --all) do_docker=1; do_npm=1; do_pip=1; do_tf=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

summary=()

if [[ $do_docker -eq 1 ]]; then
  for image in python:3.13-slim node:22-alpine nginxinc/nginx-unprivileged:1.27-alpine; do
    docker pull "$image"
  done
  # SECRET_KEY is needed only so that compose can read the file; the build does not use it.
  SECRET_KEY="${SECRET_KEY:-build-only-placeholder-0123456789abcdef0123456789}" docker compose -f docker-compose.yml build
  summary+=("docker: base images and infradesk-backend / infradesk-frontend images")
fi

if [[ $do_npm -eq 1 ]]; then
  mkdir -p .offline/npm-cache
  (cd frontend && npm ci --cache "$ROOT/.offline/npm-cache")
  summary+=("npm: cache in .offline/npm-cache ($(du -sh .offline/npm-cache | cut -f1)); later: npm ci --offline --cache .offline/npm-cache")
fi

if [[ $do_pip -eq 1 ]]; then
  mkdir -p .offline/pip-wheels
  python3 -m pip download -r backend/requirements-dev.txt -d .offline/pip-wheels
  summary+=("pip: $(find .offline/pip-wheels -type f | wc -l) files in .offline/pip-wheels; later: pip install --no-index --find-links .offline/pip-wheels -r backend/requirements-dev.txt")
fi

if [[ $do_tf -eq 1 ]]; then
  if command -v terraform >/dev/null 2>&1; then
    (cd infrastructure/terraform && terraform init -backend=false && terraform providers mirror "$ROOT/.offline/provider-mirror")
    summary+=("terraform: provider mirror in .offline/provider-mirror")
  else
    summary+=("terraform: SKIPPED (terraform is not installed)")
  fi
fi

echo
echo "Cached:"
printf '  - %s\n' "${summary[@]}"
