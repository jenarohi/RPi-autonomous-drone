# SkyScan Mission Control — Architecture (Stage A baseline)

SkyScan is the ground/companion software for AeroTHON 2026 Track 1, Mission 2 ("SkyScan:
Autonomous Rapid Delivery"). This baseline implements **Stage A — Pre-Corridor Operations**
(A1–A4) and the mission-control UI that later stages (corridor, delivery, return) plug into.

Everything runs as **one Python process** on the robotics box (`python -m skyscan`), serving a
single-page web UI at `http://<box>:8080`. The UI is the only window: Gazebo runs headless and is
shown inside the UI (3D scene + Gazebo-rendered cameras). No MAVProxy, no extra windows.

```
 Browser (Firefox kiosk on the box, or any LAN browser)
   │  WebSocket /ws (JSON)   ·  MJPEG /video/<cam>.mjpg  ·  gzweb ws://<box>:9090 (3D scene)
 ┌─┴──────────────────────────────── skyscan (python -m skyscan) ───────────────────────────────┐
 │ server/app.py  aiohttp: static UI, /ws hub, MJPEG, REST            (asyncio main thread)     │
 │ bus.py         EventBus: thread-safe publish → asyncio fan-out + latest-state cache          │
 │ sim/procman.py ProcessManager: gz sim server, SITL, gz websocket server, optional gz GUI     │
 │ gz/bridge.py   gz-transport: camera frames → FrameHub, model pose (truth), world stats      │
 │ fc/link.py     MavLink: one reader thread, VehicleState cache, commands with ACK            │
 │ vision/*       VisionPipeline: QR (down cam) + green banner (front cam) worker threads      │
 │ mission/*      MissionRunner thread: runs selected stages A1..A4, NO-GO gating, reports     │
 │ recorder.py    runs/<run_id>/: events.jsonl, telemetry.csv, stage reports, snapshots       │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
   │ MAVLink2 tcp:127.0.0.1:5760 (SITL SERIAL0)      │ gz-transport (same host)
 ArduCopter SITL (--model JSON)  ◀── UDP 9002 ──▶  gz sim -s --headless-rendering (world + iris)
```

## 1. Repository layout and ownership

```
config/skyscan.yaml          all tunables (one file; see §8)                     [foundation]
skyscan/__init__.py          version, REPO_ROOT                                  [foundation]
skyscan/types.py             shared dataclasses (the data contract, §4)          [foundation]
skyscan/bus.py               EventBus (§5)                                       [foundation]
skyscan/config.py            YAML → attribute config                             [foundation]
skyscan/geo.py               frames, angles, CameraModel (§3)                    [foundation]
skyscan/fc/link.py           MavLink (§6.1)                                      [flight]
skyscan/mission/context.py   MissionContext (§6.4)                               [flight]
skyscan/mission/stage.py     Stage base + helpers                                [flight]
skyscan/mission/stage_a.py   A1..A4 (§7)                                         [flight]
skyscan/mission/runner.py    MissionRunner (§6.5)                                [flight]
skyscan/vision/qr.py         QRScanner + parse_qr_payload (§6.3)                 [vision]
skyscan/vision/corridor.py   CorridorDetector: the green corridor floor (A4)     [vision]
skyscan/vision/banner.py     BannerDetector (+ PnP) for a standing banner; used when
                             vision.banner.mode is not "floor"                   [vision]
skyscan/vision/pipeline.py   VisionPipeline (threads, bus publishing)            [vision]
skyscan/gz/frames.py         FrameHub                                            [foundation]
skyscan/gz/bridge.py         GzBridge (cameras, pose, stats)                     [sim]
skyscan/sim/textures.py      procedural banner / QR images for the standing-banner detector
                             tests (the default world uses sim/worlds/textures)  [foundation]
skyscan/sim/procman.py       ProcessManager (§6.6)                               [sim]
skyscan/sim/course.py        Course model loaded from sim/course.yaml            [sim]
skyscan/sim/truth.py         sim ground-truth metrics for the UI                 [sim]
sim/course.yaml              course layout (sim world + UI map)                  [sim]
sim/build_world.py           generates sim/worlds/aerothon_mission.sdf (the legacy world)
                             from course.yaml; a test keeps it equal to legacy/  [sim]
sim/websocket.gzlaunch       gz-launch config for the embedded 3D view (port 9090) [sim]
sim/models/...               vendored drone + course models                      [sim]
sim/params/*.parm            SITL parameters                                     [sim]
skyscan/server/app.py        aiohttp server, WS hub, MJPEG (Services injection)  [foundation]
skyscan/server/static/...    the mission-control UI (index.html, app.js, style.css)  [frontend]
skyscan/server/static/gazebo3d.js   the GAZEBO 3D tab (gzweb + overview camera)  [frontend]
skyscan/server/static/vendor/gzweb  vendored gzweb 3.0.2 + shim (see its README)  [frontend]
skyscan/server/static/brand/        Axiom Dynamics logo + favicon                  [frontend]
skyscan/recorder.py          run recording                                       [integration]
skyscan/__main__.py          wiring + CLI                                        [integration]
scripts/skyscan.sh           one-click launcher (server + sim + one Firefox window) [integration]
scripts/dev/box.sh           dev: sync tree to a box sandbox + run a command     [foundation]
scripts/dev/ui_shot.py       dev: headless-Chrome screenshots of the UI tabs     [frontend]
scripts/dev/ui_run_stages.py dev: press the RUN buttons like an operator, report [frontend]
scripts/dev/{sim_probe,fly_capture,try_corridor}.py  dev: sim bring-up, fixtures [sim]
tests/...                    pytest; `-m sitl` / `-m gz` mark tests that need the box sim
legacy/                      the old 12-state prototype, untouched, never imported
```

Rules for every module:
- Python 3.12, standard library + numpy, opencv (cv2 5.x on the box), pyzbar, pymavlink 2.4.49,
  gz.transport13 / gz.msgs10 (box only), aiohttp, pyyaml, psutil. Nothing else without asking.
- `import skyscan.<x>` must work on a machine **without** gz-transport (import gz lazily inside
  functions/classes in `skyscan/gz/*`), so unit tests run anywhere.
- No `print()` for operational messages: publish via the bus (`bus.event(...)`) so the UI shows it.
  `logging` may be used for developer debug.
- Never block the asyncio thread (no `time.sleep`, no blocking I/O in coroutines).
- No hardcoded course coordinates in mission logic. Mission logic works in the **course frame**
  anchored at A1 (§3) and only uses tunable *priors* from config.
- JSON going to the UI must contain no NaN/Infinity — use `skyscan.bus.jsonable()`.

## 2. Process / thread model

| thread | owner | does |
|---|---|---|
| asyncio main | server | HTTP/WS, MJPEG, ProcessManager (asyncio subprocess), telemetry broadcast at 10 Hz |
| `mav-rx` | MavLink | only thread that reads MAVLink; updates VehicleState; resolves ACK waiters |
| `mav-hb` | MavLink | sends GCS HEARTBEAT at 1 Hz |
| gz-transport internal | GzBridge | callbacks → FrameHub.put() (copy bytes, no heavy work) |
| `vision-down`, `vision-front` | VisionPipeline | latest-frame-wins detection workers |
| `mission` | MissionRunner | runs stages (blocking style, abort-aware) |

Cross-thread communication: `EventBus.publish()` (thread-safe) for anything the UI shows;
`VehicleState` snapshots via `MavLink.state()` (copy under a lock); detections via
`VisionPipeline` getters (copies under a lock).

## 3. Frames and units

- **NED local** — ArduPilot `LOCAL_POSITION_NED` (x north, y east, z down, metres). Its origin is the
  **EKF origin, which is NOT the takeoff point** (in SITL+Gazebo it is the Gazebo world origin).
  Never assume `(0,0,0)` is home.
- **Course frame** (mission frame) — origin = vehicle NED position at the start of A1, `fwd` along the
  vehicle heading at A1 start, `right` 90° clockwise from fwd, `up` = −(d − d0). A2's "move forward
  1 m" is +1 m `fwd`. `skyscan.geo.CourseFrame` converts both ways. Stored in the mission state as
  `origin` by A1; later stages fail NO-GO if it is missing.
- **Heading** — degrees 0..360 clockwise from north (`VehicleState.yaw_deg`). Yaw rates °/s.
- **Gazebo world** — ENU (x east, y north, z up). Observed mapping to NED: `n = y, e = x, d = −z`
  (`geo.gz_to_ned`). Gazebo yaw (CCW from +x) → heading: `heading = 90° − yaw` (`geo.gz_yaw_to_heading_deg`).
  The sim world is the original SkyScan world (`legacy/aerothon_mission.sdf`): the drone spawns at gz
  (−3, 3, 0.195) facing +x (east), so course fwd = +x and right = −y from there. The EKF origin stays at the
  gz origin, which is why the start NED is about (3, −3, −0.19), not zero.
- **Images** — OpenCV pixel coords (u right, v down), origin top-left. For both onboard cameras
  **image top = vehicle forward**, image right = vehicle right (verified in sim).
  `geo.CameraModel.from_hfov(w, h, hfov_deg)` gives pinhole intrinsics (square pixels).
- Angles in public data structures are **degrees**; internal math may use radians.

## 4. Data contract (`skyscan/types.py`)

All public data crossing module boundaries uses these dataclasses (`.to_dict()` for JSON).
Field names are part of the WS protocol — do not rename without updating §9 and the UI.

- `VehicleState` — link/armed/mode/landed_state, attitude (deg), `ned`, `vel_ned`, lat/lon/alt,
  `rel_alt_m`, gps, `ekf_flags`/`ekf_ok`, `prearm_ok`, battery, `home`, `home_ned`, gimbal angles.
- `Frame` — `cam, seq, t, img (BGR ndarray), sim_t`.
- `QRDetection`, `QRStatus`, `QRPayload` — per-frame QR result, per-session vote state, parsed payload.
- `BannerDetection` — quad corners, score, bearing/elevation, PnP `distance_m`, `lateral_m`,
  `yaw_err_deg`, `plane_ok`.
- `Check`, `StageState`, `StageReport` — stage gating and results.
- `ProcStatus` — one supervised process.
- `Truth` — sim ground-truth pose.
- `Sev` — event severity: debug, info, good, warn, error, critical.

## 5. EventBus (`skyscan/bus.py`)

```python
bus = EventBus()
bus.attach_loop(asyncio.get_running_loop())     # server does this once
bus.publish(kind: str, payload: dict) -> msg    # any thread; kind = WS message type ("t")
bus.event(src: str, msg: str, sev: Sev|str = Sev.INFO, **data)   # kind "event"
bus.log_lines(src: str, lines: list[str])       # kind "log" (process output)
sub = bus.subscribe()      # loop thread: Subscription; batch = await sub.next_batch(); bus.unsubscribe(sub)
bus.add_listener(fn)       # sync callback(msg) on the publishing thread (recorder); must be fast
bus.latest(kind, key=None) # newest cached message of a state kind
bus.snapshot() -> {"seq", "latest": [msg], "events": [msg], "logs": {src: [line]}}
```
Every message is `{"t": kind, "ts": epoch_s, "seq": n, ...payload}` (payload keys `t/ts/seq` are reserved).
`seq` is global and strictly increasing; a client that got a snapshot with `seq == S` ignores live
messages with `seq <= S`. Latest-state cache key: `kind`, or `kind:key` when the payload has `"key"`
(vision per camera, stage per id). Per subscriber, `telem/vision/proc/truth` coalesce (only the newest
per key is delivered); other kinds queue in order (bounded; overflow drops the oldest and the server
then sends a `resync` snapshot). Payloads go through `jsonable()` (dataclasses, enums, numpy, NaN → null).
Publishers that update often (e.g. stage progress) should throttle themselves to ≤ 5 Hz.

Sources (`src`) used in events: `SYS, FC, VISION, MISSION, SIM, GZ, SITL, UI`.

## 6. Module contracts

### 6.1 `skyscan.fc.link.MavLink` (flight)
```python
link = MavLink(cfg.mavlink, bus)
link.start()            # starts mav-rx + mav-hb threads; connects/reconnects forever in background
link.stop()
link.connected -> bool  # heartbeat seen within cfg.mavlink.link_timeout_s
link.state() -> VehicleState          # copy
link.wait(pred: Callable[[VehicleState], bool], timeout: float, abort: threading.Event|None=None) -> bool
link.command_long(cmd: int, *params, timeout=3.0, retries=1) -> int | None   # MAV_RESULT or None (no ACK)
link.set_mode(name: str, timeout=5.0) -> bool        # confirmed via HEARTBEAT custom_mode
link.arm(timeout=8.0) -> tuple[bool, str]            # (ok, reason incl. latest "PreArm:"/"Arm:" text)
link.disarm(force=False, timeout=5.0) -> bool
link.takeoff(alt_m: float) -> int | None             # MAV_CMD_NAV_TAKEOFF result
link.goto_ned(n, e, d, yaw_deg: float|None=None)     # SET_POSITION_TARGET_LOCAL_NED position (+abs yaw)
link.velocity_body(vx, vy, vz, yaw_rate_dps: float|None=None)   # MAV_FRAME_BODY_OFFSET_NED
link.velocity_ned(vn, ve, vd, yaw_deg: float|None=None)
link.hold(force_guided: bool = False) -> bool   # stop & hover here: GUIDED position target = current
                          # position + yaw. If not in GUIDED: does nothing and returns False, unless
                          # force_guided (operator HOLD button) — then switches to GUIDED first.
link.set_gimbal(pitch_deg: float, yaw_deg: float = 0.0) -> bool  # DO_GIMBAL_MANAGER_PITCHYAW, fallback DO_MOUNT_CONTROL
link.land() -> bool; link.rtl() -> bool              # mode change, confirmed
link.recent_texts(n=20) -> list[tuple[float, int, str]]  # (time, severity, text)
```
- **Never fight the operator**: nothing in the link changes the flight mode on its own; only explicit
  calls do. `VehicleState.gimbal_pitch_deg` = measured gimbal pitch when the vehicle reports it, else
  the last commanded pitch (so vision can level the gimbal camera).
- MAVLink2 (`os.environ["MAVLINK20"]="1"` before importing pymavlink), `source_system=245`.
- Request streams with `MAV_CMD_SET_MESSAGE_INTERVAL` per `cfg.mavlink.stream_rates_hz` after
  every (re)connect. Send GCS heartbeat at 1 Hz.
- All sends under one write lock. Only `mav-rx` reads.
- STATUSTEXT → `bus.event("FC", text, sev)` (map MAV_SEVERITY). Mode/arm changes → events.
- `ekf_ok` = flags ⊇ {ATTITUDE, VELOCITY_HORIZ, POS_HORIZ_REL, POS_HORIZ_ABS, POS_VERT_ABS} and not
  CONST_POS_MODE. `prearm_ok` from `SYS_STATUS` `MAV_SYS_STATUS_PREARM_CHECK` bit (None if not present).
- Verified in SITL on this box: GUIDED NAV_TAKEOFF; `SET_POSITION_TARGET_LOCAL_NED` with
  `MAV_FRAME_LOCAL_NED` position+yaw (mask `0b0000100111111000`) and `MAV_FRAME_BODY_OFFSET_NED`
  velocity+yaw_rate (mask `0b0000010111000111`); `DO_GIMBAL_MANAGER_PITCHYAW` and
  `DO_MOUNT_CONTROL` both move the gimbal; EKF uses GPS ~15–45 s after SITL boot; arming with full
  checks works once `PRX1_TYPE 0`.

### 6.2 `skyscan.gz.frames.FrameHub` and `skyscan.gz.bridge.GzBridge` (sim)
```python
hub = FrameHub()
hub.put(frame: Frame)                       # called from gz callbacks (or any camera source)
hub.latest(cam: str) -> Frame | None
hub.add_listener(cam: str, fn: Callable[[Frame], None])   # called on the putting thread; keep fast
hub.stats(cam) -> {"fps": float, "age_s": float|None, "w": int, "h": int, "seq": int}

gz = GzBridge(cfg, bus, hub)                # cfg = full config
gz.start(); gz.stop()                       # (re)subscribes camera topics, pose, stats; tolerant of sim restarts
gz.truth() -> Truth | None                  # pose of cfg.sim.model_name from /world/<w>/dynamic_pose/info
gz.world_stats() -> {"rtf": float|None, "sim_time": float|None, "paused": bool|None, "age_s": float|None}
```

### 6.3 Vision (vision)
```python
vp = VisionPipeline(cfg, bus, hub, state_fn=link.state)   # state_fn: () -> VehicleState | None
vp.start(); vp.stop()                                     # (height, attitude, heading, gimbal pitch)
vp.annotate(cam, img) -> img                 # draws the latest detections (for report snapshots)
vp.qr_reset() -> int                         # new scan session id; clears votes
vp.qr_status() -> QRStatus                   # votes/confirmed text for the current session
vp.qr_latest() -> QRDetection | None
vp.banner_latest() -> BannerDetection | None
vp.banner_track(n: int) -> list[BannerDetection]   # last n detections (found or not), newest last
vp.camera_model(cam) -> CameraModel
parse_qr_payload(text: str) -> QRPayload     # in skyscan.vision.qr
```
- QR on the `down` camera (ground QR from 5 m). Decoders: pyzbar first, cv2 fallback; try 2× upscale
  when small. Confirmation: `cfg.vision.qr.confirm_votes` identical decodes in the session.
- Green corridor on the `front` (gimbal) camera (`vision.banner.mode: floor`, the SkyScan world, where the
  "green banner" is the corridor floor): green region → outline projected onto the ground plane using the
  camera height and the gimbal pitch → corridor distance, centre-line offset, axis heading and width
  (`CorridorDetector`). Reported as a `BannerDetection` with `kind="floor"`, so the UI and A4 use one type.
  Other modes keep the standing-banner detector (green quad + aspect + white-text ratio + PnP).
- Publishes `vision` messages (≤ 10 Hz per camera) — see §9.

### 6.4 `skyscan.mission.context.MissionContext` (flight)
What a stage gets:
```python
ctx.link, ctx.vision, ctx.cfg (stage config section), ctx.full_cfg, ctx.bus
ctx.state() -> VehicleState
ctx.course -> CourseFrame | None        # set by A1 (ctx.set_course)
ctx.mission -> dict                     # shared outputs across stages: "origin", "qr", "corridor_axis" ...
ctx.sleep(s)                            # abort-aware; raises Aborted
ctx.check_abort()                       # raises Aborted if abort requested
ctx.wait(pred, timeout, desc) -> bool   # abort-aware wrapper of link.wait
ctx.emit(msg, sev="info", **data)       # bus event with src=MISSION and stage id
ctx.phase(name, progress=None)          # updates StageReport.phase/progress and publishes it
ctx.metric(key, value) ; ctx.output(key, value)
ctx.snapshot(cam, name, overlay: Callable|None=None) -> str|None   # saves annotated JPEG into the run dir
ctx.truth() -> dict | None              # sim ground truth metrics (None on real hardware)
```

### 6.5 `skyscan.mission.runner.MissionRunner` (flight)
```python
runner = MissionRunner(cfg, bus, link, vision, recorder=None, truth_fn=None)
runner.stages -> list[Stage]                         # [A1, A2, A3, A4]
runner.run(stage_ids: list[str]) -> tuple[bool, str] # validates, starts the mission thread, returns at once; rejects if busy
runner.abort(reason="operator", hold=True, wait_s=2.0) -> bool  # True once the mission thread has stopped commanding
runner.busy -> bool
runner.reset()                                       # clears mission state (origin, outputs) + reports
runner.preview() -> {stage_id: [Check]}              # instant GO / NO-GO of every stage; evaluates only
runner.describe() -> list[dict]                      # stage definitions for the UI (see below)
```
- Stages run in canonical order (A1 < A2 < A3 < A4) regardless of click order. A run of some stages keeps
  the reports of the others, so running A3 alone does not wipe what A1 and A2 produced.
- `preview()` calls each stage's `preview()` (default: its `preconditions()`; A1 overrides it to skip the
  wait for the vehicle). The server publishes the result as `precond` while no run is active. Nothing is
  ever started from a preview.
