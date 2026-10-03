# ============================================================
# lidar_bridge.py — Gazebo LiDAR → MAVLink OBSTACLE_DISTANCE
#
# Subscribes to the Gazebo gpu_lidar topic, maps the 720-sample
# LaserScan to 72 × 5° bins, and sends OBSTACLE_DISTANCE to
# ArduPilot at 10 Hz in a daemon background thread.
#
# The bridge MUST stay running for the entire mission.
# ArduPilot's object avoidance (OA_TYPE=2, PRX_TYPE=2) depends on it.
#
# Angle convention:
#   Gazebo LaserScan: angle 0 = forward, positive = CCW (left)
#   ArduPilot OBSTACLE_DISTANCE: bin 0 = forward, increases CW (right)
#   Conversion: ap_angle = -(gz_angle_deg) mod 360
# ============================================================
import threading
import time
import math
import numpy as np

try:
    from gz.transport13 import Node
    from gz.msgs10 import laserscan_pb2
    HAS_GZ = True
except ImportError:
    try:
        from gz.transport12 import Node
        from gz.msgs9 import laserscan_pb2
        HAS_GZ = True
    except ImportError:
        HAS_GZ = False
        print("[LiDAR] gz.transport not available — bridge disabled")

NUM_BINS    = 72      # 72 bins × 5°/bin = 360°
BIN_DEG     = 5.0
UNKNOWN     = 65535   # ArduPilot "no data"
MIN_DIST_CM = 15      # 0.15m
MAX_DIST_CM = 1200    # 12.0m

LIDAR_TOPIC = (
    "/world/aerothon_mission/model/iris/model/iris_with_standoffs"
    "/link/base_link/sensor/lidar_360/scan"
)


class LidarBridge:
    """
    Background thread: reads Gazebo LaserScan, sends OBSTACLE_DISTANCE
    to ArduPilot at 10 Hz.

    Also exposes directional distance queries for corridor navigation:
        get_front_distance()  — forward 60° arc
        get_left_distance()   — left (north) 60° arc
        get_right_distance()  — right (south) 60° arc
    """

    def __init__(self, mavlink_master):
        self._master          = mavlink_master
        self._running         = False
        self._thread          = None
        self._distances       = [UNKNOWN] * NUM_BINS
        self._lock            = threading.Lock()
        self._scan_count      = 0
        self._last_send       = 0.0
        self._send_interval   = 0.1   # 10 Hz

    # ── Gazebo callback ───────────────────────────────────────────────────────

    def _lidar_callback(self, msg):
        try:
            ranges    = list(msg.ranges)
            n_samples = len(ranges)
            if n_samples == 0:
                return

            angle_min = msg.angle_min
            angle_inc = msg.angle_increment

            bin_min = {}
            for i, r in enumerate(ranges):
                if (r <= msg.range_min or r >= msg.range_max
                        or math.isinf(r) or math.isnan(r)):
                    continue

                gz_angle_rad = angle_min + i * angle_inc
                gz_angle_deg = math.degrees(gz_angle_rad)

                # Gazebo CCW positive → ArduPilot CW positive
                ap_angle_deg = (-gz_angle_deg) % 360.0
                bin_idx      = int(ap_angle_deg / BIN_DEG) % NUM_BINS

                d_cm = int(r * 100)
                d_cm = max(MIN_DIST_CM, min(MAX_DIST_CM, d_cm))

                if bin_idx not in bin_min or d_cm < bin_min[bin_idx]:
                    bin_min[bin_idx] = d_cm

            bins = [UNKNOWN] * NUM_BINS
            for idx, d in bin_min.items():
                bins[idx] = d

            with self._lock:
                self._distances  = bins
                self._scan_count += 1

        except Exception as e:
            print(f"[LiDAR] Callback error: {e}")

    # ── Send loop (background thread) ─────────────────────────────────────────

    def _send_loop(self):
        print("[LiDAR] Send loop started")
        while self._running:
            now = time.time()
            if now - self._last_send >= self._send_interval:
                with self._lock:
                    dists = list(self._distances)
                try:
                    self._master.mav.obstacle_distance_send(
                        int(time.time() * 1e6),   # time_usec
                        0,                         # sensor_type: LASER
                        dists,                     # distances[72] in cm
                        0,                         # increment_f (not used)
                        MIN_DIST_CM,
                        MAX_DIST_CM,
                        BIN_DEG,                   # increment deg/bin
                        0.0,                       # angle_offset (bin 0 = forward)
                    )
                except Exception as e:
                    print(f"[LiDAR] Send error: {e}")
                self._last_send = now
            time.sleep(0.01)
        print("[LiDAR] Send loop stopped")

    # ── Query API ─────────────────────────────────────────────────────────────

    def get_distances(self):
        """Return copy of 72-bin distances (cm). Thread-safe."""
        with self._lock:
            return list(self._distances)

    def get_min_distance_in_arc(self, center_deg, half_width_deg):
        """
        Minimum distance in an angular arc (ArduPilot convention: 0=fwd, CW).
        Returns metres, or inf if no data.
        """
        dists   = self.get_distances()
        n_bins  = int(half_width_deg / BIN_DEG)
        min_d   = float('inf')
        for offset in range(-n_bins, n_bins + 1):
            idx = (int(center_deg / BIN_DEG) + offset) % NUM_BINS
            d   = dists[idx]
            if d != UNKNOWN and d < min_d:
                min_d = d
        return (min_d / 100.0) if min_d < float('inf') else float('inf')

    def get_front_distance(self):
        """Min distance in forward ±30° arc. Returns metres."""
        return self.get_min_distance_in_arc(0, 30)

    def get_left_distance(self):
        """Min distance in left ±30° arc (270° = left). Returns metres."""
        return self.get_min_distance_in_arc(270, 30)

    def get_right_distance(self):
        """Min distance in right ±30° arc (90° = right). Returns metres."""
        return self.get_min_distance_in_arc(90, 30)

    @property
    def scan_count(self):
        with self._lock:
            return self._scan_count

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if not HAS_GZ:
            print("[LiDAR] gz.transport unavailable — bridge disabled")
            return

        print(f"[LiDAR] Subscribing: {LIDAR_TOPIC}")
        self._node = Node()
        self._node.subscribe(
            laserscan_pb2.LaserScan, LIDAR_TOPIC, self._lidar_callback)

        self._running = True
        self._thread  = threading.Thread(
            target=self._send_loop, daemon=True, name="lidar-bridge")
        self._thread.start()
        print("[LiDAR] Bridge active — OBSTACLE_DISTANCE at 10 Hz")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print(f"[LiDAR] Stopped ({self._scan_count} scans)")
