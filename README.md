# SkyScan — AeroTHON 2026 Mission 2 (autonomous)

Fresh mission code base for the Gazebo Harmonic + ArduPilot SITL simulation of
`aerothon_mission.sdf`. Stack: pymavlink (ArduCopter GUIDED), gz-transport
(down camera + 360° LiDAR), OpenCV + pyzbar. One plain Python process, no ROS.

## Run

Start Gazebo and SITL the way you already do, then:

```bash
cd ~/skyscan
python3 run_mission.py --check          # link + both cameras + LiDAR, does not arm
python3 run_mission.py --view           # phase 1: QR -> green banner -> corridor, then RTL
python3 run_mission.py --full --view    # whole mission (phase 2 still partly survey-based)
python3 run_mission.py --stop-after FIND_BANNER    # stop earlier, then RTL
```

Default link `tcp:127.0.0.1:5762` (SITL SERIAL1, MAVProxy keeps 5760); change with `--url`.
Each run writes `logs/<timestamp>/` with `events.log`, `telemetry.csv` (5 Hz) and
`snapshots/` (start QR, front-camera banner view, alignment, ...).

Offline tests (no simulator): `python3 -m pytest -q`.

## Sensors on the model

`iris_with_standoffs/model.sdf` carries
- `down_camera`: straight down, Raspberry Pi Camera 3 Wide geometry: 102°, 2304x1296
  (QR codes on the full frame; entrance edge and red zones on a 640 px copy). Changed
  2026-10-04; the previous model is saved as `model.sdf.before_picam3wide`.
- `front_camera`: fixed, tilted 45° down, 80°, 640x480 (green banner/corridor
  direction). Added 2026-10-04; the previous model is saved as `model.sdf.before_front_cam`.
- `lidar_360`: 360 samples, 12 m (corridor centring / obstacles)

## Phase 1 - perception driven (no course coordinates)

| Stage | What happens |
|---|---|
| TAKEOFF | GUIDED, arm, climb to 5 m (flight timer starts) |
| SCAN_START_QR | at 5 m: move ~1 m forward, keep creeping forward, then a ring, then wider rings, all relative to the take-off spot, until `TARGET:<id>` is decoded twice. The front camera already feeds the green map meanwhile |
| FIND_BANNER | at 5 m: **search -> decide -> approach loop** (below) |
| ALIGN_FORWARD | down camera, 5 m, hovering outside with the entrance edge 0.7 m ahead (creeps forward until it sees it): lateral + yaw within 0.15 m / 3° |
| CORRIDOR_FORWARD | descend to 3 m, fly on LiDAR: centre between walls (and around obstacles), heading corrected from the wall lines, INSIDE when walls appear on both sides, EXIT when they disappear |

FIND_BANNER (`groundmap.py`): every front-camera frame is projected onto the ground
and voted into a 0.2 m green map in world coordinates, so partial views add up.
- **Down camera first**: if it already shows the corridor floor and its entrance edge,
  there's no search.
- **Search** at 5 m, escalating until something is found: spin 360° in 45° steps → fly
  to search points on 10 m / 20 m rings and spin at each. A green blob that is only
  partly seen gets investigated from closer. A LiDAR return within 1.5 m ahead stops a leg.
- **Decide**: a candidate is a strip about 3.5 m wide (±35 %), at least 4.5 m long and
  mostly filled. Grass, mats and odd shapes are rejected and logged. The end nearer
  the start QR is the entrance.
- **Approach**: heading locked on the entrance, fly in 4 m legs at 5 m, re-looking after each leg. If
  the candidate stops looking right twice, go back to searching from there.
- **Handover**: once the down camera sees the corridor floor (right width) within 5 m
  of the entrance, ALIGN takes over.

**Loops instead of giving up.** If ALIGN or CORRIDOR still fails after its retry, the
drone goes back to FIND_BANNER (at most 3 times). Before that it climbs straight up:
to 5 m normally, or to 7 m if the LiDAR shows it is between the walls, so it can get
out over them. That's the only time it goes above 5 m before the corridor. If the LiDAR found no walls, that green strip is rejected first so it isn't
tried again.

Challenge worlds: `python3 worlds/make_worlds.py` writes `worlds/{offset,behind,far,fake}.sdf`
(description in the file). Start Gazebo with one of them and pass the spawn point,
e.g. `python3 run_mission.py --view --home -14 -6`. `--home` only labels the logs.

In this world the "green banner" is the green corridor floor (same colour as the
rulebook banner). At the event the banner is vertical at the entrance; the same front
camera sees it, but the measurement will need a banner-shaped detector.

## Delivery-zone search (stop-and-snap)

