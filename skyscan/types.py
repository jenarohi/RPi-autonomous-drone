"""Shared data contract.

Every structure that crosses a module boundary or goes to the UI is defined here. Field names are
part of the WebSocket protocol (docs/ARCHITECTURE.md §9) — rename only together with the UI.
Angles are degrees, distances metres, times epoch seconds unless the name says otherwise.
"""
from __future__ import annotations

import dataclasses
import enum
from dataclasses import dataclass, field
from typing import Any


class Sev(str, enum.Enum):
    """Event severity, ordered from least to most severe."""
    DEBUG = "debug"
    INFO = "info"
    GOOD = "good"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class StageState(str, enum.Enum):
    IDLE = "idle"          # never run (or reset)
    QUEUED = "queued"      # selected in the current run, waiting for its turn
    CHECKING = "checking"  # evaluating preconditions
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"      # ran and did not meet its success criteria / errored / timed out
    NOGO = "nogo"          # a blocking precondition failed; the stage did not start
    ABORTED = "aborted"    # operator abort / safety action while running
    SKIPPED = "skipped"    # not run because an earlier stage in the run did not succeed

    @property
    def terminal(self) -> bool:
        return self in (StageState.SUCCESS, StageState.FAILED, StageState.NOGO,
                        StageState.ABORTED, StageState.SKIPPED)


class _Dict:
    """Mixin: JSON-ready dict (enums → values, tuples → lists, NaN/inf → None)."""

    def to_dict(self) -> dict[str, Any]:
        from skyscan.bus import jsonable  # local import: bus imports this module
        return jsonable(self)


# ───────────────────────────── vehicle ─────────────────────────────

@dataclass
class VehicleState(_Dict):
    t: float = 0.0                      # wall time of the last MAVLink message applied
    link: bool = False                  # vehicle HEARTBEAT seen within mavlink.link_timeout_s
    hb_age_s: float | None = None       # seconds since the last vehicle HEARTBEAT
    sysid: int | None = None
    armed: bool = False
    mode: str = "UNKNOWN"               # ArduCopter flight mode name ("GUIDED", "LAND", ...)
    system_status: int | None = None    # MAV_STATE
    landed_state: int | None = None     # MAV_LANDED_STATE: 0 undef, 1 on ground, 2 in air, 3 takeoff, 4 landing
    roll_deg: float | None = None
    pitch_deg: float | None = None
    yaw_deg: float | None = None        # heading 0..360, clockwise from north
    yawspeed_dps: float | None = None
    ned: tuple[float, float, float] | None = None       # LOCAL_POSITION_NED (EKF origin, NOT home)
    vel_ned: tuple[float, float, float] | None = None
    lat: float | None = None
    lon: float | None = None
    alt_msl_m: float | None = None
    rel_alt_m: float | None = None      # above home (GLOBAL_POSITION_INT.relative_alt)
    groundspeed_mps: float | None = None
    climb_mps: float | None = None
    throttle_pct: float | None = None
    gps_fix: int | None = None          # GPS_FIX_TYPE (3 = 3D)
    gps_sats: int | None = None
    gps_hdop: float | None = None
    ekf_flags: int | None = None        # EKF_STATUS_REPORT.flags
    ekf_ok: bool = False                # attitude+velocity+horizontal/vertical position good, not const-pos
    prearm_ok: bool | None = None       # SYS_STATUS PREARM_CHECK health bit (None = not reported)
    battery_v: float | None = None
    battery_pct: float | None = None
    home: tuple[float, float, float] | None = None      # HOME_POSITION lat, lon, alt_msl
    home_ned: tuple[float, float, float] | None = None  # HOME_POSITION x, y, z (local NED)
    gimbal_pitch_deg: float | None = None
    gimbal_yaw_deg: float | None = None
    range_m: float | None = None        # downward rangefinder / lidar height above the ground (DISTANCE_SENSOR, RANGEFINDER)
    range_t: float | None = None        # wall time of the last rangefinder reading
    range_min_m: float | None = None    # the sensor's valid span
    range_max_m: float | None = None
    last_text: str | None = None        # most recent STATUSTEXT


# ───────────────────────────── cameras / vision ─────────────────────────────

