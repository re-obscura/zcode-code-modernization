#!/bin/sh
# Runs one of the plugin's ZCode-only hooks with the hook's JSON on stdin:
#   run-hook.sh xray   PostToolUse (Read): print {"additionalContext": ...} when the analysis knows the file
#   run-hook.sh guard  PreToolUse (Edit|Write|ApplyPatch): exit 2 when the write aims under legacy/
# ZCode runs command hooks through a shell and injects ${CLAUDE_PLUGIN_ROOT}, so the interpreter search
# lives here, not in hooks.json. Python is picked exactly like telemetry.sh picks it: python3 first,
# then python, then the py launcher (Windows); a 3.8-or-newer one, else the plugin stays silent.
mode="$1"
here=$(dirname "$0")

ok_version() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1
}

py=""
if command -v python3 >/dev/null 2>&1 && ok_version python3; then
  py="python3"
elif command -v python >/dev/null 2>&1 && ok_version python; then
  py="python"
elif command -v py >/dev/null 2>&1 && ok_version "py -3"; then
  py="py -3"
fi
[ -n "$py" ] || exit 0

case "$py" in
  "py -3") exec py -3 "$here/hook.py" "$mode" ;;
  *) exec "$py" "$here/hook.py" "$mode" ;;
esac
