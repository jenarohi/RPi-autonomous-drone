"""
Camera vision (pure functions on BGR numpy images - unit tested offline).

Two fixed cameras on base_link:
  down camera  : looks straight down,  image up = vehicle forward
  front camera : tilted 45 deg down,   image up = forward/up
In both, image right = vehicle right.
"""
import math
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

from . import config as C


# ── Camera model ───────────────────────────────────────────────────────────
class Camera:
    """Pinhole camera fixed on the vehicle, optical axis `tilt` rad below the
    horizontal (pi/2 = straight down)."""

    def __init__(self, width: int = 640, height: int = 480, hfov: float = C.CAM_HFOV,
                 tilt: float = math.pi / 2):
        self.hfov, self.tilt = hfov, tilt
        self.w, self.h = width, height
        self.cx, self.cy = width / 2.0, height / 2.0
        self.f = self.cx / math.tan(hfov / 2.0)

    def resize(self, width: int, height: int):
        if (width, height) != (self.w, self.h):
            self.__init__(width, height, self.hfov, self.tilt)

    def pixel_to_ground(self, u: float, v: float, height: float,
                        roll: float = 0.0, pitch: float = 0.0) -> Optional[Tuple[float, float]]:
        """Pixel -> (forward, right) metres on the ground in the level, heading-aligned
        frame, camera `height` above the ground. Roll/pitch (rad, ArduPilot sign
        convention) tilt the ray: nose-up makes the camera look further ahead.
        None if the pixel looks at or above the horizon."""
        a, b = (u - self.cx) / self.f, (self.cy - v) / self.f
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        x, y, z = ct + b * st, a, st - b * ct            # body FRD ray
        cr, sr, cp, sp = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch)
        y, z = cr * y - sr * z, sr * y + cr * z
        x, z = cp * x + sp * z, -sp * x + cp * z
        if z < 0.02:
            return None
        k = height / z
        return (x * k, y * k)

    def ground_points(self, u: np.ndarray, v: np.ndarray, height: float,
                      roll: float = 0.0, pitch: float = 0.0):
        """Vectorised pixel_to_ground: arrays u, v -> (forward, right, valid)."""
        a, b = (u - self.cx) / self.f, (self.cy - v) / self.f
        ct, st = math.cos(self.tilt), math.sin(self.tilt)
        x, y, z = ct + b * st, a, st - b * ct
        cr, sr, cp, sp = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch)
        y, z = cr * y - sr * z, sr * y + cr * z
        x, z = cp * x + sp * z, -sp * x + cp * z
        valid = z > 0.02
        k = height / np.where(valid, z, 1.0)
        return x * k, y * k, valid

    # nadir-only helpers (down camera)
    def metres_per_px(self, height: float) -> float:
        return height / self.f

    def footprint(self, height: float) -> Tuple[float, float]:
        """(forward length, lateral width) of the ground seen, metres."""
        return (self.h * height / self.f, self.w * height / self.f)


def DownCam(width: int = 640, height: int = 480) -> Camera:
    return Camera(width, height, C.CAM_HFOV, math.pi / 2)


def FrontCam(width: int = 640, height: int = 480) -> Camera:
    return Camera(width, height, C.FRONT_CAM_HFOV, C.FRONT_CAM_TILT)


# ── QR codes ───────────────────────────────────────────────────────────────
@dataclass
class QrHit:
    data: str
    u: float          # centre pixel
    v: float
    size: float       # side length, px


def _zbar(gray: np.ndarray, scale: float = 1.0, ox: float = 0.0, oy: float = 0.0) -> List[QrHit]:
    out = []
    for r in pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE]):
        pts = np.array([(p.x, p.y) for p in r.polygon], dtype=float)
        if len(pts) == 0:
            continue
        u, v = pts.mean(axis=0)
        size = math.sqrt(max(cv2.contourArea(pts.astype(np.float32)), 1.0))
        out.append(QrHit(r.data.decode("utf-8", "replace").strip(),
                         ox + u / scale, oy + v / scale, size / scale))
    return out