From 10 m one Pi Cam 3 Wide picture covers about 25 x 14 m, so the 40 x 30 m zone
needs only **6 stops** (`geometry.snap_grid` picks the heading that needs the fewest).
- Zig-zag from the corner nearest the corridor. At each stop: hold still and level,
  read 2 full frames (a QR is confirmed in one stop). QRs are also read while moving.
- Stops as soon as the target is confirmed (in the sim, usually before the first stop).
- Squares that look like a QR but did not read are looked at again from straight
  above (10 m, then 7 m).
- Red zones: red pixels are voted into a map, only from steady, near-straight-down
  views. A cell is red after 3 frames, so zones don't grow from bad views. Every leg is
  planned around the zones plus 1.5 m.
- Deliver: centre on the QR at 10 m, descend to 5 m, centre again, lower, release.

Test worlds have 7 QR codes (A-G, target C) and 3 red zones.

## Phase 2 (`--full`)

SEARCH, DELIVER, TO_RETURN_CORRIDOR, ALIGN/CORRIDOR_RETURN, HOME_LAND as before. The
search uses the delivery-zone geofence (given by the organisers); the return corridor
is still a surveyed axis in `config.py` and will be converted next.

Failures: each stage is retried once, then (phase 1) the go-back loop above, then RTL
(climbs to 15 m, above the 5 m walls).
A pilot mode change hands control back immediately; 14 min of flight time aborts.

## How the key parts work

- **Corridor (`lidar.py`)**: every LiDAR point in a look-ahead band blocks a lateral
  interval (drone radius 0.4 m + margin 0.2 m). The free interval beside the drone is
  narrowed by the bands further ahead, and the drone steers to its middle. Forward
  speed drops to zero when anything is within 0.9 m of the drone's path. Walls and
  obstacles are handled the same way, so this one routine centres the drone in the
  green corridor and slaloms through the orange one. `tests/sim2d.py` checks it on a
  2-D model of the SDF geometry. A straight-line fit to each side wall corrects the
  locked heading, and walls appearing / disappearing on both sides mark entry / exit.
- **Banner / corridor direction (`vision.floor_ground_points`)**: each image row of the
  green floor is projected to the ground using the camera tilt and the vehicle's
  roll/pitch. Rows whose projected width isn't about 3.5 m (cut off by a wall) are
  dropped. A line fit gives the corridor direction, and the near end gives the entrance.
- **Alignment (`vision.floor_axis`)**: fits a line through the mid-points of the coloured
  floor strip. The column gives the lateral offset and the slope gives the yaw error.
- **Search / red zones (`geometry.py`)**: red patches are projected to the ground using
  altitude, roll, pitch and heading. They're stored as rectangles and inflated by 1.5 m.
  Every leg is planned with a visibility graph around them, and a leg is re-planned
  when a new zone shows up.
- **Small QR codes**: a 1 m QR at 10 m is only about 2 px per module on the 640×480 sim
  camera. Candidates are cropped, upscaled 4×, sharpened and adaptively thresholded
  before decoding.

## Course and tuning

Everything lives in `skyscan/config.py`: the course layout (from `create_world.py`),
altitudes, speeds, HSV colours, corridor/LiDAR gains, timeouts. The world frame is the
SDF frame (x east, y north). ArduPilot's LOCAL_NED origin is the Gazebo origin, so the
take-off point is captured on the ground and mapped to `HOME_XY`.

For the real field:

- Re-survey the course into `config.py`.
- Swap `sensors.py` for a USB camera + RPLidar class with the same `frame()` / `scan()` methods.
- Set `PAYLOAD_SERVO` (channel, PWM) for the release servo.
- Program the organisers' geofence into the GCS (rulebook). `GEOFENCE` in the config
  is only a software guard.

## Files

```
run_mission.py        CLI entry point
skyscan/config.py     all parameters + course layout
skyscan/mission.py    state machine (stages, retries, abort/RTL)
skyscan/vehicle.py    pymavlink wrapper, WORLD <-> LOCAL_NED
skyscan/sensors.py    gz-transport cameras + LiDAR (topic auto-discovery)
skyscan/vision.py     camera model (any tilt), QR decode, floor fits, red regions
skyscan/lidar.py      corridor gap planner, wall angle, wall presence
skyscan/geometry.py   corridor axis, rectangles, detour planner, lawnmower
skyscan/groundmap.py  green ground map + corridor candidates (FIND_BANNER)
worlds/make_worlds.py challenge worlds (offset / behind / far / fake)
skyscan/missionlog.py run logs
tests/                offline unit tests + 2-D corridor simulator
```