- Before each stage: `preconditions()`; any failed **blocking** check → stage `NOGO`, run stops,
  remaining selected stages `SKIPPED`. Non-blocking failures are warnings. Readiness checks that can
  become true by waiting (EKF converging after sim start) may wait up to their timeout while the stage
  shows `checking` with live check results.
- Stage exception/timeout → `FAILED`, run stops, vehicle commanded to `hold()` if airborne.
- Abort → current stage `ABORTED`; `hold()` only when `hold=True`. `abort()` returns only after the
  mission thread can no longer send commands (or `wait_s` passes) — the server relies on this before
  sending LAND/RTL so a late stage command can never override them.
- Safety monitor while a run is active: link lost > `mavlink.link_timeout_s`, mode changed away from
  GUIDED by anyone else (RC/another GCS), disarm in flight, altitude > `safety.max_alt_m`, distance from
  the course origin > `safety.geofence_radius_m` → abort the run with the reason (geofence/altitude
  → hold; mode change → do NOT command anything, the operator took over).
- Publishes `stage` (each change; progress-only updates throttled to ≤ 5 Hz), `run` (lifecycle) and
  `mission` (shared mission state).
- `describe()` → `[{id, title, rulebook, summary, preconditions: [str], criteria: [str], config: {...}}]`.

