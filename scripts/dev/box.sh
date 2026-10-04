#!/usr/bin/env bash
# Dev helper, run on the dev machine: sync this repo tree to a sandbox on the robotics box, then run a
# command there.
#
#   scripts/dev/box.sh <sandbox> [--sim] [--no-sync] [-- <command ...>]
#
#   <sandbox>   box-side copy: /tmp/skyscan_dev/<sandbox> (plain copy, no .git; .runtime/ and runs/ survive syncs)
#   --sim       hold the box-wide sim lock (/tmp/skyscan_sim.lock) while the command runs, so only one session
#               at a time drives Gazebo / SITL instance 0 (UDP 9002, TCP 5760, websocket 9090, HTTP 8080)
#   --no-sync   skip the rsync
#
# The command runs with /opt/robotics/drone_env/setup_drone.sh sourced (ROS 2 / Gazebo / venv), cwd = sandbox,
# PYTHONPATH starting with the sandbox. Examples:
#   scripts/dev/box.sh flight -- python -m pytest -q tests
#   scripts/dev/box.sh sim --sim -- python -m skyscan.sim.procman --selftest
set -eo pipefail
BOX=${SKYSCAN_BOX:-barath@192.168.29.94}
KEY=${SKYSCAN_KEY:-$HOME/.ssh/id_ed25519_gpu}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SSH=(ssh -i "$KEY" -o ConnectTimeout=10 -o ServerAliveInterval=15 -o BatchMode=yes)

name=${1:?usage: box.sh <sandbox> [--sim] [--no-sync] [-- <command ...>]}
shift
sim=0
sync=1
while [ $# -gt 0 ]; do
  case "$1" in
    --sim) sim=1; shift ;;
    --no-sync) sync=0; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done
[[ "$name" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "box.sh: bad sandbox name: $name" >&2; exit 2; }
DEST=/tmp/skyscan_dev/$name

if [ "$sync" = 1 ]; then
  "${SSH[@]}" "$BOX" "mkdir -p $DEST"
  rsync -a --delete \
    --exclude .git --exclude __pycache__ --exclude .pytest_cache --exclude '*.pyc' \
    --exclude .runtime --exclude runs --exclude node_modules --exclude .DS_Store \
    -e "${SSH[*]}" "$ROOT/" "$BOX:$DEST/"
fi
[ $# -eq 0 ] && exit 0

cmd=$(printf '%q ' "$@")
lock=""
[ "$sim" = 1 ] && lock="flock -w 1800 /tmp/skyscan_sim.lock"
exec "${SSH[@]}" "$BOX" "cd $DEST && source /opt/robotics/drone_env/setup_drone.sh >/dev/null 2>&1; \
export PYTHONPATH=$DEST:\${PYTHONPATH:-} PYTHONDONTWRITEBYTECODE=1; $lock bash -c $(printf '%q' "$cmd")"
