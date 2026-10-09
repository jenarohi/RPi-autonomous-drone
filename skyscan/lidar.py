"""Lidar data layer: the latest 2D scan, and the geometry the corridor stages need from it.

No simulator imports here. Scans come from the Gazebo bridge in the sim profile and from the real sensor driver on
the vehicle; everything downstream (the stages, the UI panel) only ever sees a ``LidarScan`` from a ``LidarHub``.

Frame: x forward, y LEFT, angles counter-clockwise from the nose (a point at +90 deg is on the left wall).
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass

import numpy as np

from skyscan.types import LidarScan


class LidarHub:
    """Latest scan, shared between the sensor thread (writer) and the mission / UI (readers)."""

    def __init__(self, window: int = 20) -> None:
        self._lock = threading.Lock()
        self._latest: LidarScan | None = None
        self._times: deque[float] = deque(maxlen=window)

    def put(self, scan: LidarScan) -> None:
        with self._lock:
            self._latest = scan
            self._times.append(scan.t)

    def latest(self) -> LidarScan | None:
        with self._lock:
            return self._latest

    def stats(self) -> dict:
        """``{"hz", "age_s", "n", "seq"}``: rate over the recent window (0 when stale), age of the last scan."""
        now = time.time()
        with self._lock:
            scan, times = self._latest, list(self._times)
        if scan is None:
            return {"hz": 0.0, "age_s": None, "n": 0, "seq": None}
        age = now - scan.t
        hz = 0.0
        if len(times) >= 2 and age < 3.0:
            span = times[-1] - times[0]
            hz = (len(times) - 1) / span if span > 0 else 0.0
        return {"hz": round(hz, 2), "age_s": round(age, 3), "n": len(scan.ranges), "seq": scan.seq}

    def fresh(self, max_age_s: float = 1.0) -> LidarScan | None:
        scan = self.latest()
        return scan if scan is not None and time.time() - scan.t <= max_age_s else None


# ───────────────────────────── geometry ─────────────────────────────

def points(scan: LidarScan) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Valid returns as ``(x_fwd, y_left, range, angle_deg)`` arrays (angle wrapped to -180..180]."""
    r = np.asarray(scan.ranges, dtype=float)
    ang = scan.angle_min_deg + np.arange(r.size) * scan.angle_step_deg
    ang = (ang + 180.0) % 360.0 - 180.0
    ok = np.isfinite(r) & (r >= scan.range_min) & (r <= scan.range_max)
    r, ang = r[ok], ang[ok]
    a = np.radians(ang)
    return r * np.cos(a), r * np.sin(a), r, ang


def sector_min(scan: LidarScan, a0_deg: float, a1_deg: float) -> float:
    """Closest return with angle in [a0, a1] degrees (a0 <= a1, both within -180..180). ``inf`` = clear."""
    _, _, r, ang = points(scan)
    sel = (ang >= a0_deg) & (ang <= a1_deg)
    return float(r[sel].min()) if sel.any() else math.inf


def nearest(scan: LidarScan) -> float:
    """Closest return in any direction (``inf`` when nothing is in range)."""
    _, _, r, _ = points(scan)
    return float(r.min()) if r.size else math.inf


@dataclass
class WallInfo:
    """What the side sectors say about the corridor walls (perpendicular distances, metres)."""
    left_m: float | None = None          # distance to the left wall, None = no wall seen on that side
    right_m: float | None = None
    n_left: int = 0                      # supporting returns
    n_right: int = 0
    turn_to_align_deg: float | None = None   # + = turn left (CCW) to point along the walls; None = not measurable

    @property
    def both(self) -> bool:
        return self.left_m is not None and self.right_m is not None

    @property
    def any(self) -> bool:
        return self.left_m is not None or self.right_m is not None

    @property
    def width_m(self) -> float | None:
        return (self.left_m + self.right_m) if self.both else None

    @property
    def offset_m(self) -> float | None:
        """Lateral offset from the centre line, + = the vehicle is to the LEFT of centre (right wall is farther)."""
        return (self.right_m - self.left_m) / 2.0 if self.both else None

    def to_dict(self) -> dict:
        return {"left_m": self.left_m, "right_m": self.right_m, "width_m": self.width_m,
                "offset_m": self.offset_m, "turn_to_align_deg": self.turn_to_align_deg}


def _side_wall(x: np.ndarray, y: np.ndarray, sign: float, max_wall_m: float, min_points: int,
               band_m: float) -> tuple[float | None, int, float | None]:
    """One side: (perpendicular distance, support, slope angle of the wall in the body frame)."""
    lat = sign * y
    sel = (lat > 0.2) & (lat < max_wall_m + band_m)
    if int(sel.sum()) < min_points:
        return None, 0, None
    xs, ls = x[sel], lat[sel]
    med = float(np.median(ls))
    keep = np.abs(ls - med) <= band_m               # drop the odd obstacle that sits in the side sector
    if int(keep.sum()) < min_points or med > max_wall_m:
        return None, 0, None
    xs, ls = xs[keep], ls[keep]
    dist = float(np.median(ls))
    slope = None
    if xs.size >= 6 and float(xs.max() - xs.min()) > 0.8:
        m = float(np.polyfit(xs, sign * ls, 1)[0])  # y = c + m x with y signed (left +)
        slope = math.degrees(math.atan(m))
    return dist, int(keep.sum()), slope


def wall_info(scan: LidarScan, side_from_deg: float = 45.0, side_to_deg: float = 135.0,
              max_wall_m: float = 3.2, min_points: int = 6, band_m: float = 0.35) -> WallInfo:
    """Perpendicular distance to a wall on each side, from the returns in the side sectors.

    A parallel wall at lateral distance d produces returns with y = +-d whatever their range, so the median of |y|
    over the sector is the wall distance, and the slope of y against x is the wall's angle relative to the nose.
    """
    x, y, _, ang = points(scan)
    left = (ang >= side_from_deg) & (ang <= side_to_deg)
    right = (ang <= -side_from_deg) & (ang >= -side_to_deg)
    ld, ln, ls = _side_wall(x[left], y[left], +1.0, max_wall_m, min_points, band_m)
    rd, rn, rs = _side_wall(x[right], y[right], -1.0, max_wall_m, min_points, band_m)
    slopes = [s for s in (ls, rs) if s is not None]
    turn = float(sum(slopes) / len(slopes)) if slopes else None
    return WallInfo(left_m=ld, right_m=rd, n_left=ln, n_right=rn, turn_to_align_deg=turn)


def free_distance(x: np.ndarray, y: np.ndarray, theta_deg: float, half_width_m: float, lookahead_m: float) -> float:
    """How far the vehicle (a strip ``2*half_width`` wide) can travel along bearing ``theta`` before hitting a return."""
    t = math.radians(theta_deg)
    ux, uy = math.cos(t), math.sin(t)
    s = x * ux + y * uy                              # distance along the path
    d = -x * uy + y * ux                             # distance across the path
    hit = (s > 0.0) & (s < lookahead_m) & (np.abs(d) < half_width_m)
    return float(s[hit].min()) if hit.any() else float(lookahead_m)
