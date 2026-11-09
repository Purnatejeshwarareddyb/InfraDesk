#!/bin/sh
# install_or_validate.sh - copy the InfraDesk Nagios files into a Nagios Core installation and
# validate the configuration. It never reloads Nagios unless validation passed.
#
# Usage:
#   install_or_validate.sh -d OBJECTS_DIR [-p PLUGIN_DIR] [-c NAGIOS_CFG] [-r]
#     -d  directory Nagios reads object files from, e.g. /usr/local/nagios/etc/objects
#         (files go to OBJECTS_DIR/infradesk/). Required.
#     -p  plugin directory, e.g. /usr/local/nagios/libexec. The custom check is copied there and
#         the host macro _PLUGINDIR is set to it. Default: do not copy the plugin.
#     -c  main nagios.cfg, used for `nagios -v`. Default: OBJECTS_DIR/../nagios.cfg
#     -r  reload Nagios after a successful validation (needs systemctl and sudo rights)
#     -h  this help
# Without -r nothing is reloaded. Without the nagios binary the files are copied but NOT validated
# and -r is refused.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
SRC_OBJECTS="$HERE/../objects"
OBJECTS_DIR=""
PLUGIN_DIR=""
NAGIOS_CFG=""
RELOAD=0

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }

while getopts "d:p:c:rh" opt; do
  case "$opt" in
    d) OBJECTS_DIR="$OPTARG" ;;
    p) PLUGIN_DIR="$OPTARG" ;;
    c) NAGIOS_CFG="$OPTARG" ;;
    r) RELOAD=1 ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

if [ -z "$OBJECTS_DIR" ] || [ ! -d "$OBJECTS_DIR" ]; then
  echo "error: -d must name an existing directory (got '${OBJECTS_DIR}')" >&2
  usage
  exit 2
fi
[ -n "$NAGIOS_CFG" ] || NAGIOS_CFG="$OBJECTS_DIR/../nagios.cfg"

TARGET="$OBJECTS_DIR/infradesk"
mkdir -p "$TARGET"


# Files not ending in .cfg are ignored by Nagios, so the copies cannot be loaded twice.
STAMP=$(date +%Y%m%d%H%M%S)
for f in "$TARGET"/*.cfg; do
  [ -e "$f" ] || continue
  cp "$f" "$f.bak-$STAMP"
  echo "previous $(basename "$f") saved as $(basename "$f").bak-$STAMP"
done

cp "$SRC_OBJECTS"/commands.cfg "$SRC_OBJECTS"/hosts.cfg "$SRC_OBJECTS"/services.cfg "$TARGET"/
echo "copied commands.cfg, hosts.cfg, services.cfg to $TARGET"

if [ -n "$PLUGIN_DIR" ]; then
  [ -d "$PLUGIN_DIR" ] || { echo "error: plugin directory $PLUGIN_DIR does not exist" >&2; exit 2; }
  cp "$HERE/check_infradesk_http.sh" "$PLUGIN_DIR"/
  chmod 755 "$PLUGIN_DIR/check_infradesk_http.sh"
  # Point the host macro at this plugin directory (edit the COPY, not the repository file).
  sed "s#^\([[:space:]]*_PLUGINDIR[[:space:]]*\).*#\1$PLUGIN_DIR#" "$TARGET/hosts.cfg" > "$TARGET/hosts.cfg.tmp"
  mv "$TARGET/hosts.cfg.tmp" "$TARGET/hosts.cfg"
  echo "plugin installed in $PLUGIN_DIR"
else
  echo "note: -p not given; copy scripts/check_infradesk_http.sh into your plugin directory yourself"
fi

echo "reminder: nagios.cfg needs the line   cfg_dir=$TARGET"
echo "          and the sample templates (generic-host, generic-service, 24x7) must be loaded."

NAGIOS_BIN=$(command -v nagios || command -v nagios4 || true)
if [ -z "$NAGIOS_BIN" ]; then
  echo "WARNING: no nagios binary found; configuration NOT validated."
  if [ "$RELOAD" -eq 1 ]; then
    echo "refusing to reload without validation." >&2
    exit 1
  fi
  exit 0
fi

echo "validating with: $NAGIOS_BIN -v $NAGIOS_CFG"
if "$NAGIOS_BIN" -v "$NAGIOS_CFG"; then
  echo "VALIDATION PASSED"
else
  echo "VALIDATION FAILED - not reloading. Fix the errors above (old copies: *.cfg.bak-*)." >&2
  exit 1
fi

if [ "$RELOAD" -eq 1 ]; then
  SERVICE=$(basename "$NAGIOS_BIN")
  echo "reloading $SERVICE"
  systemctl reload "$SERVICE"
else
  echo "validated; reload yourself:  sudo systemctl reload nagios   (or re-run with -r)"
fi