@dataclass
class Frame:
    """One camera image. Not JSON-serialisable (holds the image)."""
    cam: str                 # "down" | "front" | "overview" | ...
    seq: int                 # per-camera frame counter
    t: float                 # wall time received
    img: Any                 # BGR np.ndarray (H, W, 3) uint8
    sim_t: float | None = None

    @property
    def w(self) -> int:
        return int(self.img.shape[1])

    @property
    def h(self) -> int:
        return int(self.img.shape[0])


@dataclass
class LidarScan(_Dict):
    """One horizontal (2D) lidar sweep in the vehicle frame.

    Angles are degrees from the nose, counter-clockwise (+ = to the LEFT), like ROS LaserScan. A reading of
    ``inf`` (or NaN, or outside [range_min, range_max]) means "no return": nothing within range along that ray.
    """
    t: float                            # wall time received
    seq: int
    angle_min_deg: float                # angle of ranges[0]
    angle_step_deg: float               # angle increment between consecutive ranges
    ranges: list[float]                 # metres
    range_min: float = 0.05
    range_max: float = 12.0

    def angle_deg(self, i: int) -> float:
        return self.angle_min_deg + i * self.angle_step_deg

    def to_wire(self, decimals: int = 2) -> dict[str, Any]:
        """Compact JSON for the UI: no-return rays are ``None``."""
        import math
        lo, hi = self.range_min, self.range_max
        r = [round(x, decimals) if (math.isfinite(x) and lo <= x <= hi) else None for x in self.ranges]
        return {"seq": self.seq, "a0": round(self.angle_min_deg, 3), "da": round(self.angle_step_deg, 4),
                "r": r, "rmin": lo, "rmax": hi}


@dataclass
class QRPayload(_Dict):
    raw: str
    kind: str = "text"                  # "json" | "kv" | "target" | "latlon" | "text"
    target: str | None = None           # delivery target identifier, e.g. "A" .. "E"
    lat: float | None = None
    lon: float | None = None
    alt_m: float | None = None
    fields: dict[str, str] = field(default_factory=dict)
    valid: bool = False                 # payload identifies a delivery location (target or lat/lon)
    note: str = ""


@dataclass
class QRDetection(_Dict):
    t: float
    cam: str
    seq: int
    found: bool                                     # a QR symbol was located (decoded or not)
    text: str | None = None                         # decoded text (None = located, not decoded)
    corners: list[list[float]] | None = None        # 4 × [u, v] pixels
    center: tuple[float, float] | None = None       # [u, v] pixels
    size_px: float | None = None                    # mean side length, pixels
    decoder: str | None = None                      # "zbar", "zbar-x2", "cv2", ...
    ground_fwd_m: float | None = None               # QR centre relative to the vehicle on the ground plane,
    ground_right_m: float | None = None             # in the heading-aligned level frame (fwd, right)
    latency_ms: float | None = None
    others: list[dict[str, Any]] | None = None      # further symbols decoded in the same frame: {text, center, size_px}


@dataclass
class QRStatus(_Dict):
    session: int = 0
    started_t: float | None = None
    frames: int = 0                     # frames processed in this session
    located: int = 0                    # frames with a located QR
    decoded: int = 0                    # frames with a decoded QR
    votes: dict[str, int] = field(default_factory=dict)   # decoded text → count
    confirmed: str | None = None        # text that reached confirm_votes
    confirmed_t: float | None = None
    payload: QRPayload | None = None



@dataclass
class RedBlob(_Dict):
    area_px: float
    centroid: tuple[float, float]                   # [u, v] pixels
    bbox: tuple[int, int, int, int]                 # x, y, w, h
    hull: list[list[float]]                         # convex hull polygon, pixels
    touches_border: bool = False                    # cut off by the image edge: the zone continues out of view


@dataclass
class RedDetection(_Dict):
    """Red (restricted-zone) pixels in one belly-camera frame."""
    t: float
    cam: str
    seq: int
    found: bool                                     # at least one red region above the minimum area
    mask_frac: float = 0.0                          # red pixels / all pixels
    blobs: list[RedBlob] = field(default_factory=list)
    latency_ms: float | None = None


