"""Frames, angles and the pinhole camera model (docs/ARCHITECTURE.md §3).

Frames
  NED     ArduPilot LOCAL_POSITION_NED: x north, y east, z down. Origin = EKF origin (NOT home).
  course  A1-anchored mission frame: (fwd, right, up) from the A1 start point / start heading.
  level   vehicle-centred, heading-aligned, gravity-levelled: (fwd, right, down).
  gz      Gazebo world ENU: x east, y north, z up.       n = y, e = x, d = -z
  camera  OpenCV optical: x right, y down (image rows), z along the optical axis.
Headings are degrees clockwise from north. Public functions take/return degrees.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

# ───────────────────────────── angles ─────────────────────────────


def wrap180(deg: float) -> float:
    """Wrap to [-180, 180)."""
    return (deg + 180.0) % 360.0 - 180.0


def wrap360(deg: float) -> float:
    """Wrap to [0, 360)."""
    return deg % 360.0


def ang_diff(a_deg: float, b_deg: float) -> float:
    """Signed smallest difference a − b in [-180, 180). Positive = a is clockwise of b."""
    return wrap180(a_deg - b_deg)


def heading_vec(heading_deg: float) -> tuple[float, float]:
    """Unit horizontal vector (north, east) for a heading."""
    r = math.radians(heading_deg)
    return math.cos(r), math.sin(r)


def heading_of(dn: float, de: float) -> float:
    """Heading (0..360) of a horizontal NED vector."""
    return wrap360(math.degrees(math.atan2(de, dn)))


# ───────────────────────────── Gazebo ↔ NED ─────────────────────────────


def gz_to_ned(x: float, y: float, z: float) -> tuple[float, float, float]:
    return y, x, -z


def ned_to_gz(n: float, e: float, d: float) -> tuple[float, float, float]:
    return e, n, -d


def gz_yaw_to_heading_deg(yaw_rad: float) -> float:
    """Gazebo yaw (CCW from +x/east) → heading (CW from north)."""
    return wrap360(90.0 - math.degrees(yaw_rad))


def heading_deg_to_gz_yaw(heading_deg: float) -> float:
    return math.radians(wrap180(90.0 - heading_deg))


# ───────────────────────────── vehicle-relative ─────────────────────────────


def level_to_ned(pos_ned: Sequence[float], heading_deg: float,
                 fwd: float, right: float, down: float = 0.0) -> tuple[float, float, float]:
    """Point given relative to the vehicle in its level frame → absolute NED."""
    c, s = heading_vec(heading_deg)
    return (pos_ned[0] + fwd * c - right * s,
            pos_ned[1] + fwd * s + right * c,
            pos_ned[2] + down)


def ned_to_level(pos_ned: Sequence[float], heading_deg: float,
                 n: float, e: float, d: float) -> tuple[float, float, float]:
    """Absolute NED point → (fwd, right, down) relative to the vehicle."""
    c, s = heading_vec(heading_deg)
    dn, de = n - pos_ned[0], e - pos_ned[1]
    return dn * c + de * s, -dn * s + de * c, d - pos_ned[2]


@dataclass(frozen=True)
class CourseFrame:
    """Mission frame anchored at the A1 start: origin (NED) and start heading."""
    origin_ned: tuple[float, float, float]
    heading_deg: float

    def to_course(self, n: float, e: float, d: float) -> tuple[float, float, float]:
        """NED → (fwd, right, up)."""
        fwd, right, down = ned_to_level(self.origin_ned, self.heading_deg, n, e, d)
        return fwd, right, -down

    def to_ned(self, fwd: float, right: float, up: float) -> tuple[float, float, float]:
        """(fwd, right, up) → NED."""
        return level_to_ned(self.origin_ned, self.heading_deg, fwd, right, -up)

    def rel_heading(self, heading_deg: float) -> float:
        """Absolute heading → relative to course fwd (+ = clockwise/right), [-180, 180)."""
        return ang_diff(heading_deg, self.heading_deg)

    def abs_heading(self, rel_deg: float) -> float:
        return wrap360(self.heading_deg + rel_deg)

    def dir_to_ned(self, fwd: float, right: float) -> tuple[float, float]:
        """Rotate a horizontal course-frame vector into (north, east)."""
        n, e, _ = level_to_ned((0.0, 0.0, 0.0), self.heading_deg, fwd, right)
        return n, e

    def to_dict(self) -> dict:
        return {"ned": list(self.origin_ned), "heading_deg": self.heading_deg}

    @classmethod
    def from_dict(cls, d: dict) -> "CourseFrame":
        return cls(tuple(float(v) for v in d["ned"]), float(d["heading_deg"]))  # type: ignore[arg-type]


# ───────────────────────────── cameras ─────────────────────────────


@dataclass(frozen=True)
class CameraModel:
    """Ideal pinhole camera (square pixels, no distortion — matches Gazebo cameras)."""
    w: int
    h: int
    fx: float
    fy: float
    cx: float
    cy: float

    @classmethod
    def from_hfov(cls, w: int, h: int, hfov_deg: float) -> "CameraModel":
        fx = (w / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        return cls(int(w), int(h), fx, fx, w / 2.0, h / 2.0)

    @property
    def hfov_deg(self) -> float:
        return math.degrees(2.0 * math.atan(self.w / (2.0 * self.fx)))

    @property
    def vfov_deg(self) -> float:
        return math.degrees(2.0 * math.atan(self.h / (2.0 * self.fy)))

    def K(self) -> np.ndarray:
        return np.array([[self.fx, 0.0, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]])

    def scaled(self, w: int, h: int) -> "CameraModel":
        sx, sy = w / self.w, h / self.h
        return CameraModel(int(w), int(h), self.fx * sx, self.fy * sy, self.cx * sx, self.cy * sy)

    def normalized(self, u: float, v: float) -> tuple[float, float]:
        return (u - self.cx) / self.fx, (v - self.cy) / self.fy

    def project(self, p_cam: Sequence[float]) -> tuple[float, float] | None:
        """Camera-frame point → pixel (None if behind the camera)."""
        x, y, z = p_cam
        if z <= 1e-9:
            return None
        return self.fx * x / z + self.cx, self.fy * y / z + self.cy


def _rx(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def _ry(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


#: body_down camera axes expressed in the body frame (x fwd, y right, z down):
#: image right → body right, image down → body backward, optical axis → body down.
_BODY_DOWN = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])


def cam_to_level(mount: str, cam_pitch_deg: float = -90.0,
                 roll_deg: float = 0.0, pitch_deg: float = 0.0) -> np.ndarray:
    """Rotation matrix taking camera-optical vectors into the level frame (fwd, right, down).

    mount="body_down": fixed to the airframe looking straight down, image top = nose; the vehicle's
                       roll/pitch (deg, aerospace convention) tilt it.
    mount="gimbal":    earth-stabilised; optical axis pitched ``cam_pitch_deg`` (0 = horizon,
                       −90 = nadir), image top towards fwd/up; vehicle roll/pitch are compensated.
    """
    if mount == "body_down":
        return _ry(pitch_deg) @ _rx(roll_deg) @ _BODY_DOWN
    if mount == "gimbal":
        p = math.radians(cam_pitch_deg)
        sp, cp = math.sin(p), math.cos(p)
        # columns: image-right, image-down, optical axis — in (fwd, right, down)
        return np.array([[0.0, sp, cp], [1.0, 0.0, 0.0], [0.0, cp, -sp]])
    raise ValueError(f"unknown camera mount {mount!r}")


def pixel_ray(cam: CameraModel, u: float, v: float, R_cam_to_level: np.ndarray) -> np.ndarray:
    """Unit ray (fwd, right, down) through pixel (u, v)."""
    x, y = cam.normalized(u, v)
    r = R_cam_to_level @ np.array([x, y, 1.0])
    return r / np.linalg.norm(r)


def ray_angles(ray_level: Sequence[float]) -> tuple[float, float]:
    """(bearing_deg, elevation_deg) of a level-frame ray: bearing + = right of heading,
    elevation + = above the horizon."""
    f, r, d = ray_level
    return math.degrees(math.atan2(r, f)), math.degrees(math.atan2(-d, math.hypot(f, r)))


def ground_point(ray_level: Sequence[float], height_m: float) -> tuple[float, float] | None:
    """Intersect a level-frame ray from a camera ``height_m`` above flat ground → (fwd, right)."""
    f, r, d = ray_level
    if d <= 1e-6 or height_m <= 0:
        return None
    t = height_m / d
    return f * t, r * t


def ground_offset_from_pixel(cam: CameraModel, u: float, v: float, height_m: float, mount: str = "body_down",
                             cam_pitch_deg: float = -90.0, roll_deg: float = 0.0,
                             pitch_deg: float = 0.0) -> tuple[float, float] | None:
    """Where a pixel lands on flat ground relative to the vehicle, in its level frame (fwd, right)."""
    R = cam_to_level(mount, cam_pitch_deg, roll_deg, pitch_deg)
    return ground_point(pixel_ray(cam, u, v, R), height_m)
