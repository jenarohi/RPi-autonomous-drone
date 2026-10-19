"""
Tiny 2-D kinematic simulator for the corridor logic (no Gazebo needed).

The drone is a point with a first-order velocity response (like ArduPilot's
GUIDED velocity control), the LiDAR is ray-cast against the same boxes as
create_world.py. The control loop mirrors Mission.traverse: locked heading
corrected from the wall lines, lidar.plan_step for centring/avoidance, and
inside/exit decided from the walls only.
"""
import math

import numpy as np

from skyscan import config as C
from skyscan import lidar
from skyscan.geometry import CorridorAxis, clamp, wrap_pi

# corridors of create_world.py (used only by the tests)
GREEN = dict(name="green", entry=(6.0, 3.0), exit=(16.0, 3.0), colour="green")
ORANGE = dict(name="orange", entry=(16.0, -3.0), exit=(6.0, -3.0), colour="orange")

# (cx, cy, sx, sy) from create_world.py
WALLS = [(11, 4.75, 10, 0.2), (11, 1.25, 10, 0.2), (11, -1.25, 10, 0.2), (11, -4.75, 10, 0.2)]
OBSTACLES = [(9, -2.0, 0.4, 1.0), (11, -4.0, 0.4, 1.0), (13, -2.5, 0.4, 1.2)]
BOXES = WALLS + OBSTACLES


def raycast(p, ang, boxes=BOXES, rmax=12.0):
    d = (math.cos(ang), math.sin(ang))
    best = math.inf
    for cx, cy, sx, sy in boxes:
        lo = (cx - sx / 2, cy - sy / 2)
        hi = (cx + sx / 2, cy + sy / 2)
        t0, t1 = -math.inf, math.inf
        for k in range(2):
            if abs(d[k]) < 1e-12:
                if not lo[k] <= p[k] <= hi[k]:
                    t0, t1 = 1, 0
                continue
            a, b = (lo[k] - p[k]) / d[k], (hi[k] - p[k]) / d[k]
            t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
        if t0 <= t1 and t0 > 0:
            best = min(best, t0)
    return best if best <= rmax else math.inf


def box_distance(p, box):
    cx, cy, sx, sy = box
    dx = max(abs(p[0] - cx) - sx / 2, 0.0)
    dy = max(abs(p[1] - cy) - sy / 2, 0.0)
    return math.hypot(dx, dy)


def run_corridor(corr_cfg, start_offset=0.0, heading_err_deg=0.0, tau=0.35, t_max=120.0,
                 boxes=BOXES, noise=0.01, seed=1):
    """heading_err_deg = error of the heading the drone locks at the entrance
    (the yaw the drone actually flies is assumed to follow the lock instantly)."""
    rng = np.random.default_rng(seed)
    axis = CorridorAxis.from_config(corr_cfg)
    p = np.array(axis.from_sd(-C.APPROACH_DIST, start_offset), dtype=float)
    v = np.zeros(2)
    heading = wrap_pi(axis.heading + math.radians(heading_err_deg))
    angles = np.linspace(-math.pi, math.pi, 360)
    step_a = angles[1] - angles[0]
    t, dt, ctrl_dt, next_ctrl = 0.0, 0.02, 0.1, 0.0
    v_cmd = np.zeros(2)
    inside, n_in, n_out = False, 0, 0
    min_clear, trace = math.inf, []
    while t < t_max:
        if t >= next_ctrl:
            next_ctrl += ctrl_dt
            ranges = [raycast(p, heading + a, boxes) + rng.normal(0, noise) for a in angles]
            pc = lidar.scan_to_points(ranges, -math.pi, step_a)      # body = locked-heading frame
            st = lidar.plan_step(pc)
            wa = lidar.wall_angle(pc)
            if inside and wa is not None and abs(wa) < math.radians(15):
                heading = wrap_pi(heading + C.HEADING_FROM_WALLS_GAIN * wa)
            n_in = n_in + 1 if lidar.walls_both_sides(st) else 0
            n_out = n_out + 1 if (inside and lidar.walls_none(st)) else 0
            if not inside and n_in >= C.WALL_CONFIRM_SCANS:
                inside = True
            if inside and n_out >= C.EXIT_CONFIRM_SCANS:
                s, _ = axis.to_sd(*p)
                return dict(ok=True, t=t, min_clear=min_clear, exit_s=s,
                            heading_err=math.degrees(wrap_pi(heading - axis.heading)), trace=trace)
            if st is None:
                v_fwd, v_lat = 0.0, 0.0
            else:
                v_fwd = lidar.forward_speed(st)
                v_lat = clamp(C.CORRIDOR_K_LAT * st.target, -C.CORRIDOR_MAX_LAT, C.CORRIDOR_MAX_LAT)
            tvec = np.array((math.cos(heading), math.sin(heading)))
            nvec = np.array((-tvec[1], tvec[0]))
            v_cmd = v_fwd * tvec + v_lat * nvec
        v += (v_cmd - v) * dt / tau
        p += v * dt
        t += dt
        min_clear = min(min_clear, min(box_distance(p, b) for b in boxes))
        trace.append((t, p[0], p[1]))
    return dict(ok=False, t=t, min_clear=min_clear, exit_s=None, heading_err=None, trace=trace)


if __name__ == "__main__":
    for cfg in (GREEN, ORANGE):
        for off, herr in ((0.0, 0.0), (0.6, 0.0), (-0.6, 5.0), (0.3, -8.0)):
            r = run_corridor(cfg, off, herr)
            print(f"{cfg['name']:6s} offset {off:+.1f} lock err {herr:+.0f} deg -> "
                  f"{'OK ' if r['ok'] else 'FAIL'} t={r['t']:5.1f}s min clearance {r['min_clear']:.2f} m "
                  f"exit at s={r['exit_s'] if r['exit_s'] is None else round(r['exit_s'], 2)} "
                  f"final heading err {r['heading_err'] if r['heading_err'] is None else round(r['heading_err'], 1)}")
