"""Delivery-zone search planning for Stage C.

Rulebook Mission 2: climb to ~10 m over the delivery zone, find the one QR code that matches the start QR among
several, and never fly over a red (restricted) zone. This module is the geometry for that: the zone, the
boustrophedon (lawnmower) strips, an occupancy grid of the red cells seen so far (inflated by a safety margin), A*
detours around them, and the evasion moves. It works in the course frame ``(fwd, right)`` in metres and does no I/O, so
it is unit-tested offline (tests/test_search.py).
"""
from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

Pt = tuple[float, float]            # (fwd, right) in the course frame


def dist(a: Pt, b: Pt) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def unit(dx: float, dy: float) -> Pt:
    n = math.hypot(dx, dy)
    return (dx / n, dy / n) if n > 1e-9 else (0.0, 0.0)


def seg_dist(p: Pt, a: Pt, b: Pt) -> float:
    """Distance from ``p`` to the segment ``a``-``b``."""
    ab = (b[0] - a[0], b[1] - a[1])
    n2 = ab[0] ** 2 + ab[1] ** 2
    t = 0.0 if n2 < 1e-12 else min(max(((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / n2, 0.0), 1.0)
    return dist(p, (a[0] + t * ab[0], a[1] + t * ab[1]))


def right_of(travel: Pt) -> Pt:
    """Unit vector pointing to the right-hand side of a direction of travel, in (fwd, right) coordinates."""
    return (-travel[1], travel[0])


# ───────────────────────────── camera footprint / strip width ─────────────────────────────

def swath_m(height_m: float, hfov_deg: float) -> float:
    """Ground width seen by a nadir camera of horizontal field of view ``hfov_deg`` from ``height_m``."""
    return 2.0 * height_m * math.tan(math.radians(hfov_deg) / 2.0)


def footprint_m(height_m: float, hfov_deg: float, w_px: int = 640, h_px: int = 480) -> tuple[float, float]:
    """(along-track, across-track) ground size seen by the belly camera (image top = nose, image right = right wing)."""
    across = swath_m(height_m, hfov_deg)
    return across * h_px / w_px, across


def strip_spacing_m(height_m: float, hfov_deg: float, overlap: float, min_m: float = 3.0) -> float:
    """Strip spacing from the camera swath and the overlap fraction (never below ``min_m``)."""
    return max(min_m, swath_m(height_m, hfov_deg) * (1.0 - overlap))


# ───────────────────────────── zone and strips ─────────────────────────────

@dataclass(frozen=True)
class Zone:
    """Delivery-zone rectangle in the course frame. The rulebook gives its geo-fence coordinates in Phase 2."""
    fwd_min: float
    fwd_max: float
    right_min: float
    right_max: float

    @classmethod
    def from_cfg(cls, cfg: Any) -> "Zone":
        f, r = list(cfg["fwd"]), list(cfg["right"])
        return cls(float(min(f)), float(max(f)), float(min(r)), float(max(r)))

    @property
    def length_m(self) -> float:
        return self.fwd_max - self.fwd_min

    @property
    def width_m(self) -> float:
        return self.right_max - self.right_min

    @property
    def centre(self) -> Pt:
        return (0.5 * (self.fwd_min + self.fwd_max), 0.5 * (self.right_min + self.right_max))

    def contains(self, p: Pt, slack: float = 0.0) -> bool:
        return (self.fwd_min - slack <= p[0] <= self.fwd_max + slack) and (self.right_min - slack <= p[1] <= self.right_max + slack)

    def inset(self, m: float) -> "Zone":
        return Zone(self.fwd_min + m, self.fwd_max - m, self.right_min + m, self.right_max - m)

    def clamp(self, p: Pt) -> Pt:
        return (min(max(p[0], self.fwd_min), self.fwd_max), min(max(p[1], self.right_min), self.right_max))

    def to_dict(self) -> dict[str, list[float]]:
        return {"fwd": [self.fwd_min, self.fwd_max], "right": [self.right_min, self.right_max]}


@dataclass(frozen=True)
class Strip:
    """One sweep line along the course fwd axis, flown from ``f_start`` to ``f_end`` at lateral position ``right``."""
    index: int
    right: float
    f_start: float
    f_end: float

    @property
    def start(self) -> Pt:
        return (self.f_start, self.right)

    @property
    def end(self) -> Pt:
        return (self.f_end, self.right)

    @property
    def length_m(self) -> float:
        return abs(self.f_end - self.f_start)

    def point_at(self, t: float) -> Pt:
        """Point ``t`` metres along the strip from its start."""
        return (self.f_start + math.copysign(t, self.f_end - self.f_start), self.right)

    def along(self, p: Pt) -> float:
        """Distance of ``p``'s projection along the strip from its start (may be negative or beyond the end)."""
        return (p[0] - self.f_start) * (1.0 if self.f_end >= self.f_start else -1.0)


def make_strips(zone: Zone, spacing_m: float, inset_m: float = 1.0, start: Pt | None = None) -> list[Strip]:
    """Boustrophedon strips along fwd, stacked across right. ``n = ceil(width / spacing)`` strips, evenly spread so the
    real spacing never exceeds ``spacing_m``. The sweep starts at whichever outer strip is nearer to ``start`` and
    alternates direction, so every turn is a short sideways hop."""
    inner = zone.inset(inset_m)
    n = max(1, math.ceil(zone.width_m / max(0.5, spacing_m) - 1e-9))
    step = zone.width_m / n
    rights = [min(max(zone.right_min + (i + 0.5) * step, inner.right_min), inner.right_max) for i in range(n)]
    f_lo, f_hi = inner.fwd_min, inner.fwd_max
    s = start if start is not None else (zone.fwd_min, zone.centre[1])
    d_first = min(dist(s, (f_lo, rights[0])), dist(s, (f_hi, rights[0])))
    d_last = min(dist(s, (f_lo, rights[-1])), dist(s, (f_hi, rights[-1])))
    if d_last < d_first:
        rights.reverse()
    first_start = f_lo if abs(s[0] - f_lo) <= abs(s[0] - f_hi) else f_hi
    strips: list[Strip] = []
    a, b = first_start, (f_hi if first_start == f_lo else f_lo)
    for i, r in enumerate(rights):
        strips.append(Strip(i, r, a, b))
        a, b = b, a
    return strips


# ───────────────────────────── red-zone occupancy grid ─────────────────────────────

def _shift_or(dst: np.ndarray, src: np.ndarray, di: int, dj: int) -> None:
    """dst |= src shifted by (di, dj) cells (no wrap-around)."""
    ni, nj = src.shape
    si0, si1 = max(0, -di), min(ni, ni - di)
    sj0, sj1 = max(0, -dj), min(nj, nj - dj)
    if si0 >= si1 or sj0 >= sj1:
        return
    dst[si0 + di:si1 + di, sj0 + dj:sj1 + dj] |= src[si0:si1, sj0:sj1]


@dataclass
class PlanResult:
    ok: bool
    path: list[Pt] = field(default_factory=list)       # excludes the start point, ends at the (possibly adjusted) goal
    goal_adjusted: bool = False
    length_m: float = 0.0


class ZoneGrid:
    """Occupancy grid of the delivery zone: which cells have been seen red, the keep-out area around them and which
    cells the camera has covered. Cells are ``res_m`` squares, index ``[i, j]`` = (fwd, right)."""

    def __init__(self, zone: Zone, res_m: float = 0.5, margin_m: float = 1.5, confirm_hits: int = 2, fence_inset_m: float = 1.0) -> None:
        self.zone, self.res, self.margin, self.confirm_hits = zone, float(res_m), float(margin_m), int(confirm_hits)
        self.nf = max(1, math.ceil(zone.length_m / self.res))
        self.nr = max(1, math.ceil(zone.width_m / self.res))
        self.hits = np.zeros((self.nf, self.nr), np.uint8)
        self.covered = np.zeros((self.nf, self.nr), bool)
        self.version = 0                                   # bumped whenever the confirmed red set changes
        self._keep: np.ndarray | None = None
        self._keep_version = -1
        ci = zone.fwd_min + (np.arange(self.nf) + 0.5) * self.res
        cj = zone.right_min + (np.arange(self.nr) + 0.5) * self.res
        self.inner = zone.inset(fence_inset_m)                # the vehicle stays inside this rectangle
        h = 0.5 * self.res
        inn = self.inner
        self.fence = ~(((ci >= inn.fwd_min - h) & (ci <= inn.fwd_max + h))[:, None] & ((cj >= inn.right_min - h) & (cj <= inn.right_max + h))[None, :])

    # --- indexing -------------------------------------------------------------------------------------------

    def cell(self, p: Pt) -> tuple[int, int]:
        i = int((p[0] - self.zone.fwd_min) // self.res)
        j = int((p[1] - self.zone.right_min) // self.res)
        return min(max(i, 0), self.nf - 1), min(max(j, 0), self.nr - 1)

    def centre(self, i: int, j: int) -> Pt:
        return (self.zone.fwd_min + (i + 0.5) * self.res, self.zone.right_min + (j + 0.5) * self.res)

    # --- red cells ------------------------------------------------------------------------------------------

    def add_polygon(self, poly: Sequence[Pt]) -> int:
        """Mark the cells under a (convex) ground polygon as seen red. Returns how many cells became confirmed red."""
        if len(poly) < 3:
            return 0
        pts = np.asarray(poly, float)
        i0, j0 = self.cell((pts[:, 0].min() - self.res, pts[:, 1].min() - self.res))
        i1, j1 = self.cell((pts[:, 0].max() + self.res, pts[:, 1].max() + self.res))
        ci = self.zone.fwd_min + (np.arange(i0, i1 + 1) + 0.5) * self.res
        cj = self.zone.right_min + (np.arange(j0, j1 + 1) + 0.5) * self.res
        gf, gr = np.meshgrid(ci, cj, indexing="ij")
        # inside test for a convex polygon + "within half a cell of its boundary" so thin slivers still mark cells
        area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
        sgn = 1.0 if area >= 0 else -1.0
        inside = np.ones(gf.shape, bool)
        near = np.zeros(gf.shape, bool)
        for k in range(len(pts)):
            a, b = pts[k], pts[(k + 1) % len(pts)]
            ex, ey = b[0] - a[0], b[1] - a[1]
            cross = (gf - a[0]) * ey - (gr - a[1]) * ex
            inside &= (sgn * cross) <= 1e-9
            seg2 = max(ex * ex + ey * ey, 1e-12)
            t = np.clip(((gf - a[0]) * ex + (gr - a[1]) * ey) / seg2, 0.0, 1.0)
            near |= np.hypot(gf - (a[0] + t * ex), gr - (a[1] + t * ey)) < 0.5 * self.res - 1e-6
        hit = inside | near
        before = self.hits[i0:i1 + 1, j0:j1 + 1] >= self.confirm_hits
        sub = self.hits[i0:i1 + 1, j0:j1 + 1]
        sub[hit & (sub < 255)] += 1
        became = (sub >= self.confirm_hits) & ~before
        n = int(became.sum())
        if n:
            self.version += 1
        return n

    @property
    def red(self) -> np.ndarray:
        return self.hits >= self.confirm_hits

    def keepout(self) -> np.ndarray:
        """Confirmed red cells inflated by the safety margin, plus the zone fence."""
        if self._keep is None or self._keep_version != self.version:
            red = self.red
            keep = red.copy()
            reach = self.margin + 0.5 * self.res               # red cells are measured from their centres: add half a cell
            r = int(math.ceil(reach / self.res))
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if math.hypot(di, dj) * self.res <= reach + 1e-9 and (di or dj):
                        _shift_or(keep, red, di, dj)
            self._keep, self._keep_version = keep | self.fence, self.version
        return self._keep

    def red_boxes(self) -> list[list[float]]:
        """Bounding boxes ``[fwd_min, fwd_max, right_min, right_max]`` of the connected red regions (for the UI)."""
        red = self.red
        seen = np.zeros_like(red)
        boxes: list[list[float]] = []
        for i in range(self.nf):
            for j in range(self.nr):
                if red[i, j] and not seen[i, j]:
                    q = deque([(i, j)])
                    seen[i, j] = True
                    lo_i = hi_i = i
                    lo_j = hi_j = j
                    while q:
                        a, b = q.popleft()
                        lo_i, hi_i, lo_j, hi_j = min(lo_i, a), max(hi_i, a), min(lo_j, b), max(hi_j, b)
                        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            x, y = a + da, b + db
                            if 0 <= x < self.nf and 0 <= y < self.nr and red[x, y] and not seen[x, y]:
                                seen[x, y] = True
                                q.append((x, y))
                    boxes.append([round(self.zone.fwd_min + lo_i * self.res, 2), round(self.zone.fwd_min + (hi_i + 1) * self.res, 2),
                                  round(self.zone.right_min + lo_j * self.res, 2), round(self.zone.right_min + (hi_j + 1) * self.res, 2)])
        return boxes

    # --- queries --------------------------------------------------------------------------------------------

    def blocked(self, p: Pt) -> bool:
        """True when ``p`` is inside the keep-out area (red + margin) or outside the fence."""
        if not self.zone.inset(0.0).contains(p):
            return True
        i, j = self.cell(p)
        return bool(self.keepout()[i, j])

    def dist_to_red(self, p: Pt, max_m: float = 20.0) -> float:
        """Distance from ``p`` to the nearest confirmed red cell centre (``max_m`` if none within range)."""
        red = self.red
        if not red.any():
            return max_m
        ii, jj = np.nonzero(red)
        f = self.zone.fwd_min + (ii + 0.5) * self.res
        r = self.zone.right_min + (jj + 0.5) * self.res
        return float(min(max_m, max(0.0, np.hypot(f - p[0], r - p[1]).min() - 0.5 * self.res)))

    def segment_clear(self, a: Pt, b: Pt) -> bool:
        """No sample along a→b (every half cell) falls in the keep-out area."""
        n = max(1, int(math.ceil(dist(a, b) / (0.5 * self.res))))
        keep = self.keepout()
        for k in range(n + 1):
            t = k / n
            i, j = self.cell((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            if keep[i, j]:
                return False
        return True

    def first_blocked_along(self, pts: Sequence[Pt], look_m: float) -> float | None:
        """Walk the polyline ``pts`` (first point = the vehicle) for ``look_m`` metres; distance to the first keep-out
        sample, or None if the way ahead is clear."""
        keep = self.keepout()
        walked = 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            seg = dist(a, b)
            n = max(1, int(math.ceil(seg / (0.5 * self.res))))
            for k in range(n + 1):
                t = k / n
                d = walked + t * seg
                if d > look_m:
                    return None
                i, j = self.cell((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
                if keep[i, j]:
                    return d
            walked += seg
        return None

    # --- coverage -------------------------------------------------------------------------------------------

    def mark_footprint(self, p: Pt, half_f: float, half_r: float) -> None:
        """Record that the camera saw the ground within ±half_f (fwd) × ±half_r (right) of ``p``."""
        i0, j0 = self.cell((p[0] - half_f, p[1] - half_r))
        i1, j1 = self.cell((p[0] + half_f, p[1] + half_r))
        self.covered[i0:i1 + 1, j0:j1 + 1] = True

    def coverage(self) -> float:
        """Fraction of the zone's non-red cells the camera has covered."""
        valid = ~self.red
        n = int(valid.sum())
        return float((self.covered & valid).sum() / n) if n else 1.0

    # --- planning -------------------------------------------------------------------------------------------

    def _nearest_free(self, p: Pt, keep: np.ndarray) -> tuple[int, int] | None:
        i, j = self.cell(p)
        if not keep[i, j]:
            return i, j
        seen = {(i, j)}
        q = deque([(i, j)])
        while q:
            a, b = q.popleft()
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                x, y = a + da, b + db
                if 0 <= x < self.nf and 0 <= y < self.nr and (x, y) not in seen:
                    if not keep[x, y]:
                        return x, y
                    seen.add((x, y))
                    q.append((x, y))
        return None

    def plan(self, start: Pt, goal: Pt) -> PlanResult:
        """Shortest path from ``start`` to ``goal`` that stays out of the keep-out area. A start inside it walks out by
        the shortest way; a goal inside it is moved to the nearest free cell (``goal_adjusted``)."""
        keep = self.keepout()
        s_cell = self._nearest_free(start, keep)
        g_cell = self._nearest_free(goal, keep)
        if s_cell is None or g_cell is None:
            return PlanResult(False)
        adjusted = tuple(self.cell(goal)) != g_cell
        head: list[Pt] = []
        if tuple(self.cell(start)) != s_cell:
            head = [self.centre(*s_cell)]
        goal_pt = self.centre(*g_cell) if adjusted else goal
        if s_cell == g_cell or (not head and self.segment_clear(start, goal_pt)):
            pts = head + [goal_pt]
            return PlanResult(True, pts, adjusted, self._len(start, pts))

        def h(c: tuple[int, int]) -> float:
            dx, dy = abs(c[0] - g_cell[0]), abs(c[1] - g_cell[1])
            return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)

        open_q: list[tuple[float, tuple[int, int]]] = [(h(s_cell), s_cell)]
        g: dict[tuple[int, int], float] = {s_cell: 0.0}
        parent: dict[tuple[int, int], tuple[int, int]] = {}
        closed: set[tuple[int, int]] = set()
        while open_q:
            _, cur = heapq.heappop(open_q)
            if cur in closed:
                continue
            if cur == g_cell:
                break
            closed.add(cur)
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = cur[0] + da, cur[1] + db
                if not (0 <= nx < self.nf and 0 <= ny < self.nr) or keep[nx, ny] or (nx, ny) in closed:
                    continue
                if da and db and (keep[cur[0] + da, cur[1]] or keep[cur[0], cur[1] + db]):
                    continue                                   # no cutting corners
                ng = g[cur] + (math.sqrt(2) if (da and db) else 1.0)
                if ng < g.get((nx, ny), math.inf):
                    g[(nx, ny)] = ng
                    parent[(nx, ny)] = cur
                    heapq.heappush(open_q, (ng + h((nx, ny)), (nx, ny)))
        if g_cell not in g:
            return PlanResult(False)
        cells = [g_cell]
        while cells[-1] != s_cell:
            cells.append(parent[cells[-1]])
        cells.reverse()
        raw = [self.centre(*c) for c in cells]
        raw[0] = head[0] if head else start
        raw[-1] = goal_pt
        smooth = [raw[0]]
        k = 0
        while k < len(raw) - 1:                                # greedy line-of-sight smoothing
            m = len(raw) - 1
            while m > k + 1 and not self.segment_clear(raw[k], raw[m]):
                m -= 1
            smooth.append(raw[m])
            k = m
        pts = head + smooth[1:]                                # smooth[0] is the start (or the escape cell, already in head)
        return PlanResult(True, pts, adjusted, self._len(start, pts))

    @staticmethod
    def _len(start: Pt, pts: Sequence[Pt]) -> float:
        total, cur = 0.0, start
        for p in pts:
            total += dist(cur, p)
            cur = p
        return total

    # --- sweep routing --------------------------------------------------------------------------------------

    def free_runs(self, strip: Strip, t0: float = 0.0, min_run_m: float = 2.0) -> list[tuple[float, float]]:
        """Stretches ``(t_from, t_to)`` (metres along the strip) that are outside the keep-out area, from ``t0`` on."""
        keep = self.keepout()
        step = 0.5 * self.res
        n = int(strip.length_m / step)
        runs: list[tuple[float, float]] = []
        run_start: float | None = None
        for k in range(n + 2):
            t = min(k * step, strip.length_m)
            if t < t0 - 1e-9:
                continue
            i, j = self.cell(strip.point_at(t))
            free = not keep[i, j]
            if free and run_start is None:
                run_start = t
            if (not free or t >= strip.length_m - 1e-9) and run_start is not None:
                t_end = t if free else t - step
                if t_end - run_start >= min_run_m or (run_start <= t0 + 1e-9 and t_end >= strip.length_m - 1e-9):
                    runs.append((run_start, t_end))
                run_start = None
            if t >= strip.length_m - 1e-9:
                break
        return runs

    def route(self, pos: Pt, strips: Sequence[Strip], first: int, from_strip_t: float | None = None) -> list["Leg"]:
        """Everything still to fly: the rest of strip ``first`` (from ``from_strip_t`` metres along it, or from where
        ``pos`` projects) and every later strip, detouring around the keep-out area. Legs alternate transit and sweep."""
        legs: list[Leg] = []
        cur = pos
        for si in range(first, len(strips)):
            strip = strips[si]
            t0 = max(0.0, (from_strip_t if (si == first and from_strip_t is not None) else (strip.along(pos) if si == first else 0.0)))
            runs = self.free_runs(strip, t0)
            if not runs:
                continue                                       # the whole strip is red: nothing to sweep
            for (ta, tb) in runs:
                a, b = strip.point_at(ta), strip.point_at(tb)
                if dist(cur, a) > 0.3:
                    plan = self.plan(cur, a)
                    if plan.ok and plan.path:
                        legs.append(Leg(si, plan.path, sweeping=False))
                        cur = plan.path[-1]
                    elif not plan.ok:
                        continue
                if dist(cur, b) > 0.05:
                    legs.append(Leg(si, [b], sweeping=True))
                    cur = b
        return legs


@dataclass
class Leg:
    """One piece of the planned route: fly through ``pts`` in order. ``sweeping`` legs run along a strip (the camera is
    covering new ground), the others are transits (strip-to-strip hops and detours)."""
    strip: int
    pts: list[Pt]
    sweeping: bool


def route_points(pos: Pt, legs: Sequence[Leg]) -> list[Pt]:
    """Flatten a route to one polyline starting at ``pos``."""
    out = [pos]
    for leg in legs:
        out.extend(leg.pts)
    return out


# ───────────────────────────── following a polyline ─────────────────────────────

class PathFollower:
    """Carrot-following on a polyline: ``update(pos)`` gives the point to steer at and how far is left."""

    def __init__(self, pts: Sequence[Pt], lookahead_m: float = 1.2, reach_m: float = 0.35, capture_m: float = 1.0) -> None:
        self.pts = list(pts)
        self.look, self.reach, self.capture = float(lookahead_m), float(reach_m), float(capture_m)
        self.seg = 0

    @property
    def done(self) -> bool:
        return self.seg >= len(self.pts) - 1

    def update(self, pos: Pt) -> tuple[Pt, float]:
        """(carrot point, remaining path length from ``pos``). Advances past waypoints that were reached."""
        while self.seg < len(self.pts) - 1:
            a, b = self.pts[self.seg], self.pts[self.seg + 1]
            seg_len = dist(a, b)
            if seg_len < 1e-6 or dist(pos, b) <= self.reach:
                self.seg += 1
                continue
            # the vehicle cut the corner: it is past the end of this segment and already within ``capture`` of the next
            # one. (Left alone, the lookahead walked from the corner would land on the vehicle and the carrot would stop
            # drawing it along.)
            if self.seg + 2 < len(self.pts) and \
                    (pos[0] - a[0]) * (b[0] - a[0]) + (pos[1] - a[1]) * (b[1] - a[1]) >= seg_len ** 2 and \
                    seg_dist(pos, b, self.pts[self.seg + 2]) <= self.capture:
                self.seg += 1
                continue
            break
        if self.done:
            return self.pts[-1], dist(pos, self.pts[-1]) if self.pts else 0.0
        # project onto the current segment, then walk `look` metres along the path from there
        a, b = self.pts[self.seg], self.pts[self.seg + 1]
        ab = (b[0] - a[0], b[1] - a[1])
        seg2 = max(ab[0] ** 2 + ab[1] ** 2, 1e-12)
        t = min(max(((pos[0] - a[0]) * ab[0] + (pos[1] - a[1]) * ab[1]) / seg2, 0.0), 1.0)
        base = (a[0] + t * ab[0], a[1] + t * ab[1])
        remaining = dist(base, b) + sum(dist(p, q) for p, q in zip(self.pts[self.seg + 1:-1], self.pts[self.seg + 2:]))
        want = self.look
        cur, k = base, self.seg + 1
        while k < len(self.pts):
            nxt = self.pts[k]
            d = dist(cur, nxt)
            if d >= want:
                f = want / d if d > 1e-9 else 0.0
                return (cur[0] + f * (nxt[0] - cur[0]), cur[1] + f * (nxt[1] - cur[1])), remaining + dist(pos, base)
            if self._sharp_turn(k):
                return nxt, remaining + dist(pos, base)       # a switchback: reach the corner first, never cut or fold over it
            want -= d
            cur, k = nxt, k + 1
        return self.pts[-1], remaining + dist(pos, base)

    def _sharp_turn(self, k: int, max_deg: float = 80.0) -> bool:
        """Does the path turn by more than ``max_deg`` at waypoint ``k``? (Walking the lookahead round such a corner
        would put the carrot back next to the vehicle, so the commanded velocity would collapse to zero.)"""
        if k <= 0 or k >= len(self.pts) - 1:
            return False
        a, b, c = self.pts[k - 1], self.pts[k], self.pts[k + 1]
        u, v = unit(b[0] - a[0], b[1] - a[1]), unit(c[0] - b[0], c[1] - b[1])
        if u == (0.0, 0.0) or v == (0.0, 0.0):
            return False
        return math.degrees(math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))) > max_deg

    def ahead(self, pos: Pt) -> list[Pt]:
        """The rest of the path as a polyline starting at ``pos`` (for ``ZoneGrid.first_blocked_along``)."""
        return [pos] + self.pts[self.seg + 1:]


# ───────────────────────────── evasion ─────────────────────────────

@dataclass
class EvasionPlan:
    ok: bool
    reverse_to: Pt
    offset_to: Pt
    side: str                       # "right" | "left" of the direction of travel
    lateral_m: float


def plan_evasion(grid: ZoneGrid, pos: Pt, travel: Pt, reverse_m: float = 2.0, look_m: float = 3.5,
                 max_lateral_m: float = 6.0, step_m: float = 0.25) -> EvasionPlan:
    """Red-zone evasion geometry: back off ``reverse_m`` along the direction we came in on, then sidestep just far enough
    that the straight line ahead (``look_m`` + the reverse distance) is clear of the keep-out area. Picks the side that
    needs the smaller sidestep; ties go to the side away from the red cells ahead."""
    t = unit(*travel)
    back = (pos[0] - t[0] * reverse_m, pos[1] - t[1] * reverse_m)
    zone = grid.zone
    if not grid.inner.contains(back):
        back = grid.inner.clamp(back)
    n = right_of(t)
    # red cells ahead decide the tie-break: which side of the path do they sit on?
    red = grid.red
    bias = 0.0
    if red.any():
        ii, jj = np.nonzero(red)
        f = zone.fwd_min + (ii + 0.5) * grid.res - pos[0]
        r = zone.right_min + (jj + 0.5) * grid.res - pos[1]
        ahead = (f * t[0] + r * t[1]) > 0
        near = np.hypot(f, r) < look_m + 3.0
        sel = ahead & near
        if sel.any():
            bias = float(np.mean(f[sel] * n[0] + r[sel] * n[1]))           # + = red mostly on the right-hand side
    best: tuple[float, float, int] | None = None                           # (lateral, tie, side)
    for side in (1, -1):
        d = step_m
        while d <= max_lateral_m + 1e-9:
            q = (back[0] + side * d * n[0], back[1] + side * d * n[1])
            far = (q[0] + t[0] * (reverse_m + look_m), q[1] + t[1] * (reverse_m + look_m))
            if not grid.blocked(q) and grid.segment_clear(q, far if zone.contains(far) else zone.clamp(far)):
                tie = 0.0 if (side * bias) <= 0 else 0.1           # prefer moving away from the red
                if best is None or (d + tie) < (best[0] + best[1]):
                    best = (d, tie, side)
                break
            d += step_m
    if best is None:                                                       # no clean sidestep: go as far as is free, away from the red
        side = 1 if bias <= 0 else -1
        d, q = step_m, back
        while d <= max_lateral_m + 1e-9:
            cand = (back[0] + side * d * n[0], back[1] + side * d * n[1])
            if grid.blocked(cand):
                break
            q, d = cand, d + step_m
        return EvasionPlan(False, back, q, "right" if side > 0 else "left", dist(back, q))
    d, _, side = best
    q = (back[0] + side * d * n[0], back[1] + side * d * n[1])
    return EvasionPlan(True, back, q, "right" if side > 0 else "left", d)
