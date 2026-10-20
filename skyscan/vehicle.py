"""
ArduCopter over MAVLink (pymavlink). Talks WORLD coordinates to the mission
(see config.py) and converts to/from ArduPilot LOCAL_NED internally.

LOCAL_NED origin is the EKF origin, which in SITL+Gazebo is the Gazebo
origin, not the spawn point - so the local position is captured on the
ground (capture_home) and the world frame is anchored to config.HOME_XY.
"""
import math
import threading
from collections import deque
import time
from dataclasses import dataclass

from pymavlink import mavutil

from . import config as C
from .geometry import wrap_pi

M = mavutil.mavlink

# SET_POSITION_TARGET_LOCAL_NED type_mask bits:
# 1|2|4 position, 8|16|32 velocity, 64|128|256 accel, 1024 yaw, 2048 yaw rate
MASK_POS_YAW = 8 | 16 | 32 | 64 | 128 | 256 | 2048
MASK_VEL_YAW = 1 | 2 | 4 | 64 | 128 | 256 | 2048


@dataclass
class State:
    x: float
    y: float
    alt: float
    heading: float        # ENU rad
    roll: float           # rad, right wing down +
    pitch: float          # rad, nose up +
    vx: float             # world east  m/s
    vy: float             # world north m/s
    vz: float             # up m/s
    mode: str
    armed: bool
    age: float            # seconds since the last position message

    @property
    def xy(self):
        return (self.x, self.y)


