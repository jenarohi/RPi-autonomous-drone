"""Random delivery-zone scenarios for the simulator (the dashboard's RANDOM pop-up).

A scenario changes only what the delivery zone holds: the no-land (red) zones, the QR codes, which of them the start QR
asks for, and optionally the obstacles in the orange return corridor. Everything else in the canonical world (start
area, green corridor, walls, zone floor) stays as it is in ``sim/course.yaml``.

``generate`` is pure and deterministic: the same parameters and seed always give the same layout, so a scenario can be
previewed first and then applied, or reproduced later from its seed. ``write`` turns a layout into a course file, QR
textures and a Gazebo world next to each other, ready for ``ProcessManager`` to launch.

Rules every generated layout obeys, so a run is winnable and the red zones are a real hazard, not an impossibility:
  * everything lies inside the delivery-zone fence, inset by ``EDGE_M``;
  * red zones do not overlap each other (at least ``RED_GAP_M`` apart) and cover at most ``max_red_fraction`` of the zone;
  * every QR code is at least ``qr_clear_m`` from the nearest red edge (the search keeps 1.5 m away from red, so a QR
    closer than that could never be approached) and at least ``qr_spacing_m`` from the other QR codes;
  * the delivery target is one of the QR codes present and the start QR reads ``DELIVERY-<target>``.
"""
from __future__ import annotations

import math
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

LETTERS = "ABCDEFGH"
EDGE_M = 1.5                  # keep-in distance from the zone fence for everything placed
RED_GAP_M = 1.0               # minimum edge-to-edge gap between red zones
RED_QR_ID_PREFIX = "red"
ORANGE_OBSTACLE_IDS = ("obs1", "obs2", "obs3")
ORANGE_WALL_L, ORANGE_WALL_R = 4.35, 7.65          # inner faces of the orange corridor walls (course "right" coordinate)
MAX_TRIES = 25                # whole-layout retries before giving up


class ScenarioError(ValueError):
    """The parameters cannot produce a valid layout (the message says why, for the pop-up)."""


# ───────────────────────────── parameters ─────────────────────────────

def _pair(v: Any, name: str, lo: float, hi: float, default: tuple[float, float]) -> tuple[float, float]:
    if v is None:
        return default
    try:
        a, b = (float(v[0]), float(v[1])) if isinstance(v, (list, tuple)) else (float(v), float(v))
    except (TypeError, ValueError, IndexError):
        raise ScenarioError(f"{name}: expected [min, max] numbers") from None
    a, b = min(a, b), max(a, b)
    if a < lo or b > hi:
        raise ScenarioError(f"{name}: must be between {lo:g} and {hi:g}")
    return a, b


def _num(v: Any, name: str, lo: float, hi: float, default: float) -> float:
    if v is None:
        return default
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ScenarioError(f"{name}: expected a number") from None
    if not lo <= x <= hi:
        raise ScenarioError(f"{name}: must be between {lo:g} and {hi:g}")
    return x


