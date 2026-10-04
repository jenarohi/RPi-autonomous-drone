"""QR code scanner, decoders and payload parser.

Implements pyzbar detection with cv2 fallback, multi-frame vote confirmation,
ground projection from pinhole camera model, and flexible delivery payload parsing.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import cv2
import numpy as np

from skyscan.geo import CameraModel
from skyscan.types import Frame, QRDetection, QRPayload, QRStatus
from skyscan.utils.logger import get_logger

log = get_logger("VISION/QR")

try:
    from pyzbar.pyzbar import decode as zbar_decode
except ImportError:
    zbar_decode = None


def parse_qr_payload(text: str) -> QRPayload:
    """Parse delivery target or coordinates from decoded QR text."""
    raw = (text or "").strip()
    if not raw:
        return QRPayload(raw="", valid=False, note="Empty payload")

    # 1. Try JSON
    if raw.startswith("{") and raw.endswith("}"):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                target = data.get("target") or data.get("zone") or data.get("location")
                lat = data.get("lat") or data.get("latitude")
                lon = data.get("lon") or data.get("longitude")
                alt = data.get("alt") or data.get("altitude")
                fields = {str(k): str(v) for k, v in data.items()}
                valid = bool(target or (lat is not None and lon is not None))
                return QRPayload(
                    raw=raw,
                    kind="json",
                    target=str(target) if target else None,
                    lat=float(lat) if lat is not None else None,
                    lon=float(lon) if lon is not None else None,
                    alt_m=float(alt) if alt is not None else None,
                    fields=fields,
                    valid=valid,
                    note="Parsed JSON payload" if valid else "JSON missing target or coordinates",
                )
        except Exception as exc:
            log.debug(f"JSON parse attempt failed: {exc}")

    # 2. Try Key-Value pairs (e.g. TARGET: C, LAT: 12.345, LON: 78.90)
    kv_pattern = re.compile(r"([A-Za-z_]+)\s*[:=]\s*([^,;\n\r]+)")
    matches = kv_pattern.findall(raw)
    if matches:
        fields = {k.strip().upper(): v.strip() for k, v in matches}
        target = fields.get("TARGET") or fields.get("ZONE") or fields.get("LOCATION") or fields.get("DEST")
        lat = fields.get("LAT") or fields.get("LATITUDE")
        lon = fields.get("LON") or fields.get("LONGITUDE")
        alt = fields.get("ALT") or fields.get("ALTITUDE")
        valid = bool(target or (lat and lon))
        return QRPayload(
            raw=raw,
            kind="kv",
            target=target,
            lat=float(lat) if lat else None,
            lon=float(lon) if lon else None,
            alt_m=float(alt) if alt else None,
            fields=fields,
            valid=valid,
            note="Parsed key-value payload" if valid else "KV missing target or coordinates",
        )

    # 3. Target pattern (e.g. DELIVERY-C, ZONE_B, TARGET A, C)
    target_match = re.search(r"\b(?:DELIVERY|TARGET|ZONE|LOC)?[-_\s]*([A-Ea-e1-9])\b", raw, re.IGNORECASE)
    if target_match:
        target = target_match.group(1).upper()
        return QRPayload(
            raw=raw,
            kind="target",
            target=target,
            valid=True,
            note=f"Parsed target identifier '{target}'",
        )

    # 4. Fallback raw text
    return QRPayload(
        raw=raw,
        kind="text",
        target=raw[:16],
        valid=bool(raw),
        note="Raw text fallback",
    )


class QRScanner:
    """Detects and decodes QR codes and manages confirmation votes."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.confirm_votes = int(getattr(cfg, "confirm_votes", 3))
        self.vote_window_s = float(getattr(cfg, "vote_window_s", 15.0))
        self.upscale_below_px = float(getattr(cfg, "upscale_below_px", 140.0))

        self.session_id = 0
        self.started_t: float | None = None
        self.frames = 0
        self.located = 0
        self.decoded = 0
        self._vote_history: list[tuple[float, str]] = []
        self._votes: dict[str, int] = {}
        self.confirmed: str | None = None
        self.confirmed_t: float | None = None
        self.payload: QRPayload | None = None

        self._cv2_detector = cv2.QRCodeDetector()

    def reset(self, session_id: int | None = None) -> int:
        """Reset vote session."""
        self.session_id = (self.session_id + 1) if session_id is None else session_id
        self.started_t = time.time()
        self.frames = 0
        self.located = 0
        self.decoded = 0
        self._vote_history.clear()
        self._votes.clear()
        self.confirmed = None
        self.confirmed_t = None
        self.payload = None
        log.info(f"QR session reset to id={self.session_id}")
        return self.session_id

    def vote(self, text: str) -> QRStatus:
        """Record a decode vote and check confirmation."""
        now = time.time()
        self._vote_history.append((now, text))

        # Evict old votes outside vote window
        cutoff = now - self.vote_window_s
        self._vote_history = [v for v in self._vote_history if v[0] >= cutoff]

        # Recount
        counts: dict[str, int] = {}
        for _, t in self._vote_history:
            counts[t] = counts.get(t, 0) + 1
        self._votes = counts

        if self.confirmed is None and text:
            if counts.get(text, 0) >= self.confirm_votes:
                self.confirmed = text
                self.confirmed_t = now
                self.payload = parse_qr_payload(text)
                log.info(f"QR confirmed with {counts[text]} votes: '{text}' -> target={self.payload.target}")

        return self.status()

    def status(self) -> QRStatus:
        """Return current session status."""
        return QRStatus(
            session=self.session_id,
            started_t=self.started_t,
            frames=self.frames,
            located=self.located,
            decoded=self.decoded,
            votes=dict(self._votes),
            confirmed=self.confirmed,
            confirmed_t=self.confirmed_t,
            payload=self.payload,
        )

    def scan(
        self,
        frame: Frame,
        camera_model: CameraModel | None = None,
        rel_alt_m: float | None = None,
    ) -> QRDetection:
        """Scan a frame for QR code."""
        t0 = time.time()
        self.frames += 1
        img = frame.img

        if img is None:
            return QRDetection(
                t=frame.t, cam=frame.cam, seq=frame.seq, found=False, latency_ms=0.0
            )

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img

        text: str | None = None
        corners: list[list[float]] | None = None
        decoder: str | None = None

        # Try pyzbar first
        if zbar_decode is not None:
            results = zbar_decode(gray)
            if results:
                res = results[0]
                text = res.data.decode("utf-8", errors="replace")
                pts = [[float(p.x), float(p.y)] for p in res.polygon]
                if len(pts) == 4:
                    corners = pts
                elif len(pts) > 4:
                    rect = cv2.minAreaRect(np.array(pts, dtype=np.float32))
                    box = cv2.boxPoints(rect)
                    corners = box.tolist()
                decoder = "zbar"

        # Try cv2.QRCodeDetector fallback if not decoded
        if not text:
            try:
                ret, pts, _ = self._cv2_detector.detectAndDecode(gray)
                if ret:
                    text = ret
                    corners = pts[0].tolist() if (pts is not None and len(pts) > 0) else None
                    decoder = "cv2"
                elif pts is not None and len(pts) > 0:
                    corners = pts[0].tolist()
                    decoder = "cv2-loc"
            except Exception as exc:
                log.debug(f"cv2 QRCodeDetector error: {exc}")

        # Check if we should upscale and retry
        found = bool(text or corners)
        size_px: float | None = None
        center: tuple[float, float] | None = None

        if corners and len(corners) == 4:
            pts_arr = np.array(corners, dtype=np.float32)
            center = (float(np.mean(pts_arr[:, 0])), float(np.mean(pts_arr[:, 1])))
            side1 = np.linalg.norm(pts_arr[0] - pts_arr[1])
            side2 = np.linalg.norm(pts_arr[1] - pts_arr[2])
            size_px = float((side1 + side2) / 2.0)

            # If small symbol and not yet decoded, try 2x upscale on cropped ROI
            if (not text) and (size_px < self.upscale_below_px) and zbar_decode is not None:
                pad = int(size_px * 0.5)
                h, w = gray.shape[:2]
                x0 = max(0, int(center[0] - size_px / 2 - pad))
                y0 = max(0, int(center[1] - size_px / 2 - pad))
                x1 = min(w, int(center[0] + size_px / 2 + pad))
                y1 = min(h, int(center[1] + size_px / 2 + pad))
                roi = gray[y0:y1, x0:x1]
                if roi.size > 0:
                    scaled = cv2.resize(roi, (0, 0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                    up_res = zbar_decode(scaled)
                    if up_res:
                        text = up_res[0].data.decode("utf-8", errors="replace")
                        decoder = "zbar-x2"

        if found:
            self.located += 1
        if text:
            self.decoded += 1
            self.vote(text)

        # Ground projection for belly camera
        ground_fwd_m: float | None = None
        ground_right_m: float | None = None
        if center and camera_model and (rel_alt_m is not None and rel_alt_m > 0.5):
            # For belly camera: optical axis points down (-z), image top is vehicle forward (+x)
            # image right is vehicle right (+y)
            u, v = center
            dx_px = u - camera_model.cx
            dy_px = v - camera_model.cy
            # fx, fy: focal length in pixels
            # tan(theta_right) = dx_px / fx, tan(theta_fwd) = -dy_px / fy
            # ground_right_m = rel_alt_m * (dx_px / camera_model.fx)
            # ground_fwd_m = rel_alt_m * (-dy_px / camera_model.fy)
            ground_right_m = float(rel_alt_m * (dx_px / camera_model.fx))
            ground_fwd_m = float(rel_alt_m * (-dy_px / camera_model.fy))

        latency_ms = round((time.time() - t0) * 1000.0, 1)

        return QRDetection(
            t=frame.t,
            cam=frame.cam,
            seq=frame.seq,
            found=found,
            text=text,
            corners=corners,
            center=center,
            size_px=round(size_px, 1) if size_px else None,
            decoder=decoder,
            ground_fwd_m=round(ground_fwd_m, 2) if ground_fwd_m is not None else None,
            ground_right_m=round(ground_right_m, 2) if ground_right_m is not None else None,
            latency_ms=latency_ms,
        )
