"""Sim ground-truth telemetry computer for UI and mission verification."""
from __future__ import annotations

import math
from typing import Any

from skyscan.geo import ang_diff, gz_to_ned, gz_yaw_to_heading_deg, wrap180
from skyscan.sim.course import Course
from skyscan.types import Truth
from skyscan.utils.logger import get_logger

log = get_logger("SIM/TRUTH")


class TruthComputer:
    """Computes course-frame and corridor-relative truth metrics from simulator pose."""

    def __init__(self, course: Course | None = None) -> None:
        self.course = course

    def compute(self, raw_truth: Truth | None) -> dict[str, Any] | None:
        """Calculate enriched truth dictionary."""
        if raw_truth is None:
            return None

        x, y, z = raw_truth.pos_gz
        heading = raw_truth.heading_deg

        res: dict[str, Any] = {
            "pos_gz": [round(x, 3), round(y, 3), round(round(z, 3))],
            "ned": [round(n, 3) for n in raw_truth.ned],
            "heading_deg": round(heading, 1),
            "sim_time": raw_truth.sim_time,
            "course": None,
            "corridor": None,
        }

        if self.course is None:
            return res

        fwd, right, up = self.course.gz_to_course(x, y, z)
        course_yaw_err = wrap180(heading - self.course.origin_heading_deg)

        res["course"] = {
            "fwd": round(fwd, 2),
            "right": round(right, 2),
            "up": round(up, 2),
            "yaw_deg": round(course_yaw_err, 1),
        }

        # Delivery-zone truth: distance to every restricted (red) rectangle and the offset to every QR code, from the
        # vehicle's ground point. Used only to check Stage C afterwards, never to fly it.
        restricted, qrs = [], []
        for o in self.course.objects:
            if o.type == "restricted":
                dx = max(abs(fwd - o.fwd) - o.size[0] / 2.0, 0.0)
                dy = max(abs(right - o.right) - o.size[1] / 2.0, 0.0)
                restricted.append({"id": o.id, "dist_m": round(math.hypot(dx, dy), 2), "inside": bool(dx == 0.0 and dy == 0.0)})
            elif o.type == "qr":
                dfwd, dright = o.fwd - fwd, o.right - right
                qrs.append({"id": o.id, "content": o.extras.get("content"), "fwd": o.fwd, "right": o.right,
                            "dfwd": round(dfwd, 2), "dright": round(dright, 2), "dist_m": round(math.hypot(dfwd, dright), 2)})
        if restricted:
            res["restricted"] = restricted
        if qrs:
            res["qrs"] = qrs

        # Corridor metrics: the forward (green) and the return (orange) corridor, relative to the vehicle
        for key, name in (("corridor", "forward"), ("return_corridor", "return")):
            cor = self.course.corridors.get(name)
            if cor and "entrance" in cor:
                res[key] = self._corridor_truth(cor, fwd, right, course_yaw_err)

        return res

    @staticmethod
    def _corridor_truth(cor: dict[str, Any], fwd: float, right: float, course_yaw_err: float) -> dict[str, float]:
        ent = cor["entrance"]
        ent_fwd, ent_right = float(ent[0]), float(ent[1])
        axis_yaw = float(cor.get("axis_yaw_deg", 0.0))

        # Vector from entrance to vehicle in course frame
        df = fwd - ent_fwd
        dr = right - ent_right

        # Rotate by axis_yaw to get along-axis and cross-axis components
        rad = math.radians(axis_yaw)
        ca, sa = math.cos(rad), math.sin(rad)
        return {
            "dist_to_entrance_m": round(math.sqrt(df * df + dr * dr), 2),
            "along_axis_m": round(df * ca + dr * sa, 2),
            "lateral_m": round(-df * sa + dr * ca, 2),  # + = right of axis
            "yaw_err_deg": round(wrap180(course_yaw_err - axis_yaw), 1),
        }
