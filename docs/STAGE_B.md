# Stage B: green corridor navigation

Runs after Stage A (the vehicle sits ~4 m before the corridor entrance, 5 m up, heading along the corridor axis).
Select B1..B4 in the cockpit (each has its own RUN button) or `python scripts/dev/ws_run.py B1 B2 B3 B4`.

| Stage | What it does | Success criteria (blocking unless noted) |
|---|---|---|
| **B1** Descent to corridor altitude | Descends at <= 0.5 m/s to 3.0 m (10 ft) and holds position | height within +-0.25 m for 2 s, drift <= 0.6 m, GUIDED. Not blocking: height came from a lidar/rangefinder rather than the EKF |
| **B2** Corridor entry | Flies forward until the lidar sees both walls, then 1.5 m past the entrance line, centred | both walls seen, width ~3.5 m (+-0.8), centre offset <= 0.5 m, depth >= 1.2 m, height held. Not blocking: heading along the walls, agreement with A4's camera estimate |
| **B3** Static obstacle traversal | Reactive flight along the corridor: centres between the walls, slides round obstacles, slows or stops when there is no gap | 6 m covered, clearance >= 0.35 m, <= 0.8 m off the centre line, height held, never stuck > 12 s |
| **B4** Corridor exit detection | Keeps going until both walls disappear (the exit), clears it by 1 m and holds | exit detected, measured length ~10 m (+-3.5) when B2 measured the entrance, clearance, height held, stopped |

## Sensors (no simulator data is used to fly or to decide a result)
* **2D lidar** (`skyscan/lidar.py`, `LidarHub`): walls, obstacles, entrance and exit. Sim: the Gazebo `lidar_360`
  (RPLidar A2M12 class) via `GzBridge`; hardware: a driver must `LidarHub.put()` a `LidarScan` (angles CCW from the nose).
* **Height** (`MissionContext.height()`): the downward lidar/rangefinder (MAVLink `DISTANCE_SENSOR` / `RANGEFINDER` from the
  flight controller, tilt-corrected) when it reports, else the EKF. `height.source` in the config forces one. Each report says
  which one it used. A 2D scanning lidar cannot measure height; a single-point downward rangefinder is needed for that.
* Entrance/exit geometry: the 45..135 deg side sectors see a wall half a corridor-width *ahead* of the vehicle on the way
  in and the same distance *behind* on the way out, and both estimates are corrected for it.

## Controller (`skyscan/mission/corridor_ctrl.py`)
Pure function of one scan. For a fan of bearings it measures how far the vehicle's strip (half-width 0.55 m) can travel
before touching a return, picks the bearing with the most room biased towards re-centring, scales speed with the free
distance, strafes sideways only as a recovery when the way ahead is blocked, and holds (BLOCKED) when nothing is free.
Streams `nav` messages (mode, velocity) that the cockpit draws over the lidar view.

## Verified
* Unit/closed-loop tests (`tests/test_corridor_ctrl.py`, `tests/test_stage_b.py`), including the legacy orange corridor's
  three obstacles and a full-width barrier.
* SITL: A1..A4 then B1..B4 all succeed in the canonical world. Measured from the lidar alone: entrance 9.2 m (true 9.0),
  exit 18.9 m (true 19.0), length 9.7 m, closest approach 1.6 m.
* Not covered in SITL: obstacle avoidance (the green corridor in the canonical world has no obstacles; only the orange one does),
  and a downward rangefinder (the sim drone has none, so height comes from the EKF and B1 reports that).
