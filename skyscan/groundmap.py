"""
Ground map of one floor colour (green corridor), in WORLD coordinates.

A single front-camera frame never shows the whole corridor: the image edge cuts
it, walls hide part of the floor, it may be far away or seen at an angle. So no
single frame is trusted. Every coloured pixel of every frame is projected to the
ground and voted into a 0.2 m grid. Corridor candidates are strips in that map:
about CORRIDOR_WIDTH wide, at least a few metres long and mostly filled.
Grass, mats and blobs of the wrong shape are rejected; a strip that the LiDAR
later shows has no walls is put on the `rejected` list by the mission.
"""
import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import cv2
import numpy as np

from .geometry import CorridorAxis, Point, dist


@dataclass
class Strip:
    centre: Point
    width: float
    length: float
    fill: float
    entry: Point          # end nearest the reference point (where we come from)
    far: Point

    @property
    def heading(self) -> float:
        return math.atan2(self.far[1] - self.entry[1], self.far[0] - self.entry[0])

    def axis(self, name: str, colour: str) -> CorridorAxis:
        return CorridorAxis(name, self.entry, self.far, colour)

    def describe(self) -> str:
        return (f"{self.width:.1f} x {self.length:.1f} m strip, entrance ({self.entry[0]:.1f}, "
                f"{self.entry[1]:.1f}), heading {math.degrees(self.heading):.0f} deg, fill {self.fill:.2f}")