def qr_candidates(gray: np.ndarray, min_side: int = 14, max_side: int = 260):
    """Square-ish high-contrast patches (QR codes too small for a direct decode)."""
    edges = cv2.Canny(gray, 60, 160)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(edges)
    boxes = []
    for x, y, w, h, area in stats[1:]:
        if min_side <= w <= max_side and min_side <= h <= max_side and 0.6 < w / h < 1.6 \
                and area > 0.25 * w * h:
            boxes.append((x, y, w, h))
    return boxes


def decode_qrs(bgr: np.ndarray) -> List[QrHit]:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hits = _zbar(gray)
    # Small / oblique codes (frame edge, or ~2 px per module): crop each candidate that
    # is not already decoded, upscale 4x, unsharp-mask, adaptive threshold, re-try.
    # Always done - a wide frame can hold several codes, only some decode directly.
    H, W = gray.shape
    for x, y, w, h in qr_candidates(gray):
        if any(x - 5 <= hh.u <= x + w + 5 and y - 5 <= hh.v <= y + h + 5 for hh in hits):
            continue
        m = int(0.25 * max(w, h)) + 4
        x0, y0, x1, y1 = max(0, x - m), max(0, y - m), min(W, x + w + m), min(H, y + h + m)
        s = 4.0
        big = cv2.resize(gray[y0:y1, x0:x1], None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        sharp = cv2.addWeighted(big, 2.0, cv2.GaussianBlur(big, (0, 0), 0.8 * s), -1.0, 0)
        found = _zbar(sharp, s, x0, y0)
        if not found:
            bw = cv2.adaptiveThreshold(sharp, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                       int(8 * s) + 1, 0)
            found = _zbar(bw, s, x0, y0)
        hits += [f for f in found if all(f.data != h.data or abs(f.u - h.u) > 10 for h in hits)]
    return hits


def unread_qr_spots(bgr: np.ndarray, hits: List[QrHit], expect_px: float) -> List[Tuple[float, float]]:
    """Centres of square, high-contrast patches about the size of a QR code (expect_px
    side at the image centre) that did NOT decode - worth a closer look."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    out = []
    for x, y, w, h in qr_candidates(gray, min_side=max(10, int(0.35 * expect_px)),
                                    max_side=int(1.6 * expect_px)):
        cu, cv_ = x + w / 2.0, y + h / 2.0
        if any(abs(hh.u - cu) < max(w, h) and abs(hh.v - cv_) < max(w, h) for hh in hits):
            continue
        patch = gray[y:y + h, x:x + w]
        dark = (patch < 100).mean()
        if patch.std() > 50 and 0.2 < dark < 0.8:            # black/white mix like a QR
            out.append((cu, cv_))
    return out


def qr_scout(bgr: np.ndarray, cam: "Camera", height: float, roll: float = 0.0, pitch: float = 0.0,
             max_range: float = 30.0, side_m: float = 1.0) -> List[Tuple[float, float]]:
    """FRONT camera, far away: spots that look like a QR code lying on the ground -
    sharp black/white texture, not coloured, about the size a 1 m square would have
    at that distance (foreshortened). Too small to read; they are only places worth
    flying to. Returns ground points (forward, right) in metres."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mean = cv2.blur(gray, (5, 5))
    std = np.sqrt(np.maximum(cv2.blur(gray * gray, (5, 5)) - mean * mean, 0.0))
    sat = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[:, :, 1]
    bright = gray > np.median(gray) + 40
    mask = (((std > 30) | bright) & (sat < 70)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, _, stats, cents = cv2.connectedComponentsWithStats(mask)
    out = []
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if area < 6:
            continue
        g = cam.pixel_to_ground(cents[k][0], cents[k][1], height, roll, pitch)
        if g is None:
            continue
        rng = math.hypot(*g)
        if rng > max_range:
            continue
        slant = math.hypot(rng, height)
        exp_w = cam.f * side_m / slant                      # expected width in px
        exp_h = exp_w * height / slant                      # ... and height (foreshortened)
        if not (0.5 * exp_w <= w <= 1.8 * exp_w + 3 and 0.4 * exp_h <= h <= 2.2 * exp_h + 3):
            continue
        if area < 0.35 * w * h:
            continue
        out.append(g)
    return out


def parse_start_qr(payload: str) -> Optional[str]:
    """'TARGET:C' -> 'C'. Returns None for payloads that are not a start code."""
    m = re.match(r"^\s*TARGET\s*[:=]\s*(.+?)\s*$", payload, re.IGNORECASE)
    return m.group(1).upper() if m else None


def same_id(a: str, b: str) -> bool:
    return a.strip().upper() == b.strip().upper()


# ── Colour masks ───────────────────────────────────────────────────────────
def colour_mask(bgr: np.ndarray, colour: str) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in C.HSV[colour]:
        mask |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))


