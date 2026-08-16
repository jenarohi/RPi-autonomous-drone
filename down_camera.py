# ============================================================
# down_camera.py — Downward-facing camera processor
#
# Responsibilities:
#   1. Green corridor floor detection + lateral Y-offset (north-south)
#      for PID corridor centering. green_offset_x = east offset,
#      green_offset_y = north offset (what corridor PID actually needs).
#   2. QR code detection + confirmation (pyzbar)
#   3. Red zone detection + QR proximity check
#   4. Target matching (confirmed QR vs set_target string)
#
# Thread model:
#   _gz_callback() → stores raw frame (gz.transport thread, lock-free)
#   update()       → processes + returns annotated frame (MAIN thread only)
# ============================================================
import cv2
import numpy as np
from collections import deque
import threading
from config import (
    DOWN_CAM_TOPIC, DOWN_CAM_PROC_W, DOWN_CAM_PROC_H,
    GREEN_LOWER, GREEN_UPPER,
    RED_LOWER1, RED_UPPER1, RED_LOWER2, RED_UPPER2,
    QR_CONFIRM_FRAMES, QR_SCAN_EVERY_N,
    BANNER_MIN_AREA_DOWN,
)

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False
    print("[DownCam] WARNING: pyzbar not installed — QR detection disabled")
    print("[DownCam]   Install: pip install pyzbar")

try:
    from gz.transport13 import Node
    from gz.msgs10 import image_pb2
    HAS_GZ = True
except ImportError:
    HAS_GZ = False
    print("[DownCam] WARNING: gz.transport not available — camera disabled")