@dataclass
class Params:
    seed: int | None = None
    red_count: tuple[float, float] = (2, 4)                # how many red zones (min, max)
    red_w: tuple[float, float] = (2.0, 5.0)                # red zone extent along the course (m)
    red_d: tuple[float, float] = (2.0, 5.0)                # red zone extent across the course (m)
    red_square: bool = False                               # depth = width
    max_red_fraction: float = 0.20                         # red area / zone area
    qr_count: int = 5
    qr_size: tuple[float, float] = (1.0, 1.0)              # side of each QR code (m)
    qr_spacing_m: float = 4.0
    qr_clear_m: float = 2.5                                # QR centre to the nearest red edge, minus nothing: centre distance
    target_mode: str = "random"                            # random | specific
    target: str | None = None                              # a letter, when specific
    order_mode: str = "random"                             # random | specific
    order: list[str] = field(default_factory=list)         # letters nearest -> farthest from the start, when specific
    obstacles: bool = False                                # also move the obstacles in the orange return corridor

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "Params":
        d = d or {}
        p = cls()
        seed = d.get("seed")
        if seed not in (None, ""):
            try:
                p.seed = int(seed)
            except (TypeError, ValueError):
                raise ScenarioError("seed: expected a whole number (or leave it empty)") from None
        p.red_count = _pair(d.get("red_count"), "red zones", 0, 8, p.red_count)
        p.red_count = (int(p.red_count[0]), int(p.red_count[1]))
        p.red_w = _pair(d.get("red_w"), "red width", 0.5, 12.0, p.red_w)
        p.red_d = _pair(d.get("red_d"), "red depth", 0.5, 12.0, p.red_d)
        p.red_square = bool(d.get("red_square", p.red_square))
        p.max_red_fraction = _num(d.get("max_red_fraction"), "max red share", 0.0, 0.5, p.max_red_fraction)
        p.qr_count = int(_num(d.get("qr_count"), "QR codes", 1, len(LETTERS), p.qr_count))
        p.qr_size = _pair(d.get("qr_size"), "QR size", 0.4, 2.0, p.qr_size)
        p.qr_spacing_m = _num(d.get("qr_spacing_m"), "QR spacing", 2.0, 15.0, p.qr_spacing_m)
        p.qr_clear_m = _num(d.get("qr_clear_m"), "QR clearance from red", 1.5, 10.0, p.qr_clear_m)
        p.target_mode = str(d.get("target_mode") or "random")
        if p.target_mode not in ("random", "specific"):
            raise ScenarioError("target_mode must be random or specific")
        t = d.get("target")
        p.target = str(t).strip().upper() if t not in (None, "") else None
        p.order_mode = str(d.get("order_mode") or "random")
        if p.order_mode not in ("random", "specific"):
            raise ScenarioError("order_mode must be random or specific")
        o = d.get("order") or []
        if isinstance(o, str):
            o = [c for c in o.replace(",", " ").upper().split() if c] if (" " in o or "," in o) else list(o.upper().strip())
        p.order = [str(c).strip().upper() for c in o if str(c).strip()]
        p.obstacles = bool(d.get("obstacles", p.obstacles))
        p.validate()
        return p

    def letters(self) -> list[str]:
        return list(LETTERS[: self.qr_count])

    def validate(self) -> None:
        if self.order_mode == "specific":
            if sorted(self.order) != sorted(self.letters()):
                raise ScenarioError(f"order: give each of {', '.join(self.letters())} exactly once (nearest to farthest)")
        if self.target_mode == "specific":
            pool = self.order if self.order_mode == "specific" else self.letters()
            if self.target not in pool:
                raise ScenarioError(f"target: pick one of {', '.join(pool)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed, "red_count": list(self.red_count), "red_w": list(self.red_w), "red_d": list(self.red_d),
            "red_square": self.red_square, "max_red_fraction": self.max_red_fraction, "qr_count": self.qr_count,
            "qr_size": list(self.qr_size), "qr_spacing_m": self.qr_spacing_m, "qr_clear_m": self.qr_clear_m,
            "target_mode": self.target_mode, "target": self.target, "order_mode": self.order_mode, "order": list(self.order),
            "obstacles": self.obstacles,
        }


# ───────────────────────────── layout ─────────────────────────────

@dataclass
class Zone:
    fwd_min: float
    fwd_max: float
    right_min: float
    right_max: float

    @classmethod
    def from_cfg(cls, cfg: Any) -> "Zone":
        f, r = list(cfg["fwd"]), list(cfg["right"])
        return cls(float(min(f)), float(max(f)), float(min(r)), float(max(r)))

    @property
    def area(self) -> float:
        return (self.fwd_max - self.fwd_min) * (self.right_max - self.right_min)

    def to_dict(self) -> dict[str, list[float]]:
        return {"fwd": [self.fwd_min, self.fwd_max], "right": [self.right_min, self.right_max]}


@dataclass
class Layout:
    seed: int
    zone: Zone
    reds: list[dict[str, float]]          # {fwd, right, w, d}
    qrs: list[dict[str, Any]]             # {letter, fwd, right, size}
    target: str
    obstacles: list[dict[str, float]]     # {id, fwd, right, width}  (orange corridor), may be empty
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        red_area = sum(r["w"] * r["d"] for r in self.reds)
        return {
            "seed": self.seed, "zone": self.zone.to_dict(), "reds": self.reds, "qrs": self.qrs, "target": self.target,
            "start_text": f"DELIVERY-{self.target}", "obstacles": self.obstacles, "notes": self.notes,
            "stats": {"red_zones": len(self.reds), "red_share": round(red_area / self.zone.area, 3), "qr_codes": len(self.qrs)},
        }


def box_dist(f: float, r: float, red: dict[str, float]) -> float:
    """Distance from a point to a red rectangle (0 inside it)."""
    dx = max(abs(f - red["fwd"]) - red["w"] / 2.0, 0.0)
    dy = max(abs(r - red["right"]) - red["d"] / 2.0, 0.0)
    return math.hypot(dx, dy)


