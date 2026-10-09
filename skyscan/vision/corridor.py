"""Green / orange corridor detector (front camera): where is the corridor entrance relative to the vehicle?

In the SkyScan world the "green banner" the mission aligns on is the green corridor itself: a 3.5 m x 10 m green floor
between two grey walls (legacy/create_world.py). Seen from 5 m up the floor is a small green trapezoid. Because the
floor lies on the ground, every pixel of its outline can be projected onto the ground plane (camera height + gimbal
pitch known), which turns the trapezoid back into the true rectangle and gives, in the vehicle's level frame:

    distance_m   along-corridor distance to the entrance line
    lateral_m    corridor centre line, + = to the vehicle's right
    yaw_err_deg  corridor axis heading minus vehicle heading, + = turn right
    width_m      measured width (sanity check: must be ~3.5 m)

The detection is returned as a ``BannerDetection`` with ``kind="floor"`` so the rest of the system (UI, A4) is unchanged.

The return lap uses the same geometry on the orange corridor (legacy world: floor rgb 0.95 0.55 0.05): ``set_colour``
swaps the colour range, nothing else changes.
"""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from skyscan.geo import CameraModel, cam_to_level, ground_point, pixel_ray
from skyscan.types import BannerDetection, Frame
from skyscan.utils.logger import get_logger

log = get_logger("VISION/CORRIDOR")