### 6.6 `skyscan.sim.procman.ProcessManager` (sim)
```python
pm = ProcessManager(cfg, bus)                  # asyncio-based; create inside the loop
await pm.start_sim() ; await pm.stop_sim() ; await pm.restart_sim()
await pm.open_gz_gui() ; await pm.close_gz_gui()
pm.status() -> {"sim": "down|starting|up|stopping|error", "procs": [ProcStatus...], "detail": str}
```
- Starts, in order: `gz sim -s -r --headless-rendering <world>` (env: our `sim/models` first in BOTH
  `GZ_SIM_RESOURCE_PATH` and `SDF_PATH` — `SDF_PATH` wins for `model://` includes), waits for the
  ArduPilot plugin's UDP 9002; then `arducopter --model JSON ... --defaults <parm files> -I0 -w` with
  cwd `.runtime/sitl` (SITL **exits when its parent dies**, so it must stay our child); waits for TCP 5760;
  then `gz launch sim/websocket.gzlaunch` (gzweb 3D, port `cfg.sim.websocket.port`).
- Each process in its own process group; stop = SIGINT → SIGTERM → SIGKILL on the group.
- Streams stdout/stderr lines to `bus.log_lines("gazebo"|"sitl"|"gz_ws"|"gz_gui", ...)` (batched,
  filtered of the per-frame "JSON received" spam).
