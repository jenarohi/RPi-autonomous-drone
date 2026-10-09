"""Vision processing pipeline coordinator.

Spawns worker threads for cameras, processes frames with latest-frame-wins semantics,
tracks detections, draws annotations, and publishes vision telemetry to the event bus.
"""
from __future__ import annotations

import collections
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

import cv2
import numpy as np

from skyscan.bus import EventBus
from skyscan.geo import CameraModel
from skyscan.gz.frames import FrameHub
from skyscan.types import BannerDetection, Frame, QRDetection, QRStatus, RedDetection, VehicleState
from skyscan.utils.logger import get_logger
from skyscan.vision.banner import BannerDetector
from skyscan.vision.corridor import CorridorDetector
from skyscan.vision.qr import QRScanner
from skyscan.vision.redzone import RedZoneDetector

log = get_logger("VISION/PIPELINE")


@dataclass
class DownObs:
    """One belly-camera frame's detections together with the vehicle state when it was processed (Stage C turns the
    pixels into ground positions with it)."""
    seq: int
    t: float
    w: int
    h: int
    qr: QRDetection
    red: RedDetection | None
    state: VehicleState | None


class VisionPipeline:
    """Multi-threaded vision processing pipeline."""

    def __init__(
        self,
        cfg: Any,
        bus: EventBus,
        hub: FrameHub,
        state_fn: Callable[[], VehicleState | None] | None = None,
    ) -> None:
        self.cfg = cfg
        self.bus = bus
        self.hub = hub
        self.state_fn = state_fn

        vcfg = getattr(cfg, "vision", cfg)
        self.max_fps = float(getattr(vcfg, "max_fps", 10.0))
        self.min_period = 1.0 / max(1.0, self.max_fps)

        self.qr_scanner = QRScanner(getattr(vcfg, "qr", vcfg))
        self.red_detector = RedZoneDetector(getattr(vcfg, "red", vcfg))
        bcfg = getattr(vcfg, "banner", vcfg)
        self.banner_mode = str(getattr(bcfg, "mode", "floor"))          # floor: green corridor floor | banner: vertical banner
        self.banner_detector = BannerDetector(bcfg)
        self.corridor_detector = CorridorDetector(bcfg)
        front_cfg = getattr(getattr(cfg, "cameras", None), "front", None)
        self.front_height_offset_m = float(getattr(front_cfg, "height_offset_m", 0.0))

        self._running = False
        self._threads: list[threading.Thread] = []

        self._lock = threading.Lock()
        self._qr_latest: QRDetection | None = None
        self._red_latest: RedDetection | None = None
        self._down_hist: collections.deque[DownObs] = collections.deque(maxlen=200)
        self._down_rx = 0.0                                  # wall time the last belly-camera frame was processed
        self._banner_latest: BannerDetection | None = None
        self._banner_history: collections.deque[BannerDetection] = collections.deque(maxlen=30)

        # Camera models cache
        self._cam_models: dict[str, CameraModel] = {}
        self._init_camera_models()

    def _init_camera_models(self) -> None:
        """Create CameraModel for known cameras from config."""
        cameras = getattr(self.cfg, "cameras", {})
        for cam_name, cam_cfg in cameras.items():
            hfov = float(getattr(cam_cfg, "hfov_deg", 70.0))
            # Default resolution 640x480 until first frame arrives
            self._cam_models[cam_name] = CameraModel.from_hfov(640, 480, hfov)

    def camera_model(self, cam: str, w: int = 640, h: int = 480) -> CameraModel:
        """Get CameraModel for camera, updated with frame resolution."""
        cameras = getattr(self.cfg, "cameras", {})
        cam_cfg = getattr(cameras, cam, None)
        hfov = float(getattr(cam_cfg, "hfov_deg", 70.0)) if cam_cfg else 70.0
        with self._lock:
            existing = self._cam_models.get(cam)
            if existing and existing.w == w and existing.h == h:
                return existing
            model = CameraModel.from_hfov(w, h, hfov)
            self._cam_models[cam] = model
            return model

    def start(self) -> None:
        """Start vision worker threads."""
        if self._running:
            return
        log.info("Starting VisionPipeline worker threads")
        self._running = True

        t_down = threading.Thread(target=self._down_worker, name="vision-down", daemon=True)
        t_front = threading.Thread(target=self._front_worker, name="vision-front", daemon=True)
        self._threads = [t_down, t_front]
        for t in self._threads:
            t.start()

    def stop(self) -> None:
        """Stop vision pipeline."""
        log.info("Stopping VisionPipeline")
        self._running = False
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=1.0)
        self._threads.clear()

    def qr_reset(self) -> int:
        """Reset QR scanning session."""
        with self._lock:
            return self.qr_scanner.reset()

    def qr_status(self) -> QRStatus:
        """Get current QR status."""
        with self._lock:
            return self.qr_scanner.status()

    def qr_latest(self) -> QRDetection | None:
        """Get latest QR detection."""
        with self._lock:
            return self._qr_latest

    def red_latest(self) -> RedDetection | None:
        """Latest red-zone detection on the belly camera."""
        with self._lock:
            return self._red_latest

    def down_age_s(self) -> float | None:
        """Seconds since the last belly-camera frame was processed (None: none yet)."""
        with self._lock:
            return (time.time() - self._down_rx) if self._down_rx else None

    def down_since(self, seq: int) -> list[DownObs]:
        """Belly-camera observations newer than frame ``seq`` (oldest first), each with the vehicle state it was taken at."""
        with self._lock:
            return [o for o in self._down_hist if o.seq > seq]

    @property
    def corridor_colour(self) -> str:
        return self.corridor_detector.colour

    def set_corridor_colour(self, name: str) -> bool:
        """Switch the front-camera corridor detector between the ``green`` and ``orange`` corridor. Old detections of the
        other colour are dropped so a stage never confirms a corridor from them."""
        with self._lock:
            if name == self.corridor_detector.colour:
                return True
            if not self.corridor_detector.set_colour(name):
                return False
            self._banner_latest = None
            self._banner_history.clear()
        log.info(f"corridor detector now looks for the {name} corridor")
        return True

    def banner_latest(self) -> BannerDetection | None:
        """Get latest banner detection."""
        with self._lock:
            return self._banner_latest

    def banner_track(self, n: int = 10) -> list[BannerDetection]:
        """Get last n banner detections."""
        with self._lock:
            return list(self._banner_history)[-n:]

    def annotate(self, cam: str, img: np.ndarray) -> np.ndarray:
        """Draw detection overlays onto an image copy."""
        out = img.copy()
        if cam == "down":
            with self._lock:
                det = self._qr_latest
                status = self.qr_scanner.status()

            if det and det.found and det.corners:
                pts = np.array(det.corners, dtype=np.int32)
                cv2.polylines(out, [pts], True, (0, 255, 0), 2)
                label = det.text or "QR LOCATED"
                cv2.putText(out, label, (pts[0][0], max(20, pts[0][1] - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            if status and status.confirmed:
                cv2.putText(out, f"CONFIRMED: {status.confirmed}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            with self._lock:
                red = self._red_latest
            if red and red.found:
                for blob in red.blobs:
                    pts = np.array(blob.hull, dtype=np.int32)
                    cv2.polylines(out, [pts], True, (0, 0, 255), 3)
                    cv2.putText(out, "RED ZONE", (int(blob.centroid[0]) - 40, int(blob.centroid[1])),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        elif cam == "front":
            with self._lock:
                det = self._banner_latest

            if det and det.found and det.kind == "floor":
                color = (0, 255, 0) if det.plane_ok else (0, 165, 255)
                if det.corners:
                    pts = np.array(det.corners, dtype=np.int32)
                    cv2.polylines(out, [pts], True, color, 2)
                    # entrance edge (near side) highlighted, centre line drawn from near to far middle
                    cv2.line(out, tuple(pts[3]), tuple(pts[2]), (255, 255, 0), 3)
                    near_mid = ((pts[2] + pts[3]) // 2).tolist()
                    far_mid = ((pts[0] + pts[1]) // 2).tolist()
                    cv2.line(out, tuple(near_mid), tuple(far_mid), (255, 255, 0), 1)
                txt = f"{self.corridor_detector.colour.upper()} CORRIDOR {det.distance_m}m  lat {det.lateral_m:+.2f}m  yaw {det.yaw_err_deg:+.1f}deg  w {det.width_m}m"
                cv2.putText(out, txt, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                if not det.plane_ok:
                    cv2.putText(out, det.reason or "REJECTED", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            elif det and det.found and det.corners:
                pts = np.array(det.corners, dtype=np.int32)
                color = (0, 255, 0) if det.plane_ok else (0, 165, 255)
                cv2.polylines(out, [pts], True, color, 3)
                txt = f"DIST: {det.distance_m}m  YAW_ERR: {det.yaw_err_deg}deg"
                cv2.putText(out, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                if det.plane_ok:
                    cv2.putText(out, "VERTICAL BANNER OK", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                else:
                    cv2.putText(out, det.reason or "REJECTED", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            elif det is not None and not det.found:
                cv2.putText(out, f"no corridor: {det.reason}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)

        return out

    # ───────────────────────────── Worker threads ─────────────────────────────

    def _down_worker(self) -> None:
        """Process down camera frames for QR detection."""
        last_seq = -1
        while self._running:
            t0 = time.time()
            frame = self.hub.latest("down")
            if frame is None or frame.seq == last_seq:
                time.sleep(0.02)
                continue

            last_seq = frame.seq
            st = self.state_fn() if self.state_fn else None
            rel_alt = st.rel_alt_m if st else None
            cam_model = self.camera_model("down", frame.w, frame.h)

            det = self.qr_scanner.scan(frame, camera_model=cam_model, rel_alt_m=rel_alt)
            try:
                red = self.red_detector.detect(frame)
            except Exception as exc:  # noqa: BLE001 - a vision glitch must not kill the QR path
                log.warn(f"red-zone detection failed: {exc}")
                red = None
            with self._lock:
                self._qr_latest = det
                self._red_latest = red
                self._down_hist.append(DownObs(seq=frame.seq, t=frame.t, w=frame.w, h=frame.h, qr=det, red=red, state=st))
                self._down_rx = time.time()
                status = self.qr_scanner.status()

            # Publish vision telemetry message (coalesced by bus)
            stats = self.hub.stats("down")
            self.bus.publish("vision", {
                "key": "down",
                "cam": "down",
                "seq": frame.seq,
                "w": frame.w,
                "h": frame.h,
                "fps": stats.get("fps", 0.0),
                "qr": det,
                "qr_status": status,
                "red": red,
                "banner": None,
            })

            elapsed = time.time() - t0
            sleep_s = max(0.01, self.min_period - elapsed)
            time.sleep(sleep_s)

    def _front_worker(self) -> None:
        """Process front camera frames for banner detection."""
        last_seq = -1
        while self._running:
            t0 = time.time()
            frame = self.hub.latest("front")
            if frame is None or frame.seq == last_seq:
                time.sleep(0.02)
                continue

            last_seq = frame.seq
            st = self.state_fn() if self.state_fn else None
            pitch_deg = st.gimbal_pitch_deg if (st and st.gimbal_pitch_deg is not None) else 0.0
            cam_model = self.camera_model("front", frame.w, frame.h)

            if self.banner_mode == "floor":
                height = (st.rel_alt_m + self.front_height_offset_m) if (st and st.rel_alt_m is not None) else None
                det = self.corridor_detector.detect(frame, camera_model=cam_model, gimbal_pitch_deg=pitch_deg, height_m=height)
            else:
                det = self.banner_detector.detect(frame, camera_model=cam_model, gimbal_pitch_deg=pitch_deg)
            with self._lock:
                self._banner_latest = det
                self._banner_history.append(det)

            # Publish vision telemetry message (coalesced by bus)
            stats = self.hub.stats("front")
            self.bus.publish("vision", {
                "key": "front",
                "cam": "front",
                "seq": frame.seq,
                "w": frame.w,
                "h": frame.h,
                "fps": stats.get("fps", 0.0),
                "qr": None,
                "qr_status": None,
                "banner": det,
            })

            elapsed = time.time() - t0
            sleep_s = max(0.01, self.min_period - elapsed)
            time.sleep(sleep_s)