class Vehicle:
    def __init__(self, url: str, log):
        self.url, self.log = url, log
        self.m = None
        self.sys = self.comp = None
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._running = False
        self._lpos = None          # (n, e, d, vn, ve, vd)
        self._lpos_t = 0.0
        self._att = None           # (roll, pitch, yaw NED) rad
        self._hist = deque(maxlen=900)   # (monotonic time, lpos, att) for state_at()
        self._mode = "UNKNOWN"
        self._armed = False
        self._landed_state = None
        self._origin = None        # LOCAL_NED of the take-off point
        self.home_xy = C.HOME_XY

    # ── connection ────────────────────────────────────────────────────────
    def connect(self, timeout: float = 60.0):
        self.log("FC", f"connecting {self.url}")
        self.m = mavutil.mavlink_connection(self.url, source_system=C.MAVLINK_SOURCE_SYSTEM,
                                            autoreconnect=True)
        t_end = time.monotonic() + timeout
        while time.monotonic() < t_end:
            hb = self.m.recv_match(type="HEARTBEAT", blocking=True, timeout=1.0)
            if hb and hb.autopilot == M.MAV_AUTOPILOT_ARDUPILOTMEGA and hb.type != M.MAV_TYPE_GCS:
                self.sys, self.comp = hb.get_srcSystem(), hb.get_srcComponent()
                break
        else:
            raise ConnectionError(f"no ArduPilot heartbeat on {self.url}")
        self.log("FC", f"heartbeat from system {self.sys} component {self.comp}")
        self._running = True
        threading.Thread(target=self._reader, daemon=True).start()
        for msg_id, hz in ((M.MAVLINK_MSG_ID_LOCAL_POSITION_NED, 25), (M.MAVLINK_MSG_ID_ATTITUDE, 50),
                           (M.MAVLINK_MSG_ID_EXTENDED_SYS_STATE, 2)):
            self.command(M.MAV_CMD_SET_MESSAGE_INTERVAL, msg_id, 1e6 / hz)
        while time.monotonic() < t_end and (self._lpos is None or self._att is None):
            time.sleep(0.1)
        if self._lpos is None:
            raise ConnectionError("no LOCAL_POSITION_NED - EKF has no origin yet (GPS?)")

    def close(self):
        self._running = False

    def _reader(self):
        while self._running:
            try:
                msg = self.m.recv_match(blocking=True, timeout=0.5)
            except Exception as e:           # socket hiccup: keep going
                self.log("FC", f"recv error {e}")
                time.sleep(0.2)
                continue
            if msg is None or msg.get_srcSystem() != self.sys:
                continue
            t = msg.get_type()
            with self._lock:
                if t == "HEARTBEAT" and msg.get_srcComponent() == self.comp:
                    self._mode = mavutil.mode_string_v10(msg)
                    self._armed = bool(msg.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED)
                elif t == "LOCAL_POSITION_NED":
                    self._lpos = (msg.x, msg.y, msg.z, msg.vx, msg.vy, msg.vz)
                    self._lpos_t = time.monotonic()
                    if self._att is not None:
                        self._hist.append((self._lpos_t, self._lpos, self._att))
                elif t == "ATTITUDE":
                    self._att = (msg.roll, msg.pitch, msg.yaw)
                    if self._lpos is not None:
                        self._hist.append((time.monotonic(), self._lpos, self._att))
                elif t == "EXTENDED_SYS_STATE":
                    self._landed_state = msg.landed_state
            if t == "STATUSTEXT":
                self.log("AP", msg.text)
            elif t == "COMMAND_ACK" and msg.result not in (M.MAV_RESULT_ACCEPTED, M.MAV_RESULT_IN_PROGRESS):
                self.log("FC", f"command {msg.command} rejected (result {msg.result})")

    # ── state ─────────────────────────────────────────────────────────────
    def capture_home(self):
        """Anchor WORLD coordinates: the current position is config.HOME_XY, alt 0."""
        with self._lock:
            n, e, d = self._lpos[:3]
        self._origin = (n, e, d)
        self.log("FC", f"home captured: LOCAL_NED ({n:+.2f}, {e:+.2f}, {d:+.2f}) = world {self.home_xy}")

    def state(self) -> State:
        with self._lock:
            n, e, d, vn, ve, vd = self._lpos
            (roll, pitch, yaw), mode, armed, t = self._att, self._mode, self._armed, self._lpos_t
        n0, e0, d0 = self._origin if self._origin else (n, e, d)
        return State(self.home_xy[0] + (e - e0), self.home_xy[1] + (n - n0), -(d - d0),
                     wrap_pi(math.pi / 2 - yaw), roll, pitch, ve, vn, -vd, mode, armed,
                     time.monotonic() - t)

    def state_at(self, t: float) -> State:
        """Pose at monotonic time `t` (e.g. the camera exposure), interpolated between the two telemetry
        samples around it. The newest sample is used if `t` is newer than the history, the oldest if older."""
        with self._lock:
            h = list(self._hist)
            mode, armed, tl = self._mode, self._armed, self._lpos_t
        if len(h) < 2:
            return self.state()
        if t >= h[-1][0]:
            a = b = h[-1]
            w = 0.0
        elif t <= h[0][0]:
            a = b = h[0]
            w = 0.0
        else:
            lo, hi = 0, len(h) - 1
            while hi - lo > 1:
                mid = (lo + hi) // 2
                if h[mid][0] <= t:
                    lo = mid
                else:
                    hi = mid
            a, b = h[lo], h[hi]
            w = (t - a[0]) / max(b[0] - a[0], 1e-6)
        lp = [x + w * (y - x) for x, y in zip(a[1], b[1])]
        r = a[2][0] + w * (b[2][0] - a[2][0])
        p = a[2][1] + w * (b[2][1] - a[2][1])
        yaw = a[2][2] + w * wrap_pi(b[2][2] - a[2][2])
        n, e, d, vn, ve, vd = lp
        n0, e0, d0 = self._origin if self._origin else (n, e, d)
        return State(self.home_xy[0] + (e - e0), self.home_xy[1] + (n - n0), -(d - d0),
                     wrap_pi(math.pi / 2 - yaw), r, p, ve, vn, -vd, mode, armed, time.monotonic() - tl)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def armed(self) -> bool:
        return self._armed

    def on_ground(self) -> bool:
        return self._landed_state == M.MAV_LANDED_STATE_ON_GROUND

    # ── low-level senders ─────────────────────────────────────────────────
    def command(self, cmd, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
        with self._send_lock:
            self.m.mav.command_long_send(self.sys, self.comp, cmd, 0, p1, p2, p3, p4, p5, p6, p7)

    def _target(self, mask, n=0.0, e=0.0, d=0.0, vn=0.0, ve=0.0, vd=0.0, yaw=0.0):
        with self._send_lock:
            self.m.mav.set_position_target_local_ned_send(
                0, self.sys, self.comp, M.MAV_FRAME_LOCAL_NED, mask,
                n, e, d, vn, ve, vd, 0, 0, 0, yaw, 0)

    # ── high-level commands (WORLD frame) ─────────────────────────────────
    def goto(self, x: float, y: float, alt: float, heading: float):
        n0, e0, d0 = self._origin
        self._target(MASK_POS_YAW, n=n0 + (y - self.home_xy[1]), e=e0 + (x - self.home_xy[0]),
                     d=d0 - alt, yaw=wrap_pi(math.pi / 2 - heading))

    def velocity(self, vx: float, vy: float, vz: float, heading: float):
        """World-frame velocity (east, north, up) with a held heading. ArduPilot
        stops by itself if this is not re-sent within ~3 s."""
        self._target(MASK_VEL_YAW, vn=vy, ve=vx, vd=-vz, yaw=wrap_pi(math.pi / 2 - heading))

    def set_speed(self, mps: float):
        self.command(M.MAV_CMD_DO_CHANGE_SPEED, 1, mps, -1)

    def set_servo(self, channel: int, pwm: int):
        self.command(M.MAV_CMD_DO_SET_SERVO, channel, pwm)

    def set_mode(self, name: str, timeout: float = 6.0) -> bool:
        mode_id = {v: k for k, v in mavutil.mode_mapping_acm.items()}[name]
        t_end = time.monotonic() + timeout
        while time.monotonic() < t_end:
            with self._send_lock:
                self.m.mav.set_mode_send(self.sys, M.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id)
            for _ in range(10):
                if self._mode == name:
                    return True
                time.sleep(0.1)
        return False

    def arm(self, timeout: float = 60.0) -> bool:
        t_end = time.monotonic() + timeout
        while time.monotonic() < t_end:
            self.command(M.MAV_CMD_COMPONENT_ARM_DISARM, 1)
            for _ in range(20):
                if self._armed:
                    return True
                time.sleep(0.1)
        return False

    def takeoff(self, alt: float):
        self.command(M.MAV_CMD_NAV_TAKEOFF, p7=alt)