- On startup detect stale processes holding UDP 9002 / TCP 5760 (e.g. an old tmux session) and stop
  them if they are ours (pid files in `.runtime/`), else report them clearly.
- Publishes `proc` at 1 Hz.

### 6.7 Embedded Gazebo (the GAZEBO 3D tab)

- `gz launch sim/websocket.gzlaunch` (started by the ProcessManager) is a websocket server (port 9090) that
  publishes the scene at 30 Hz. The page loads gzweb (vendored, `static/vendor/gzweb`) only the first time the
  tab is opened with the sim up, and connects to `ws://<host>:9090`.
- gzweb's protocol bundle lacks two top-level enums the server sends (`PixelFormatType`,
  `SphericalCoordinatesType`); `vendor/gzweb/globals.js` adds them (see the README next to it).
- *Overview cam* is the fixed Gazebo camera (`overview_cam`) streamed as MJPEG: it needs no WebGL and is the
  automatic fallback when the 3D link fails.
- A private `GZ_PARTITION` (`sim.gz_partition`) keeps other Gazebo windows on the box from joining this world.

## 7. Stage A definitions (rulebook §4.2.4, p.35–37)

| id | title | rulebook | end state |
|---|---|---|---|
| A1 | Autonomous Takeoff | "take off autonomously from the designated ground start point" | armed, GUIDED, stable hover at `a1.takeoff_alt_m` above the start point; course frame recorded |
| A2 | Climb & Positioning | "ascend to 5-meter altitude, move forward approximately 1-meter" | hover at 5.0 m, +1.0 m fwd of start, heading = start heading |
| A3 | Start QR Detection & Decoding | "scan the start QR code from a 5-meter altitude and decode the delivery location information" | QR confirmed (N identical decodes), payload parsed; `mission.qr` set |
| A4 | Green Corridor Detection & Entry Alignment | "identify the AeroTHON 2026 Green Banner marking the entrance … and align itself before descending" (in the SkyScan world: the green corridor floor) | hovering 4 m before the corridor entrance, on the centre line, heading along the axis, still at 5 m; `mission.corridor_axis` set |

