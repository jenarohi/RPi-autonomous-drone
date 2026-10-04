"""MavLink connection and flight control interface.

Thread model:
  mav-rx: sole thread that reads MAVLink messages; updates VehicleState; resolves ACK waiters.
  mav-hb: sends GCS heartbeat at 1 Hz.
All writes are guarded by a single write lock.
"""
from __future__ import annotations

import collections
import math
import os
import threading
import time
from typing import Any, Callable, Sequence

os.environ["MAVLINK20"] = "1"
from pymavlink import mavutil

from skyscan.bus import EventBus
from skyscan.types import Sev, VehicleState, replace
from skyscan.utils.logger import get_logger

log = get_logger("FC/LINK")

# Severity mapping from MAV_SEVERITY to Sev
_SEV_MAP = {
    0: Sev.CRITICAL,  # EMERGENCY
    1: Sev.CRITICAL,  # ALERT
    2: Sev.CRITICAL,  # CRITICAL
    3: Sev.ERROR,     # ERROR
    4: Sev.WARN,      # WARNING
    5: Sev.INFO,      # NOTICE
    6: Sev.INFO,      # INFO
    7: Sev.DEBUG,     # DEBUG
}

# EKF flags required for ekf_ok
# ATTITUDE (1), VELOCITY_HORIZ (2), POS_HORIZ_REL (4), POS_HORIZ_ABS (8), POS_VERT_ABS (16)
_EKF_REQUIRED_FLAGS = 0x1F
_EKF_CONST_POS_MODE = 0x400  # 1 << 10


