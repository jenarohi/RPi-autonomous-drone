"""Pure 2-D geometry: frames, corridor axis, red-zone rectangles, detour planning."""
import heapq
import math
from typing import List, NamedTuple, Optional, Tuple

Point = Tuple[float, float]


def wrap_pi(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def dist(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def body_to_world(x: float, y: float, heading: float, fwd: float, right: float) -> Point:
    """Offset (fwd, right) in the vehicle frame -> world point."""
    c, s = math.cos(heading), math.sin(heading)
    return (x + fwd * c + right * s, y + fwd * s - right * c)


# ── Corridor axis ──────────────────────────────────────────────────────────
class CorridorAxis:
    """Straight corridor. s = distance along the axis from the entry,
    d = lateral offset (left of the travel direction positive)."""

    def __init__(self, name: str, entry: Point, exit_: Point, colour: str):
        self.name, self.colour = name, colour
        self.entry = (float(entry[0]), float(entry[1]))
        self.exit = (float(exit_[0]), float(exit_[1]))
        self.length = dist(self.entry, self.exit)
        self.heading = math.atan2(self.exit[1] - self.entry[1], self.exit[0] - self.entry[0])

    @classmethod
    def from_config(cls, c: dict) -> "CorridorAxis":
        return cls(c["name"], c["entry"], c["exit"], c["colour"])

    @property
    def t(self) -> Point:
        return (math.cos(self.heading), math.sin(self.heading))

    @property
    def n(self) -> Point:
        return (-math.sin(self.heading), math.cos(self.heading))

    def to_sd(self, x: float, y: float) -> Point:
        dx, dy = x - self.entry[0], y - self.entry[1]
        t, n = self.t, self.n
        return (dx * t[0] + dy * t[1], dx * n[0] + dy * n[1])

    def from_sd(self, s: float, d: float) -> Point:
        t, n = self.t, self.n
        return (self.entry[0] + s * t[0] + d * n[0], self.entry[1] + s * t[1] + d * n[1])

    def realigned(self, point: Point, heading: float) -> "CorridorAxis":
        """Same corridor, axis moved to pass through `point` with `heading`
        (a camera measurement). Entry/exit are projected onto the new line."""
        t = (math.cos(heading), math.sin(heading))

        def project(p: Point) -> Point:
            k = (p[0] - point[0]) * t[0] + (p[1] - point[1]) * t[1]
            return (point[0] + k * t[0], point[1] + k * t[1])

        entry = project(self.entry)
        exit_ = (entry[0] + self.length * t[0], entry[1] + self.length * t[1])
        return CorridorAxis(self.name, entry, exit_, self.colour)


# ── Rectangles (red zones) ─────────────────────────────────────────────────
class Rect(NamedTuple):
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def inflate(self, m: float) -> "Rect":
        return Rect(self.xmin - m, self.xmax + m, self.ymin - m, self.ymax + m)

    def contains(self, p: Point, eps: float = 0.0) -> bool:
        return (self.xmin + eps < p[0] < self.xmax - eps) and (self.ymin + eps < p[1] < self.ymax - eps)

    def overlaps(self, o: "Rect", gap: float = 0.0) -> bool:
        return not (o.xmin > self.xmax + gap or o.xmax < self.xmin - gap or
                    o.ymin > self.ymax + gap or o.ymax < self.ymin - gap)

    def union(self, o: "Rect") -> "Rect":
        return Rect(min(self.xmin, o.xmin), max(self.xmax, o.xmax),
                    min(self.ymin, o.ymin), max(self.ymax, o.ymax))

    def corners(self) -> List[Point]:
        return [(self.xmin, self.ymin), (self.xmax, self.ymin),
                (self.xmax, self.ymax), (self.xmin, self.ymax)]

    def centre(self) -> Point:
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2)


def rect_from_points(pts: List[Point]) -> Rect:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return Rect(min(xs), max(xs), min(ys), max(ys))


def segment_hits_rect(a: Point, b: Point, r: Rect) -> bool:
    """True if segment a-b passes through the open interior of r (Liang-Barsky)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - r.xmin), (dx, r.xmax - a[0]),
                 (-dy, a[1] - r.ymin), (dy, r.ymax - a[1])):
        if abs(p) < 1e-12:
            if q <= 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return False
    # touching only an edge or a corner does not count
    mid = (a[0] + dx * (t0 + t1) / 2, a[1] + dy * (t0 + t1) / 2)
    return r.contains(mid, eps=1e-6)


def segment_clear(a: Point, b: Point, rects: List[Rect]) -> bool:
    return not any(segment_hits_rect(a, b, r) for r in rects)


def push_out(p: Point, rects: List[Rect], extra: float = 0.1) -> Point:
    """If p is inside a rectangle, move it to the nearest point just outside."""
    for _ in range(4):
        inside = [r for r in rects if r.contains(p)]
        if not inside:
            return p
        r = inside[0]
        options = [((r.xmin - extra, p[1]), p[0] - r.xmin), ((r.xmax + extra, p[1]), r.xmax - p[0]),
                   ((p[0], r.ymin - extra), p[1] - r.ymin), ((p[0], r.ymax + extra), r.ymax - p[1])]
        p = min(options, key=lambda o: o[1])[0]
    return p


def plan_path(a: Point, b: Point, rects: List[Rect]) -> Optional[List[Point]]:
    """Shortest path a -> b around rectangles (visibility graph over corners).
    Returns the waypoints after `a` (ending with b), or None if b is unreachable."""
    if any(r.contains(b) for r in rects):
        return None
    if segment_clear(a, b, rects):
        return [b]
    nodes = [a, b]
    for r in rects:
        for c in r.inflate(0.05).corners():
            if not any(o.contains(c) for o in rects):
                nodes.append(c)
    best = {0: 0.0}
    prev = {}
    heap = [(0.0, 0)]
    while heap:
        cost, i = heapq.heappop(heap)
        if i == 1:
            break
        if cost > best.get(i, math.inf):
            continue
        for j in range(1, len(nodes)):
            if j == i or not segment_clear(nodes[i], nodes[j], rects):
                continue
            c = cost + dist(nodes[i], nodes[j])
            if c < best.get(j, math.inf):
                best[j], prev[j] = c, i
                heapq.heappush(heap, (c, j))
    if 1 not in prev:
        return None
    path, k = [], 1
    while k != 0:
        path.append(nodes[k])
        k = prev[k]
    return path[::-1]


def lawnmower(zone: Tuple[float, float, float, float], lane_spacing: float,
              lane_inset_y: float, inset_x: float, start: Point) -> List[Point]:
    """East-west lanes over zone=(xmin,xmax,ymin,ymax), snake order, beginning
    with the outer lane and lane end closest to `start`."""
    xmin, xmax, ymin, ymax = zone
    lo, hi = ymin + lane_inset_y, ymax - lane_inset_y
    n = max(1, math.ceil((hi - lo) / lane_spacing - 1e-9) + 1)
    ys = [lo + i * (hi - lo) / (n - 1) for i in range(n)] if n > 1 else [(lo + hi) / 2]
    if abs(start[1] - ys[-1]) < abs(start[1] - ys[0]):
        ys.reverse()
    x0, x1 = xmin + inset_x, xmax - inset_x
    if abs(start[0] - x1) < abs(start[0] - x0):
        x0, x1 = x1, x0
    wps = []
    for i, y in enumerate(ys):
        a, b = (x0, x1) if i % 2 == 0 else (x1, x0)
        wps += [(a, y), (b, y)]
    return wps


def snap_grid(zone: Tuple[float, float, float, float], across: float, along: float,
              start: Point) -> Tuple[List[Point], float]:
    """Stop-and-snap points covering `zone` (xmin, xmax, ymin, ymax) with a down-camera
    footprint `across` (image width) x `along` (image height) metres.
    Heading 0 (east): image height lies along x; heading pi/2 (north): image width
    lies along x. The heading needing fewer stops is used. Points are the centres of
    an even grid, visited in a zig-zag starting at the corner nearest `start`.
    Returns (points, heading)."""
    xmin, xmax, ymin, ymax = zone
    lx, ly = xmax - xmin, ymax - ymin
    options = []
    for heading, fx, fy in ((0.0, along, across), (math.pi / 2, across, along)):
        nx, ny = max(1, math.ceil(lx / fx - 1e-6)), max(1, math.ceil(ly / fy - 1e-6))
        options.append((nx * ny, heading, nx, ny))
    _, heading, nx, ny = min(options)
    xs = [xmin + (i + 0.5) * lx / nx for i in range(nx)]
    ys = [ymin + (j + 0.5) * ly / ny for j in range(ny)]
    if abs(start[0] - xmax) < abs(start[0] - xmin):
        xs.reverse()
    if abs(start[1] - ymax) < abs(start[1] - ymin):
        ys.reverse()
    pts: List[Point] = []
    if nx >= ny:                                   # long rows along x, step in y
        for j, y in enumerate(ys):
            pts += [(x, y) for x in (xs if j % 2 == 0 else xs[::-1])]
    else:                                          # long columns along y, step in x
        for i, x in enumerate(xs):
            pts += [(x, y) for y in (ys if i % 2 == 0 else ys[::-1])]
    return pts, heading
