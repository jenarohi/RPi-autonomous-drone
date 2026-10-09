# Stage C: delivery zone search, QR verification and payload delivery

Source of truth: the AeroTHON 2026 Track 1 rulebook, Mission 2 (copy in `docs/rulebook/`, summary and page numbers in
`docs/RULEBOOK.md`). Runs after Stage B (the vehicle has just left the corridor). Select C1..C4 in the cockpit (each has its own
RUN button) or `python scripts/dev/ws_run.py C1 C2 C3 C4`. Nothing starts by itself.

| Stage | Rulebook | What it does | Success criteria (blocking unless noted) |
|---|---|---|---|
| **C1** Zone entry | C.1 | Climbs to 10 m AGL and flies to the delivery-zone entry coordinates (config `c1.entry`) | inside the zone geo-fence, height 10 +-0.5 m, held for 2 s, heading along the course |
| **C2** Search | C.2 | Boustrophedon sweep of the zone with the down camera, dual-range HSV red masking and the red-zone evasion protocol | search flown, a QR found, never over a red cell, evasions within 5 s, coverage >= 95 % (not blocking when the match stopped the sweep early) |
| **C3** QR verification | C.3 | Visits each candidate nearest first, centres on it and reads it; goes down 8.5 / 7 / 6 m for a closer look if it is not readable from 10 m | the target code read `verify_votes` times, position scatter <= 0.4 m, delivery point clear of every red keep-out, back at 10 m |
| **C4** Descent and release | C.4 | Centres over the target QR, descends 10 -> 5 m keeping it centred, lowers the payload on the winch, releases it on the ground and winds the rope back | 5 +-0.25 m, drop error <= 0.5 m, stable, winch commands ACKed, payload released, rope retracted |

## C.2 search
* **Strips.** The zone (`mission.stage_c.zone`: fwd 22..62 m, right -12..18 m in the course frame) is split into strips along the
  course axis. The camera swath is `2 h tan(hfov/2)` = 11.55 m at 10 m (60 deg hfov). `c2.strip_spacing_m: 5.4` is the team's
  figure for 30 % overlap and is used as the *target* spacing; the strips are then evenly spread so the zone is covered with no
  gap: 6 strips at 5.0 m (centres -9.5 .. 15.5). `null` derives the spacing from the camera instead (8.1 m at 30 %).
* **Red mask.** HSV, two ranges OR-ed because red wraps the hue axis: (0,100,100)-(8,255,255) and (172,100,100)-(180,255,255),
  morphological open/close, blobs >= 600 px, convex hull. Each hull is projected to the ground with the height above ground and the
  vehicle attitude (`vision.red` in the config, `skyscan/vision/redzone.py`).
* **Map.** The zone is a 0.5 m grid (`skyscan/mission/search.py`). A cell turns red after 2 sightings. The keep-out is the red
  area grown by `red.margin_m` (1.5 m edge to edge) and the 1 m inset of the zone fence. Routes are A* with line-of-sight
  smoothing; strips are cut into free runs and the gaps are detoured, so the sweep never crosses a red boundary.
* **Evasion protocol.** When new red cells appear and the way ahead now leads within `red.halt_m` (3 m) of them:
  1. halt forward progress at once (`HOLD`);
  2. reverse `red.reverse_m` (2 m) along the entry vector;
  3. sidestep laterally, to the side that needs the smaller move, until the straight line ahead is clear; the budget for the
     offset is `red.offset_budget_s` (5 s);
  4. re-plan the remaining strips on the updated map and resume the sweep.
  Each evasion is logged with its timings (`halt_s`, `reverse_s`, `offset_s`, `within_budget`) in the stage output.
* **Following.** `PathFollower` steers at a carrot 1.5 m ahead on the route. It stops at sharp corners, advances when the vehicle
  has cut a corner and re-plans when the map changes. A progress watchdog (`nav.stall_s`, 10 s) re-plans and, after 3 tries, ends
  the stage as `stalled` rather than hovering forever.

## C.3 verification
A candidate becomes `match`, `decoy` or `unknown` after `c2.confirm_decodes` readings. The start QR (Stage A) defines the target
(`DELIVERY-C` in the canonical world). C3 flies to each unresolved candidate, nearest first, holds over it and counts
`verify_votes` readings of the target text; if the code cannot be read from 10 m it descends to 8.5, 7 and 6 m in turn.

