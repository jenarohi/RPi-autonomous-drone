#!/bin/bash
# usage: tools/fly_test.sh <run-name> <world.sdf path or name> [run_mission args...]
# Headless: restarts Gazebo (server only, no GUI) + SITL, flies run_mission.py, stops everything.
# Log: /tmp/sitl_test/<run-name>.log
NAME=$1; WORLD=${2:-aerothon_mission.sdf}; shift 2
export GALLIUM_DRIVER=d3d12
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/gz_ws/src/ardupilot_gazebo/build
export GZ_SIM_RESOURCE_PATH=$HOME/gz_ws/src/ardupilot_gazebo/models:$HOME/gz_ws/src/ardupilot_gazebo/worlds:$HOME/gz_ws/src/aerothon_world/worlds
pkill -9 -f "[a]rducopter"; pkill -9 -f "[g]z sim"; pkill -9 -f "[r]un_mission.py"; sleep 1
mkdir -p /tmp/sitl_test && cd /tmp/sitl_test
gz sim -s -r -v 2 "$WORLD" > gz_$NAME.log 2>&1 < /dev/null &
GZ=$!
sleep 8
DP=$HOME/ardupilot/Tools/autotest/default_params
$HOME/ardupilot/build/sitl/bin/arducopter -w --model JSON --speedup 1 --slave 0 \
  --defaults $DP/copter.parm,$DP/gazebo-iris.parm --sim-address=127.0.0.1 -I0 > sitl_$NAME.log 2>&1 < /dev/null &
SITL=$!
sleep 3
cd ~/skyscan && timeout 900 python3 -u run_mission.py --url tcp:127.0.0.1:5760 "$@" 2>&1 \
  | grep --line-buffered -v -E "pkg_resources|declare_namespace" > /tmp/sitl_test/$NAME.log
echo "mission exit ${PIPESTATUS[0]}" >> /tmp/sitl_test/$NAME.log
kill -9 $SITL $GZ 2>/dev/null; pkill -9 -f "[g]z sim"; pkill -9 -f "[a]rducopter"