def _line_dir(pts: np.ndarray) -> np.ndarray:
    """Unit direction (pointing to +fwd) of the robust line through 2D points."""
    vx, vy, _, _ = cv2.fitLine(pts.astype(np.float32), cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    d = np.array([vx, vy], dtype=float)
    if d[0] < 0:
        d = -d
    return d / (np.linalg.norm(d) + 1e-12)


class CorridorDetector:
    """Detects the green corridor floor and measures the corridor pose relative to the vehicle."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.ranges = {
            "green": (np.array(getattr(cfg, "hsv_lo", [40, 80, 30]), dtype=np.uint8),
                      np.array(getattr(cfg, "hsv_hi", [85, 255, 255]), dtype=np.uint8)),
            # OpenCV hue 9..26 is orange; the red zones (hue < 8 or > 172) and the green floor stay outside it
            "orange": (np.array(getattr(cfg, "orange_hsv_lo", [9, 100, 80]), dtype=np.uint8),
                       np.array(getattr(cfg, "orange_hsv_hi", [26, 255, 255]), dtype=np.uint8)),
        }
        self.colour = "green"
        self.hsv_lo, self.hsv_hi = self.ranges["green"]
        self.width_m = float(getattr(cfg, "corridor_width_m", 3.5))
        self.width_tol_m = float(getattr(cfg, "width_tol_m", 0.6))
        self.min_area_px = int(getattr(cfg, "min_area_px", 250))
        self.edge_margin_px = int(getattr(cfg, "edge_margin_px", 3))
        self.max_ground_m = float(getattr(cfg, "max_ground_m", 60.0))

    def set_colour(self, name: str) -> bool:
        """Look for the ``green`` (forward lap) or ``orange`` (return lap) corridor. False for an unknown colour."""
        if name not in self.ranges:
            return False
        self.colour = name
        self.hsv_lo, self.hsv_hi = self.ranges[name]
        return True

    # ── helpers ───────────────────────────────────────────────────────────────────────────────────────────────
    def _ground_points(self, pix: np.ndarray, cam: CameraModel, R: np.ndarray, height_m: float) -> np.ndarray:
        out = []
        for u, v in pix:
            g = ground_point(pixel_ray(cam, float(u), float(v), R), height_m)
            if g is not None and math.hypot(*g) <= self.max_ground_m:
                out.append(g)
        return np.array(out, dtype=float).reshape(-1, 2)

    @staticmethod
    def _to_pixel(p_ground: tuple[float, float], cam: CameraModel, R: np.ndarray, height_m: float) -> list[float] | None:
        """Ground point (fwd, right) -> pixel."""
        p_cam = R.T @ np.array([p_ground[0], p_ground[1], height_m])
        uv = cam.project(p_cam)
        return None if uv is None else [float(uv[0]), float(uv[1])]

    def _edge_axis(self, cnt: np.ndarray, cam: CameraModel, R: np.ndarray, height_m: float, w: int, h: int,
                   a0: np.ndarray) -> np.ndarray | None:
        """Corridor axis from the straight edges of the floor outline, or None when they do not agree.

        Seen from above, the walls (and the obstacles inside the corridor) hide part of the floor. Every edge of what
        stays visible is then one of: parallel to the axis (wall bases, shadows of wall / obstacle tops), perpendicular
        to it (entrance, obstacle shadow ends), or radial: the shadow of a vertical wall / obstacle edge, a ground line
        through the camera's own ground point. Radial edges say nothing about the axis but they bend a long-edge fit
        (19 deg on the return lap from a 3.6 m lateral offset), so drop them and take the dominant direction of the
        rest modulo 90 deg (the strongest direction, so a stray edge cannot drag it); ``a0`` (the long-edge estimate)
        picks which of the two directions is the axis.
        """
        poly = cv2.approxPolyDP(cnt, 1.5, True).reshape(-1, 2).astype(float) + 0.5
        if len(poly) < 3:
            return None
        m = self.edge_margin_px
        on_border = lambda p: p[0] <= m or p[0] >= w - m or p[1] <= m or p[1] >= h - m   # noqa: E731
        phis, wgts = [], []                                      # edge direction modulo 90 deg, weight (m of edge)
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            if on_border(p) or on_border(q):                     # the image frame, not the corridor
                continue
            gp = ground_point(pixel_ray(cam, float(p[0]), float(p[1]), R), height_m)
            gq = ground_point(pixel_ray(cam, float(q[0]), float(q[1]), R), height_m)
            if gp is None or gq is None:
                continue
            d = np.array(gq, dtype=float) - np.array(gp, dtype=float)
            mid = 0.5 * (np.array(gp, dtype=float) + np.array(gq, dtype=float))
            length, rng = float(np.linalg.norm(d)), float(np.linalg.norm(mid))
            if length < 0.4 or rng < 1e-6:
                continue
            off_radial = math.degrees(math.asin(min(1.0, abs(d[0] * mid[1] - d[1] * mid[0]) / (length * rng))))
            wgt = length * min(1.0, max(0.0, (off_radial - 3.0) / 4.0))   # radial (< 3 deg) counts 0, > 7 deg fully
            if wgt <= 0.0:
                continue
            phis.append(math.degrees(math.atan2(d[1], d[0])) % 90.0)
            wgts.append(wgt)
        if sum(wgts) < 1.5:
            return None
        phis_a, wgts_a = np.array(phis), np.array(wgts)
        diff = lambda th: (phis_a - th + 45.0) % 90.0 - 45.0                  # noqa: E731  signed, modulo 90 deg
        grid = np.arange(0.0, 90.0, 0.5)
        score = [float(np.sum(wgts_a * np.exp(-0.5 * (diff(th) / 4.0) ** 2))) for th in grid]
        peak = float(grid[int(np.argmax(score))])
        near = np.abs(diff(peak)) <= 7.0
        if wgts_a[near].sum() < 1.5:                             # too little straight edge agrees on one direction
            return None
        base = math.radians(peak + float(np.sum(wgts_a[near] * diff(peak)[near]) / wgts_a[near].sum()))
        ang0 = math.atan2(a0[1], a0[0])
        best = min((base + k * math.pi / 2.0 for k in range(-4, 5)),
                   key=lambda x: abs(math.atan2(math.sin(x - ang0), math.cos(x - ang0))))
        a = np.array([math.cos(best), math.sin(best)])
        return -a if a[0] < 0 else a

    @staticmethod
    def _fail(frame: Frame, reason: str) -> BannerDetection:
        return BannerDetection(t=frame.t, cam=frame.cam, seq=frame.seq, found=False, reason=reason, kind="floor")

    # ── main ──────────────────────────────────────────────────────────────────────────────────────────────────
    def detect(self, frame: Frame, camera_model: CameraModel, gimbal_pitch_deg: float = 0.0,
               height_m: float | None = None) -> BannerDetection:
        img = frame.img
        if img is None:
            return self._fail(frame, "no image")
        if height_m is None or height_m < 0.3:
            return self._fail(frame, "camera height unknown or too low")

        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lo, self.hsv_hi)
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts:
            return self._fail(frame, f"no {self.colour} in view")
        cnt = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        if area < self.min_area_px:
            return self._fail(frame, f"{self.colour} blob too small ({area:.0f} px)")

        pix = cnt.reshape(-1, 2).astype(float) + 0.5
        m = self.edge_margin_px
        x0, y0, bw, bh = cv2.boundingRect(cnt)
        near_clipped = (y0 + bh) >= h - m                       # entrance edge touches the bottom of the image
        side_clipped = x0 <= m or (x0 + bw) >= w - m
        if len(pix) > 400:
            pix = pix[:: int(math.ceil(len(pix) / 400))]

        R = cam_to_level("gimbal", gimbal_pitch_deg)
        P = self._ground_points(pix, camera_model, R, height_m)
        if len(P) < 12:
            return self._fail(frame, f"{self.colour} region is above the horizon / not on the ground")

        # 1. initial axis from the min-area rectangle of the ground outline (long side)
        (cx, cy), (rw, rh), ang = cv2.minAreaRect(P.astype(np.float32))
        long_side_deg = ang if rw >= rh else ang + 90.0
        a = np.array([math.cos(math.radians(long_side_deg)), math.sin(math.radians(long_side_deg))])
        if a[0] < 0:
            a = -a

        # 2. refine: fit the two long edges (skip the end caps), average their directions
        for _ in range(2):
            n = np.array([-a[1], a[0]])                         # unit vector to the vehicle's right of the axis
            t, s = P @ a, P @ n
            t_lo, t_hi = t.min(), t.max()
            body = (t > t_lo + 0.5) & (t < t_hi - 0.5)
            if body.sum() < 8:
                break
            s_mid = float(np.median(s[body]))
            left, right = P[body & (s < s_mid)], P[body & (s >= s_mid)]
            if len(left) < 4 or len(right) < 4:
                break
            a_new = _line_dir(left) + _line_dir(right)
            a = a_new / (np.linalg.norm(a_new) + 1e-12)

        # 3. walls hiding part of the floor bend the long-edge fit: when the outline's non-radial edges disagree with
        #    it, trust them, and measure the width at the entrance edge (always in full view) instead of along the body
        a_edges = self._edge_axis(cnt, camera_model, R, height_m, w, h, a)
        occluded = a_edges is not None and math.degrees(math.acos(min(1.0, abs(float(a_edges @ a))))) > 2.0
        if occluded:
            a = a_edges

        n = np.array([-a[1], a[0]])
        t, s = P @ a, P @ n
        t_lo, t_hi = float(t.min()), float(t.max())
        if occluded:
            band = t < t_lo + 0.35                              # the entrance edge, corner to corner
            s_left, s_right = float(s[band].min()), float(s[band].max())
        else:
            body = (t > t_lo + 0.3) & (t < t_hi - 0.3)
            if body.sum() < 6:
                body = np.ones_like(t, dtype=bool)
            s_mid = float(np.median(s[body]))
            s_left = float(np.median(s[body & (s < s_mid)])) if (body & (s < s_mid)).any() else float(s.min())
            s_right = float(np.median(s[body & (s >= s_mid)])) if (body & (s >= s_mid)).any() else float(s.max())
            # edge medians sit slightly inside the true edges only if the edge is noisy; use the extremes of the body
            s_left, s_right = min(s_left, float(s[body].min())), max(s_right, float(s[body].max()))
        width = s_right - s_left
        centre_s = 0.5 * (s_left + s_right)

        # entrance = nearest line crossing the green: robust min over the points inside the corridor width
        inside = (s > s_left - 0.2) & (s < s_right + 0.2)
        t_near = float(np.percentile(t[inside], 1.0)) if inside.any() else t_lo
        t_far = float(np.percentile(t[inside], 99.0)) if inside.any() else t_hi

        ent = a * t_near + n * centre_s                         # entrance centre (fwd, right)
        ent_dist = float(math.hypot(ent[0], ent[1]))
        yaw_err = math.degrees(math.atan2(a[1], a[0]))
        bearing = math.degrees(math.atan2(ent[1], ent[0]))
        elevation = -math.degrees(math.atan2(height_m, max(ent_dist, 1e-6)))

        width_ok = abs(width - self.width_m) <= self.width_tol_m
        score = max(0.0, 1.0 - abs(width - self.width_m) / self.width_m) * min(1.0, area / 600.0)
        reason = "Detected"
        if not width_ok:
            reason = f"Rejected: measured width {width:.2f} m, expected {self.width_m:.1f} +/- {self.width_tol_m:.1f} m"
        elif near_clipped:
            reason = "Detected, but the entrance edge is cut off by the image bottom (distance unreliable)"
        elif side_clipped:
            reason = f"Detected, but the {self.colour} region touches the image side"

        # corners for the overlay: far-left, far-right, near-right, near-left (image TL, TR, BR, BL)
        quad = []
        for tt, ss in ((t_far, s_left), (t_far, s_right), (t_near, s_right), (t_near, s_left)):
            g = a * tt + n * ss
            quad.append(self._to_pixel((float(g[0]), float(g[1])), camera_model, R, height_m))
        corners = quad if all(q is not None for q in quad) else None

        return BannerDetection(
            t=frame.t, cam=frame.cam, seq=frame.seq, found=True, kind="floor",
            score=round(score, 2), corners=corners, center=(float(pix[:, 0].mean()), float(pix[:, 1].mean())),
            area_frac=round(area / float(w * h), 4),
            bearing_deg=round(bearing, 1), elevation_deg=round(elevation, 1),
            distance_m=round(t_near, 2), range_m=round(math.hypot(ent_dist, height_m), 2),
            lateral_m=round(centre_s, 2), height_m=round(-height_m, 2), yaw_err_deg=round(yaw_err, 1),
            plane_ok=bool(width_ok and not near_clipped), width_m=round(width, 2),
            near_clipped=bool(near_clipped), length_visible_m=round(t_far - t_near, 1), reason=reason,
        )