Detailed preconditions / procedure / success criteria / failure modes: `docs/STAGE_A.md` (flight).
No silent fallbacks: if the QR is not decoded, A3 FAILS (the old code invented "DELIVERY-C").

## 8. Configuration (`config/skyscan.yaml`)

Single YAML, loaded by `skyscan.config.load_config(path=None)` → attribute access
(`cfg.mission.stage_a.a2.target_alt_m`). Paths are relative to the repo root. `{world}`/`{model}`
placeholders in camera topics are substituted. See the file for every key; it is the source of truth.

## 9. WebSocket protocol (`/ws`, JSON text frames)

Server → client (`t` = type; every message also has `ts` and, except hello/resync/ack, `seq`):

| t | payload | rate |
|---|---|---|
| `hello` | `{server:{version, profile, host, pid, started_at}, config:{ui, cameras:{cam:{hfov_deg, mount, w, h}}, gzweb:{enabled, port}, mission, safety, telem_hz}, course: Course.to_dict()|null, stages: runner.describe(), snapshot: bus.snapshot()}` | first message on connect |
| `resync` | `{snapshot}` — the client fell behind; replace state from this snapshot | rare |
| `telem` | `{v: VehicleState}` | 10 Hz |
| `event` | `{src, sev, msg, data}` | as they happen |
| `log` | `{src, lines:[str]}` | batched ≤ 4 Hz |
| `stage` | `{key: stage_id, report: StageReport}` (checks, criteria, metrics, outputs, log, snapshots) | on change |
| `precond` | `{key: stage_id, go: bool, checks: [Check]}` live GO / NO-GO; only while no run is active; sent on change and every 5 s | ≤ 1 Hz per stage |
| `run` | `{state: "idle|running|done|failed|aborted|nogo", run_id, stages:[ids], current: id|null, started_at, ended_at, message}` | on change |
| `mission` | `{origin: {ned:[n,e,d], heading_deg, lat, lon}|null, outputs:{...}}` | on change |
| `vision` | `{key: cam, cam, seq, w, h, fps, qr: QRDetection|null, qr_status: QRStatus|null, banner: BannerDetection|null}` | ≤ 10 Hz per cam |
| `proc` | `{sim: state, detail, rtf, sim_time, paused, procs:[ProcStatus], cams:{cam: FrameHub.stats}, host:{cpu_pct, mem_pct, load}}` | 1 Hz |
| `truth` | `{pos_gz:[x,y,z], ned:[n,e,d], heading_deg, sim_time, course:{fwd,right,up,yaw_deg}|null, corridor:{lateral_m, yaw_err_deg, dist_to_entrance_m}|null}` (corridor = forward-lap corridor axis; lateral + = vehicle right of the axis) | 5 Hz, sim only |
| `ack` | `{id, cmd, ok, msg}` — only to the client that sent the command | reply to a command |

