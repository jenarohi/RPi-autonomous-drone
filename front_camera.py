# ============================================================
# front_camera.py — Forward-facing camera (gimbal pitch_link)
#
# FRONT CAMERA NOT SHOWING FIX:
#   The root cause is that the iris_with_gimbal model's camera sensor
#   may publish on a different topic path depending on the ardupilot_gazebo
#   version. We try the known topic first, then fall back to topic discovery.
#
# What this module detects:
#   - GREEN banner (corridor forward entry)
#   - ORANGE banner (corridor return entry)
#   - Outputs: detected, confirmed, colour, offset_x, aligned
#
# colour field: "green" | "orange" | None
# The mission uses colour to know which corridor entrance it's at.
# ============================================================
import cv2
import numpy as np
from collections import deque
import threading
from config import (
    FRONT_CAM_TOPIC, FRONT_CAM_W, FRONT_CAM_H,
    GREEN_LOWER, GREEN_UPPER,
    ORANGE_LOWER, ORANGE_UPPER,
    BANNER_MIN_AREA_FRONT, BANNER_CONFIRM_FRAMES,
    BANNER_ALIGN_THRESH,
)

try:
    from gz.transport13 import Node
    from gz.msgs10 import image_pb2
    HAS_GZ = True
except ImportError:
    try:
        from gz.transport12 import Node
        from gz.msgs9 import image_pb2
        HAS_GZ = True
        print("[FrontCam] Using gz.transport12 / gz.msgs9")
    except ImportError:
        HAS_GZ = False
        print("[FrontCam] WARNING: gz.transport not available — disabled")


# Alternative topic paths to try if the primary fails
# (ardupilot_gazebo versions differ in sensor naming)
FRONT_CAM_TOPIC_ALTERNATIVES = [
    FRONT_CAM_TOPIC,
    "/world/aerothon_mission/model/iris/model/gimbal/link/pitch_link/sensor/camera/image",
    "/world/aerothon_mission/model/iris/link/gimbal_pitch/sensor/camera/image",
    "/camera",
]


