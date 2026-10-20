"""
Gazebo sensors over gz-transport: down camera, 45-deg front camera, 2-D LiDAR.

Only this file knows about Gazebo. On the real drone, replace it with a
class offering the same frame() / scan() methods (USB camera + RPLidar).
"""
import threading
import time
from collections import deque
from typing import Optional, Tuple

import cv2
import numpy as np
from gz.msgs10.image_pb2 import Image
from gz.msgs10.laserscan_pb2 import LaserScan
from gz.transport13 import Node

from . import config as C
from .lidar import scan_to_points


def find_topic(node: Node, sensor: str, suffix: str, timeout: float = 15.0) -> Optional[str]:
    """Topic of the form .../sensor/<sensor>/<suffix> (exact path varies with model nesting)."""
    want = f"/sensor/{sensor}/{suffix}"
    t_end = time.monotonic() + timeout
    while time.monotonic() < t_end:
        hits = [t for t in node.topic_list() if t.endswith(want)]
        if hits:
            return sorted(hits, key=lambda t: (C.WORLD_NAME not in t, len(t)))[0]
        time.sleep(0.5)
    return None


class GzSensors:
    def __init__(self, log):
        self.log = log
        self.node = Node()
        self._lock = threading.Lock()
        self._img = {"down": None, "front": None}       # latest Image message per camera
        self._img_t = {"down": 0.0, "front": 0.0}
        self._img_seq = {"down": 0, "front": 0}
        self._img_q = {"down": deque(maxlen=60), "front": deque(maxlen=60)}   # (arrival, msg, seq): latency injection
        self._scan: Optional[LaserScan] = None
        self._scan_t = 0.0
        self._scan_seq = 0

    def start(self, timeout: float = 15.0):
        down = find_topic(self.node, C.CAM_SENSOR, "image", timeout)
        front = find_topic(self.node, C.FRONT_CAM_SENSOR, "image", timeout)
        lid = find_topic(self.node, C.LIDAR_SENSOR, "scan", timeout)
        if not down or not front or not lid:
            raise RuntimeError(f"sensor topics not found (down={down}, front={front}, lidar={lid}) "
                               "- is Gazebo running, and does the model have the front camera?")
        self.node.subscribe(Image, down, lambda m: self._on_image("down", m))
        self.node.subscribe(Image, front, lambda m: self._on_image("front", m))
        self.node.subscribe(LaserScan, lid, self._on_scan)
        self.log("SENSORS", f"down cam  {down}")
        self.log("SENSORS", f"front cam {front}")
        self.log("SENSORS", f"lidar     {lid}")
        t_end = time.monotonic() + timeout
        while time.monotonic() < t_end and (None in self._img.values() or self._scan is None):
            time.sleep(0.1)
        if None in self._img.values() or self._scan is None:
            raise RuntimeError("subscribed, but camera/lidar data is not arriving")

    def _on_image(self, which: str, msg: Image):
        with self._lock:
            self._img[which], self._img_t[which] = msg, time.monotonic()
            self._img_seq[which] += 1
            self._img_q[which].append((self._img_t[which], msg, self._img_seq[which]))

    def _on_scan(self, msg: LaserScan):
        with self._lock:
            self._scan, self._scan_t = msg, time.monotonic()
            self._scan_seq += 1

    def frame(self, which: str = "down") -> Tuple[Optional[np.ndarray], float, int]:
        """(BGR image, arrival time, sequence number) of camera "down" or "front"."""
        with self._lock:
            msg, t, seq = self._img[which], self._img_t[which], self._img_seq[which]
            L = C.SIM_CAM_LATENCY_S
            if L > 0.0:                       # simulator: hand out the newest frame that is at least L old
                ok = [x for x in self._img_q[which] if x[0] <= time.monotonic() - L]
                if not ok:
                    return None, 0.0, 0
                t, msg, seq = ok[-1]
                t = t + L                     # time it becomes available (exposure time + latency)
        if msg is None:
            return None, 0.0, 0
        a = np.frombuffer(msg.data, np.uint8)
        ch = a.size // (msg.height * msg.width)
        a = a.reshape(msg.height, msg.width, ch)
        return cv2.cvtColor(a, cv2.COLOR_RGB2BGR if ch == 3 else cv2.COLOR_RGBA2BGR), t, seq

    def scan(self) -> Tuple[np.ndarray, float, int]:
        """(Nx2 points in body frame x fwd / y left, arrival time, sequence number)."""
        with self._lock:
            msg, t, seq = self._scan, self._scan_t, self._scan_seq
        if msg is None:
            return np.zeros((0, 2)), 0.0, 0
        return scan_to_points(msg.ranges, msg.angle_min, msg.angle_step), t, seq

    def ages(self) -> Tuple[float, float, float]:
        now = time.monotonic()
        return now - self._img_t["down"], now - self._img_t["front"], now - self._scan_t