`course` (from `skyscan.sim.course.Course.to_dict()`, built from `sim/course.yaml`; `null` when unknown):
```
{ "name": str,
  "origin": {"gz": [x, y, z], "heading_deg": 90.0},     # where the course frame sits (take-off point, facing +x)
  "objects": [ { "id": str, "type": "pad|qr|corridor|wall|floor|banner|obstacle|zone|restricted|camera|marker",
                 "label": str, "fwd": m, "right": m, "up": m,   # object centre in the course frame
                 "yaw_deg": deg,                              # about up, + clockwise, relative to course fwd
                 "size": [length (local fwd), width (local right), height],
                 "color": "#rrggbb", ... type-specific extras: "content" (qr), "lap" (corridor/banner) } ],
  "corridors": { "forward": {"entrance": [fwd, right], "axis_yaw_deg": 0.0, "width_m": 3.5, "length_m": 10.0,
                             "banner_id": str}, "return": {...} } }
```
A banner's local fwd axis is its outward normal (the side with the print). `truth.course` is the vehicle
position in this frame from simulator ground truth (independent of A1), with `yaw_deg` relative to course fwd.

Snapshot handling (client): process `hello.snapshot` / `resync.snapshot` directly — every message in
`latest` and `events` through the normal handlers, `logs` as per-source line lists — then ignore live
messages with `seq <= snapshot.seq`. Every operator command is also broadcast as a `UI` event.