def largest_blob(mask: np.ndarray, min_area: int) -> Optional[np.ndarray]:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n <= 1:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[i, cv2.CC_STAT_AREA] < min_area:
        return None
    return (labels == i).astype(np.uint8)


@dataclass
class FloorAxis:
    u_centre: float     # centre-line column at the image centre row (px)
    slope: float        # du/dv of the centre line
    width_px: float     # median floor width
    rows: int           # rows used in the fit
    v_lo: float = 0.0   # first / last image row of the fit
    v_hi: float = 0.0


def floor_rows(bgr: np.ndarray, colour: str, step: int = 2) -> np.ndarray:
    """Rows of the largest blob of `colour` where BOTH edges are inside the image:
    array of (v, u_left, u_right)."""
    blob = largest_blob(colour_mask(bgr, colour), min_area=2000)
    if blob is None:
        return np.zeros((0, 3))
    H, W = blob.shape
    out = []
    for v in range(0, H, step):
        cols = np.flatnonzero(blob[v])
        if cols.size < 20:
            continue
        lo, hi = cols[0], cols[-1]
        if lo <= 2 or hi >= W - 3:
            continue
        out.append((v, lo, hi))
    return np.array(out, dtype=float).reshape(-1, 3)


def floor_axis(bgr: np.ndarray, colour: str, min_rows: int = 15) -> Optional[FloorAxis]:
    """Centre line of a coloured corridor floor strip running up the image (down camera)."""
    fr = floor_rows(bgr, colour)
    if len(fr) < min_rows:            # rows are sampled every 2 px
        return None
    rows, centres, widths = fr[:, 0], (fr[:, 1] + fr[:, 2]) / 2.0, fr[:, 2] - fr[:, 1]
    b, a = np.polyfit(rows, centres, 1)
    resid = centres - (a + b * rows)
    keep = np.abs(resid) < max(3.0, 2.5 * resid.std())
    if keep.sum() >= 10:
        b, a = np.polyfit(rows[keep], centres[keep], 1)
    cy = bgr.shape[0] / 2.0
    return FloorAxis(u_centre=a + b * cy, slope=b, width_px=float(np.median(widths)), rows=int(keep.sum()),
                     v_lo=float(rows.min()), v_hi=float(rows.max()))


def floor_ground_points(bgr: np.ndarray, colour: str, cam: Camera, height: float,
                        roll: float, pitch: float, width_m: float, max_range: float = 14.0):
    """Corridor floor seen by a (tilted) camera, projected to the ground.
    Returns an Nx2 array of centre-line points (forward, right) in metres, one per
    image row whose projected floor width is within 25 % of `width_m` (rows cut
    by a wall or the image edge are dropped)."""
    pts = []
    for v, lo, hi in floor_rows(bgr, colour):
        g_lo = cam.pixel_to_ground(lo, v, height, roll, pitch)
        g_hi = cam.pixel_to_ground(hi, v, height, roll, pitch)
        g_c = cam.pixel_to_ground((lo + hi) / 2.0, v, height, roll, pitch)
        if g_lo is None or g_hi is None or g_c is None or g_c[0] > max_range:
            continue
        w = math.hypot(g_hi[0] - g_lo[0], g_hi[1] - g_lo[1])
        if 0.75 * width_m < w < 1.25 * width_m:
            pts.append(g_c)
    return np.array(pts, dtype=float).reshape(-1, 2)


