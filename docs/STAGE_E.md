# Stage E: return corridor, return home, landing

Rulebook Mission 2 phases 6 (return through the orange corridor), 7 (landing at the take-off point) and 8 (mission
time), p.36-37; scored as items 6, 7 and 8 on p.42. Runs after Stage D: D3 leaves the vehicle 10 m before the orange
corridor entrance, 10 m up, nose along the corridor axis (back towards the start). Select E1..E6 in the cockpit or
`python scripts/dev/ws_run.py E1 E2 E3 E4 E5 E6`.

| Stage | What it does | Success criteria (blocking unless noted) |
|---|---|---|
| **E1** Descent to return-corridor altitude | Descends from 10 m to 3.0 m (10 ft) and holds | height within +-0.25 m for 2 s, drift <= 0.6 m, GUIDED. Not blocking: height from a lidar/rangefinder |
| **E2** Return corridor entry | Flies along the D3 axis until the lidar sees both walls, then 1.5 m inside | both walls seen, width ~3.5 m (+-0.8), centre offset <= 1.0 m, depth, height held. Not blocking: heading along the walls, entrance within 1.5 m of the D3 camera estimate |
| **E3** Return obstacle traversal | Reactive lidar flight past the three obstacles | 6.5 m covered, clearance >= 0.35 m, <= 1.3 m off the centre line, height held, never stuck > 15 s |
| **E4** Return corridor exit | Keeps going until both walls disappear, clears the exit by 1 m and holds | exit detected, measured length ~10 m (+-3.5), clearance, height held, stopped |
| **E5** Return to the take-off point | Climbs to 5 m, flies to the start QR, re-reads it for 4 s to measure the EKF drift since take-off, then holds over the corrected take-off point | at 5 m, <= 0.3 m over the take-off point for 2 s, facing the take-off heading. A drift over 3 m is treated as a misread and ignored |
| **E6** Precision landing | Descends to 1 m, hands over to the flight controller's LAND mode, waits for touchdown and disarm | on the ground, disarmed, <= 1.0 m from the take-off point. Not blocking: mission time <= 15 min (900 s from A1's take-off) |

## How it reuses Stage B
E1..E4 are the B1..B4 classes with `lap = RETURN` (`skyscan/mission/stage_b.py`, `Lap`):
* the corridor axis comes from D3 (`return_entry_aligned`), else D2 (`return_corridor`), else the reverse of the course
  heading; progress is measured along that heading (`along_heading`), so "forward" means back towards the start;
* outputs and snapshots are keyed `return_*` (`return_corridor_entry`, `return_traverse`, ...), so the forward-lap
  products stay untouched;
* config lives under `mission.stage_e` (`config/skyscan.yaml`).

Geometry note (E2 centre tolerance): in the return direction obstacle 3 stands on the centre line about 3 m past the
entrance. When E2 stops 1.5 m inside, the avoidance is already sliding round it (to ~0.85 m off centre), so E2 allows
1.0 m where B2 allows 0.5 m.

## Landing and the safety monitor
E6 is the only stage that leaves GUIDED: it sets `ctx.mission["_allowed_modes"] = ["LAND"]` for the hand-over, so the
runner's safety monitor does not treat the LAND mode as a pilot takeover, and removes it again when the stage ends.
Touchdown is the flight controller's landed state (`EXTENDED_SYS_STATE`) plus disarm.

## Mission time
A1 records the take-off time (`ctx.mission["_t_takeoff"]`). E6 reports `mission_time_s` against `MISSION_LIMIT_S = 900`
as a non-blocking criterion: a late landing is still a landing.

## Verified
* Offline: `tests/test_stage_e.py` (8 tests: lap heading/progress, drift correction, QR sightings, E1, E2-E4 through the
  three obstacles, E5 home, E6 landing and the 15-minute report); the whole offline suite passes (135 tests).
* SITL, full mission A1..E6 in one run (2026-10-09): all 21 stages SUCCESS. Return corridor: entrance -18.68 m (true
  -19.0), 3 avoidance manoeuvres, closest approach 0.55 m, measured length 9.58 m. Start QR read 16 times, drift
  0.03 m. Landed 0.04 m from the true take-off point, disarmed; mission time 6 min 29 s.
