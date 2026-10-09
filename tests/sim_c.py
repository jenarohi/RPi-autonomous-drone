"""Test rig for Stage C: a kinematic drone, a synthetic belly camera and the delivery zone, all in-process.

The camera image is rendered from the drone's pose over a raster of the zone (red patches in the sim's colour), and the
REAL ``RedZoneDetector`` runs on it. QR codes are simulated by geometry (``SimQR``): a code inside the field of view is
reported with its pixel centre, and it only decodes below ``decode_below_m`` (so both the "readable from 10 m" and the
"needs a closer look" paths can be tested without the zbar library). Time runs ``SPEED_UP`` times faster than the wall
clock inside the drone model.
"""
from __future__ import annotations

import collections
import math
import threading
import time
from typing import Any

import cv2
import numpy as np

from skyscan.geo import CameraModel, CourseFrame
from skyscan.types import Frame, QRDetection, VehicleState
from skyscan.vision.pipeline import DownObs
from skyscan.vision.redzone import RedZoneDetector

SPEED_UP = 4.0
HEADING = 90.0
COURSE = CourseFrame(origin_ned=(0.0, 0.0, 0.0), heading_deg=HEADING)
RES = 0.02                                             # raster metres per pixel
F_MIN, F_MAX, R_MIN, R_MAX = 14.0, 66.0, -17.0, 23.0   # raster extent in the course frame
RED_BGR = (26, 26, 230)                                # rgb (0.9, 0.1, 0.1) of the sim's no-land zones
FLOOR_BGR = (205, 200, 200)

#: the sim course (sim/course.yaml): QR codes and no-land zones in course (fwd, right)
SIM_QRS = {"A": (25.0, -7.0), "B": (33.0, 11.0), "C": (41.0, -2.0), "D": (49.0, 15.0), "E": (57.0, -6.0)}
SIM_REDS = [(29.0, -3.0, 3.0, 3.0), (47.0, 8.0, 3.0, 3.0)]          # fwd, right, size_fwd, size_right


def build_world(reds, qrs=None) -> np.ndarray:
    h = int((F_MAX - F_MIN) / RES)
    w = int((R_MAX - R_MIN) / RES)
    img = np.full((h, w, 3), FLOOR_BGR, np.uint8)

    def px(f: float, r: float) -> tuple[int, int]:
        return int((r - R_MIN) / RES), int((F_MAX - f) / RES)

    for f, r, sf, sr in reds:
        x0, y0 = px(f + sf / 2, r - sr / 2)
        x1, y1 = px(f - sf / 2, r + sr / 2)
        img[y0:y1, x0:x1] = RED_BGR
    return img


class SimQR:
    """Geometry-based QR scanner stand-in: what the belly camera would report for the codes on the ground."""

    def __init__(self, codes: dict[str, tuple[float, float]], decode_below_m: float = 11.0, noise_px: float = 1.5) -> None:
        self.codes = codes
        self.decode_below_m = decode_below_m
        self.noise = noise_px
        self.rng = np.random.default_rng(1)

    def detect(self, f: float, r: float, h: float, cam: CameraModel, t: float, seq: int) -> QRDetection:
        hits = []
        for name, (qf, qr) in self.codes.items():
            u = cam.cx + cam.fx * (qr - r) / h
            v = cam.cy - cam.fy * (qf - f) / h
            size = cam.fx * 1.0 / h
            if size < 20 or not (size / 2 < u < cam.w - size / 2 and size / 2 < v < cam.h - size / 2):
                continue
            u += float(self.rng.normal(0, self.noise))
            v += float(self.rng.normal(0, self.noise))
            text = f"DELIVERY-{name}" if (h <= self.decode_below_m and size >= 40) else None
            hits.append({"center": [u, v], "size_px": size, "text": text})
        if not hits:
            return QRDetection(t=t, cam="down", seq=seq, found=False)
        first, rest = hits[0], hits[1:]
        return QRDetection(t=t, cam="down", seq=seq, found=True, text=first["text"], center=tuple(first["center"]),
                           size_px=first["size_px"], corners=None, decoder="sim", others=rest or None)


