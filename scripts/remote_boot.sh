#!/usr/bin/env bash
# Boot service for remote control of the box: SkyScan server (+ Gazebo + SITL), a Cloudflare quick tunnel, and a
# Discord message with the new public link every time the tunnel (re)starts.
#
# Run by the systemd user unit scripts/systemd/skyscan-remote.service. Settings come from
# ~/.config/skyscan/remote.env (mode 600, never in the repo):
#     SKYSCAN_REMOTE_AUTH=pilot:<password>      login required for requests that arrive through the tunnel
#     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SKYSCAN_REMOTE_ENV:-$HOME/.config/skyscan/remote.env}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/skyscan"
PORT=8080
mkdir -p "$STATE_DIR"

if [ ! -r "$ENV_FILE" ]; then
    echo "remote_boot: missing $ENV_FILE" >&2
    exit 2
fi
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
if [ -z "${SKYSCAN_REMOTE_AUTH:-}" ]; then
    echo "remote_boot: SKYSCAN_REMOTE_AUTH is empty; refusing to open a tunnel without a password" >&2
    exit 2
fi

say() {   # post a line to Discord (best effort)
    [ -n "${DISCORD_WEBHOOK_URL:-}" ] || return 0
    local body
    body=$(printf '{"content":"%s"}' "$1")
    curl -fsS --max-time 15 -H 'Content-Type: application/json' -d "$body" "$DISCORD_WEBHOOK_URL" >/dev/null 2>&1 || true
}

healthy() { curl -fs --max-time 2 "http://127.0.0.1:$PORT/api/health" 2>/dev/null | grep -q '"ok"'; }

# 1. server + sim (skyscan.sh reuses a healthy server if one is already up)
"$SCRIPT_DIR/skyscan.sh" --no-browser >>"$STATE_DIR/boot_server.log" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 180); do
    healthy && break
    kill -0 "$SERVER_PID" 2>/dev/null || { echo "remote_boot: server exited while starting" >&2; exit 1; }
    sleep 1
done
healthy || { echo "remote_boot: server never became healthy" >&2; exit 1; }

# 2. tunnel, restarted (and re-announced) whenever it drops
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
while kill -0 "$SERVER_PID" 2>/dev/null; do
    : > "$STATE_DIR/tunnel.log"
    cloudflared tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" >>"$STATE_DIR/tunnel.log" 2>&1 &
    TUNNEL_PID=$!
    URL=""
    for _ in $(seq 1 90); do
        URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$STATE_DIR/tunnel.log" | head -1)
        [ -n "$URL" ] && break
        kill -0 "$TUNNEL_PID" 2>/dev/null || break
        sleep 1
    done
    if [ -n "$URL" ]; then
        echo "$URL" > "$STATE_DIR/public_url"
        say "SkyScan Mission Control (Axiom Dynamics) is online: $URL  | login: pilot | LAN: http://$IP:$PORT"
        echo "remote_boot: tunnel $URL"
    else
        echo "remote_boot: no tunnel URL yet, retrying" >&2
    fi
    # block until the tunnel or the server dies
    while kill -0 "$TUNNEL_PID" 2>/dev/null && kill -0 "$SERVER_PID" 2>/dev/null; do sleep 5; done
    kill "$TUNNEL_PID" 2>/dev/null || true
    wait "$TUNNEL_PID" 2>/dev/null || true
    sleep 5
done

echo "remote_boot: server stopped" >&2
exit 1
