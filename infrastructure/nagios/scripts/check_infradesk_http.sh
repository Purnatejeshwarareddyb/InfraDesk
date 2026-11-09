#!/bin/sh
# check_infradesk_http.sh - Nagios plugin: checks one URL of InfraDesk with curl.
#
# Output follows the Nagios plugin format:  "SERVICE STATUS - message | perfdata"
# Exit codes: 0 OK, 1 WARNING, 2 CRITICAL, 3 UNKNOWN.
#
#   OK       HTTP status 2xx, expected text present, answered faster than -w seconds
#   WARNING  correct answer but slower than -w seconds
#   CRITICAL no connection / timeout / HTTP status not 2xx / expected text missing / slower than -c
#   UNKNOWN  the plugin was called with bad arguments or curl is missing

HOST="127.0.0.1"
PORT="8080"
URLPATH="/health"
WARN="2"
CRIT="5"
EXPECT=""

usage() {
  cat <<USAGE
Usage: $0 [-H host] [-p port] [-u path] [-w warn_seconds] [-c crit_seconds] [-e expected_string]
  -H  host name or IP          (default $HOST)
  -p  TCP port                 (default $PORT)
  -u  URL path                 (default $URLPATH)
  -w  warning threshold, sec   (default $WARN)
  -c  critical threshold, sec  (default $CRIT)
  -e  string that must appear in the response body (optional)
Example: $0 -H 127.0.0.1 -p 8080 -u /ready -e ready -w 1 -c 3
USAGE
}

unknown() {
  echo "HTTP UNKNOWN - $1"
  exit 3
}

while getopts "H:p:u:w:c:e:h" opt; do
  case "$opt" in
    H) HOST="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    u) URLPATH="$OPTARG" ;;
    w) WARN="$OPTARG" ;;
    c) CRIT="$OPTARG" ;;
    e) EXPECT="$OPTARG" ;;
    h) usage; exit 3 ;;
    *) usage; unknown "invalid option" ;;
  esac
done

# --- validate arguments (all failures are UNKNOWN, never a guess) ---
command -v curl >/dev/null 2>&1 || unknown "curl is not installed"
case "$PORT" in
  ''|*[!0-9]*) unknown "port must be a number, got '$PORT'" ;;
esac
{ [ "$PORT" -ge 1 ] && [ "$PORT" -le 65535 ]; } || unknown "port out of range: $PORT"
for value in "$WARN" "$CRIT"; do
  case "$value" in
    ''|*[!0-9.]*|*.*.*) unknown "thresholds must be numbers (seconds), got '$value'" ;;
  esac
done
awk -v w="$WARN" -v c="$CRIT" 'BEGIN { exit !(w <= c) }' || unknown "warning threshold must not exceed critical threshold"
case "$URLPATH" in
  /*) ;;
  *) unknown "path must start with /, got '$URLPATH'" ;;
esac

URL="http://$HOST:$PORT$URLPATH"
BODY=$(mktemp) || unknown "cannot create a temporary file"
trap 'rm -f "$BODY"' EXIT

# curl gives up after the critical threshold + 2 s, so a hanging server cannot block Nagios.
MAXTIME=$(awk -v c="$CRIT" 'BEGIN { printf "%d", c + 2 }')
RESULT=$(curl -s -o "$BODY" -w '%{http_code} %{time_total}' --max-time "$MAXTIME" "$URL" 2>/dev/null)
CURL_RC=$?

if [ "$CURL_RC" -ne 0 ]; then
  echo "HTTP CRITICAL - cannot get $URL (curl exit code $CURL_RC: refused, timeout or DNS error) | time=0s;$WARN;$CRIT;0"
  exit 2
fi

CODE=${RESULT%% *}
TIME=${RESULT##* }
PERF="time=${TIME}s;$WARN;$CRIT;0"

case "$CODE" in
  2??) ;;
  *) echo "HTTP CRITICAL - $URL returned HTTP $CODE | $PERF"; exit 2 ;;
esac

if [ -n "$EXPECT" ] && ! grep -qF -- "$EXPECT" "$BODY"; then
  echo "HTTP CRITICAL - $URL returned HTTP $CODE but the text '$EXPECT' is missing | $PERF"
  exit 2
fi

if awk -v t="$TIME" -v c="$CRIT" 'BEGIN { exit !(t >= c) }'; then
  echo "HTTP CRITICAL - $URL answered in ${TIME}s (critical at ${CRIT}s) | $PERF"
  exit 2
fi
if awk -v t="$TIME" -v w="$WARN" 'BEGIN { exit !(t >= w) }'; then
  echo "HTTP WARNING - $URL answered in ${TIME}s (warning at ${WARN}s) | $PERF"
  exit 1
fi

echo "HTTP OK - $URL returned HTTP $CODE in ${TIME}s | $PERF"
exit 0
