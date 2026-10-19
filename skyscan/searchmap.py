"""
Delivery search without any zone coordinates: WHERE IS THE QR FIELD?

What we know: the 6-7 codes all lie in one field of about SEARCH_FIELD_SIZE
(40 x 30 m), somewhere after the green corridor exit, at an unknown position and
rotation, not marked on the ground.

So the drone keeps a belief over every possible placement of that field
(centre on a 1 m grid x SEARCH_FIELD_ANGLES rotations) and scores each one:
  - it must contain EVERY code already read          (else ~impossible)
  - photographed area of it that showed few codes     (binomial: unlikely)
  - lying behind the corridor exit                    (impossible)
  - scout pins (QR-looking squares) inside it          (more likely)
  - distance from the exit                             (prior: ~SEARCH_PRIOR_DIST ahead)
Heat of a ground cell = probability that a code not read yet (e.g. the target)
lies there = sum over placements of weight x "cell inside, not photographed" /
unphotographed area of that placement. It always sums to 1.

Every rule is a rectangle-sum over the map, i.e. one image convolution per field
rotation, so the whole belief updates in a few tens of milliseconds.

Best next look: for every candidate stop (every 2 m, two camera orientations):
probability of the target being in its picture / seconds to fly there and look.

Map frame: aligned with the corridor exit, u = metres forward, v = metres left.
"""
import math
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from . import config as C
from .geometry import Point


def _rect_kernel(length_cells: float, width_cells: float, angle: float) -> np.ndarray:
    """1 inside a length x width rectangle rotated by angle (u axis = rows, v = cols)."""
    half = int(math.ceil(0.5 * math.hypot(length_cells, width_cells))) + 1
    g = np.arange(-half, half + 1)
    U, V = np.meshgrid(g, g, indexing="ij")
    a = U * math.cos(angle) + V * math.sin(angle)
    b = -U * math.sin(angle) + V * math.cos(angle)
    return ((np.abs(a) <= length_cells / 2) & (np.abs(b) <= width_cells / 2)).astype(np.float32)