Client → server: `{"cmd": ..., "id": "<client id>", ...}`

| cmd | fields | effect |
|---|---|---|
| `run` | `stages: ["A1",...]` | run selected stages (canonical order) |
| `abort` | | abort run → hold |
| `hold` | | abort run + `link.hold(force_guided=True)` |
| `land` / `rtl` | | abort run (no hold) + LAND / RTL |
| `disarm` | `force: bool`, `confirm: "FORCE"` (required with force) | disarm |
| `gimbal` | `pitch: deg` (−90..30), `yaw: deg` | set gimbal |
| `reset_mission` | | `runner.reset()` (rejected while running) |
| `sim` | `action: start|stop|restart` | ProcessManager (runs in background; progress via `proc`/events) |
| `gz_gui` | `action: open|close` | Gazebo GUI client window on the box display |
| `ping` | | ack only |

HTTP: `GET /` UI (`skyscan/server/static/index.html`; assets under `/static/...`) ·
`GET /video/<cam>.mjpg[?fps=N]` (raw frames, overlays drawn client-side from `vision`) ·
`GET /snapshot/<cam>.jpg` · `GET /api/state` · `GET /api/health` · `GET /runs/<run_id>/<file>`.
With a simulator attached, any other absolute path is served read-only when it is a mesh or texture
(`.dae .stl .obj .mtl .glb .gltf .png .jpg`) inside the sim model/world folders or `GZ_SIM_RESOURCE_PATH`:
gzweb asks the page origin for the paths Gazebo reports before it falls back to the websocket.
Optional `server.auth_token`: when set, `/ws?token=<token>` is required.

## 10. Box facts (verified 2026-10-04)

- i3-8100 (4 cores, no HT), Intel UHD 630 (Mesa), 11 GB RAM, Ubuntu 24.04, Gazebo Harmonic 8.15,
  ArduPilot master (4.7-dev), pymavlink 2.4.49, OpenCV 5.0, Python 3.12 venv `/opt/robotics/drone_env`.
- `source /opt/robotics/drone_env/setup_drone.sh` sets ROS/gz/venv. It is **not** `set -u` safe.
  Its `GZ_SIM_RESOURCE_PATH`/`SDF_PATH` put the stock `iris_with_standoffs` (no down camera, no LiDAR)
  first — SkyScan always prepends its own `sim/models`.
- Headless `gz sim -s --headless-rendering` (EGL) renders cameras; RTF ≈ 1.0 with 2 cameras + LiDAR
  once SITL is connected (≈ 0.2 before SITL connects — lockstep plugin waiting).
- Gazebo GUI alone costs ≈ 75 % of a core — it is optional (button), not part of the default run.
- `pkill -f <pattern>` over ssh kills your own shell if the pattern appears in the command line —
  use pid files or the `[x]yz` bracket trick.
