"""FrameHub — latest camera frame per camera, shared by vision, the MJPEG server and snapshots.

Frame sources (Gazebo bridge, a real camera, the UI mock) call ``put()`` from their own threads.
No Gazebo imports here: this module is usable anywhere.
"""
from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Callable

from skyscan.types import Frame

log = logging.getLogger(__name__)


class FrameHub:
    def __init__(self, fps_window: int = 30) -> None:
        self._lock = threading.Lock()
        self._latest: dict[str, Frame] = {}
        self._listeners: dict[str, list[Callable[[Frame], None]]] = collections.defaultdict(list)
        self._times: dict[str, collections.deque[float]] = collections.defaultdict(
            lambda: collections.deque(maxlen=fps_window))

    def put(self, frame: Frame) -> None:
        """Publish a frame (any thread). Listeners run on this thread — they must be fast."""
        with self._lock:
            self._latest[frame.cam] = frame
            self._times[frame.cam].append(frame.t)
            listeners = tuple(self._listeners.get(frame.cam, ()))
        for fn in listeners:
            try:
                fn(frame)
            except Exception:  # noqa: BLE001
                log.exception("frame listener for %s failed", frame.cam)

    def latest(self, cam: str) -> Frame | None:
        with self._lock:
            return self._latest.get(cam)

    def cams(self) -> list[str]:
        with self._lock:
            return sorted(self._latest)

    def add_listener(self, cam: str, fn: Callable[[Frame], None]) -> None:
        with self._lock:
            self._listeners[cam].append(fn)

    def remove_listener(self, cam: str, fn: Callable[[Frame], None]) -> None:
        with self._lock:
            if fn in self._listeners.get(cam, []):
                self._listeners[cam].remove(fn)

    def stats(self, cam: str) -> dict:
        """``{"fps", "age_s", "w", "h", "seq"}`` — fps over the recent window (0 when stale)."""
        now = time.time()
        with self._lock:
            f = self._latest.get(cam)
            times = list(self._times.get(cam, ()))
        if f is None:
            return {"fps": 0.0, "age_s": None, "w": None, "h": None, "seq": None}
        age = now - f.t
        fps = 0.0
        if len(times) >= 2 and age < 2.0:
            span = times[-1] - times[0]
            fps = (len(times) - 1) / span if span > 0 else 0.0
        return {"fps": round(fps, 2), "age_s": round(age, 3), "w": f.w, "h": f.h, "seq": f.seq}
