#!/usr/bin/env bash
# dev_stop.sh - stop the processes started by scripts/dev_start.sh (reads .run/*.pid).
# Usage: scripts/dev_stop.sh
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '2,3p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

RUN="$(cd "$(dirname "$0")/.." && pwd)/.run"

for name in frontend backend; do
  pidfile="$RUN/$name.pid"
  if [[ ! -f "$pidfile" ]]; then
    echo "$name: no PID file, nothing to stop."
    continue
  fi
  pid=$(cat "$pidfile")
  if kill -0 "$pid" 2>/dev/null; then
    # Kill the child processes first (npm and uvicorn --reload spawn children), then the parent.
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    echo "$name stopped (PID $pid)."
  else
    echo "$name: process $pid was not running."
  fi
  rm -f "$pidfile"
done
