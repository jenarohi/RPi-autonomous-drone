#!/bin/bash
# one long overnight-style queue; each block appends to /tmp/queue_progress.txt
P=/tmp/queue_progress.txt; : > $P
W=$HOME/skyscan/worlds; T=$HOME/skyscan/tools
note() { echo "$(date +%H:%M) $*" >> $P; }
note "block 1: latency tolerance (sim 0.12 s, compensation 0.06 / 0.20)"
SKYSCAN_SIM_LATENCY=0.12 SKYSCAN_LATENCY_COMP=0.06 $T/fly_all.sh _e5 dz_ahead > /dev/null 2>&1
SKYSCAN_SIM_LATENCY=0.12 SKYSCAN_LATENCY_COMP=0.20 $T/fly_all.sh _e6 dz_ahead > /dev/null 2>&1
note "block 2: regression, latency 0.12 s compensated"
export SKYSCAN_SIM_LATENCY=0.12 SKYSCAN_LATENCY_COMP=0.12
$T/fly_all.sh _L dz_side dz_rot dz_far rb_north rb_shift_e rb_shift_w rb_wide_s ret_near ret_south ret_north > /dev/null 2>&1
note "block 3: fault injection"
$T/fly_all.sh _fx fi_no_target fi_no_return > /dev/null 2>&1
note "block 4: GPS/compass noise"
$T/fly_all_noise.sh _nz dz_ahead rb_north ret_south > /dev/null 2>&1
unset SKYSCAN_SIM_LATENCY SKYSCAN_LATENCY_COMP
note "block 5: challenge worlds (offset start, behind, far, fake corridor)"
bash $T/fly_test.sh offset_ch $W/offset.sdf --home -14 -6 --full > /dev/null 2>&1
bash $T/fly_test.sh behind_ch $W/behind.sdf --home -6 3 --full > /dev/null 2>&1
bash $T/fly_test.sh far_ch $W/far.sdf --home -24 -12 --full > /dev/null 2>&1
bash $T/fly_test.sh fake_ch $W/fake.sdf --home -14 3 --full > /dev/null 2>&1
note "ALL DONE"
