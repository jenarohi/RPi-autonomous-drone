#!/usr/bin/env bash
# SkyScan Mission Control: one-click launcher (server + Gazebo/SITL + a single full-screen Firefox window).
#
#   scripts/skyscan.sh [--no-sim] [--window] [--no-browser] [--port N] [-- extra `python -m skyscan` args]
#
#   --no-sim       do not autostart Gazebo + SITL (press "Start Sim" in the UI, or fly real hardware)
#   --window       open a normal Firefox window instead of kiosk mode
#   --no-browser   only run the server (open http://<box>:8080 from any machine)
#   --port N       server port (default 8080)
#
# The server's log goes to ~/.local/state/skyscan/server.log. Closing the Firefox window (Alt+F4 / Ctrl+Q in kiosk
# mode) stops the server, Gazebo and SITL again. If a server is already running on the port it is reused and left
# running. There are no terminal or MAVProxy windows: everything is in the UI.
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/skyscan"
LOG="$STATE_DIR/server.log"
# the Firefox snap can only write to non-hidden folders under $HOME
PROFILE="$HOME/snap/firefox/common/skyscan-profile"
[ -d "$HOME/snap/firefox" ] || PROFILE="$STATE_DIR/firefox-profile"

SIM=1
KIOSK=1
BROWSER=1
PORT=8080
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --no-sim) SIM=0 ;;
        --window) KIOSK=0 ;;
        --no-browser) BROWSER=0 ;;
        --port) PORT="${2:?--port needs a value}"; shift ;;
        --) shift; ARGS+=("$@"); break ;;
        -h|--help) sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) ARGS+=("$1") ;;
    esac
    shift
done

notify() {
    echo "skyscan: $*" >&2
    if [ -n "$DISPLAY" ] && command -v notify-send >/dev/null 2>&1; then
        notify-send -u critical "SkyScan Mission Control" "$*" || true
    fi
}

if [ -z "$DISPLAY" ] && [ -e /tmp/.X11-unix/X0 ]; then
    export DISPLAY=":0"
fi
[ -z "$DISPLAY" ] && BROWSER=0

# shellcheck disable=SC1091
[ -f /opt/robotics/drone_env/setup_drone.sh ] && source /opt/robotics/drone_env/setup_drone.sh >/dev/null 2>&1 || true
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
mkdir -p "$STATE_DIR"

URL="http://127.0.0.1:$PORT"
healthy() { curl -fs --max-time 2 "$URL/api/health" 2>/dev/null | grep -q '"ok"'; }

SERVER_PID=""
if healthy; then
    echo "skyscan: server already running on port $PORT, reusing it"
else
    CMD=(python3 -m skyscan --set "server.port=$PORT")
    [ "$SIM" = 1 ] && CMD+=(--set sim.autostart=true)
    CMD+=("${ARGS[@]}")
    : > "$LOG"
    "${CMD[@]}" >>"$LOG" 2>&1 &
    SERVER_PID=$!
    echo "skyscan: starting server (pid $SERVER_PID), log: $LOG"
    for _ in $(seq 1 120); do
        healthy && break
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            notify "The server stopped while starting. Last log lines: $(tail -n 4 "$LOG" | tr '\n' ' ')"
            exit 1
        fi
        sleep 0.5
    done
    if ! healthy; then
        notify "The server did not answer on port $PORT within 60 s. See $LOG"
        kill -TERM "$SERVER_PID" 2>/dev/null || true
        exit 1
    fi
fi

stop_server() {
    [ -n "$SERVER_PID" ] || return 0
    kill -0 "$SERVER_PID" 2>/dev/null || return 0
    echo "skyscan: stopping server, Gazebo and SITL ..."
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    for _ in $(seq 1 60); do
        kill -0 "$SERVER_PID" 2>/dev/null || return 0
        sleep 0.5
    done
    kill -KILL "$SERVER_PID" 2>/dev/null || true
}
trap stop_server EXIT
trap 'exit 0' INT TERM HUP

if [ "$BROWSER" = 1 ]; then
    if command -v firefox >/dev/null 2>&1; then
        mkdir -p "$PROFILE"
        cat > "$PROFILE/user.js" <<'EOF'
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.page", 0);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("media.autoplay.default", 0);
EOF
        FF=(firefox --new-instance --profile "$PROFILE")
        [ "$KIOSK" = 1 ] && FF+=(--kiosk)
        echo "skyscan: opening the cockpit ($URL)"
        # runs until the window is closed; then the EXIT trap shuts the stack down
        "${FF[@]}" "$URL" >/dev/null 2>&1 || true
        exit 0
    fi
    notify "Firefox is not installed. Open $URL in any browser."
fi

echo "skyscan: cockpit at http://$(hostname).local:$PORT  (Ctrl+C to stop)"
if [ -n "$SERVER_PID" ]; then
    wait "$SERVER_PID" || true
else
    while healthy; do sleep 5; done
fi