## C.4 delivery
Descends at <= 0.5 m/s from 10 m to 5 m while steering on the QR's camera offset (pausing the descent if the error is above
`pause_err`), holds for 2 s, then the winch (`skyscan/payload.py`) runs: lower -> settle on the ground -> release -> raise.
* **Winch.** `MAV_CMD_DO_SET_SERVO` on servo 12 (`winch.servo_channel`; SITL already reserves it), PWM 1100 lower, 1500 stop,
  1900 raise, each command ACK-checked. There is no rope-length sensor, so rope paid out = `lower_mps` x time. The rope must be
  hover height + slack long: 5 m + 0.2 m, so `winch.rope_length_m` is 5.5 (the legacy mock's 5.0 m was too short).
* `winch.backend: mock` runs the same state machine without sending any servo command.

## Cockpit
The stage cards for C1..C4 come from the stage list like the others. While a C stage flies, the server streams a `search` message
(about 3 per second) and the 2D course map switches to the delivery zone once the vehicle is at it: the zone fence, the sweep
strips, the red zones the camera has mapped (solid) with their keep-out margin (dashed), the route still to fly, each QR seen
(green = the target, amber = another code, grey = not read yet), the delivery point, and a status line (stage, mode, altitude,
coverage, red zones, evasions). The map returns to the course view when the vehicle is not at the zone. Voice callouts for
C1..C4 and for each evasion use the browser's speech synthesis (there are no recorded clips for them).

## Not in the rulebook (decisions made here)
* **Lidar and sensors.** The rulebook does not mention a lidar or any sensor. Stage B's lidar navigation stays; the Stage C
  search needs only the down camera.
* **Return height.** The rulebook's return-leg altitude reads 10 m in one place and 10 ft in another (see `docs/RULEBOOK.md`).
* **Lowered or dropped.** The rulebook says "lowered with a controlled pulley mechanism" and also "dropped"; the winch lowers it.

## Verified
* Unit tests (`tests/test_search.py`, `tests/test_vision.py`) and closed-loop tests (`tests/test_stage_c.py`, an in-process drone
  with a *rendered* belly camera and the real red detector): the full C1-C4 chain, an unexpected extra red patch, a target that
  needs the closer look, the NO-GO paths. 87 tests pass on the Mac and on the box (box Python, pyzbar).
* **SITL + Gazebo (the canonical world), A1..C4 in one run: every stage succeeds.** Measured: the 10 m search finds the target
  QR `DELIVERY-C` at (41.1, -2.6) in the course frame (true (41, -2)), C3 reads it 8 times with 0.01 m scatter, C4 descends to
  5.01 m, the payload is lowered 5.2 m of rope in 10.5 s, released 0.01 m from the QR centre and the rope wound back in; the
  flight controller accepted all 4 servo commands. Earlier full sweeps (6 strips, 100 % coverage, 350 s) mapped both red zones,
  stayed 1.3-1.7 m clear of them and ran the evasion protocol in 2.8-3.2 s (budget 5 s) with zero red-zone violations.
* **Small QR codes at 10 m.** A 1 m code is ~55 px on the 640 x 480 sim camera (~1.7 px per module), below what zbar reads on the
  whole frame. `QRScanner.scan_tiles` (`vision.qr.tile_*`) scans an empty frame above 6 m in overlapping 240 px tiles enlarged 3x
  with local contrast equalisation, then a plain 2x pass for already-compressed video. Measured on 21 raw sim frames with a code
  2-4 m off the camera axis: 0 of 21 read before, 21 of 21 after, ~140 ms per empty frame. A higher-resolution down camera
  would make this unnecessary.
* **Not verifiable in the simulator:** the payload itself. There is no payload model in the Gazebo world, so the winch is
  checked at the command, ACK and timing level only.
* **Not exercised in the last full run:** the evasion protocol (the sweep found the target before reaching a red zone); it was
  exercised in the earlier SITL sweeps above and in the closed-loop tests.
* **Speed.** ArduPilot caps GUIDED moves at `WPNAV_SPEED` (50 cm/s in `sim/params/skyscan_sitl.parm`). The sweep ran at that cap
  and the evasion budget was met with it, so it was left as it is.

## Debugging aid
`mission.stage_c.c2.debug_frames_dir` (null by default, sim only): a folder to save the raw belly frame whenever the simulator's
truth has a QR code in view, with a log line saying what the live scanner reported for it.