@dataclass
class BannerDetection(_Dict):
    """AeroTHON 2026 green banner seen by a (gimbal) camera.

    Geometry is expressed in the vehicle's heading-aligned level frame at frame time
    (fwd = vehicle heading, right = 90° clockwise, up), assuming the gimbal yaw follows the vehicle.
    """
    t: float
    cam: str
    seq: int
    found: bool
    score: float | None = None                    # 0..1 confidence
    corners: list[list[float]] | None = None      # 4 × [u, v]: TL, TR, BR, BL
    center: tuple[float, float] | None = None
    area_frac: float | None = None                # quad area / image area
    aspect: float | None = None                   # apparent width / height
    text_ratio: float | None = None               # white-text pixel fraction inside the quad
    bearing_deg: float | None = None              # banner centre angle from vehicle heading, + right
    elevation_deg: float | None = None            # banner centre angle above the horizon, + up
    distance_m: float | None = None               # horizontal distance to the banner plane (along its normal)
    range_m: float | None = None                  # straight-line distance to the banner centre
    lateral_m: float | None = None                # banner centre offset ⟂ corridor axis, + = to the vehicle's right
    height_m: float | None = None                 # banner centre height relative to the camera, + = above
    yaw_err_deg: float | None = None              # corridor-axis heading − vehicle heading, + = turn right
    plane_ok: bool | None = None                  # geometry plausible: banner = PnP vertical plane; floor = measured width ok
    reason: str | None = None                     # why not found / rejected (debug)
    kind: str = "banner"                          # "banner" (vertical PnP) | "floor" (green corridor floor on the ground)
    width_m: float | None = None                  # floor: measured corridor width (expected 3.5 m)
    near_clipped: bool | None = None              # floor: entrance edge cut off by the image bottom (distance unreliable)
    length_visible_m: float | None = None         # floor: how much of the corridor length is in view


# ───────────────────────────── mission ─────────────────────────────

@dataclass
class Check(_Dict):
    name: str
    ok: bool
    detail: str = ""
    blocking: bool = True    # a failed blocking check → NO-GO (or FAILED for success criteria)
    value: Any = None        # measured value, for the UI
    limit: Any = None        # threshold it was compared to


@dataclass
class StageReport(_Dict):
    stage_id: str
    title: str
    state: StageState = StageState.IDLE
    run_id: str | None = None
    phase: str = ""                     # current step, human readable
    progress: float | None = None       # 0..1 when known
    started_at: float | None = None
    ended_at: float | None = None
    checks: list[Check] = field(default_factory=list)       # preconditions (GO / NO-GO)
    criteria: list[Check] = field(default_factory=list)     # success criteria evaluation
    metrics: dict[str, Any] = field(default_factory=dict)   # measured numbers (times, errors, ...)
    outputs: dict[str, Any] = field(default_factory=dict)   # products (qr payload, corridor axis, ...)
    log: list[dict[str, Any]] = field(default_factory=list) # stage-scoped events {ts, sev, msg}
    snapshots: list[str] = field(default_factory=list)      # URLs under /runs/
    message: str = ""                   # one-line summary
    error: str | None = None            # exception / failure reason

    @property
    def duration_s(self) -> float | None:
        if self.started_at is None:
            return None
        import time
        return (self.ended_at or time.time()) - self.started_at


# ───────────────────────────── processes / sim ─────────────────────────────

@dataclass
class ProcStatus(_Dict):
    name: str                       # "gazebo" | "sitl" | "gz_ws" | "gz_gui"
    state: str = "down"             # down | starting | up | stopping | exited | error
    pid: int | None = None
    started_at: float | None = None
    exit_code: int | None = None
    cpu_pct: float | None = None
    rss_mb: float | None = None
    detail: str = ""


@dataclass
class Truth(_Dict):
    """Simulator ground truth for the vehicle model."""
    t: float
    pos_gz: tuple[float, float, float]      # Gazebo world (ENU) metres
    yaw_gz_rad: float                       # Gazebo yaw, CCW from +x
    ned: tuple[float, float, float]         # same point in NED (n = y, e = x, d = -z)
    heading_deg: float                      # 0..360 clockwise from north
    sim_time: float | None = None


def replace(obj, **changes):
    """dataclasses.replace re-exported for convenience."""
    return dataclasses.replace(obj, **changes)
