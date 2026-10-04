"""Course model loading and coordinate conversion between course frame and Gazebo world."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from skyscan.geo import ang_diff, wrap180, wrap360
from skyscan.utils.logger import get_logger

log = get_logger("SIM/COURSE")


def _colour(o: dict[str, Any]) -> tuple[tuple[float, float, float], str]:
    """Object colour as (rgb 0..1, '#rrggbb'). The yaml gives either rgb: [r, g, b] (exact) or color: '#rrggbb'."""
    if "rgb" in o:
        r, g, b = (float(v) for v in o["rgb"])
    else:
        hx = str(o.get("color", "#888888")).lstrip("#")
        r, g, b = (int(hx[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) if len(hx) == 6 else (0.53, 0.53, 0.53)
    return (r, g, b), "#%02x%02x%02x" % tuple(round(max(0.0, min(1.0, v)) * 255) for v in (r, g, b))


@dataclass
class CourseObject:
    id: str
    type: str  # pad, qr, corridor, wall, floor, banner, obstacle, zone, restricted, camera, marker
    label: str
    fwd: float
    right: float
    up: float
    yaw_deg: float
    size: list[float]  # [length (local fwd), width (local right), height]
    color: str = "#888888"                       # hex, derived from rgb (UI map)
    rgb: tuple[float, float, float] = (0.53, 0.53, 0.53)   # 0..1, the exact material colour used in the SDF
    extras: dict[str, Any] = field(default_factory=dict)  # texture, content, collision, corridor, ...

    def to_dict(self) -> dict[str, Any]:
        d = {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "fwd": self.fwd,
            "right": self.right,
            "up": self.up,
            "yaw_deg": self.yaw_deg,
            "size": list(self.size),
            "color": self.color,
            "rgb": list(self.rgb),
        }
        d.update(self.extras)
        return d


@dataclass
class Course:
    name: str
    origin_gz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    origin_heading_deg: float = 90.0  # +x in Gazebo = east = 90 deg heading
    spawn_z: float = 0.195            # drone spawn height above ground
    objects: list[CourseObject] = field(default_factory=list)
    corridors: dict[str, Any] = field(default_factory=dict)
    overview_camera: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Course:
        """Load course layout from YAML definition."""
        path = Path(path)
        log.info(f"Loading course from {path}")
        if not path.exists():
            log.warn(f"Course file does not exist: {path}, using default empty course")
            return cls(name="default_course")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        name = data.get("name", "aerothon_mission")
        orig_data = data.get("origin", {})
        origin_gz = tuple(orig_data.get("gz", [0.0, 0.0, 0.0]))
        origin_heading = float(orig_data.get("heading_deg", 90.0))

        objs = []
        for o in data.get("objects", []):
            extras = {k: v for k, v in o.items() if k not in (
                "id", "type", "label", "fwd", "right", "up", "yaw_deg", "size", "color", "rgb"
            )}
            rgb, color = _colour(o)
            objs.append(CourseObject(
                id=str(o.get("id", "")),
                type=str(o.get("type", "marker")),
                label=str(o.get("label", "")),
                fwd=float(o.get("fwd", 0.0)),
                right=float(o.get("right", 0.0)),
                up=float(o.get("up", 0.0)),
                yaw_deg=float(o.get("yaw_deg", 0.0)),
                size=list(o.get("size", [1.0, 1.0, 1.0])),
                color=color,
                rgb=rgb,
                extras=extras,
            ))

        corridors = data.get("corridors", {})
        return cls(
            name=name,
            origin_gz=origin_gz,
            origin_heading_deg=origin_heading,
            spawn_z=float(orig_data.get("spawn_z", 0.195)),
            objects=objs,
            corridors=corridors,
            overview_camera=dict(data.get("overview_camera") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert course layout to JSON-serialisable dictionary."""
        return {
            "name": self.name,
            "origin": {
                "gz": list(self.origin_gz),
                "heading_deg": self.origin_heading_deg,
                "spawn_z": self.spawn_z,
            },
            "objects": [o.to_dict() for o in self.objects],
            "corridors": self.corridors,
            "overview_camera": self.overview_camera,
        }

    def gz_to_course(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        """Convert Gazebo ENU coordinate to course frame (fwd, right, up)."""
        x0, y0, z0 = self.origin_gz
        # Course fwd = +x (east), right = -y (south), up = +z
        fwd = x - x0
        right = -(y - y0)
        up = z - z0
        return fwd, right, up

    def course_to_gz(self, fwd: float, right: float, up: float) -> tuple[float, float, float]:
        """Convert course frame (fwd, right, up) to Gazebo ENU coordinate."""
        x0, y0, z0 = self.origin_gz
        x = x0 + fwd
        y = y0 - right
        z = z0 + up
        return x, y, z

    def get_object(self, obj_id: str) -> CourseObject | None:
        """Find course object by id."""
        for o in self.objects:
            if o.id == obj_id:
                return o
        return None
