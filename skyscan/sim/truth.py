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

        # Corridor metrics if forward corridor exists
        fwd_corridor = self.course.corridors.get("forward")
        if fwd_corridor and "entrance" in fwd_corridor:
            ent = fwd_corridor["entrance"]
            ent_fwd, ent_right = float(ent[0]), float(ent[1])
            axis_yaw = float(fwd_corridor.get("axis_yaw_deg", 0.0))

            # Vector from entrance to vehicle in course frame
            df = fwd - ent_fwd
            dr = right - ent_right

            # Rotate by axis_yaw to get along-axis and cross-axis components
            rad = math.radians(axis_yaw)
            ca, sa = math.cos(rad), math.sin(rad)
            along_axis = df * ca + dr * sa
            cross_axis = -df * sa + dr * ca

            yaw_err = wrap180(course_yaw_err - axis_yaw)

            res["corridor"] = {
                "dist_to_entrance_m": round(math.sqrt(df * df + dr * dr), 2),
                "along_axis_m": round(along_axis, 2),
                "lateral_m": round(cross_axis, 2),  # + = right of axis
                "yaw_err_deg": round(yaw_err, 1),
            }

        return res