def _boxes_gap(a: dict[str, float], b: dict[str, float]) -> float:
    gx = abs(a["fwd"] - b["fwd"]) - (a["w"] + b["w"]) / 2.0
    gy = abs(a["right"] - b["right"]) - (a["d"] + b["d"]) / 2.0
    return max(gx, gy) if (gx < 0 or gy < 0) else math.hypot(gx, gy)


def _place_reds(rng: random.Random, p: Params, z: Zone) -> list[dict[str, float]]:
    n = rng.randint(p.red_count[0], p.red_count[1])
    reds: list[dict[str, float]] = []
    area = 0.0
    for _ in range(n):
        for _try in range(300):
            w = round(rng.uniform(*p.red_w), 1)
            d = w if p.red_square else round(rng.uniform(*p.red_d), 1)
            f = rng.uniform(z.fwd_min + EDGE_M + w / 2, z.fwd_max - EDGE_M - w / 2)
            r = rng.uniform(z.right_min + EDGE_M + d / 2, z.right_max - EDGE_M - d / 2)
            box = {"fwd": round(f, 1), "right": round(r, 1), "w": w, "d": d}
            if area + w * d > p.max_red_fraction * z.area:
                continue
            if any(_boxes_gap(box, o) < RED_GAP_M for o in reds):
                continue
            reds.append(box)
            area += w * d
            break
    return reds


def _place_qrs(rng: random.Random, p: Params, z: Zone, reds: list[dict[str, float]]) -> list[dict[str, Any]] | None:
    pts: list[dict[str, Any]] = []
    for _ in range(p.qr_count):
        for _try in range(600):
            size = round(rng.uniform(*p.qr_size), 2)
            m = EDGE_M + size / 2
            f = round(rng.uniform(z.fwd_min + m, z.fwd_max - m), 1)
            r = round(rng.uniform(z.right_min + m, z.right_max - m), 1)
            if any(box_dist(f, r, red) < p.qr_clear_m for red in reds):
                continue
            if any(math.hypot(f - q["fwd"], r - q["right"]) < p.qr_spacing_m for q in pts):
                continue
            pts.append({"fwd": f, "right": r, "size": size})
            break
        else:
            return None
    return pts


def _place_obstacles(rng: random.Random) -> list[dict[str, float]]:
    """New fwd / side for the three orange-corridor obstacles: alternate sides, hugging a wall so >= 1.8 m stays free."""
    wall_l, wall_r = ORANGE_WALL_L, ORANGE_WALL_R
    out: list[dict[str, float]] = []
    side = rng.choice((-1, 1))
    for _try in range(200):
        f = sorted(round(rng.uniform(10.5, 17.5), 1) for _ in ORANGE_OBSTACLE_IDS)
        if all(f[i + 1] - f[i] >= 2.5 for i in range(len(f) - 1)):
            break
    else:
        f = [11.0, 14.0, 17.0]
    for i, oid in enumerate(ORANGE_OBSTACLE_IDS):
        width = round(rng.uniform(1.0, 1.2), 1)
        gap = round(rng.uniform(0.0, 0.3), 2)
        s = side * (-1) ** i
        centre = wall_r - gap - width / 2 if s > 0 else wall_l + gap + width / 2
        out.append({"id": oid, "fwd": f[i], "right": round(centre, 2), "width": width})
    return out


def generate(params: Params, zone: Zone) -> Layout:
    """A layout for ``params`` (deterministic in ``params.seed``; a missing seed is drawn and recorded)."""
    seed = params.seed if params.seed is not None else random.SystemRandom().randrange(1, 10**9)
    rng = random.Random(seed)
    inner_f = zone.fwd_max - zone.fwd_min - 2 * EDGE_M
    inner_r = zone.right_max - zone.right_min - 2 * EDGE_M
    if inner_f <= 0 or inner_r <= 0:
        raise ScenarioError("the delivery zone is too small for a scenario")
    for attempt in range(MAX_TRIES):
        reds = _place_reds(rng, params, zone)
        if len(reds) < params.red_count[0]:
            continue
        pts = _place_qrs(rng, params, zone, reds)
        if pts is None:
            continue
        break
    else:
        raise ScenarioError("could not fit that many QR codes clear of the red zones: lower the QR count, the spacing or the "
                            "clearance, or use fewer / smaller red zones")
    # letters follow the order, nearest to the start first
    pts.sort(key=lambda q: (q["fwd"], q["right"]))
    letters = params.letters()
    if params.order_mode == "specific":
        letters = list(params.order)
    else:
        rng.shuffle(letters)
    qrs = [dict(q, letter=L) for q, L in zip(pts, letters)]
    target = params.target if params.target_mode == "specific" else rng.choice(sorted(letters))
    obstacles = _place_obstacles(rng) if params.obstacles else []
    notes = []
    if len(reds) < params.red_count[1]:
        notes.append(f"{len(reds)} red zone(s) placed (asked for up to {params.red_count[1]}; the rest did not fit the rules)")
    return Layout(seed=seed, zone=zone, reds=reds, qrs=qrs, target=target, obstacles=obstacles, notes=notes)


