"""Run folder logs/<timestamp>/ with events.log, telemetry.csv and snapshots/."""
import csv
import math
import os
import threading
import time

import cv2


class MissionLog:
    def __init__(self, root: str):
        self.dir = os.path.join(root, time.strftime("%Y%m%d_%H%M%S"))
        os.makedirs(os.path.join(self.dir, "snapshots"), exist_ok=True)
        self.t0 = time.monotonic()
        self._lock = threading.Lock()
        self._events = open(os.path.join(self.dir, "events.log"), "w", buffering=1)
        self._csv_file = open(os.path.join(self.dir, "telemetry.csv"), "w", newline="", buffering=1)
        self._csv = csv.writer(self._csv_file)
        self._csv.writerow(["t", "stage", "x", "y", "alt", "heading_deg", "vx", "vy", "vz", "mode", "armed"])
        self._snap_n = 0

    def elapsed(self) -> float:
        return time.monotonic() - self.t0

    def __call__(self, tag: str, msg: str):
        line = f"[{self.elapsed():7.1f}s][{tag:<10}] {msg}"
        with self._lock:
            print(line, flush=True)
            self._events.write(line + "\n")

    def telemetry(self, stage: str, s):
        with self._lock:
            self._csv.writerow([f"{self.elapsed():.2f}", stage, f"{s.x:.2f}", f"{s.y:.2f}", f"{s.alt:.2f}",
                                f"{math.degrees(s.heading):.1f}", f"{s.vx:.2f}", f"{s.vy:.2f}", f"{s.vz:.2f}",
                                s.mode, int(s.armed)])

    def snapshot(self, name: str, img):
        if img is None:
            return
        self._snap_n += 1
        cv2.imwrite(os.path.join(self.dir, "snapshots", f"{self._snap_n:03d}_{name}.png"), img)

    def close(self):
        with self._lock:
            self._events.close()
            self._csv_file.close()
