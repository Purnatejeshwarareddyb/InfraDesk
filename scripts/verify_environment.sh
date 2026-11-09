#!/usr/bin/env bash
# verify_environment.sh - report which tools are installed (read-only, changes nothing).
# Usage: scripts/verify_environment.sh [-h]
# Exit code: 0 if all REQUIRED tools exist (docker, docker compose, python3, node, npm), else 1.
# Optional tools (terraform, puppet, ansible, nagios, ...) and the Docker daemon never change the exit code.
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

missing=0

# check NAME REQUIRED(yes|no) COMMAND VERSION_COMMAND...
check() {
  local name=$1 required=$2 cmd=$3
  shift 3
  if command -v "$cmd" >/dev/null 2>&1; then
    local version
    version=$("$@" 2>&1 | head -n 1 || true)
    printf '  [ok]       %-12s %s\n' "$name" "$version"
  else
    if [[ "$required" == "yes" ]]; then
      printf '  [MISSING]  %-12s (required)\n' "$name"
      missing=1
    else
      printf '  [absent]   %-12s (optional)\n' "$name"
    fi
  fi
}

echo "Required tools"
check docker   yes docker  docker --version
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  printf '  [ok]       %-12s %s\n' "compose" "$(docker compose version | head -n 1)"
else
  printf '  [MISSING]  %-12s (required: the "docker compose" plugin)\n' "compose"
  missing=1
fi
check python3  yes python3 python3 --version
check node     yes node    node --version
check npm      yes npm     npm --version

echo "Optional tools"
check git       no git       git --version
check make      no make      make --version
check terraform no terraform terraform version
check puppet    no puppet    puppet --version
check ansible   no ansible   ansible --version
check nagios    no nagios    nagios --version
check shellcheck no shellcheck shellcheck --version
check yamllint  no yamllint  yamllint --version

echo "Docker daemon"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "  [ok]       daemon reachable"
  else
    echo "  [not reachable] start Docker (Docker Desktop on Windows, 'sudo systemctl start docker' on Linux)"
  fi
else
  echo "  [skipped]  docker CLI not installed"
fi

if [[ $missing -ne 0 ]]; then
  echo "Result: a REQUIRED tool is missing."
  exit 1
fi
echo "Result: all required tools are installed."