class DownCamera:
    """
    Downward-facing camera processor.

    Key output fields (via get_result()):
        confirmed_qr  : str   — confirmed QR text (empty if none)
        qr_offset     : (x,y) — normalised -1..1 offset of QR from image centre
                                 x = east offset, y = north offset
        target_found  : bool  — confirmed_qr matches set_target()
        qr_near_red   : bool  — QR bounding box overlaps red zone
        red_zone      : bool  — red zone pixels detected in frame
        red_area_px   : int   — pixel count of red zone
        green_detect  : bool  — green floor detected
        green_offset_x: float — green centroid east offset (-1..1)
        green_offset_y: float — green centroid NORTH offset (-1..1)
                                 POSITIVE = floor centroid is NORTH of image centre
                                 → drone drifted south → send positive north velocity
        corridor_exit : bool  — green floor lost for N frames (exit detected)
    """

    def __init__(self):
        self._frame     = None
        self._frame_lock = threading.Lock()
        self._frame_cnt = 0

        # QR state
        self._qr_buf     = deque(maxlen=QR_CONFIRM_FRAMES)
        self._target_id  = ""
        self.confirmed_qr  = ""
        self.qr_offset     = (0.0, 0.0)
        self.target_found  = False
        self.qr_near_red   = False

        # Corridor green floor
        self.green_detect   = False
        self.green_offset_x = 0.0   # east (along corridor axis — not used for PID)
        self.green_offset_y = 0.0   # north (lateral — THIS is what PID corrects)
        self.corridor_exit  = False
        self._lost_green    = 0

        # Red zone
        self.red_zone    = False
        self.red_area_px = 0

        # Precomputed HSV arrays
        self._k    = np.ones((5, 5), np.uint8)
        self._glo  = np.array(GREEN_LOWER,  dtype=np.uint8)
        self._ghi  = np.array(GREEN_UPPER,  dtype=np.uint8)
        self._r1lo = np.array(RED_LOWER1,   dtype=np.uint8)
        self._r1hi = np.array(RED_UPPER1,   dtype=np.uint8)
        self._r2lo = np.array(RED_LOWER2,   dtype=np.uint8)
        self._r2hi = np.array(RED_UPPER2,   dtype=np.uint8)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_target(self, target_id: str):
        """Set which QR code string is the delivery target."""
        self._target_id   = target_id.strip()
        self.target_found = False
        self._qr_buf.clear()
        self.confirmed_qr = ""
        print(f"[DownCam] Target set: '{self._target_id}'")

    def get_result(self) -> dict:
        return {
            "confirmed_qr":   self.confirmed_qr,
            "qr_offset":      self.qr_offset,
            "target_found":   self.target_found,
            "qr_near_red":    self.qr_near_red,
            "red_zone":       self.red_zone,
            "red_area_px":    self.red_area_px,
            "green_detect":   self.green_detect,
            "green_offset_x": self.green_offset_x,
            "green_offset_y": self.green_offset_y,
            "corridor_exit":  self.corridor_exit,
        }

    # ── Gazebo callback (gz.transport thread) ─────────────────────────────────

    def _gz_callback(self, msg):
        try:
            img = np.frombuffer(msg.data, dtype=np.uint8)
            # pixel_format_type 4 = RGBA8, 3 = RGB8
            if msg.pixel_format_type == 4:
                img = img.reshape(msg.height, msg.width, 4)[:, :, :3]
            else:
                img = img.reshape(msg.height, msg.width, 3)
            bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            with self._frame_lock:
                self._frame = bgr
        except Exception as e:
            pass  # silently skip bad frames

    # ── Main thread processor ─────────────────────────────────────────────────

    def update(self):
        """
        Process latest frame. Call from MAIN thread each loop iteration.
        Returns annotated BGR image for display, or None if no frame yet.
        """
        with self._frame_lock:
            frame = self._frame
        if frame is None:
            return None

        self._frame_cnt += 1
        small   = cv2.resize(frame, (DOWN_CAM_PROC_W, DOWN_CAM_PROC_H))
        display = small.copy()
        h, w    = small.shape[:2]
        cx, cy  = w // 2, h // 2

        # Crosshair
        cv2.line(display, (cx - 25, cy), (cx + 25, cy), (0, 255, 255), 1)
        cv2.line(display, (cx, cy - 25), (cx, cy + 25), (0, 255, 255), 1)

        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

        # ── 1. GREEN FLOOR (corridor lateral sensing) ──────────────────────
        gm = cv2.inRange(hsv, self._glo, self._ghi)
        gm = cv2.morphologyEx(gm, cv2.MORPH_OPEN,  self._k)
        gm = cv2.morphologyEx(gm, cv2.MORPH_CLOSE, self._k)
        g_cnts, _ = cv2.findContours(
            gm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.green_detect = False
        if g_cnts:
            lg = max(g_cnts, key=cv2.contourArea)
            if cv2.contourArea(lg) > BANNER_MIN_AREA_DOWN:
                self.green_detect = True
                self._lost_green  = 0
                M = cv2.moments(lg)
                gcx = int(M["m10"] / M["m00"])
                gcy = int(M["m01"] / M["m00"])

                # East offset: centroid X vs image centre X
                # Image X = east/west for nadir camera (east = right in image)
                self.green_offset_x = (gcx - cx) / cx   # +ve = floor east of drone

                # North offset: centroid Y vs image centre Y
                # Image Y increases downward = SOUTH in world.
                # So: centroid below centre (gcy > cy) → floor is SOUTH of drone
                #   → green_offset_y NEGATIVE (floor south of image centre)
                # We define: positive green_offset_y = floor is NORTH of drone
                # So: green_offset_y = -(gcy - cy) / cy
                self.green_offset_y = -(gcy - cy) / cy  # +ve = floor NORTH of drone

                cv2.drawContours(display, [lg], -1, (0, 220, 0), 2)
                cv2.circle(display, (gcx, gcy), 5, (0, 200, 0), -1)
                cv2.putText(display,
                            f"GRN x={self.green_offset_x:+.2f} "
                            f"y={self.green_offset_y:+.2f}",
                            (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                            (0, 220, 0), 1)

        if not self.green_detect:
            self._lost_green += 1

        # Corridor exit: green gone for N consecutive frames
        self.corridor_exit = (self._lost_green >= 8)

        # ── 2. RED ZONE DETECTION ──────────────────────────────────────────
        rm = cv2.bitwise_or(
            cv2.inRange(hsv, self._r1lo, self._r1hi),
            cv2.inRange(hsv, self._r2lo, self._r2hi))
        self.red_area_px = int(cv2.countNonZero(rm))
        self.red_zone    = self.red_area_px > 4000

        if self.red_zone:
            cv2.putText(display, "RED ZONE!",
                        (6, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 0, 255), 2)

        # ── 3. QR CODE DETECTION (every QR_SCAN_EVERY_N frames) ───────────
        if self._frame_cnt % QR_SCAN_EVERY_N == 0 and HAS_PYZBAR:
            self._process_qr(small, rm, w, h, display)

        cv2.putText(display, "DOWN", (w - 50, h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        return display

    def _process_qr(self, small, red_mask, w, h, display):
        decoded = pyzbar_decode(small)
        if not decoded:
            if len(self._qr_buf) > 0:
                self._qr_buf.clear()
            return

        # Pick largest QR by polygon bounding box area
        best = max(decoded, key=lambda q: _qr_area(q))
        text = best.data.decode("utf-8", errors="replace").strip()

        self._qr_buf.append(text)

        # Confirm after N identical consecutive reads
        if (len(self._qr_buf) == QR_CONFIRM_FRAMES
                and len(set(self._qr_buf)) == 1):
            self.confirmed_qr = text

            # QR centroid offset from image centre (normalised)
            pts  = best.polygon
            qcx  = sum(p.x for p in pts) / len(pts)
            qcy  = sum(p.y for p in pts) / len(pts)
            # x: positive = QR east of drone centre
            # y: positive = QR SOUTH of drone (image y down = south)
            # For delivery centering: we want QR at image centre.
            # Correction velocities: if qr_offset[0] > 0 → move east.
            #                        if qr_offset[1] > 0 → move south (NED north neg)
            self.qr_offset = (
                (qcx - w / 2) / (w / 2),
                (qcy - h / 2) / (h / 2)
            )

            # Target match
            if self._target_id and text == self._target_id:
                self.target_found = True

            # Red zone proximity
            self._check_qr_near_red(best, red_mask, w, h)

            # Draw
            col = (0, 50, 255) if self.target_found else (0, 200, 255)
            pts_px = [(int(p.x), int(p.y)) for p in pts]
            for i in range(len(pts_px)):
                cv2.line(display, pts_px[i],
                         pts_px[(i + 1) % len(pts_px)], col, 2)
            label = f"QR:{text}"
            if self.target_found:
                label += " ★TARGET"
            cv2.putText(display, label, (6, h - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, col, 1)
            if self.target_found:
                cv2.circle(display, (w // 2, h // 2), 45, (0, 255, 0), 3)

    def _check_qr_near_red(self, qr_obj, red_mask, w, h):
        rect   = qr_obj.rect
        margin = 60
        x1 = max(0, rect.left - margin)
        y1 = max(0, rect.top  - margin)
        x2 = min(w, rect.left + rect.width  + margin)
        y2 = min(h, rect.top  + rect.height + margin)
        roi = red_mask[y1:y2, x1:x2]
        self.qr_near_red = int(cv2.countNonZero(roi)) > 150

    # ── Gz transport ──────────────────────────────────────────────────────────

    def start(self):
        if HAS_GZ:
            self._node = Node()
            self._node.subscribe(
                image_pb2.Image, DOWN_CAM_TOPIC, self._gz_callback)
            print(f"[DownCam] Subscribed: {DOWN_CAM_TOPIC}")
        else:
            print("[DownCam] gz.transport not available — running headless")

    def stop(self):
        pass


def _qr_area(q):
    pts = q.polygon
    if len(pts) < 3:
        return 0
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))