class FrontCamera:
    """
    Forward-facing gimbal camera processor.

    Detects green or orange coloured banners at corridor entrances.

    get_result() returns:
        detected  : bool  — banner of any colour visible
        confirmed : bool  — stable detection for N frames
        colour    : str   — "green" | "orange" | None
        offset_x  : float — horizontal banner offset from centre (-1..1)
                            positive = banner is RIGHT of frame centre
        aligned   : bool  — abs(offset_x) < BANNER_ALIGN_THRESH
    """

    def __init__(self):
        self._frame      = None
        self._frame_lock = threading.Lock()
        self._frame_cnt  = 0
        self._confirm_buf = deque(maxlen=BANNER_CONFIRM_FRAMES)
        self._subscribed_topic = None

        self.detected     = False
        self.confirmed    = False
        self.colour       = None    # "green" or "orange"
        self.offset_x     = 0.0
        self.aligned      = False

        self._glo  = np.array(GREEN_LOWER,  dtype=np.uint8)
        self._ghi  = np.array(GREEN_UPPER,  dtype=np.uint8)
        self._olo  = np.array(ORANGE_LOWER, dtype=np.uint8)
        self._ohi  = np.array(ORANGE_UPPER, dtype=np.uint8)
        self._k    = np.ones((5, 5), np.uint8)

    def get_result(self) -> dict:
        return {
            "detected":  self.detected,
            "confirmed": self.confirmed,
            "colour":    self.colour,
            "offset_x":  self.offset_x,
            "aligned":   self.aligned,
        }

    # ── Gazebo callback ───────────────────────────────────────────────────────

    def _gz_callback(self, msg):
        try:
            img = np.frombuffer(msg.data, dtype=np.uint8)
            if msg.pixel_format_type == 4:
                img = img.reshape(msg.height, msg.width, 4)[:, :, :3]
            else:
                img = img.reshape(msg.height, msg.width, 3)
            bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            with self._frame_lock:
                self._frame = bgr
        except Exception:
            pass

    # ── Main thread processor ─────────────────────────────────────────────────

    def update(self):
        """Process latest frame. Call from main thread. Returns display image."""
        with self._frame_lock:
            frame = self._frame
        if frame is None:
            return None

        self._frame_cnt += 1
        frame   = cv2.resize(frame, (FRONT_CAM_W, FRONT_CAM_H))
        display = frame.copy()
        h, w    = frame.shape[:2]
        cx      = w // 2

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ── Detect GREEN banner ────────────────────────────────────────────
        gm = cv2.inRange(hsv, self._glo, self._ghi)
        gm = cv2.morphologyEx(gm, cv2.MORPH_OPEN,  self._k)
        gm = cv2.morphologyEx(gm, cv2.MORPH_CLOSE, self._k)
        g_cnts, _ = cv2.findContours(
            gm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # ── Detect ORANGE banner ───────────────────────────────────────────
        om = cv2.inRange(hsv, self._olo, self._ohi)
        om = cv2.morphologyEx(om, cv2.MORPH_OPEN,  self._k)
        om = cv2.morphologyEx(om, cv2.MORPH_CLOSE, self._k)
        o_cnts, _ = cv2.findContours(
            om, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Pick the dominant colour by largest contour area
        g_area = (cv2.contourArea(max(g_cnts, key=cv2.contourArea))
                  if g_cnts else 0)
        o_area = (cv2.contourArea(max(o_cnts, key=cv2.contourArea))
                  if o_cnts else 0)

        self.detected = False
        self.colour   = None
        best_cnt = None

        if g_area > BANNER_MIN_AREA_FRONT and g_area >= o_area:
            self.detected = True
            self.colour   = "green"
            best_cnt      = max(g_cnts, key=cv2.contourArea)
            draw_col      = (0, 220, 0)
        elif o_area > BANNER_MIN_AREA_FRONT:
            self.detected = True
            self.colour   = "orange"
            best_cnt      = max(o_cnts, key=cv2.contourArea)
            draw_col      = (0, 140, 255)

        if self.detected and best_cnt is not None:
            M   = cv2.moments(best_cnt)
            bcx = int(M["m10"] / M["m00"])
            bcy = int(M["m01"] / M["m00"])

            self.offset_x = (bcx - cx) / cx   # +ve = banner right of centre
            self.aligned  = abs(self.offset_x) < BANNER_ALIGN_THRESH

            # Draw bounding rect
            rect = cv2.minAreaRect(best_cnt)
            box  = cv2.boxPoints(rect).astype(int)
            col  = (0, 255, 0) if self.aligned else draw_col
            cv2.drawContours(display, [box], -1, col, 2)
            cv2.circle(display, (bcx, bcy), 6, (0, 0, 255), -1)
            cv2.line(display, (cx, 0), (cx, h), (200, 200, 0), 1)

            status = "ALIGNED" if self.aligned else f"off={self.offset_x:+.2f}"
            cv2.putText(display,
                        f"{self.colour.upper()} {status}",
                        (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 2)
        else:
            self.offset_x = 0.0
            self.aligned  = False

        # Confirmation: True only when banner visible for N consecutive frames
        self._confirm_buf.append(self.detected)
        self.confirmed = (len(self._confirm_buf) == BANNER_CONFIRM_FRAMES
                          and all(self._confirm_buf))

        # Labels
        cv2.putText(display, "FRONT", (w - 55, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        if self.confirmed:
            cv2.putText(display, "CONFIRMED",
                        (5, h - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.4, (0, 255, 0), 1)
        if not self.detected:
            cv2.putText(display, "NO BANNER",
                        (5, 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.4, (100, 100, 100), 1)

        return display

    # ── Gz transport ──────────────────────────────────────────────────────────

    def start(self):
        """
        Subscribe to the front camera Gazebo topic.
        Tries multiple topic paths to handle different ardupilot_gazebo versions.
        """
        if not HAS_GZ:
            print("[FrontCam] gz.transport not available — running headless")
            return

        self._node = Node()

        # Try primary topic first
        try:
            self._node.subscribe(
                image_pb2.Image, FRONT_CAM_TOPIC, self._gz_callback)
            self._subscribed_topic = FRONT_CAM_TOPIC
            print(f"[FrontCam] Subscribed: {FRONT_CAM_TOPIC}")
            return
        except Exception as e:
            print(f"[FrontCam] Primary topic failed: {e}")

        # Try fallback topics
        for topic in FRONT_CAM_TOPIC_ALTERNATIVES[1:]:
            try:
                self._node.subscribe(
                    image_pb2.Image, topic, self._gz_callback)
                self._subscribed_topic = topic
                print(f"[FrontCam] ✓ Subscribed to fallback: {topic}")
                return
            except Exception:
                continue

        print("[FrontCam] WARNING: Could not subscribe to any front camera topic.")
        print("[FrontCam] Run in WSL2: gz topic -l | grep image")
        print("[FrontCam] Then update FRONT_CAM_TOPIC in config.py")

    def stop(self):
        pass
