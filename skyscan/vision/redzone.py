"""Red (restricted) zone detector for the belly camera.

Red wraps around the hue axis in HSV, so it takes two ranges (OpenCV H is 0..179): 0-8 and 172-180, both with
saturation and value >= 100. The two masks are OR-ed, cleaned up with a morphological open/close and split into
connected regions; each region above the minimum area is reported with its convex hull in pixels. Turning pixels into
ground positions needs the camera height and attitude, so that happens where the vehicle state is known
(``skyscan.mission.stage_c``), not here.
"""
from __future__ import annotations

import time
from typing import Any

import cv2
import numpy as np

from skyscan.types import Frame, RedBlob, RedDetection


def _arr(v: Any, default: tuple[int, int, int]) -> np.ndarray:
    return np.array(list(v) if v is not None else list(default), np.uint8)


class RedZoneDetector:
    def __init__(self, cfg: Any) -> None:
        self.lo1 = _arr(getattr(cfg, "hsv_lo1", None), (0, 100, 100))
        self.hi1 = _arr(getattr(cfg, "hsv_hi1", None), (8, 255, 255))
        self.lo2 = _arr(getattr(cfg, "hsv_lo2", None), (172, 100, 100))
        self.hi2 = _arr(getattr(cfg, "hsv_hi2", None), (180, 255, 255))
        self.min_area_px = float(getattr(cfg, "min_area_px", 600))
        k = int(getattr(cfg, "morph_px", 5))
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)) if k > 1 else None

    def mask(self, bgr: np.ndarray) -> np.ndarray:
        """Binary red mask (255 = red) of a BGR image."""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        m = cv2.inRange(hsv, self.lo1, self.hi1) | cv2.inRange(hsv, self.lo2, self.hi2)
        if self._kernel is not None:
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, self._kernel)
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, self._kernel)
        return m

    def detect(self, frame: Frame) -> RedDetection:
        t0 = time.time()
        img = frame.img
        if img is None or img.ndim != 3:
            return RedDetection(t=frame.t, cam=frame.cam, seq=frame.seq, found=False)
        m = self.mask(img)
        h, w = m.shape[:2]
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blobs: list[RedBlob] = []
        for c in contours:
            area = float(cv2.contourArea(c))
            if area < self.min_area_px:
                continue
            x, y, bw, bh = cv2.boundingRect(c)
            mom = cv2.moments(c)
            cx, cy = (mom["m10"] / mom["m00"], mom["m01"] / mom["m00"]) if mom["m00"] > 0 else (x + bw / 2.0, y + bh / 2.0)
            hull = cv2.convexHull(c)
            hull = cv2.approxPolyDP(hull, 0.01 * cv2.arcLength(hull, True), True)
            blobs.append(RedBlob(
                area_px=round(area, 1), centroid=(round(cx, 1), round(cy, 1)), bbox=(int(x), int(y), int(bw), int(bh)),
                hull=[[float(p[0][0]), float(p[0][1])] for p in hull],
                touches_border=bool(x <= 1 or y <= 1 or x + bw >= w - 1 or y + bh >= h - 1),
            ))
        blobs.sort(key=lambda b: -b.area_px)
        return RedDetection(t=frame.t, cam=frame.cam, seq=frame.seq, found=bool(blobs),
                            mask_frac=round(float(np.count_nonzero(m)) / float(m.size), 4), blobs=blobs,
                            latency_ms=round((time.time() - t0) * 1000.0, 1))