class GroundMap:
    def __init__(self, centre: Point, half_size: float = 70.0, res: float = 0.2):
        self.res = res
        self.n = int(round(2 * half_size / res))
        self.x0, self.y0 = centre[0] - half_size, centre[1] - half_size
        self.votes = np.zeros((self.n, self.n), np.uint16)      # [row = y, col = x]
        self.frames = 0

    def add(self, pts: np.ndarray):
        """One frame's ground points (Nx2 WORLD). A cell gets at most one vote per frame."""
        self.frames += 1
        if len(pts) == 0:
            return
        i = np.floor((pts[:, 0] - self.x0) / self.res).astype(int)
        j = np.floor((pts[:, 1] - self.y0) / self.res).astype(int)
        ok = (i >= 0) & (i < self.n) & (j >= 0) & (j < self.n)
        flat = np.unique(j[ok] * self.n + i[ok])
        self.votes.reshape(-1)[flat] += 1

    def _components(self, min_votes: int):
        m = (self.votes >= min_votes).astype(np.uint8)
        if not m.any():
            return None
        k = max(3, int(round(1.0 / self.res)) | 1)             # close gaps up to ~1 m
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
        return cv2.connectedComponentsWithStats(m, connectivity=8)

    def boxes(self, min_votes: int, min_area: float) -> List[Tuple[float, float, float, float]]:
        """Axis-aligned (xmin, xmax, ymin, ymax) of every blob of cells with at least
        min_votes votes (red zones)."""
        m = (self.votes >= min_votes).astype(np.uint8)
        if not m.any():
            return []
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        n, _, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        out = []
        for c in range(1, n):
            x, y, w, h, area = stats[c]
            if area * self.res * self.res < min_area:
                continue
            out.append((self.x0 + x * self.res, self.x0 + (x + w) * self.res,
                        self.y0 + y * self.res, self.y0 + (y + h) * self.res))
        return out

    def strips(self, width: float, min_length: float, ref: Point, min_votes: int = 2,
               rejected: Sequence[Point] = ()) -> Tuple[List[Strip], List[Point], List[str]]:
        """-> (corridor candidates nearest-first, centres of plausible but too-short
        blobs worth a closer look, notes on everything rejected)."""
        cc = self._components(min_votes)
        if cc is None:
            return [], [], []
        n, labels, stats, _ = cc
        r = self.res
        out, partial, notes = [], [], []
        for c in range(1, n):
            area = stats[c, cv2.CC_STAT_AREA] * r * r
            if area < 1.0:                                      # specks
                continue
            x, y, w, h = stats[c, :4]
            jj, ii = np.nonzero(labels[y:y + h, x:x + w] == c)
            P = np.column_stack([self.x0 + (ii + x + 0.5) * r, self.y0 + (jj + y + 0.5) * r])
            ctr = P.mean(axis=0)
            d = np.linalg.svd(P - ctr, full_matrices=False)[2][0]
            nrm = np.array([-d[1], d[0]])
            t, s = (P - ctr) @ d, (P - ctr) @ nrm
            t_lo, t_hi = np.percentile(t, [1, 99])
            s_lo, s_hi = np.percentile(s, [2, 98])
            length, wid = t_hi - t_lo + r, s_hi - s_lo + r
            fill = area / max(length * wid, 1e-6)
            mid_s = nrm * (s_lo + s_hi) / 2
            e1, e2 = ctr + d * t_lo + mid_s, ctr + d * t_hi + mid_s
            e1, e2 = (float(e1[0]), float(e1[1])), (float(e2[0]), float(e2[1]))
            entry, far = (e1, e2) if dist(e1, ref) <= dist(e2, ref) else (e2, e1)
            centre = (float(ctr[0] + mid_s[0]), float(ctr[1] + mid_s[1]))
            strip = Strip(centre, float(wid), float(length), float(fill), entry, far)
            why = None
            if wid > 1.35 * width:
                why = "too wide (grass / big patch)"
            elif wid < 0.65 * width and length >= min_length:
                why = "too narrow (mat / line)"
            elif fill < 0.6:
                why = "irregular shape"
            elif any(dist(entry, q) < 3.0 or dist(centre, q) < 3.0 for q in rejected):
                why = "rejected earlier (no walls)"
            elif length < min_length or wid < 0.65 * width:
                partial.append(centre)                          # maybe the corridor, seen only in part
                why = "only partly seen"
            if why:
                notes.append(f"{strip.describe()}: {why}")
            else:
                out.append(strip)
        out.sort(key=lambda s_: dist(s_.entry, ref))
        return out, partial, notes

    def render(self, strips: Sequence[Strip] = (), marks: Sequence[Point] = (), min_votes: int = 2,
               margin: float = 4.0) -> np.ndarray:
        """Debug image of the map (north up) cropped to what has been seen."""
        ys, xs = np.nonzero(self.votes)
        pts = list(marks) + [p for s in strips for p in (s.entry, s.far)]
        if xs.size == 0 and not pts:
            return np.zeros((50, 50, 3), np.uint8)
        wx = [self.x0 + xs.min() * self.res, self.x0 + xs.max() * self.res] if xs.size else []
        wy = [self.y0 + ys.min() * self.res, self.y0 + ys.max() * self.res] if ys.size else []
        wx += [p[0] for p in pts]
        wy += [p[1] for p in pts]
        i0 = max(0, int((min(wx) - margin - self.x0) / self.res))
        i1 = min(self.n, int((max(wx) + margin - self.x0) / self.res))
        j0 = max(0, int((min(wy) - margin - self.y0) / self.res))
        j1 = min(self.n, int((max(wy) + margin - self.y0) / self.res))
        v = self.votes[j0:j1, i0:i1].astype(float)
        img = np.full(v.shape + (3,), 40, np.uint8)
        img[v > 0] = (0, 90, 0)
        img[v >= min_votes] = (0, 220, 0)

        def px(p):
            return (int((p[0] - self.x0) / self.res) - i0, int((p[1] - self.y0) / self.res) - j0)

        for s in strips:
            cv2.line(img, px(s.entry), px(s.far), (0, 0, 255), 2)
            cv2.circle(img, px(s.entry), 6, (255, 0, 255), 2)
        for p in marks:
            cv2.drawMarker(img, px(p), (0, 255, 255), cv2.MARKER_CROSS, 12, 2)
        img = cv2.flip(img, 0)                                  # north up
        scale = max(1, int(600 / max(img.shape[:2])))
        return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
