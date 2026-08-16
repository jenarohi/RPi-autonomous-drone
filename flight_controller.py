# ============================================================
# flight_controller.py — pymavlink ArduCopter SITL wrapper
#
# Key design decisions:
#   - goto() uses SET_POSITION_TARGET_GLOBAL_INT (correct for GUIDED)
#     NOT mission_item_int_send (that's for AUTO mode missions)
#   - All velocity commands at 10 Hz are NED frame
#   - Body-frame velocity for banner approach (heading-relative)
#   - Proper GUIDED mode check before every command
#   - Speed params set at connect, not per-command
# ============================================================
import time
import math
from pymavlink import mavutil
from config import SITL_CONNECTION


class FlightController:
    def __init__(self):
        self.master   = None
        self.home_lat = 0.0
        self.home_lon = 0.0
        self._tick    = None

    def set_tick(self, fn):
        """Register a function to call every time we poll MAVLink."""
        self._tick = fn

    def _do_tick(self):
        if self._tick:
            self._tick()

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self, timeout=180):
        """
        Connect to ArduCopter SITL.
        Port 5762 = ArduCopter second TCP server (direct pymavlink, no MAVProxy).
        Port 5760 = first TCP server (fallback).
        Wait until heartbeat confirmed.
        """
        for port in [5762, 5760]:
            conn_str = f"tcp:127.0.0.1:{port}"
            print(f"[FC] Trying {conn_str} ...")
            try:
                self.master = mavutil.mavlink_connection(
                    conn_str, autoreconnect=True)
                break
            except Exception as e:
                print(f"[FC] {conn_str} failed: {e}")
                self.master = None

        if self.master is None:
            raise RuntimeError(
                "[FC] Cannot open any SITL port. Is sim_vehicle.py running?")

        print("[FC] Connected. Waiting for heartbeat ...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            hb = self.master.recv_match(
                type='HEARTBEAT', blocking=True, timeout=3)
            if hb:
                print(f"[FC] ✓ Heartbeat (sys={self.master.target_system} "
                      f"comp={self.master.target_component})")
                break
            elapsed = int(time.time() - (deadline - timeout))
            print(f"[FC]   waiting... {elapsed}s")
        else:
            raise RuntimeError(
                "[FC] No heartbeat after 180s.\n"
                "  → Is Gazebo loaded?\n"
                "  → Is sim_vehicle.py running with --model JSON?\n"
                "  → Did you wait for EKF GPS lock?")

        # Request all streams at 10 Hz
        self.master.mav.request_data_stream_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
        time.sleep(1)

        # Set nav speed 5 m/s
        self._set_param(b'WPNAV_SPEED', 500,
                        mavutil.mavlink.MAV_PARAM_TYPE_REAL32)

        # LiDAR proximity avoidance params
        avoid = [
            (b'PRX_TYPE',     2,   mavutil.mavlink.MAV_PARAM_TYPE_INT32),
            (b'AVOID_ENABLE', 3,   mavutil.mavlink.MAV_PARAM_TYPE_INT32),
            (b'OA_TYPE',      2,   mavutil.mavlink.MAV_PARAM_TYPE_INT32),
            (b'OA_LOOKAHEAD', 4.0, mavutil.mavlink.MAV_PARAM_TYPE_REAL32),
            (b'AVOID_MARGIN', 1.0, mavutil.mavlink.MAV_PARAM_TYPE_REAL32),
        ]
        for name, val, ptype in avoid:
            self._set_param(name, val, ptype)
        print("[FC] ✓ LiDAR avoidance params set")

    def _set_param(self, name: bytes, value, ptype):
        self.master.mav.param_set_send(
            self.master.target_system, self.master.target_component,
            name, float(value), ptype)
        time.sleep(0.2)

    # ── GPS ───────────────────────────────────────────────────────────────────

    def wait_gps(self, min_sats=6):
        """Block until GPS fix with minimum satellite count."""
        print("[FC] Waiting for GPS lock ...")
        while True:
            self._do_tick()
            msg = self.master.recv_match(
                type='GPS_RAW_INT', blocking=True, timeout=1)
            if msg and msg.fix_type >= 3 and msg.satellites_visible >= min_sats:
                print(f"[FC] GPS OK (fix={msg.fix_type} "
                      f"sats={msg.satellites_visible})")
                break

        pos = self.get_position()
        if pos:
            self.home_lat = pos['lat']
            self.home_lon = pos['lon']
            print(f"[FC] Home: {self.home_lat:.7f}, {self.home_lon:.7f}")

    # ── Flight Mode ───────────────────────────────────────────────────────────

    def set_mode(self, mode: str, timeout=10):
        self.master.set_mode_apm(self.master.mode_mapping()[mode])
        t = time.time()
        while time.time() - t < timeout:
            self._do_tick()
            msg = self.master.recv_match(
                type='HEARTBEAT', blocking=True, timeout=1)
            if msg and mavutil.mode_string_v10(msg) == mode:
                print(f"[FC] Mode: {mode}")
                return True
            time.sleep(0.1)
        print(f"[FC] WARNING: mode {mode} not confirmed")
        return False

    # ── Arm / Takeoff ─────────────────────────────────────────────────────────

    def arm(self):
        print("[FC] Arming ...")
        self.master.arducopter_arm()
        for _ in range(40):
            self._do_tick()
            msg = self.master.recv_match(
                type='HEARTBEAT', blocking=True, timeout=1)
            if msg and (msg.base_mode
                        & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                print("[FC] Armed ✓")
                return True
            time.sleep(0.2)
        print("[FC] WARNING: arm not confirmed")
        return False

    def takeoff(self, alt):
        print(f"[FC] Takeoff → {alt}m")
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0,
            0, 0, 0, 0, 0, 0, alt)

    def arm_and_takeoff(self, alt):
        """GUIDED mode → arm → takeoff → wait for altitude."""
        self.set_mode('GUIDED')
        time.sleep(0.5)
        self.arm()
        self.takeoff(alt)
        ok = self.wait_for_alt(alt, tol=0.5, timeout=35)
        if ok:
            print(f"[FC] At {alt}m ✓")
        return ok

    def wait_for_alt(self, target_alt, tol=0.4, timeout=30):
        """Block until within tol metres of target altitude."""
        t = time.time()
        while time.time() - t < timeout:
            self._do_tick()
            pos = self.get_position()
            if pos and abs(pos['alt'] - target_alt) < tol:
                return True
            time.sleep(0.15)
        return False

    # ── Land / RTL ────────────────────────────────────────────────────────────

    def land(self):
        print("[FC] Landing ...")
        self.set_mode('LAND')
        for _ in range(120):
            self._do_tick()
            if not self.is_armed():
                print("[FC] Landed ✓")
                return
            time.sleep(0.5)

    def rtl(self):
        print("[FC] RTL")
        self.set_mode('RTL')

    # ── Navigation ────────────────────────────────────────────────────────────

    def goto(self, lat, lon, alt):
        """
        Non-blocking goto in GUIDED mode.
        Uses SET_POSITION_TARGET_GLOBAL_INT — the correct MAVLink command
        for position control in GUIDED. (mission_item_int is for AUTO mode.)
        """
        self.master.mav.set_position_target_global_int_send(
            0,  # time_boot_ms (not used)
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            # type_mask: use position only (ignore velocity/accel/yaw)
            0b0000111111111000,
            int(lat * 1e7),
            int(lon * 1e7),
            alt,
            0, 0, 0,   # vx, vy, vz
            0, 0, 0,   # afx, afy, afz
            0, 0       # yaw, yaw_rate
        )

    def goto_wait(self, lat, lon, alt, radius=1.5, timeout=30):
        """Goto and block until within radius horizontally and 0.5m vertically."""
        self.goto(lat, lon, alt)
        t = time.time()
        while time.time() - t < timeout:
            self._do_tick()
            pos = self.get_position()
            if pos:
                dist = self._gps_dist(pos['lat'], pos['lon'], lat, lon)
                dalt = abs(pos['alt'] - alt)
                if dist < radius and dalt < 0.6:
                    return True
            time.sleep(0.12)
        return False

    def goto_offset(self, north_m, east_m, alt):
        """Non-blocking goto offset from home."""
        lat, lon = self._offset_to_gps(north_m, east_m)
        self.goto(lat, lon, alt)

    def goto_offset_wait(self, north_m, east_m, alt, radius=1.5, timeout=30):
        """Blocking goto offset from home."""
        lat, lon = self._offset_to_gps(north_m, east_m)
        return self.goto_wait(lat, lon, alt, radius, timeout)

    def _offset_to_gps(self, north_m, east_m):
        cos_lat = math.cos(math.radians(self.home_lat))
        lat = self.home_lat + north_m / 111000.0
        lon = self.home_lon + east_m  / (111000.0 * cos_lat)
        return lat, lon

    # ── Velocity Commands ─────────────────────────────────────────────────────

    def set_velocity_ned(self, vn, ve, vd):
        """
        NED velocity command (m/s). Must be called at ≥ 5 Hz for continuous
        motion — ArduPilot stops after ~3s without refresh.
        vn=north, ve=east, vd=down (positive=downward).
        """
        self.master.mav.set_position_target_local_ned_send(
            0,
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            0b0000111111000111,   # velocity mask (ignore pos & accel)
            0, 0, 0,
            vn, ve, vd,
            0, 0, 0, 0, 0)

    def set_velocity_body(self, vx, vy, vz):
        """
        Body-frame velocity command (m/s).
        vx=forward (along heading), vy=right, vz=down.
        Used for banner approach (heading-relative movement).
        """
        self.master.mav.set_position_target_local_ned_send(
            0,
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_BODY_NED,
            0b0000111111000111,
            0, 0, 0,
            vx, vy, vz,
            0, 0, 0, 0, 0)

    def stop(self):
        """Zero velocity twice to brake."""
        self.set_velocity_ned(0, 0, 0)
        time.sleep(0.05)
        self.set_velocity_ned(0, 0, 0)

    # ── Attitude ──────────────────────────────────────────────────────────────

    def set_yaw(self, heading_deg, relative=False, rate_dps=25):
        """Yaw to absolute compass heading (or relative offset)."""
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW, 0,
            heading_deg, rate_dps, 1, 1 if relative else 0,
            0, 0, 0)

    # ── Telemetry ─────────────────────────────────────────────────────────────

    def get_position(self):
        msg = self.master.recv_match(
            type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
        if msg:
            return {
                'lat':     msg.lat / 1e7,
                'lon':     msg.lon / 1e7,
                'alt':     msg.relative_alt / 1000.0,
                'heading': msg.hdg / 100.0,
                'vn':      msg.vx / 100.0,
                've':      msg.vy / 100.0,
            }
        return None

    def is_armed(self):
        msg = self.master.recv_match(
            type='HEARTBEAT', blocking=True, timeout=1)
        return bool(
            msg and msg.base_mode
            & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _gps_dist(self, lat1, lon1, lat2, lon2):
        """Flat-earth horizontal distance in metres."""
        dn = (lat2 - lat1) * 111000.0
        de = (lon2 - lon1) * 111000.0 * math.cos(math.radians(lat1))
        return math.sqrt(dn * dn + de * de)

    def dist_to_home(self):
        pos = self.get_position()
        if not pos:
            return float('inf')
        return self._gps_dist(
            pos['lat'], pos['lon'], self.home_lat, self.home_lon)
