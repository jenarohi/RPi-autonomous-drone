"""
LiDAR corridor planner (pure functions - unit tested offline).

Frames
  body     : x forward, y left (as published by the gpu_lidar on base_link)
  corridor : a = along the corridor travel direction, l = left of it,
             origin at the drone. Same as body when the drone is perfectly
             yawed to the corridor heading.

Idea: every LiDAR point inside a look-ahead band blocks a lateral interval
[l - r, l + r] (r = drone radius + margin). The free lateral intervals of the
nearest band (beside the drone) are narrowed with the next bands as long as
something stays free, and we steer to the middle of what is left. Walls and
obstacles are treated the same way, so the same code centres the drone in an
empty corridor and slaloms through the obstacle corridor.
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from . import config as C

Interval = Tuple[float, float]


def scan_to_points(ranges, angle_min: float, angle_step: float,
                   rmin: float = C.LIDAR_MIN_RANGE, rmax: float = C.LIDAR_MAX_RANGE) -> np.ndarray:
    r = np.asarray(ranges, dtype=float)
    ang = angle_min + angle_step * np.arange(r.size)
    ok = np.isfinite(r) & (r >= rmin) & (r <= rmax)
    r, ang = r[ok], ang[ok]
    return np.column_stack((r * np.cos(ang), r * np.sin(ang)))


def to_corridor_frame(points: np.ndarray, heading_error: float) -> np.ndarray:
    """heading_error = drone heading - corridor heading (rad)."""
    if points.size == 0:
        return points.reshape(0, 2)
    c, s = math.cos(heading_error), math.sin(heading_error)
    x, y = points[:, 0], points[:, 1]
    return np.column_stack((x * c - y * s, x * s + y * c))


def free_intervals(pts: np.ndarray, a_lo: float, a_hi: float,
                   inflate: float, span: float) -> List[Interval]:
    sel = pts[(pts[:, 0] >= a_lo) & (pts[:, 0] <= a_hi)] if pts.size else pts
    blocked = sorted((l - inflate, l + inflate) for l in (sel[:, 1] if sel.size else []))
    free, cur = [], -span
    for lo, hi in blocked:
        if lo > cur:
            free.append((cur, min(lo, span)))
        cur = max(cur, hi)
        if cur >= span:
            break
    if cur < span:
        free.append((cur, span))
    return [(lo, hi) for lo, hi in free if hi > lo]


def intersect(a: List[Interval], b: List[Interval]) -> List[Interval]:
    out = []
    for lo1, hi1 in a:
        for lo2, hi2 in b:
            lo, hi = max(lo1, lo2), min(hi1, hi2)
            if hi > lo:
                out.append((lo, hi))
    return out


def pick(intervals: List[Interval], ref: float = 0.0) -> Interval:
    """The interval containing ref, otherwise the closest one."""
    def gap(iv):
        lo, hi = iv
        return 0.0 if lo <= ref <= hi else min(abs(lo - ref), abs(hi - ref))
    return min(intervals, key=gap)


@dataclass
class Step:
    target: float            # lateral set-point relative to the drone (m, left +)
    clear: float             # free distance straight ahead in our swept band (m)
    interval: Interval       # chosen free interval
    walls: Tuple[Optional[float], Optional[float]]   # nearest left / right return beside us


def plan_step(pts: np.ndarray,
              windows=C.CORRIDOR_WINDOWS,
              inflate: float = C.DRONE_RADIUS + C.SAFETY_MARGIN,
              span: float = C.CORRIDOR_SPAN) -> Optional[Step]:
    """pts in the corridor frame. None = no free lateral position beside us."""
    free = free_intervals(pts, windows[0][0], windows[0][1], inflate, span)
    if not free:
        return None
    chosen = pick(free)
    for a_lo, a_hi in windows[1:]:
        narrowed = [iv for iv in intersect([chosen], free_intervals(pts, a_lo, a_hi, inflate, span))
                    if iv[1] - iv[0] >= 0.02]
        if not narrowed:
            break                      # can't satisfy this band yet - deal with it when closer
        chosen = pick(narrowed)

    lo, hi = chosen
    lo_open, hi_open = lo <= -span + 1e-6, hi >= span - 1e-6
    if lo_open and hi_open:
        target = 0.0
    elif hi_open:                      # only something on the right: keep clear of it
        target = max(0.0, min(lo + 0.3, hi))
    elif lo_open:
        target = min(0.0, max(hi - 0.3, lo))
    else:
        target = (lo + hi) / 2.0

    if pts.size:
        band = pts[(pts[:, 0] > 0.0) & (np.abs(pts[:, 1]) < inflate)]
        clear = float(band[:, 0].min()) if band.size else math.inf
        side = pts[np.abs(pts[:, 0]) < 0.5]
        left = side[side[:, 1] > 0][:, 1]
        right = side[side[:, 1] < 0][:, 1]
        walls = (float(left.min()) if left.size else None,
                 float(-right.max()) if right.size else None)
    else:
        clear, walls = math.inf, (None, None)
    return Step(target, clear, chosen, walls)


def forward_speed(step: Step, vmax: float = C.CORRIDOR_SPEED,
                  stop: float = C.CORRIDOR_STOP_DIST, k: float = C.CORRIDOR_K_FWD) -> float:
    """Slow down for obstacles in our path and while side-stepping."""
    v = min(vmax, max(0.0, k * (step.clear - stop)))
    return v * max(0.2, 1.0 - abs(step.target) / 0.8)


def wall_angle(pts: np.ndarray, a_lo: float = -1.5, a_hi: float = 3.0,
               l_lo: float = 0.4, l_hi: float = C.WALL_DIST, max_resid: float = 0.12) -> Optional[float]:
    """Direction of the corridor walls relative to the x axis of `pts` (rad, CCW +).
    A straight line is fitted to the returns on each side; a side is ignored when
    it is not one clean straight wall (obstacle beside us, wall end, too few points).
    None when neither side qualifies."""
    angles = []
    for sign in (1.0, -1.0):
        if pts.size == 0:
            break
        side = pts[(pts[:, 0] >= a_lo) & (pts[:, 0] <= a_hi) &
                   (sign * pts[:, 1] >= l_lo) & (sign * pts[:, 1] <= l_hi)]
        if len(side) < 15:
            continue
        m, c = np.polyfit(side[:, 0], side[:, 1], 1)
        if np.abs(side[:, 1] - (m * side[:, 0] + c)).max() > max_resid:
            continue
        angles.append(math.atan(m))
    return float(np.mean(angles)) if angles else None


def walls_both_sides(step: Optional[Step], dist: float = C.WALL_DIST) -> bool:
    return bool(step and step.walls[0] is not None and step.walls[1] is not None
                and step.walls[0] < dist and step.walls[1] < dist)


def walls_none(step: Optional[Step], dist: float = C.WALL_DIST) -> bool:
    return bool(step) and all(w is None or w >= dist for w in step.walls)
