# Stage A: Pre-Corridor Operations (A1 to A4)

Team Axiom Dynamics, AeroTHON 2026 Track 1, Mission 2. Stage A is everything before the drone enters the
corridor: take off, climb to scan height, read the start QR code, find the green corridor and line up with it.
The code is `skyscan/mission/stage_a.py`; the numbers below are the defaults in `config/skyscan.yaml`
(`mission.stage_a.*`).

## The course (the original SkyScan world)

The simulator uses the world of the original prototype, kept byte-for-byte in `legacy/aerothon_mission.sdf` and
generated from `sim/course.yaml` by `sim/build_world.py` (a unit test fails if the two ever drift apart).

```
 fwd (course +x, east in Gazebo)  ───────────────────────────────────────────▶
 spawn (-3, 3, 0.195) facing east
   ●──▶  QR (3 m ahead, flat on the ground, 1 m x 1 m)       ┌──────────── green corridor (right 0) ─────────────┐
                                                             │ floor 3.5 m x 10 m, entrance 9 m ahead            │
                                                             └───────────────────────────────────────────────────┘
                                                             ┌──────────── orange corridor (right 6) ────────────┐
                                                             │ with 3 obstacles                                  │
                                                             └───────────────────────────────────────────────────┘
```

* Course frame: origin = where A1 starts, `fwd` = heading at A1 start, `right` = 90 degrees clockwise.
* The "green banner" of this world is the green corridor floor itself (there is no standing banner), so A4
  detects and aligns on that floor.
* QR content in the sim: `DELIVERY-C`. If the QR cannot be decoded A3 fails; nothing is invented.

## How a stage is gated

Every stage has **preconditions**. The UI shows them live as a GO / NO-GO pill on the stage card and lists them in
the card's DETAILS drawer. Nothing starts by itself: a stage only runs when an operator presses its RUN button
or RUN SELECTED. When a stage is started its preconditions are checked first; a failed blocking check
ends it as **NO-GO** without commanding the vehicle. Non-blocking checks (shown with `!`) are warnings.

When several stages are ticked together, a later stage whose preconditions depend on an earlier ticked stage
shows `AFTER A1` instead of NO-GO: those preconditions become true as the earlier stage finishes.

Each stage ends in one of `success`, `failed` (ran, did not meet its criteria or timed out), `nogo`, `aborted`
or `skipped` (an earlier stage in the same run did not succeed). The DETAILS drawer shows the preconditions as
they were at the start of the run, the success criteria with measured value and limit, measurements, products,
the stage log and snapshots. Running one stage alone keeps the results of the others.

## A1 Autonomous Takeoff

| | |
|---|---|
| Preconditions | telemetry link, EKF converged with position valid, pre-arm passing, vehicle disarmed, local NED available |
| Procedure | record the ground origin and heading as the course frame, switch to GUIDED, arm, take off to 2.5 m, settle 2 s |
| Success | altitude within 0.3 m of 2.5 m, horizontal drift at most 0.6 m, still armed in GUIDED |
| Products | `origin` (course frame), `final_alt_m`, `drift_m`, a down-camera snapshot |
| Fails when | cannot enter GUIDED, arming refused (the reason from the autopilot is shown), climb takes longer than 30 s |

## A2 Climb and Positioning

| | |
|---|---|
| Preconditions | course frame from A1, armed and above 1 m, mode GUIDED |
| Procedure | fly to course (fwd 1.0 m, right 0, up 5.0 m) holding the start heading, settle 2 s |
| Success | altitude within 0.25 m of 5 m, position within 0.25 m of 1 m forward, heading within 10 degrees of the course |
| Fails when | the position is not reached in 45 s |

## A3 Start QR Detection and Decoding

| | |
|---|---|
| Preconditions | course frame, altitude within 1 m of 5 m, vision pipeline running |
| Procedure | gimbal straight down, watch the down camera. A decode is accepted after 3 identical reads in a session. If the symbol is seen but not decoded the drone centres over it; otherwise it searches a small pattern around the A2 point (dwell 6 s per point, 90 s overall) |
| Success | QR confirmed, payload parsed into a delivery location |
| Products | `qr` (raw text, target), annotated down-camera snapshot |
| Fails when | no confirmed decode before the timeout |