# ───────────────────────────── course file, textures, world ─────────────────────────────

def _drop(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The canonical objects without the ones a scenario replaces (red zones and target QR codes)."""
    out = []
    for o in objects:
        t, i = o.get("type"), str(o.get("id", ""))
        if t == "restricted" or (t == "qr" and i != "start_qr"):
            continue
        out.append(o)
    return out


def apply_to_course(base: dict[str, Any], layout: Layout) -> dict[str, Any]:
    """The course data (as in ``sim/course.yaml``) with the scenario's red zones, QR codes and start text in it."""
    data = {k: v for k, v in base.items() if k != "objects"}
    objs = _drop([dict(o) for o in base.get("objects", [])])
    for o in objs:
        if o.get("id") == "start_qr":
            o["label"] = f"Start QR (DELIVERY-{layout.target})"
            o["content"] = f"DELIVERY-{layout.target}"
        if o.get("id") in ORANGE_OBSTACLE_IDS and layout.obstacles:
            ob = next(x for x in layout.obstacles if x["id"] == o["id"])
            o["fwd"], o["right"] = ob["fwd"], ob["right"]
            o["size"] = [o["size"][0], ob["width"], o["size"][2]]
    for i, q in enumerate(layout.qrs):
        L = q["letter"]
        objs.append({"id": f"qr_{L.lower()}", "type": "qr", "label": f"Target QR {L}" + (" (match)" if L == layout.target else ""),
                     "fwd": q["fwd"], "right": q["right"], "up": 0.011, "size": [q["size"], q["size"], 0.001],
                     "rgb": [1.0, 1.0, 1.0], "texture": f"qr_{L.lower()}.png", "content": f"DELIVERY-{L}"})
    for i, r in enumerate(layout.reds, 1):
        objs.append({"id": f"{RED_QR_ID_PREFIX}{i}", "type": "restricted", "label": f"No-land zone {i}", "fwd": r["fwd"],
                     "right": r["right"], "up": 0.008, "size": [r["w"], r["d"], 0.005], "rgb": [0.9, 0.1, 0.1]})
    data["objects"] = objs
    return data


def write(layout: Layout, base_course_yaml: Path, out_dir: Path) -> dict[str, Path]:
    """Write ``course.yaml``, the QR textures and ``aerothon_mission.sdf`` for ``layout`` into ``out_dir`` (replacing it)."""
    import sys
    repo = Path(__file__).resolve().parents[2]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from sim.build_world import build_world
    from skyscan.sim.textures import qr_image, save_png

    base = yaml.safe_load(Path(base_course_yaml).read_text(encoding="utf-8")) or {}
    data = apply_to_course(base, layout)
    tmp = Path(str(out_dir) + ".new")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "textures").mkdir(parents=True)
    course_file = tmp / "course.yaml"
    course_file.write_text("# GENERATED scenario (skyscan/sim/scenario.py): seed %d, target %s\n" % (layout.seed, layout.target)
                           + yaml.safe_dump(data, sort_keys=False, default_flow_style=None), encoding="utf-8")
    save_png(tmp / "textures" / "qr_start.png", qr_image(f"DELIVERY-{layout.target}"))
    for q in layout.qrs:
        save_png(tmp / "textures" / f"qr_{q['letter'].lower()}.png", qr_image(f"DELIVERY-{q['letter']}"))
    world = build_world(course_file=course_file, out_file=tmp / "aerothon_mission.sdf")
    shutil.rmtree(out_dir, ignore_errors=True)
    tmp.rename(out_dir)
    return {"course": out_dir / "course.yaml", "world": out_dir / world.name, "dir": out_dir}


def describe(layout: Layout, params: Params) -> dict[str, Any]:
    d = layout.to_dict()
    d["params"] = params.to_dict()
    d["created"] = time.time()
    return d
