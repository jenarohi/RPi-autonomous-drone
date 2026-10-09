"""Reactive corridor controller: wall centring + static-obstacle avoidance from one 2D lidar scan.

Pure function of the scan (no I/O): ``CorridorController.step(scan)`` returns the body-frame velocity to fly next.
The vehicle keeps its heading along the corridor axis; the controller only chooses *where to slide and how fast*.

Method (a small vector-field-histogram): for a fan of candidate bearings it measures how far the vehicle's
strip (drone width + margin) can travel before touching a lidar return, then picks the bearing with the most free
distance, biased towards the one that re-centres the vehicle between the walls. Speed falls off as the chosen
direction gets short, and drops to zero (BLOCKED) when every direction is shorter than the stop distance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from skyscan.lidar import WallInfo, free_distance, nearest, points, wall_info
from skyscan.types import LidarScan


@dataclass
class AvoidParams:
    cruise_mps: float = 0.6             # forward speed with a clear path
    max_lat_mps: float = 0.5            # limit on the sideways component
    half_width_m: float = 0.55          # strip half-width: drone half-span (~0.3) + margin
    lookahead_m: float = 3.5            # how far ahead obstacles are considered
    slow_dist_m: float = 2.2            # start slowing below this free distance
    stop_dist_m: float = 0.9            # no forward motion below this free distance
    k_center: float = 0.6               # (m/s) per metre of offset from the centre line
    wall_min_m: float = 0.8             # push away from a wall closer than this
    k_wall: float = 0.8                 # (m/s) per metre inside wall_min_m
    fan_deg: float = 65.0               # normal candidate bearings span +-fan
    side_deg: float = 90.0              # recovery: pure sideways bearings, allowed only when forward is blocked
    side_room_m: float = 0.7            # recovery strafe stops when the wall/obstacle beside is this close (body half-size + margin)
    side_mps: float = 0.3               # recovery strafe speed
    step_deg: float = 5.0
    turn_penalty: float = 0.30          # score cost of bearing away from the centring bias, per fan width
    smooth: float = 0.5                 # 0 = no smoothing of the chosen bearing, towards 1 = sluggish
    max_wall_m: float = 3.2             # side returns farther than this are not the corridor wall

    @classmethod
    def from_cfg(cls, cfg: Any) -> "AvoidParams":
        base = cls()
        for f in base.__dataclass_fields__:
            if cfg is not None and hasattr(cfg, "get") and cfg.get(f) is not None:
                setattr(base, f, float(cfg.get(f)))
        return base


@dataclass
class NavCmd:
    vx: float = 0.0                     # m/s forward
    vy: float = 0.0                     # m/s to the RIGHT
    mode: str = "HOLD"                  # CRUISE | CENTER | AVOID | BLOCKED | HOLD
    theta_deg: float = 0.0              # chosen bearing, + = left
    free_m: float = 0.0                 # free distance along the chosen bearing
    nearest_m: float = math.inf         # closest return in any direction
    walls: WallInfo | None = None

    def to_dict(self) -> dict:
        return {"mode": self.mode, "vx": round(self.vx, 2), "vy": round(self.vy, 2),
                "theta_deg": round(self.theta_deg, 1), "free_m": round(self.free_m, 2)}


class CorridorController:
    def __init__(self, params: AvoidParams | None = None) -> None:
        self.p = params or AvoidParams()
        self._theta = 0.0

    def reset(self) -> None:
        self._theta = 0.0

    def step(self, scan: LidarScan, speed_scale: float = 1.0) -> NavCmd:
        p = self.p
        x, y, _, _ = points(scan)
        walls = wall_info(scan, max_wall_m=p.max_wall_m)
        near = nearest(scan)

        # lateral push from centring between the walls (or away from the one wall that is too close)
        v_left = 0.0                                  # + = move LEFT
        if walls.both:
            v_left = p.k_center * walls.offset_m * -1.0   # offset + means we are left of centre -> move right
        if walls.left_m is not None and walls.left_m < p.wall_min_m:
            v_left -= p.k_wall * (p.wall_min_m - walls.left_m)
        if walls.right_m is not None and walls.right_m < p.wall_min_m:
            v_left += p.k_wall * (p.wall_min_m - walls.right_m)
        v_left = max(-p.max_lat_mps, min(p.max_lat_mps, v_left))
        bias = math.degrees(math.atan2(v_left, max(0.1, p.cruise_mps)))

        # candidate bearings and how far each is free. Forward fan first; the sideways recovery bearings join in only
        # when nothing in the forward fan has room (so the vehicle can strafe round the end of an obstacle but never
        # drifts sideways for no reason)
        def best_in(lo_deg: float, hi_deg: float) -> tuple[float, float, float]:
            bt, bs, bf = 0.0, -1e9, 0.0
            k0, k1 = int(round(lo_deg / p.step_deg)), int(round(hi_deg / p.step_deg))
            for k in range(k0, k1 + 1):
                th = k * p.step_deg
                free = free_distance(x, y, th, p.half_width_m, p.lookahead_m)
                score = free / p.lookahead_m - p.turn_penalty * abs(th - bias) / p.fan_deg
                if score > bs + 1e-9:
                    bt, bs, bf = th, score, free
            return bt, bs, bf

        best_theta, best_score, best_free = best_in(-p.fan_deg, p.fan_deg)
        recovering = False
        if best_free < p.stop_dist_m + 0.3:
            for lo, hi in ((-p.side_deg, -p.fan_deg - p.step_deg), (p.fan_deg + p.step_deg, p.side_deg)):
                th, sc, fr = best_in(lo, hi)
                if fr > p.side_room_m and fr > best_free:
                    best_theta, best_score, best_free = th, sc, fr
                    recovering = True
        self._theta = p.smooth * self._theta + (1.0 - p.smooth) * best_theta
        theta = self._theta

        # speed from the free distance along the bearing we are actually going to fly
        free_now = free_distance(x, y, theta, p.half_width_m, p.lookahead_m)
        scale = max(0.0, min(1.0, speed_scale))
        if recovering and abs(theta) > p.fan_deg:     # strafing round the end of an obstacle: steady slow slide
            speed = p.side_mps * scale
        else:
            k_speed = (free_now - p.stop_dist_m) / max(0.1, p.slow_dist_m - p.stop_dist_m)
            speed = p.cruise_mps * max(0.0, min(1.0, k_speed)) * scale
            if best_free < p.stop_dist_m and free_now < p.stop_dist_m:
                return NavCmd(0.0, 0.0, "BLOCKED", theta, free_now, near, walls)
            if speed < 0.06:                          # creeping is not progress: hold, and say so
                return NavCmd(0.0, 0.0, "BLOCKED", theta, free_now, near, walls)

        vx = speed * math.cos(math.radians(theta))
        vy_left = speed * math.sin(math.radians(theta))
        # centring still applies when the best path is straight ahead but speed is low
        if abs(theta) < 1.0 and walls.both:
            vy_left += v_left * (0.5 if speed > 0 else 0.0)
        vy_left = max(-p.max_lat_mps, min(p.max_lat_mps, vy_left))
        mode = "AVOID" if abs(theta - bias) > 12.0 or free_now < p.slow_dist_m else ("CENTER" if abs(v_left) > 0.08 else "CRUISE")
        return NavCmd(vx, -vy_left, mode, theta, free_now, near, walls)
