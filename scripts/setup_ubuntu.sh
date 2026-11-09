#!/usr/bin/env bash
# setup_ubuntu.sh - prepare an Ubuntu 22.04 / 24.04 machine for InfraDesk.
# Safe to run again: it only installs what is missing and never overwrites an existing .env.
#
# Usage: scripts/setup_ubuntu.sh [--yes]
#   --yes   do not ask before the steps that need sudo
# Steps: 1) install packages (sudo)  2) create .env with a generated SECRET_KEY if missing
set -euo pipefail

ASSUME_YES=0
case "${1:-}" in
  --yes) ASSUME_YES=1 ;;
  -h|--help) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  "") ;;
  *) echo "unknown option: $1" >&2; exit 2 ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
fi
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "This script is written for Ubuntu (found: ${PRETTY_NAME:-unknown}). Nothing was changed." >&2
  exit 1
fi

ask() {
  [[ $ASSUME_YES -eq 1 ]] && return 0
  read -r -p "$1 [y/N] " answer
  [[ "$answer" == "y" || "$answer" == "Y" ]]
}

# --- 1. packages ---------------------------------------------------------------------------------
packages=(ca-certificates curl git python3 python3-venv python3-pip sqlite3 make docker.io)
# The `docker compose` plugin is packaged as docker-compose-v2 from Ubuntu 24.04.
if [[ "${VERSION_ID%%.*}" -ge 24 ]]; then
  packages+=(docker-compose-v2)
fi

to_install=()
for pkg in "${packages[@]}"; do
  dpkg -s "$pkg" >/dev/null 2>&1 || to_install+=("$pkg")
done

if [[ ${#to_install[@]} -eq 0 ]]; then
  echo "All packages are already installed."
elif ask "Install with sudo: ${to_install[*]} ?"; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends "${to_install[@]}"
else
  echo "Skipped package installation."
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "NOTE: the 'docker compose' plugin is missing. On Ubuntu 22.04 install docker-compose-plugin"
  echo "      from Docker's apt repository: https://docs.docker.com/engine/install/ubuntu/"
fi
if ! command -v node >/dev/null 2>&1; then
  echo "NOTE: Node.js 22 is not installed (needed only for frontend development, not for Docker)."
  echo "      Install it with nvm (https://github.com/nvm-sh/nvm) or NodeSource, then run: nvm install 22"
fi

# --- 2. .env ----------------------------------------------------------------------------------------
if [[ -f .env ]]; then
  echo ".env already exists; left unchanged."
else
  secret=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  # '#' is not in the token_urlsafe alphabet, so it is a safe sed delimiter.
  sed "s#^SECRET_KEY=.*#SECRET_KEY=${secret}#" .env.example > .env
  chmod 600 .env
  echo "Created .env with a generated SECRET_KEY (file mode 600). It is git-ignored; never commit it."
fi

echo "Next: make up     (then open http://localhost:\${INFRADESK_PORT:-8080})"
echo "Docker group: to run docker without sudo, run 'sudo usermod -aG docker \$USER' and log in again"
echo "              (this gives the user root-equivalent rights on the machine; only do it if you accept that)."
