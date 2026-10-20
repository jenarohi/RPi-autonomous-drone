#!/bin/bash
# usage: tools/fly_all.sh <suffix> [worlds...]  - full missions in the delivery-search worlds, one summary per world
W=$HOME/skyscan/worlds; SUF=$1; shift
for n in ${@:-dz_ahead dz_side dz_rot dz_far}; do
  bash $HOME/skyscan/tools/fly_test_noise.sh ${n}$SUF $W/$n.sdf --home -3 3 --full
  echo "######## $n"
  grep -E 'SEARCH    \]|PAYLOAD  .*RELEASED|MISSION COMPLETE|ABORT|mission exit|Traceback|Error|=== ' /tmp/sitl_test/${n}$SUF.log | cut -c1-200
done