def colour_ground_samples(bgr: np.ndarray, colour: str, cam: Camera, height: float,
                          roll: float, pitch: float, max_range: float, step: int = 4) -> np.ndarray:
    """Every `step`-th pixel of `colour`, projected to the ground: Nx2 (forward, right)
    metres. Pixels at/above the horizon or further than max_range are dropped.
    Only valid for things lying on the ground (floor strips, mats)."""
    mask = colour_mask(bgr, colour)
    vs, us = np.nonzero(mask[step // 2::step, step // 2::step])
    if vs.size == 0:
        return np.zeros((0, 2))
    us = us * step + step // 2
    vs = vs * step + step // 2
    f, r, ok = cam.ground_points(us.astype(float), vs.astype(float), height, roll, pitch)
    ok &= np.hypot(f, r) < max_range
    if cam.tilt < math.pi / 2 - 0.01:                   # tilted camera: only ground ahead
        ok &= f > 0
    return np.column_stack([f[ok], r[ok]])


@dataclass
class EntranceEdge:
    fwd: float          # entrance midpoint, metres ahead of the drone
    right: float        # ... and to its right
    angle: float        # corridor axis direction, rad to the RIGHT of the nose
    width: float        # corner-to-corner length of the edge (m)
    pts: Tuple[Tuple[int, int], Tuple[int, int]]   # edge end pixels (debug)


def entrance_edge(bgr: np.ndarray, colour: str, cam: Camera, height: float,
                  roll: float = 0.0, pitch: float = 0.0) -> Optional[EntranceEdge]:
    """Near edge of a corridor floor seen from OUTSIDE the entrance (down camera).
    Close to tall walls the floor's side edges are hidden by the walls, but the near
    edge - a straight line from wall to wall - stays clean. Its bottom boundary is
    fitted with a line, its two ends projected to the ground: the midpoint is the
    entrance centre, the perpendicular is the corridor direction.
    None if the edge is not fully in view (floor touches the image sides/bottom)."""
    blob = largest_blob(colour_mask(bgr, colour), min_area=1500)
    if blob is None:
        return None
    H, W = blob.shape
    cols = np.flatnonzero(blob.any(axis=0))
    u0, u1 = int(cols[0]), int(cols[-1])
    if u0 <= 2 or u1 >= W - 3 or u1 - u0 < 60:
        return None
    bottom = H - 1 - np.argmax(blob[::-1, :], axis=0)          # lowest blob row per column
    if bottom[u0:u1 + 1].max() >= H - 3:
        return None                                              # floor runs out of the image bottom
    # The bottom boundary is the near edge plus, for a rotated corridor, part of a side
    # edge. Pick the straight, flat-ish segment with the most columns on it (RANSAC on
    # a column sample), then refine with a least-squares fit.
    us = np.arange(u0, u1 + 1)
    vs = bottom[us].astype(float)
    sample = np.linspace(0, len(us) - 1, min(40, len(us))).astype(int)
    best, best_n = None, 0
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            p, q = sample[i], sample[j]
            if us[q] - us[p] < 15:
                continue
            bb = (vs[q] - vs[p]) / (us[q] - us[p])
            if abs(bb) > 0.8:                                    # not a near edge
                continue
            aa = vs[p] - bb * us[p]
            n = int((np.abs(vs - (aa + bb * us)) < 2.5).sum())
            if n > best_n:
                best, best_n = (aa, bb), n
    if best is None or best_n < 30:
        return None
    a, b = best
    for _ in range(2):
        keep = np.abs(vs - (a + b * us)) < 3.0
        b, a = np.polyfit(us[keep], vs[keep], 1)
    # corners: where the bottom boundary leaves the edge line (a rotated floor's far
    # side can stick out further left/right than the near corners)
    on = np.concatenate([[0], (np.abs(vs - (a + b * us)) < 3.0).astype(int), [0]])
    d = np.diff(on)
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
    k = int(np.argmax(ends - starts))                           # longest straight run = the edge
    c0, c1 = u0 + int(starts[k]), u0 + int(ends[k])
    if c1 - c0 < 30:
        return None
    gl = cam.pixel_to_ground(c0, a + b * c0, height, roll, pitch)
    gr = cam.pixel_to_ground(c1, a + b * c1, height, roll, pitch)
    if gl is None or gr is None:
        return None
    ef, er = gr[0] - gl[0], gr[1] - gl[1]
    return EntranceEdge(fwd=(gl[0] + gr[0]) / 2, right=(gl[1] + gr[1]) / 2, angle=math.atan2(-ef, er),
                        width=math.hypot(ef, er), pts=((c0, int(a + b * c0)), (c1, int(a + b * c1))))


def draw_entrance(bgr: np.ndarray, edge: Optional[EntranceEdge]) -> np.ndarray:
    out = bgr.copy()
    if edge is not None:
        cv2.line(out, edge.pts[0], edge.pts[1], (0, 0, 255), 2)
        mu = ((edge.pts[0][0] + edge.pts[1][0]) // 2, (edge.pts[0][1] + edge.pts[1][1]) // 2)
        cv2.circle(out, mu, 6, (255, 0, 255), 2)
    cv2.line(out, (out.shape[1] // 2, 0), (out.shape[1] // 2, out.shape[0]), (255, 255, 0), 1)
    return out


def draw_floor_axis(bgr: np.ndarray, colour: str) -> np.ndarray:
    """Debug image: floor mask outline + fitted centre line."""
    out = bgr.copy()
    blob = largest_blob(colour_mask(bgr, colour), min_area=2000)
    if blob is not None:
        contours, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, contours, -1, (255, 0, 255), 2)
    fa = floor_axis(bgr, colour)
    if fa is not None:
        H = out.shape[0]
        u0 = fa.u_centre - fa.slope * H / 2
        cv2.line(out, (int(u0), 0), (int(u0 + fa.slope * H), H), (0, 0, 255), 2)
    cv2.line(out, (out.shape[1] // 2, 0), (out.shape[1] // 2, out.shape[0]), (255, 255, 0), 1)
    return out


def floor_measurement(fa: FloorAxis, cam: Camera, height: float,
                      roll: float = 0.0, pitch: float = 0.0) -> Tuple[float, float, float]:
    """-> (lateral offset of the centre line to the RIGHT of the drone (m),
           angle of the corridor axis to the RIGHT of the nose (rad),
           floor width (m)).
    Two points of the fitted image line are projected to the ground with the
    vehicle tilt, so a drone that is still rolled after a move measures right."""
    def centre_at(v):
        return cam.pixel_to_ground(fa.u_centre + fa.slope * (v - cam.cy), v, height, roll, pitch)

    v_top, v_bot = fa.v_lo, max(fa.v_hi, fa.v_lo + 1.0)
    f1, r1 = centre_at(v_top)          # further forward
    f2, r2 = centre_at(v_bot)
    df, dr = f1 - f2, r1 - r2
    if abs(df) < 1e-6:
        df = 1e-6
    lateral = r2 - f2 * dr / df        # where the line crosses fwd = 0
    return lateral, math.atan2(dr, df), fa.width_px * cam.metres_per_px(height)


def red_regions(bgr: np.ndarray, min_area: int = 150) -> List[np.ndarray]:
    """Corner pixels (4x2) of every red patch."""
    mask = colour_mask(bgr, "red")
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boxPoints(cv2.minAreaRect(c)) for c in contours if cv2.contourArea(c) >= min_area]