## A4 Green Corridor Detection and Entry Alignment

| | |
|---|---|
| Preconditions | course frame, armed and GUIDED above 1 m, altitude at least 3 m, front camera streaming. Warnings only: gimbal reports its pitch, corridor already visible, A3 QR decoded earlier |
| Procedure | pitch the front gimbal to -25 degrees (earth-stabilised), look for the green floor. If it is not in view, sweep the heading (0, -20, +20, -40, +40 degrees from the course heading). Confirm it over 3 consecutive frames, then compute the corridor pose from the floor outline projected on the ground plane (camera height and gimbal pitch known): distance to the entrance, centre-line offset, axis heading, width. Fly to the point 4 m before the entrance on the centre line, heading along the axis, at 5 m altitude (no descent in Stage A). Re-measure and refine up to 6 times, then require 2 s of steady alignment |
| Success | corridor confirmed, measured width 3.5 m +/- 0.6, lateral error at most 0.3 m, heading error at most 5 degrees, stand-off 4 m +/- 0.5, alignment held, altitude held within 0.5 m. In the simulator the result is also compared with ground truth |
| Products | `corridor_axis` (heading, entrance position in the course frame), annotated front-camera snapshot |
| Fails when | corridor not found in any heading, alignment target further than 15 m from the start, 150 s timeout |

Vision details: `skyscan/vision/corridor.py`. The measured pose is validated against simulator truth in
`tests/test_corridor.py` (real Gazebo frames) with limits of 0.35 m distance, 0.15 m lateral, 1.5 degrees yaw.

## Running it

* One click: the **SkyScan Mission Control** icon on the box desktop (or `scripts/skyscan.sh`). It starts
  Gazebo (headless), ArduPilot SITL and the server, and opens the cockpit full screen in one Firefox window.
  Close that window (Alt+F4) and everything shuts down.
* From another computer: open `http://barathros.local:8080`.
* In the UI: tick stages and press **RUN SELECTED**, or press **RUN A1 ... A4** on a stage card. While a run is
  active the main button becomes **ABORT RUN**; HOLD, LAND, RTL and DISARM are always available.
* Embedded Gazebo: the **GAZEBO 3D** tab is the live Gazebo scene (orbit, pan, zoom, follow the drone). The
  *Overview cam* switch shows a fixed Gazebo camera instead, which also works without WebGL.

## Tuning

All numbers are in `config/skyscan.yaml` under `mission.stage_a`, `vision`, `cameras` and `sim`. Nothing about the
course is hard-coded in the mission logic; it works in the course frame recorded by A1.

## A5 - Safety Backup (between A4 and B1)

A team safety step, not a rulebook stage. A4 leaves the vehicle hovering about 4 m before the corridor entrance at the 5 m scan
altitude, which is right in front of the entry arch (top flush with the 5 m wall tops). Before B1 descends to the 3 m corridor
altitude, A5 flies **straight back 1 m along the corridor axis** (A4\x27s measured axis heading, so the vehicle keeps facing the corridor),
at the same altitude, then holds 1.5 s.

| criterion | limit |
|---|---|
| Moved straight back | 1.0 m +- 0.25 |
| Sideways drift from the axis line | <= 0.3 m |
| Heading vs the corridor axis | <= 5 deg |
| Altitude change (no descent) | <= 0.4 m |
| Armed, GUIDED | - |
| Truth (sim, non-blocking): entrance distance grew by the backup distance | +- 0.4 m |

Needs A1 (course frame) and A4 (product `corridor_axis`). Config: `mission.stage_a.a5` (`back_m`, tolerances, `hold_s`, `timeout_s`).
Product: `safety_backup`. B1 descends from wherever A5 left the vehicle, so B1 itself is unchanged.
