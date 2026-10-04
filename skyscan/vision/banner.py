"""AeroTHON 2026 green banner detector and PnP pose estimator."""
from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from skyscan.geo import CameraModel, ang_diff, wrap180
from skyscan.types import BannerDetection, Frame
from skyscan.utils.logger import get_logger

log = get_logger("VISION/BANNER")


class BannerDetector:
    """Detects AeroTHON green banner in front camera frames and calculates 3D pose."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.size_m = list(getattr(cfg, "size_m", [3.0, 1.0]))  # [width, height]
        self.hsv_lo = np.array(getattr(cfg, "hsv_lo", [40, 90, 60]), dtype=np.uint8)
        self.hsv_hi = np.array(getattr(cfg, "hsv_hi", [85, 255, 255]), dtype=np.uint8)
        self.min_area_frac = float(getattr(cfg, "min_area_frac", 0.0015))
        self.max_area_frac = float(getattr(cfg, "max_area_frac", 0.7))
        self.aspect_range = list(getattr(cfg, "aspect_range", [1.5, 6.0]))
        self.min_fill = float(getattr(cfg, "min_fill", 0.65))
        self.text_ratio_range = list(getattr(cfg, "text_ratio_range", [0.02, 0.5]))
        self.plane_tilt_max_deg = float(getattr(cfg, "plane_tilt_max_deg", 25.0))
        self.min_score = float(getattr(cfg, "min_score", 0.5))

        # 3D object points for solvePnP: centered on banner, width along X, height along Y, Z=0
        bw, bh = self.size_m[0], self.size_m[1]
        self._obj_pts = np.array([
            [-bw / 2.0, -bh / 2.0, 0.0],  # Top-Left
            [bw / 2.0, -bh / 2.0, 0.0],   # Top-Right
            [bw / 2.0, bh / 2.0, 0.0],    # Bottom-Right
            [-bw / 2.0, bh / 2.0, 0.0],   # Bottom-Left
        ], dtype=np.float32)

    def _sort_corners(self, pts: np.ndarray) -> np.ndarray:
        """Sort 4 vertices as [Top-Left, Top-Right, Bottom-Right, Bottom-Left]."""
        pts = pts.reshape(4, 2)
        # Sum (x + y): smallest is top-left, largest is bottom-right
        s = pts.sum(axis=1)
        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]

        # Diff (y - x): smallest is top-right, largest is bottom-left
        d = pts[:, 1] - pts[:, 0]
        tr = pts[np.argmin(d)]
        bl = pts[np.argmax(d)]

        return np.array([tl, tr, br, bl], dtype=np.float32)

    def detect(
        self,
        frame: Frame,
        camera_model: CameraModel,
        gimbal_pitch_deg: float = 0.0,
    ) -> BannerDetection:
        """Detect banner in the frame and calculate 3D position and orientation."""
        img = frame.img
        if img is None:
            return BannerDetection(
                t=frame.t, cam=frame.cam, seq=frame.seq, found=False, reason="No image"
            )

        h, w = img.shape[:2]
        img_area = float(w * h)

        # 1. Color filtering in HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lo, self.hsv_hi)

        # Morphological opening/closing to clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return BannerDetection(
                t=frame.t, cam=frame.cam, seq=frame.seq, found=False, reason="No green contours"
            )

        best_cand: dict[str, Any] | None = None
        best_score = -1.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            area_frac = area / img_area
            if area_frac < self.min_area_frac or area_frac > self.max_area_frac:
                continue

            # Quad approximation
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
            if len(approx) != 4:
                # Try convex hull
                hull = cv2.convexHull(cnt)
                peri_h = cv2.arcLength(hull, True)
                approx = cv2.approxPolyDP(hull, 0.035 * peri_h, True)
                if len(approx) != 4:
                    continue

            ordered_pts = self._sort_corners(approx)
            tl, tr, br, bl = ordered_pts

            # Dimensions
            width_top = float(np.linalg.norm(tr - tl))
            width_bot = float(np.linalg.norm(br - bl))
            height_l = float(np.linalg.norm(bl - tl))
            height_r = float(np.linalg.norm(br - tr))

            mean_w = max(1.0, (width_top + width_bot) / 2.0)
            mean_h = max(1.0, (height_l + height_r) / 2.0)
            aspect = mean_w / mean_h

            if aspect < self.aspect_range[0] or aspect > self.aspect_range[1]:
                continue

            # Fill ratio
            quad_area = cv2.contourArea(ordered_pts)
            if quad_area <= 0:
                continue
            fill_ratio = area / quad_area
            if fill_ratio < self.min_fill:
                continue

            # Text ratio: check white/light text pixels inside the quad
            quad_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(quad_mask, [ordered_pts.astype(np.int32)], 255)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Text is bright / white
            _, text_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            text_inside = cv2.bitwise_and(text_mask, text_mask, mask=quad_mask)
            text_pixels = float(cv2.countNonZero(text_inside))
            quad_pixels = float(cv2.countNonZero(quad_mask))
            text_ratio = (text_pixels / quad_pixels) if quad_pixels > 0 else 0.0

            # Score based on fill, aspect and text
            aspect_target = self.size_m[0] / self.size_m[1]  # 3.0 / 1.0 = 3.0
            aspect_score = max(0.0, 1.0 - abs(aspect - aspect_target) / 3.0)
            fill_score = min(1.0, fill_ratio)
            text_score = 1.0 if (self.text_ratio_range[0] <= text_ratio <= self.text_ratio_range[1]) else 0.4
            score = 0.4 * aspect_score + 0.3 * fill_score + 0.3 * text_score

            if score > best_score:
                best_score = score
                best_cand = {
                    "corners": ordered_pts,
                    "center": (float(np.mean(ordered_pts[:, 0])), float(np.mean(ordered_pts[:, 1]))),
                    "area_frac": area_frac,
                    "aspect": aspect,
                    "text_ratio": text_ratio,
                    "score": score,
                }

        if best_cand is None or best_score < self.min_score:
            return BannerDetection(
                t=frame.t, cam=frame.cam, seq=frame.seq, found=False, reason="No candidate passed criteria"
            )

        # 2. PnP 3D pose calculation
        ordered_pts = best_cand["corners"]
        K = camera_model.K() if callable(camera_model.K) else camera_model.K
        dist_coeffs = np.zeros(4, dtype=np.float32)

        success, rvec, tvec = cv2.solvePnP(
            self._obj_pts,
            ordered_pts,
            K,
            dist_coeffs,
            flags=cv2.SOLVEPNP_IPPE
        )
        if not success:
            success, rvec, tvec = cv2.solvePnP(
                self._obj_pts, ordered_pts, K, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

        if not success:
            return BannerDetection(
                t=frame.t, cam=frame.cam, seq=frame.seq, found=False, reason="solvePnP failed"
            )

        # Camera optical frame: x right, y down, z forward
        # tvec = [x_cam, y_cam, z_cam]
        x_c, y_c, z_c = float(tvec[0, 0]), float(tvec[1, 0]), float(tvec[2, 0])
        range_m = float(math.sqrt(x_c * x_c + y_c * y_c + z_c * z_c))

        # Bearing and elevation from camera optical axis
        bearing_deg = math.degrees(math.atan2(x_c, z_c))  # + right
        elevation_deg = math.degrees(math.atan2(-y_c, z_c))  # + up

        # Rotate from camera frame to vehicle level frame accounting for gimbal pitch
        # Gimbal pitch is rotation around camera x-axis: pitch_deg positive = pitch up, negative = pitch down
        pitch_rad = math.radians(gimbal_pitch_deg)
        cp, sp = math.cos(pitch_rad), math.sin(pitch_rad)
        # In level vehicle frame: fwd = z_c * cp - y_c * sp; right = x_c; up = y_c * cp + z_c * sp (with y down)
        # Let's verify: when looking level (pitch=0): fwd = z_c, right = x_c, up = -y_c
        fwd_m = z_c * cp - y_c * sp
        right_m = x_c
        up_m = -y_c * cp - z_c * sp

        # Banner normal vector in camera frame:
        # In object frame, banner normal is Z = [0, 0, 1]. In camera frame: R @ [0, 0, 1]
        R, _ = cv2.Rodrigues(rvec)
        normal_cam = R @ np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # Transform normal into vehicle level frame
        # Level frame: fwd, right, up
        norm_fwd = normal_cam[2] * cp - normal_cam[1] * sp
        norm_right = normal_cam[0]
        norm_up = -normal_cam[1] * cp - normal_cam[2] * sp

        # Plane vertical check: normal should be horizontal in level frame, i.e. norm_up should be small
        tilt_deg = math.degrees(math.asin(max(-1.0, min(1.0, abs(norm_up)))))
        plane_ok = tilt_deg <= self.plane_tilt_max_deg

        # Yaw error: banner normal direction in horizontal plane vs vehicle forward
        # A banner facing the drone has normal pointing back towards the drone (-fwd)
        banner_facing_yaw = math.degrees(math.atan2(norm_right, -norm_fwd))
        yaw_err_deg = wrap180(banner_facing_yaw)

        # Distance along normal to the banner
        # distance_m = horizontal distance to banner plane
        distance_m = max(0.1, abs(fwd_m))
        lateral_m = right_m  # + = to the vehicle's right

        return BannerDetection(
            t=frame.t,
            cam=frame.cam,
            seq=frame.seq,
            found=True,
            score=round(best_score, 2),
            corners=ordered_pts.tolist(),
            center=best_cand["center"],
            area_frac=round(best_cand["area_frac"], 4),
            aspect=round(best_cand["aspect"], 2),
            text_ratio=round(best_cand["text_ratio"], 3),
            bearing_deg=round(bearing_deg, 1),
            elevation_deg=round(elevation_deg, 1),
            distance_m=round(distance_m, 2),
            range_m=round(range_m, 2),
            lateral_m=round(lateral_m, 2),
            height_m=round(up_m, 2),
            yaw_err_deg=round(yaw_err_deg, 1),
            plane_ok=plane_ok,
            reason="Detected" if plane_ok else f"Rejected: plane tilt {tilt_deg:.1f}° > {self.plane_tilt_max_deg}°",
        )