class HeatMap:
    def __init__(self, origin: Point, heading: float):
        self.o = (float(origin[0]), float(origin[1]))
        self.h = heading
        self.c, self.s = math.cos(heading), math.sin(heading)
        r = C.SEARCH_CELL
        self.r = r
        self.u0, self.u1 = -C.SEARCH_BACK, C.SEARCH_MAX_AHEAD
        self.v0, self.v1 = -C.SEARCH_MAX_SIDE, C.SEARCH_MAX_SIDE
        nu, nv = int(round((self.u1 - self.u0) / r)), int(round((self.v1 - self.v0) / r))
        self.uc = self.u0 + (np.arange(nu) + 0.5) * r
        self.vc = self.v0 + (np.arange(nv) + 0.5) * r
        self.U, self.V = np.meshgrid(self.uc, self.vc, indexing="ij")
        self.allowed = self.U >= 1.0                       # never search behind the exit line
        self.unseen = np.ones(self.U.shape, np.float32)    # 1 = never photographed
        self.behind = (~self.allowed).astype(np.float32)
        d = np.hypot(self.U, self.V)
        self.prior = np.exp(-0.5 * ((d - C.SEARCH_PRIOR_DIST) / C.SEARCH_PRIOR_SPREAD) ** 2).astype(np.float32)
        L, W = C.SEARCH_FIELD_SIZE
        L, W = (L + C.SEARCH_FIELD_MARGIN) / r, (W + C.SEARCH_FIELD_MARGIN) / r
        self.kernels = [_rect_kernel(L, W, math.radians(a)) for a in np.arange(0, 180, C.SEARCH_FIELD_ANGLES)]
        self.qrs: List[Tuple[float, float]] = []           # (u, v) of codes read
        self.pins: List[Tuple[float, float]] = []          # (u, v) of QR-looking spots
        self._heat = None
        self.field_belief = None                           # (most likely centre xy, angle deg, share)

    # ── frames ────────────────────────────────────────────────────────────
    def to_uv(self, p: Point) -> Tuple[float, float]:
        dx, dy = p[0] - self.o[0], p[1] - self.o[1]
        return dx * self.c + dy * self.s, -dx * self.s + dy * self.c

    def to_xy(self, u: float, v: float) -> Point:
        return self.o[0] + u * self.c - v * self.s, self.o[1] + u * self.s + v * self.c

    def _cell(self, uv) -> Optional[Tuple[int, int]]:
        i = int((uv[0] - self.u0) / self.r)
        j = int((uv[1] - self.v0) / self.r)
        if 0 <= i < self.U.shape[0] and 0 <= j < self.U.shape[1]:
            return i, j
        return None

    # ── observations ──────────────────────────────────────────────────────
    def _footprint(self, p: Point, heading: float, along: float, across: float):
        u, v = self.to_uv(p)
        a = heading - self.h
        du, dv = self.U - u, self.V - v
        fwd = du * math.cos(a) + dv * math.sin(a)
        lat = -du * math.sin(a) + dv * math.cos(a)
        return (np.abs(fwd) <= along / 2) & (np.abs(lat) <= across / 2)

    def seen(self, p: Point, heading: float, along: float, across: float, factor: float):
        """A picture from `p` covered this footprint: a code there would have been read
        with probability 1 - factor."""
        self.unseen[self._footprint(p, heading, along, across)] *= factor
        self._heat = None

    def seen_picture(self, p: Point, heading: float, along: float, across: float):
        """One stop's picture (full footprint along x across): the sharp middle
        (SEARCH_USABLE) is checked with SEARCH_SEEN_FACTOR left, the outer band with
        SEARCH_EDGE_FACTOR left (codes there usually read, not always)."""
        self.seen(p, heading, along, across, C.SEARCH_EDGE_FACTOR)
        self.seen(p, heading, C.SEARCH_USABLE * along, C.SEARCH_USABLE * across,
                  C.SEARCH_SEEN_FACTOR / C.SEARCH_EDGE_FACTOR)

    def pin(self, p: Point, weight: float = 1.0):
        """QR-looking spot (front-camera scout or a square that did not read)."""
        self.pins.append(self.to_uv(p))
        self._heat = None

    def qr_found(self, p: Point):
        self.qrs.append(self.to_uv(p))
        self._heat = None

    # ── belief ────────────────────────────────────────────────────────────
    @staticmethod
    def _sum(img: np.ndarray, k: np.ndarray) -> np.ndarray:
        return cv2.filter2D(np.asarray(img, np.float32), cv2.CV_32F, k, borderType=cv2.BORDER_CONSTANT)

    def heat(self) -> np.ndarray:
        if self._heat is not None:
            return self._heat
        n_found = len(self.qrs)
        codes = np.zeros(self.U.shape, np.float32)
        for q in self.qrs:
            c = self._cell(q)
            if c:
                codes[c] += 1.0
        pins = np.zeros(self.U.shape, np.float32)
        for q in self.pins:
            c = self._cell(q)
            if c:
                pins[c] += 1.0
        seen = 1.0 - self.unseen
        n_tot = C.SEARCH_FIELD_CODES
        heat = np.zeros(self.U.shape, np.float32)
        best = (0.0, None, 0.0)
        weights = []
        for k_idx, k in enumerate(self.kernels):
            area = float(k.sum())
            inside = self._sum(codes, k)                    # codes read inside each placement
            cov = np.clip(self._sum(seen, k) / area, 0.0, 1.0)
            behind = self._sum(self.behind, k) / area
            n_pins = self._sum(pins, k)
            ok = inside >= n_found - 0.5
            p_cov = cov * C.SEARCH_DETECT_P
            lik = (p_cov ** min(n_found, n_tot)) * ((1.0 - p_cov) ** max(n_tot - n_found, 0))
            w = self.prior * np.where(ok, lik, 1e-6 * lik) * np.exp(-C.SEARCH_BEHIND_PENALTY * behind)
            w *= (1.0 + C.SEARCH_PIN_WEIGHT) ** np.minimum(n_pins, 3)
            weights.append(w)
            m = float(w.max())
            if m > best[0]:
                i, j = np.unravel_index(int(w.argmax()), w.shape)
                best = (m, (self.uc[i], self.vc[j]), k_idx * C.SEARCH_FIELD_ANGLES)
        total_w = float(sum(w.sum() for w in weights)) or 1.0
        for k, w in zip(self.kernels, weights):
            unseen_area = np.maximum(self._sum(self.unseen, k), 1.0)
            heat += self._sum((w / total_w) / unseen_area, k)
        heat *= self.unseen
        heat[~self.allowed] = 0.0
        s = float(heat.sum())
        self._heat = heat / s if s > 0 else heat
        share = best[0] / total_w
        self.field_belief = (self.to_xy(*best[1]), best[2], share) if best[1] is not None else None
        return self._heat

    def total(self) -> float:
        return float(self.heat().sum())

    # ── decision ──────────────────────────────────────────────────────────
    def best_stop(self, here: Point, here_heading: float, along: float, across: float,
                  blocked=lambda p: False) -> Optional[Tuple[Point, float, float, str]]:
        """-> (stop xy, camera heading, probability the target is in its picture, why)."""
        H = self.heat()
        sat = np.pad(H, ((1, 0), (1, 0))).cumsum(0).cumsum(1)        # summed-area table
        r = self.r
        best = None
        step = max(1, int(round(C.SEARCH_CANDIDATE_STEP / r)))
        hu, hv = self.to_uv(here)
        for k, extra in ((0, 0.0), (1, math.pi / 2)):
            hu_half, hv_half = (along / 2, across / 2) if k == 0 else (across / 2, along / 2)
            nu_h, nv_h = int(round(hu_half / r)), int(round(hv_half / r))
            hdg = self.h + extra
            dyaw = abs((hdg - here_heading + math.pi) % (2 * math.pi) - math.pi)
            for i in range(0, H.shape[0], step):
                i0, i1 = max(0, i - nu_h), min(H.shape[0], i + nu_h + 1)
                for j in range(0, H.shape[1], step):
                    if not self.allowed[i, j]:
                        continue
                    j0, j1 = max(0, j - nv_h), min(H.shape[1], j + nv_h + 1)
                    gain = sat[i1, j1] - sat[i0, j1] - sat[i1, j0] + sat[i0, j0]
                    if gain <= 1e-9:
                        continue
                    dist = math.hypot(self.uc[i] - hu, self.vc[j] - hv)
                    t = dist / C.SPEED_SEARCH + dyaw / math.radians(45) + C.SEARCH_STOP_TIME
                    score = gain / t
                    if best is None or score > best[0]:
                        p = self.to_xy(self.uc[i], self.vc[j])
                        if blocked(p):
                            continue
                        best = (score, p, hdg, gain)
        if best is None:
            return None
        _, p, hdg, gain = best
        if self.qrs:
            why = f"field around the {len(self.qrs)} code(s) read"
        elif self.pins:
            why = "scout pins / most likely field position"
        else:
            why = "most likely field position"
        return p, hdg, float(gain), why

    # ── debug image ───────────────────────────────────────────────────────
    def render(self, stops: Sequence[Point] = (), here: Optional[Point] = None,
               qrs: Sequence[Point] = (), pins: Sequence[Point] = ()) -> np.ndarray:
        """Heat image, map-up = forward from the exit, left = left."""
        H = self.heat()
        img = (255 * np.clip(H / max(float(H.max()), 1e-9), 0, 1) ** 0.5).astype(np.uint8)
        img = cv2.applyColorMap(img, cv2.COLORMAP_INFERNO)
        img[~self.allowed] = (60, 40, 40)
        img = np.ascontiguousarray(img[::-1, ::-1])
        s = 6
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)

        def px(p):
            u, v = self.to_uv(p)
            return (int((self.v1 - v) / self.r * s), int((self.u1 - u) / self.r * s))

        for a, b in zip(stops, stops[1:]):
            cv2.line(img, px(a), px(b), (255, 255, 255), 1)
        for i, p in enumerate(stops):
            cv2.circle(img, px(p), 7, (255, 255, 255), 2)
            cv2.putText(img, str(i), (px(p)[0] + 8, px(p)[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        for p in pins:
            cv2.drawMarker(img, px(p), (0, 255, 255), cv2.MARKER_TILTED_CROSS, 10, 2)
        for p in qrs:
            cv2.rectangle(img, (px(p)[0] - 5, px(p)[1] - 5), (px(p)[0] + 5, px(p)[1] + 5), (0, 255, 0), 2)
        if here is not None:
            cv2.drawMarker(img, px(here), (255, 0, 255), cv2.MARKER_CROSS, 14, 2)
        cv2.drawMarker(img, px(self.o), (255, 128, 0), cv2.MARKER_TRIANGLE_UP, 14, 2)
        return img
