#!/bin/bash
# camera-latency experiment: <sim latency> <compensation> <suffix> triples, flown in dz_ahead
for cfg in "0 0 e0" "0.12 0 e1" "0.12 0.12 e2" "0.25 0 e3" "0.25 0.25 e4"; do
  set -- $cfg
  SKYSCAN_SIM_LATENCY=$1 SKYSCAN_LATENCY_COMP=$2 ~/skyscan/tools/fly_all.sh _$3 dz_ahead > /tmp/lat_$3_summary.txt 2>&1
done
echo ALLDONE > /tmp/lat_done.txt