class MavLink:
    """Thread-safe MAVLink link to ArduPilot."""

    def __init__(self, cfg: Any, bus: EventBus) -> None:
        self.cfg = cfg
        self.bus = bus
        self._url = getattr(cfg, "url", "tcp:127.0.0.1:5760")
        self._source_system = int(getattr(cfg, "source_system", 245))
        self._source_component = int(getattr(cfg, "source_component", 190))
        self._link_timeout_s = float(getattr(cfg, "link_timeout_s", 3.0))
        self._reconnect_s = float(getattr(cfg, "reconnect_s", 2.0))
        # pymavlink's TCP connection does not raise when the peer goes away (SITL restarted): it prints
        # "EOF on TCP socket" and returns nothing forever, so silence is the only sign. Reconnect after this long.
        self._stale_s = float(getattr(cfg, "stale_reconnect_s", max(5.0, 2.0 * self._link_timeout_s)))
        self._heartbeat_hz = float(getattr(cfg, "heartbeat_hz", 1.0))
        self._stream_rates_hz = getattr(cfg, "stream_rates_hz", {})

        self._state = VehicleState()
        self._state_lock = threading.Lock()
        self._write_lock = threading.Lock()

        self._master: Any = None
        self._running = False
        self._rx_thread: threading.Thread | None = None
        self._hb_thread: threading.Thread | None = None

        self._last_hb_time: float = 0.0
        self._target_system = 1
        self._target_component = 1

        self._ack_waiters: dict[int, list[tuple[threading.Event, list[int]]]] = collections.defaultdict(list)
        self._ack_lock = threading.Lock()

        self._recent_texts: collections.deque[tuple[float, int, str]] = collections.deque(maxlen=50)
        self._commanded_gimbal_pitch: float | None = None
        self._commanded_gimbal_yaw: float | None = None

    @property
    def connected(self) -> bool:
        """True if a vehicle heartbeat was seen within link_timeout_s."""
        with self._state_lock:
            return self._state.link

    def start(self) -> None:
        """Start receiver and heartbeat threads."""
        if self._running:
            return
        log.info(f"Starting MavLink service connecting to {self._url}")
        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, name="mav-rx", daemon=True)
        self._hb_thread = threading.Thread(target=self._hb_loop, name="mav-hb", daemon=True)
        self._rx_thread.start()
        self._hb_thread.start()

    def stop(self) -> None:
        """Stop threads and close connection."""
        log.info("Stopping MavLink service")
        self._running = False
        with self._write_lock:
            if self._master is not None:
                try:
                    self._master.close()
                except Exception as exc:
                    log.debug(f"Error closing master: {exc}")
                self._master = None

        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=2.0)
        if self._hb_thread and self._hb_thread.is_alive():
            self._hb_thread.join(timeout=2.0)

        with self._state_lock:
            self._state = replace(self._state, link=False, hb_age_s=None)

    def state(self) -> VehicleState:
        """Return a copy of the current vehicle state."""
        with self._state_lock:
            age = (time.time() - self._last_hb_time) if self._last_hb_time > 0 else None
            is_link = bool(age is not None and age <= self._link_timeout_s)
            if self._state.link != is_link or self._state.hb_age_s != age:
                self._state = replace(self._state, link=is_link, hb_age_s=age)
            return replace(self._state)

    def recent_texts(self, n: int = 20) -> list[tuple[float, int, str]]:
        """Return most recent STATUSTEXT entries (ts, severity, text)."""
        with self._state_lock:
            return list(self._recent_texts)[-n:]

    def wait(self, pred: Callable[[VehicleState], bool], timeout: float,
             abort: threading.Event | None = None) -> bool:
        """Wait until predicate is satisfied or timeout/abort occurs."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if abort is not None and abort.is_set():
                return False
            st = self.state()
            if pred(st):
                return True
            time.sleep(0.05)
        return False

    def command_long(self, cmd: int, *params: float, target_system: int | None = None,
                     target_component: int | None = None, timeout: float = 3.0,
                     retries: int = 1) -> int | None:
        """Send COMMAND_LONG and wait for COMMAND_ACK. Returns MAV_RESULT or None."""
        p = list(params) + [0.0] * (7 - len(params))
        tsys = target_system if target_system is not None else self._target_system
        tcomp = target_component if target_component is not None else self._target_component

        for attempt in range(max(1, retries + 1)):
            evt = threading.Event()
            box: list[int] = []
            with self._ack_lock:
                self._ack_waiters[cmd].append((evt, box))

            try:
                with self._write_lock:
                    if self._master is None:
                        log.warn(f"Cannot send command {cmd}: not connected")
                        return None
                    self._master.mav.command_long_send(
                        tsys, tcomp, cmd, 0,
                        float(p[0]), float(p[1]), float(p[2]), float(p[3]),
                        float(p[4]), float(p[5]), float(p[6])
                    )
                if evt.wait(timeout):
                    return box[0]
            finally:
                with self._ack_lock:
                    waiters = self._ack_waiters[cmd]
                    self._ack_waiters[cmd] = [w for w in waiters if w[0] is not evt]

            if attempt < retries:
                log.debug(f"Retrying command {cmd} (attempt {attempt + 1})")
                time.sleep(0.1)

        return None

    def set_mode(self, name: str, timeout: float = 5.0) -> bool:
        """Set flight mode by name and confirm via HEARTBEAT custom_mode."""
        log.info(f"Setting flight mode to {name}")
        with self._write_lock:
            if self._master is None:
                return False
            mode_mapping = self._master.mode_mapping()
            if not mode_mapping or name not in mode_mapping:
                log.error(f"Unknown flight mode: {name}")
                return False
            mode_id = mode_mapping[name]
            self._master.set_mode(mode_id)

        ok = self.wait(lambda s: s.mode == name, timeout=timeout)
        if ok:
            log.info(f"Flight mode confirmed: {name}")
        else:
            log.warn(f"Timeout waiting for flight mode {name}")
        return ok

    def arm(self, timeout: float = 8.0) -> tuple[bool, str]:
        """Arm motors with checks enabled. Returns (ok, reason/prearm message)."""
        log.info("Requesting vehicle arm")
        # Ensure we are in GUIDED mode or already armed
        st = self.state()
        if not st.link:
            return False, "Not connected to vehicle"
        if st.armed:
            return True, "Already armed"

        # If prearm_ok is known and False, report prearm messages
        if st.prearm_ok is False:
            texts = [t[2] for t in self.recent_texts(10) if "PreArm:" in t[2]]
            reason = texts[-1] if texts else "Pre-arm checks failing"
            log.warn(f"Pre-arm checks not ready: {reason}")

        # Send MAV_CMD_COMPONENT_ARM_DISARM with param1=1
        res = self.command_long(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1.0, 0.0, timeout=2.0, retries=2)
        armed = self.wait(lambda s: s.armed, timeout=timeout)
        if armed:
            log.info("Motors armed successfully")
            return True, "Armed"

        # Find latest PreArm or Arm error message
        recent = [t[2] for t in self.recent_texts(15) if "PreArm" in t[2] or "Arm" in t[2]]
        reason = recent[-1] if recent else f"Arming failed (ACK={res})"
        log.error(f"Arming failed: {reason}")
        return False, reason

    def disarm(self, force: bool = False, timeout: float = 5.0) -> bool:
        """Disarm motors. If force is True, force disarm (param2 = 21196)."""
        log.info(f"Disarming motors (force={force})")
        st = self.state()
        if not st.armed:
            return True

        param2 = 21196.0 if force else 0.0
        self.command_long(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0.0, param2, timeout=2.0, retries=2)
        disarmed = self.wait(lambda s: not s.armed, timeout=timeout)
        if disarmed:
            log.info("Motors disarmed successfully")
        else:
            log.warn("Failed to confirm disarm")
        return disarmed

    def takeoff(self, alt_m: float) -> int | None:
        """Command MAV_CMD_NAV_TAKEOFF to target altitude."""
        log.info(f"Commanding takeoff to {alt_m:.2f} m")
        return self.command_long(
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, float(alt_m),
            timeout=3.0, retries=2
        )

    def goto_ned(self, n: float, e: float, d: float, yaw_deg: float | None = None) -> None:
        """Position target in LOCAL_NED with optional absolute yaw target."""
        with self._write_lock:
            if self._master is None:
                return
            if yaw_deg is not None:
                # Mask: pos + yaw (mask 0b0000100111111000 = 0x09F8)
                mask = 0b0000100111111000
                target_yaw_rad = math.radians(yaw_deg)
            else:
                # Mask: pos only (mask 0b0000111111111000 = 0x0FF8)
                mask = 0b0000111111111000
                target_yaw_rad = 0.0

            self._master.mav.set_position_target_local_ned_send(
                0, self._target_system, self._target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED, mask,
                float(n), float(e), float(d),
                0.0, 0.0, 0.0,
                0.0, 0.0, 0.0,
                target_yaw_rad, 0.0
            )

    def velocity_body(self, vx: float, vy: float, vz: float,
                      yaw_rate_dps: float | None = None) -> None:
        """Command velocity in body frame (forward, right, down) and optional yaw rate."""
        with self._write_lock:
            if self._master is None:
                return
            # Mask: use vx, vy, vz and yaw_rate (0b0000010111000111 = 0x05C7)
            mask = 0b0000010111000111
            yaw_rate_rad = math.radians(yaw_rate_dps) if yaw_rate_dps is not None else 0.0
            self._master.mav.set_position_target_local_ned_send(
                0, self._target_system, self._target_component,
                mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, mask,
                0.0, 0.0, 0.0,
                float(vx), float(vy), float(vz),
                0.0, 0.0, 0.0,
                0.0, yaw_rate_rad
            )

    def velocity_ned(self, vn: float, ve: float, vd: float,
                     yaw_deg: float | None = None) -> None:
        """Command velocity in LOCAL_NED with optional absolute yaw."""
        with self._write_lock:
            if self._master is None:
                return
            if yaw_deg is not None:
                mask = 0b0000000111000111  # vel + yaw
                target_yaw_rad = math.radians(yaw_deg)
            else:
                mask = 0b0000010111000111  # vel only
                target_yaw_rad = 0.0

            self._master.mav.set_position_target_local_ned_send(
                0, self._target_system, self._target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_NED, mask,
                0.0, 0.0, 0.0,
                float(vn), float(ve), float(vd),
                0.0, 0.0, 0.0,
                target_yaw_rad, 0.0
            )

    def hold(self, force_guided: bool = False) -> bool:
        """Hover in place at current position and yaw.

        If not in GUIDED: returns False unless force_guided is True.
        """
        st = self.state()
        if not st.link:
            return False

        if st.mode != "GUIDED":
            if force_guided:
                log.info("Switching to GUIDED to enforce HOLD")
                if not self.set_mode("GUIDED", timeout=3.0):
                    return False
                st = self.state()
            else:
                log.debug("Hold requested but vehicle is not in GUIDED")
                return False

        if st.ned is not None:
            log.info(f"Holding at NED {st.ned}, yaw {st.yaw_deg}")
            self.goto_ned(st.ned[0], st.ned[1], st.ned[2], st.yaw_deg)
            return True
        return False

    def land(self) -> bool:
        """Switch to LAND mode and confirm."""
        log.info("Commanding LAND mode")
        return self.set_mode("LAND", timeout=5.0)

    def rtl(self) -> bool:
        """Switch to RTL mode and confirm."""
        log.info("Commanding RTL mode")
        return self.set_mode("RTL", timeout=5.0)

    def set_gimbal(self, pitch_deg: float, yaw_deg: float = 0.0) -> bool:
        """Control gimbal pitch and yaw.

        Tries DO_GIMBAL_MANAGER_PITCHYAW first, then DO_MOUNT_CONTROL.
        """
        log.info(f"Setting gimbal pitch={pitch_deg}°, yaw={yaw_deg}°")
        self._commanded_gimbal_pitch = pitch_deg
        self._commanded_gimbal_yaw = yaw_deg

        # MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW
        res = self.command_long(
            mavutil.mavlink.MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW,
            float(pitch_deg), float(yaw_deg),
            float("nan"), float("nan"),
            0.0, 0.0, 0.0,
            timeout=1.5, retries=1
        )
        if res == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            return True

        # Fallback: DO_MOUNT_CONTROL (pitch, roll, yaw, ..., mode 2 = MAVLINK_TARGETING)
        res_fallback = self.command_long(
            mavutil.mavlink.MAV_CMD_DO_MOUNT_CONTROL,
            float(pitch_deg), 0.0, float(yaw_deg),
            0.0, 0.0, 0.0,
            float(mavutil.mavlink.MAV_MOUNT_MODE_MAVLINK_TARGETING),
            timeout=1.5, retries=1
        )
        return res_fallback == mavutil.mavlink.MAV_RESULT_ACCEPTED

    # ───────────────────────────── Internal loops ─────────────────────────────

    def _request_stream_rates(self) -> None:
        """Request telemetry message rates via MAV_CMD_SET_MESSAGE_INTERVAL."""
        log.info("Requesting telemetry stream intervals")
        msg_ids = {
            "HEARTBEAT": mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT,
            "SYS_STATUS": mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS,
            "ATTITUDE": mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
            "LOCAL_POSITION_NED": mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED,
            "GLOBAL_POSITION_INT": mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
            "GPS_RAW_INT": mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT,
            "VFR_HUD": mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD,
            "EKF_STATUS_REPORT": mavutil.mavlink.MAVLINK_MSG_ID_EKF_STATUS_REPORT,
            "EXTENDED_SYS_STATE": mavutil.mavlink.MAVLINK_MSG_ID_EXTENDED_SYS_STATE,
            "HOME_POSITION": mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION,
            "BATTERY_STATUS": mavutil.mavlink.MAVLINK_MSG_ID_BATTERY_STATUS,
            "GIMBAL_DEVICE_ATTITUDE_STATUS": mavutil.mavlink.MAVLINK_MSG_ID_GIMBAL_DEVICE_ATTITUDE_STATUS,
            "MOUNT_STATUS": mavutil.mavlink.MAVLINK_MSG_ID_MOUNT_STATUS,
        }

        rates: dict[str, float] = dict(self._stream_rates_hz)
        for name, hz in rates.items():
            if name in msg_ids and hz > 0:
                interval_us = int(1e6 / hz)
                self.command_long(
                    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                    float(msg_ids[name]), float(interval_us),
                    timeout=0.5, retries=0
                )

    def _hb_loop(self) -> None:
        """Broadcast GCS heartbeat at 1 Hz."""
        while self._running:
            with self._write_lock:
                if self._master is not None:
                    try:
                        self._master.mav.heartbeat_send(
                            mavutil.mavlink.MAV_TYPE_GCS,
                            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                            0, 0, 0
                        )
                    except Exception as exc:
                        log.debug(f"Heartbeat send failed: {exc}")
            time.sleep(1.0 / max(0.5, self._heartbeat_hz))

    def _rx_loop(self) -> None:
        """Sole MAVLink receive loop."""
        last_rx = time.time()
        while self._running:
            # Connect or reconnect
            with self._write_lock:
                if self._master is None:
                    try:
                        log.info(f"Connecting to MAVLink endpoint: {self._url}")
                        self._master = mavutil.mavlink_connection(
                            self._url,
                            source_system=self._source_system,
                            source_component=self._source_component
                        )
                        last_rx = time.time()
                    except Exception as exc:
                        log.warn(f"Connection failed to {self._url}: {exc}")
                        self._master = None

            if self._master is None:
                time.sleep(self._reconnect_s)
                last_rx = time.time()
                continue

            # Wait for heartbeat to establish targets and sync parameters
            try:
                msg = self._master.recv_match(blocking=True, timeout=0.1)
            except Exception as exc:
                log.warn(f"Error reading from MAVLink link: {exc}")
                with self._write_lock:
                    if self._master is not None:
                        try:
                            self._master.close()
                        except Exception:
                            pass
                        self._master = None
                time.sleep(self._reconnect_s)
                continue

            if msg is None:
                if time.time() - last_rx > self._stale_s:
                    log.warn(f"No MAVLink data for {self._stale_s:.0f} s from {self._url}: reconnecting")
                    with self._write_lock:
                        if self._master is not None:
                            try:
                                self._master.close()
                            except Exception:
                                pass
                            self._master = None
                continue

            last_rx = time.time()
            self._handle_msg(msg)

    def _handle_msg(self, msg: Any) -> None:
        """Parse incoming MAVLink message and update state."""
        msg_type = msg.get_type()
        now = time.time()

        if msg_type == "HEARTBEAT":
            # Filter GCS / companion heartbeats (only care about the autopilot)
            if msg.type not in (mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER):
                was_connected = self.connected
                self._last_hb_time = now
                self._target_system = msg.get_srcSystem()
                self._target_component = msg.get_srcComponent()

                mode_name = "UNKNOWN"
                if self._master:
                    mode_mapping = self._master.mode_mapping()
                    if mode_mapping:
                        rev_map = {v: k for k, v in mode_mapping.items()}
                        mode_name = rev_map.get(msg.custom_mode, f"MODE_{msg.custom_mode}")

                armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

                with self._state_lock:
                    prev_mode = self._state.mode
                    prev_armed = self._state.armed

                    self._state = replace(
                        self._state,
                        t=now,
                        link=True,
                        hb_age_s=0.0,
                        sysid=self._target_system,
                        armed=armed,
                        mode=mode_name,
                        system_status=msg.system_status,
                    )

                if not was_connected:
                    log.info(f"Vehicle connected! System ID: {self._target_system}, Mode: {mode_name}")
                    self.bus.event("FC", f"Vehicle connected: sysid={self._target_system} mode={mode_name}", Sev.GOOD)
                    # Request data streams
                    threading.Thread(target=self._request_stream_rates, daemon=True).start()

                if mode_name != prev_mode and prev_mode != "UNKNOWN":
                    log.info(f"Mode change detected: {prev_mode} -> {mode_name}")
                    self.bus.event("FC", f"Mode changed to {mode_name}", Sev.INFO)

                if armed != prev_armed:
                    log.info(f"Armed state changed: {prev_armed} -> {armed}")
                    self.bus.event("FC", "Motors armed" if armed else "Motors disarmed", Sev.INFO)

        elif msg_type == "COMMAND_ACK":
            with self._ack_lock:
                waiters = self._ack_waiters.get(msg.command, [])
                for evt, box in waiters:
                    box.append(msg.result)
                    evt.set()

        elif msg_type == "STATUSTEXT":
            text = msg.text
            sev_int = getattr(msg, "severity", 6)
            sev = _SEV_MAP.get(sev_int, Sev.INFO)
            with self._state_lock:
                self._recent_texts.append((now, sev_int, text))
                self._state = replace(self._state, last_text=text)
            self.bus.event("FC", text, sev)

        elif msg_type == "ATTITUDE":
            roll = math.degrees(msg.roll)
            pitch = math.degrees(msg.pitch)
            yaw = (math.degrees(msg.yaw) + 360.0) % 360.0
            yawspeed = math.degrees(msg.yawspeed)
            with self._state_lock:
                self._state = replace(
                    self._state,
                    t=now,
                    roll_deg=roll,
                    pitch_deg=pitch,
                    yaw_deg=yaw,
                    yawspeed_dps=yawspeed
                )

        elif msg_type == "LOCAL_POSITION_NED":
            ned = (float(msg.x), float(msg.y), float(msg.z))
            vel = (float(msg.vx), float(msg.vy), float(msg.vz))
            with self._state_lock:
                self._state = replace(self._state, t=now, ned=ned, vel_ned=vel)

        elif msg_type == "GLOBAL_POSITION_INT":
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt_msl = msg.alt / 1e3
            rel_alt = msg.relative_alt / 1e3
            with self._state_lock:
                self._state = replace(
                    self._state,
                    t=now,
                    lat=lat,
                    lon=lon,
                    alt_msl_m=alt_msl,
                    rel_alt_m=rel_alt
                )

        elif msg_type == "VFR_HUD":
            with self._state_lock:
                self._state = replace(
                    self._state,
                    t=now,
                    groundspeed_mps=float(msg.groundspeed),
                    climb_mps=float(msg.climb),
                    throttle_pct=float(msg.throttle)
                )

        elif msg_type == "GPS_RAW_INT":
            hdop = (msg.eph / 100.0) if hasattr(msg, "eph") else None
            with self._state_lock:
                self._state = replace(
                    self._state,
                    t=now,
                    gps_fix=msg.fix_type,
                    gps_sats=msg.satellites_visible,
                    gps_hdop=hdop
                )

        elif msg_type == "EKF_STATUS_REPORT":
            flags = msg.flags
            ekf_good = ((flags & _EKF_REQUIRED_FLAGS) == _EKF_REQUIRED_FLAGS) and not (flags & _EKF_CONST_POS_MODE)
            with self._state_lock:
                self._state = replace(self._state, t=now, ekf_flags=flags, ekf_ok=bool(ekf_good))

        elif msg_type == "SYS_STATUS":
            bit = mavutil.mavlink.MAV_SYS_STATUS_PREARM_CHECK
            prearm = None
            if msg.onboard_control_sensors_present & bit:
                prearm = bool(msg.onboard_control_sensors_health & bit)
            batt_v = msg.voltage_battery / 1000.0 if msg.voltage_battery != -1 else None
            batt_pct = float(msg.battery_remaining) if msg.battery_remaining != -1 else None
            with self._state_lock:
                self._state = replace(
                    self._state,
                    t=now,
                    prearm_ok=prearm,
                    battery_v=batt_v,
                    battery_pct=batt_pct
                )

        elif msg_type == "EXTENDED_SYS_STATE":
            with self._state_lock:
                self._state = replace(self._state, t=now, landed_state=msg.landed_state)

        elif msg_type == "HOME_POSITION":
            home_latlon = (msg.latitude / 1e7, msg.longitude / 1e7, msg.altitude / 1e3)
            home_ned = (float(msg.x), float(msg.y), float(msg.z))
            with self._state_lock:
                self._state = replace(self._state, t=now, home=home_latlon, home_ned=home_ned)

        elif msg_type == "MOUNT_STATUS":
            pitch = msg.pointing_a / 100.0
            yaw = msg.pointing_c / 100.0
            with self._state_lock:
                self._state = replace(self._state, t=now, gimbal_pitch_deg=pitch, gimbal_yaw_deg=yaw)

        elif msg_type == "GIMBAL_DEVICE_ATTITUDE_STATUS":
            # Convert quaternion to euler pitch/yaw if available
            q = [msg.q[0], msg.q[1], msg.q[2], msg.q[3]]
            pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2.0 * (q[0] * q[2] - q[3] * q[1])))))
            yaw = math.degrees(math.atan2(2.0 * (q[0] * q[3] + q[1] * q[2]), 1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3])))
            with self._state_lock:
                self._state = replace(self._state, t=now, gimbal_pitch_deg=pitch, gimbal_yaw_deg=yaw)
        else:
            # Update last commanded gimbal pitch if reported pitch is None
            with self._state_lock:
                if self._state.gimbal_pitch_deg is None and self._commanded_gimbal_pitch is not None:
                    self._state = replace(
                        self._state,
                        gimbal_pitch_deg=self._commanded_gimbal_pitch,
                        gimbal_yaw_deg=self._commanded_gimbal_yaw
                    )