class SimDrone:
    """Point-mass drone in the course frame (fwd, right, up) with first-order velocity tracking and a speed cap."""

    def __init__(self, fwd=20.0, right=0.0, up=3.0, max_xy=1.2) -> None:
        self.p = [fwd, right, up]
        self.v = [0.0, 0.0, 0.0]
        self.max_xy = max_xy
        self.vel_cmd: tuple[float, float, float] | None = None
        self.target: tuple[float, float, float] | None = None
        self.servo: list[tuple[int, int]] = []
        self.trace: list[tuple[float, float, float]] = []
        self.lock = threading.Lock()
        self.run = True
        threading.Thread(target=self._loop, daemon=True).start()

    # --- the MavLink-like surface the stages use ---------------------------------------------------------------
    def state(self) -> VehicleState:
        f, r, u = self.p
        n, e, d = COURSE.to_ned(f, r, u)
        vn, ve = COURSE.dir_to_ned(self.v[0], self.v[1])
        return VehicleState(t=time.time(), link=True, armed=True, mode="GUIDED", ekf_ok=True, ned=(n, e, d), yaw_deg=HEADING,
                            roll_deg=0.0, pitch_deg=0.0, rel_alt_m=u, vel_ned=(vn, ve, -self.v[2]))

    def velocity_ned(self, vn, ve, vd, yaw_deg=None) -> None:
        h = math.radians(HEADING)                      # rotate the NED velocity into the course frame (no translation)
        vf = vn * math.cos(h) + ve * math.sin(h)
        vr = -vn * math.sin(h) + ve * math.cos(h)
        with self.lock:
            self.vel_cmd, self.target = (vf, vr, -vd), None

    def goto_ned(self, n, e, d, yaw_deg=None) -> None:
        f, r, u = COURSE.to_course(n, e, d)
        with self.lock:
            self.target, self.vel_cmd = (f, r, u), None

    def hold(self, force_guided=False) -> bool:
        return True

    def set_servo(self, channel: int, pwm: int, timeout: float = 2.0) -> bool:
        self.servo.append((channel, pwm))
        return True

    def set_mode(self, *a, **k) -> bool:
        return True

    # --- physics -----------------------------------------------------------------------------------------------
    def _loop(self) -> None:
        t_prev, t_trace = time.time(), 0.0
        while self.run:
            time.sleep(0.01)
            now = time.time()
            dt = (now - t_prev) * SPEED_UP
            t_prev = now
            with self.lock:
                vel, tgt = self.vel_cmd, self.target
            if vel is not None:
                want = list(vel)
            elif tgt is not None:
                want = [max(-1.0, min(1.0, 1.0 * (tgt[i] - self.p[i]))) for i in range(3)]
            else:
                want = [0.0, 0.0, 0.0]
            n = math.hypot(want[0], want[1])
            if n > self.max_xy:
                want[0], want[1] = want[0] / n * self.max_xy, want[1] / n * self.max_xy
            want[2] = max(-1.5, min(1.5, want[2]))
            for i in range(3):
                self.v[i] += (want[i] - self.v[i]) * min(1.0, dt * 3.0)
                self.p[i] += self.v[i] * dt
            self.p[2] = max(0.0, self.p[2])
            if now - t_trace > 0.05:
                t_trace = now
                self.trace.append(tuple(self.p))


class SimVision:
    """Stands in for VisionPipeline: renders the belly camera, runs the real red detector, reports simulated QR codes."""

    def __init__(self, cfg: Any, drone: SimDrone, world: np.ndarray, qr: SimQR, fps: float = 10.0) -> None:
        self.cfg, self.drone, self.world, self.qr = cfg, drone, world, qr
        self.red_detector = RedZoneDetector(cfg.vision.red)
        self.cam = CameraModel.from_hfov(640, 480, 60.0)
        self.hist: collections.deque[DownObs] = collections.deque(maxlen=200)
        self.seq = 0
        self.rx = 0.0
        self.lock = threading.Lock()
        self.run = True
        self.period = 1.0 / fps
        threading.Thread(target=self._loop, daemon=True).start()

    def render(self, f: float, r: float, h: float) -> np.ndarray:
        cam = self.cam
        u = np.arange(cam.w)
        v = np.arange(cam.h)
        mx = np.tile(((r + h * (u - cam.cx) / cam.fx - R_MIN) / RES).astype(np.float32), (cam.h, 1))
        my = np.tile(((F_MAX - (f + h * (cam.cy - v) / cam.fy)) / RES).astype(np.float32)[:, None], (1, cam.w))
        return cv2.remap(self.world, mx, my, cv2.INTER_LINEAR, borderValue=FLOOR_BGR)

    def _loop(self) -> None:
        while self.run:
            t0 = time.time()
            st = self.drone.state()
            f, r, u = self.drone.p
            if u > 0.5:
                self.seq += 1
                img = self.render(f, r, u)
                frame = Frame(cam="down", seq=self.seq, t=t0, img=img)
                red = self.red_detector.detect(frame)
                qrd = self.qr.detect(f, r, u, self.cam, t0, self.seq)
                with self.lock:
                    self.hist.append(DownObs(seq=self.seq, t=t0, w=640, h=480, qr=qrd, red=red, state=st))
                    self.rx = time.time()
            time.sleep(max(0.0, self.period - (time.time() - t0)))

    # --- VisionPipeline surface --------------------------------------------------------------------------------
    def down_since(self, seq: int):
        with self.lock:
            return [o for o in self.hist if o.seq > seq]

    def down_age_s(self):
        with self.lock:
            return (time.time() - self.rx) if self.rx else None

    def camera_model(self, cam: str, w: int = 640, h: int = 480) -> CameraModel:
        return self.cam

    def stop(self) -> None:
        self.run = False


def truth_fn_for(drone: SimDrone, reds, qrs):
    """Same shape as skyscan.sim.truth.TruthComputer.compute for the zone: distance to red rectangles and to each QR."""

    def fn():
        f, r, u = drone.p
        restricted = []
        for i, (rf, rr, sf, sr) in enumerate(reds):
            dx = max(abs(f - rf) - sf / 2, 0.0)
            dy = max(abs(r - rr) - sr / 2, 0.0)
            restricted.append({"id": f"red{i + 1}", "dist_m": round(math.hypot(dx, dy), 2), "inside": bool(dx == 0.0 and dy == 0.0)})
        q = [{"id": f"qr_{n.lower()}", "content": f"DELIVERY-{n}", "fwd": qf, "right": qr, "dfwd": qf - f, "dright": qr - r,
              "dist_m": round(math.hypot(qf - f, qr - r), 2)} for n, (qf, qr) in qrs.items()]
        return {"course": {"fwd": f, "right": r, "up": u}, "restricted": restricted, "qrs": q}

    return fn
