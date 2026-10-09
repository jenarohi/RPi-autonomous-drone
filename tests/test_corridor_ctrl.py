"""Lidar geometry and the reactive corridor controller, against a synthetic ray-caster (no simulator)."""
import math

import numpy as np

from skyscan.lidar import LidarHub, free_distance, nearest, points, sector_min, wall_info
from skyscan.mission.corridor_ctrl import AvoidParams, CorridorController
from skyscan.types import LidarScan

INF = math.inf


def raycast(px, py, rects, n=360, rmax=12.0, rmin=0.15, yaw=0.0):
    """Scan from (px, py) in a world of axis-aligned rectangles (x0, x1, y0, y1); x forward, y LEFT.
    ``yaw`` (deg, CCW) rotates the vehicle nose in the world."""
    step = 360.0 / n
    ranges = []
    for i in range(n):
        a = math.radians(-180.0 + i * step + yaw)
        dx, dy = math.cos(a), math.sin(a)
        best = INF
        for x0, x1, y0, y1 in rects:
            tmin, tmax = 0.0, INF
            ok = True
            for p, d, lo, hi in ((px, dx, x0, x1), (py, dy, y0, y1)):
                if abs(d) < 1e-9:
                    if p < lo or p > hi:
                        ok = False
                        break
                else:
                    t1, t2 = (lo - p) / d, (hi - p) / d
                    tmin, tmax = max(tmin, min(t1, t2)), min(tmax, max(t1, t2))
            if ok and tmax >= tmin and tmin > 0:
                best = min(best, tmin)
        ranges.append(best if rmin <= best <= rmax else INF)
    return LidarScan(t=0.0, seq=1, angle_min_deg=-180.0, angle_step_deg=step, ranges=ranges, range_min=rmin, range_max=rmax)


# the green corridor of the canonical world, course frame: entrance x=9, 10 m long, inner width 3.3 m (walls 0.2 thick)
GREEN = [(9.0, 19.0, 1.65, 1.85), (9.0, 19.0, -1.85, -1.65)]
# the orange corridor's three obstacles (legacy world, sim/course.yaml obs1..3: right = 5.0 / 7.0 / 5.5, widths 1.0 / 1.0 / 1.2,
# corridor centre at right = 6.0), expressed in a corridor with the same walls but its centre line at y = 0 (y is LEFT)
ORANGE_WALLS = [(9.0, 19.0, 1.65, 1.85), (9.0, 19.0, -1.85, -1.65)]
OBSTACLES = [(11.8, 12.2, 0.5, 1.5), (13.8, 14.2, -1.5, -0.5), (15.8, 16.2, -0.1, 1.1)]


def test_wall_info_centred_and_offset():
    s = raycast(12.0, 0.0, GREEN)
    w = wall_info(s)
    assert w.both and abs(w.left_m - 1.65) < 0.06 and abs(w.right_m - 1.65) < 0.06
    assert abs(w.offset_m) < 0.06 and abs(w.width_m - 3.3) < 0.12
    s = raycast(12.0, 0.5, GREEN)                    # 0.5 m LEFT of centre
    w = wall_info(s)
    assert abs(w.left_m - 1.15) < 0.06 and abs(w.right_m - 2.15) < 0.06
    assert abs(w.offset_m - 0.5) < 0.06             # + = vehicle is left of centre


def test_wall_info_open_air_has_no_walls():
    w = wall_info(raycast(2.0, 0.0, GREEN))         # well before the entrance: side sectors are empty
    assert not w.any


def test_wall_info_heading_error():
    s = raycast(12.0, 0.0, GREEN, yaw=10.0)         # nose turned 10 deg to the left of the walls
    w = wall_info(s)
    assert w.turn_to_align_deg is not None and w.turn_to_align_deg < -6.0   # must turn RIGHT (negative) to realign


def test_sector_and_nearest():
    s = raycast(12.0, 0.0, GREEN + [(13.0, 13.4, -0.2, 0.2)])
    assert abs(sector_min(s, -5, 5) - 1.0) < 0.1
    assert nearest(s) < 1.1
    assert free_distance(*points(s)[:2], 0.0, 0.55, 3.5) < 1.2


def test_controller_centred_cruises():
    c = CorridorController()
    cmd = c.step(raycast(12.0, 0.0, GREEN))
    assert cmd.mode in ("CRUISE", "CENTER") and cmd.vx > 0.5 and abs(cmd.vy) < 0.1


def test_controller_recentres():
    c = CorridorController()
    for _ in range(4):
        cmd = c.step(raycast(12.0, 0.6, GREEN))     # left of centre -> must slide RIGHT (+vy)
    assert cmd.vy > 0.08 and cmd.vx > 0.3


def test_controller_avoids_obstacle_ahead():
    c = CorridorController()
    scan = raycast(10.0, 0.0, GREEN + [(11.5, 11.9, -0.3, 0.3)])   # 0.6 m wide block dead ahead (1.35 m gaps either side)
    for _ in range(5):
        cmd = c.step(scan)
    assert cmd.mode == "AVOID" and abs(cmd.vy) > 0.1
    assert cmd.free_m > 0.9


def test_controller_stops_in_front_of_a_full_barrier():
    """No gap: the vehicle may shuffle sideways at most a little, then must end up stopped, clear of every return."""
    c = CorridorController()
    world = GREEN + [(11.0, 11.4, -1.65, 1.65)]      # a full-width barrier
    x, y, dt = 8.0, 0.0, 0.1
    worst, cmd = INF, None
    for _ in range(400):
        scan = raycast(x, y, world)
        worst = min(worst, nearest(scan))
        cmd = c.step(scan)
        x += cmd.vx * dt
        y += -cmd.vy * dt
    assert cmd.mode == "BLOCKED" and cmd.vx == 0.0 and cmd.vy == 0.0
    assert worst > 0.5 and abs(y) < 1.2 and x < 10.6


def test_controller_clear_beyond_exit():
    c = CorridorController()
    cmd = c.step(raycast(21.0, 0.0, GREEN))          # past the end of the walls
    assert cmd.mode == "CRUISE" and cmd.vx > 0.5


def test_closed_loop_through_obstacle_corridor():
    """Fly the obstacle corridor with the controller on a point-mass vehicle: never closer than 0.4 m, gets through."""
    p = AvoidParams()
    c = CorridorController(p)
    x, y, dt = 8.0, 0.0, 0.1
    world = ORANGE_WALLS + OBSTACLES
    worst = INF
    for _ in range(900):
        scan = raycast(x, y, world)
        worst = min(worst, nearest(scan))
        cmd = c.step(scan)
        x += cmd.vx * dt
        y += -cmd.vy * dt                              # vy is to the RIGHT, y is LEFT
        if x > 19.5:
            break
    assert x > 19.0, f"stuck at x={x:.1f}"
    assert worst > 0.4, f"closest approach {worst:.2f} m"


def test_lidar_hub_stats_and_wire():
    hub = LidarHub()
    assert hub.latest() is None and hub.stats()["n"] == 0
    import time
    s = LidarScan(t=time.time(), seq=3, angle_min_deg=-180.0, angle_step_deg=1.0,
                  ranges=[1.234, INF, float("nan"), 50.0], range_min=0.15, range_max=12.0)
    hub.put(s)
    assert hub.fresh(1.0) is s and hub.stats()["n"] == 4
    w = s.to_wire()
    assert w["r"] == [1.23, None, None, None] and w["a0"] == -180.0
