"""Stage D implementations (D1-D3): the start of the return lap.

D1: after the payload is released, climb straight up to the 10 m return altitude and clear the drop point
D2: find the orange return corridor (front camera) and localise its entrance and axis
D3: approach it around the red zones and align on its centre line in front of the entrance

Rulebook Mission 2 (p.36-37): "After payload delivery, the UAS must ascend to 10-meter altitude, navigate back through
the corridor while avoiding obstacles ... Corridor Entry Detection Return Lap: detect the corridor-entrance banner and
autonomously align with the corridor before beginning corridor navigation". In the simulated world (the canonical one,
legacy/create_world.py) the return corridor is the ORANGE floor 3.5 m x 10 m between two grey walls, with obstacles; the
rulebook text says green for the banner, so the colour is a setting of the vision pipeline, not of the stages.

Sensors: the front camera (corridor floor, projected onto the ground plane exactly as in A4), the belly camera (red
zones, via the C-stage observer), the flight controller's height reference and the EKF position. Simulator ground truth
is read only to cross-check results afterwards, never to fly. D3 stops in front of the entrance at the return altitude:
descending to the corridor height and flying through it belongs to the stages after it.
"""
from __future__ import annotations

import math
import time
from typing import Any

from skyscan.geo import ang_diff, level_to_ned, wrap180, wrap360
from skyscan.mission.context import MissionContext
from skyscan.mission.search import Pt, Zone, ZoneGrid, dist, unit
from skyscan.mission.stage import Stage
from skyscan.mission.stage_a import StageA4, _confirmed_corridor
from skyscan.mission.stage_c import (ZoneFlight, ZoneNavigator, ZoneObserver, ZoneState, _fmt, vehicle_checks, zone_state)
from skyscan.types import Check, Sev
from skyscan.utils.logger import get_logger

log = get_logger("STAGE/D")

LOOP_S = 0.1


# ───────────────────────────── config helpers ─────────────────────────────

def _group(ctx: MissionContext) -> Any:
    return getattr(getattr(ctx.full_cfg, "mission", None), "stage_d", None) or {}


def return_alt(ctx: MissionContext) -> float:
    return float(getattr(_group(ctx), "return_alt_m", 10.0))


def alt_tol(ctx: MissionContext) -> float:
    return float(getattr(_group(ctx), "alt_tol_m", 0.5))


# ───────────────────────────── geometry (pure, unit tested) ─────────────────────────────

def bearing_rel_deg(frm: Pt, to: Pt) -> float:
    """Direction from ``frm`` to ``to`` as a course-relative heading (0 = course forward, + = clockwise / to the right)."""
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0]))


def entrance_estimate(course: Any, ned: tuple[float, float, float], yaw_deg: float, meas: dict[str, float]) -> dict[str, float]:
    """Where a corridor measurement says the entrance is: its centre in the course frame and the axis heading.

    ``meas`` is what the corridor detector reports in the vehicle's level frame: distance along the axis to the entrance
    line, lateral offset of the centre line (+ = right), and the axis heading minus the vehicle heading (+ = turn right).
    """
    yaw = math.radians(meas["yaw_err_deg"])
    d_fwd = math.cos(yaw) * meas["distance_m"] - math.sin(yaw) * meas["lateral_m"]
    d_right = math.sin(yaw) * meas["distance_m"] + math.cos(yaw) * meas["lateral_m"]
    n, e, d = level_to_ned(ned, yaw_deg, d_fwd, d_right, 0.0)
    f, r, _ = course.to_course(n, e, ned[2])
    axis_abs = wrap360(yaw_deg + meas["yaw_err_deg"])
    return {"fwd": f, "right": r, "axis_heading_deg": axis_abs, "axis_rel_deg": wrap180(course.rel_heading(axis_abs))}


def standoff_point(entrance: Pt, axis_rel_deg: float, standoff_m: float) -> Pt:
    """The point ``standoff_m`` before the entrance, on the corridor's centre line (the vehicle arrives travelling along
    the axis)."""
    a = (math.cos(math.radians(axis_rel_deg)), math.sin(math.radians(axis_rel_deg)))
    return (entrance[0] - a[0] * standoff_m, entrance[1] - a[1] * standoff_m)


# ───────────────────────────── shared pieces ─────────────────────────────

def _pos(ctx: MissionContext, course: Any) -> Pt:
    f, r, _ = course.to_course(*ctx.state().ned)
    return (f, r)


def front_camera_check(ctx: MissionContext, blocking: bool = True) -> Check:
    cam = ctx.vision.hub.stats("front") if (ctx.vision is not None and hasattr(ctx.vision, "hub")) else {}
    age = cam.get("age_s")
    return Check(name="Front camera streaming", ok=bool(age is not None and age < 3.0 and cam.get("fps", 0) > 0), blocking=blocking,
                 detail=f"fps={cam.get('fps')} age={age}s", value=cam.get("fps"))


def _corridor_conf(ctx: MissionContext) -> int:
    bcfg = getattr(getattr(ctx.full_cfg, "vision", None), "banner", None)
    return int(getattr(bcfg, "confirm_frames", 3))


def _look_for_orange(ctx: MissionContext) -> bool:
    """Point the corridor detector at the orange corridor. False when the vision pipeline cannot."""
    vis = ctx.vision
    return bool(vis is not None and hasattr(vis, "set_corridor_colour") and vis.set_corridor_colour("orange"))


def _acquire(ctx: MissionContext, window_s: float, since: float | None = None) -> dict[str, float] | None:
    """A stable corridor measurement taken after ``since`` within ``window_s`` seconds (None if there is none)."""
    n_conf = _corridor_conf(ctx)
    t0 = time.time()
    since = t0 if since is None else since
    while time.time() - t0 < window_s:
        ctx.check_abort()
        m = _confirmed_corridor(ctx, n_conf, since)
        if m:
            return m
        time.sleep(0.2)
    return None


def _nav_rig(ctx: MissionContext, course: Any, alt: float, heading_deg: float) -> tuple[ZoneState, ZoneFlight, ZoneNavigator]:
    """The C-stage red-zone navigator on a map that reaches from the delivery zone back to the corridor.

    The red zones C2 mapped are copied into the bigger grid; the belly camera keeps adding any it sees on the way back, and
    the same halt / reverse / sidestep protocol applies.
    """
    g = _group(ctx)
    nz = getattr(g, "nav_zone", None) or {}
    zone = Zone.from_cfg(nz) if nz else Zone(8.0, 66.0, -16.0, 22.0)
    zs = ZoneState(ctx)
    old = zs.grid
    zs.zone = zone
    zs.grid = ZoneGrid(zone, res_m=old.res, margin_m=old.margin, confirm_hits=old.confirm_hits, fence_inset_m=old.inner.fwd_min - old.zone.fwd_min)
    prev = zone_state(ctx)
    if prev is not None:
        for fmin, fmax, rmin, rmax in prev.grid.red_boxes():
            poly = [(fmin, rmin), (fmax, rmin), (fmax, rmax), (fmin, rmax)]
            for _ in range(zs.grid.confirm_hits):
                zs.grid.add_polygon(poly)
    nav_cfg = getattr(getattr(getattr(ctx.full_cfg, "mission", None), "stage_c", None), "nav", None) or {}
    flight = ZoneFlight(ctx, course, alt, nav_cfg)
    flight.heading = float(heading_deg)
    observer = ZoneObserver(ctx, course, zs)
    nav = ZoneNavigator(ctx, course, zs, flight, observer)
    return zs, flight, nav


# ───────────────────────────── D1: post-delivery ascent and clearance ─────────────────────────────

class StageD1(Stage):
    id = "D1"
    title = "Post-Delivery Ascent & Clearance"
    rulebook = "Stage D, D1: after delivery climb to the 10 m return altitude, straight up, clear of the drop point"
    summary = "Check the rope is wound in, then climb vertically over the drop point to 10 m and hold. No sideways move until clear."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        deliv = ctx.mission.get("delivery")
        winch = (deliv or {}).get("winch") or {}
        rope = winch.get("rope_out_m")
        hanging = bool(deliv) and not (winch.get("phase") in ("stowed", "released") and (rope or 0.0) < 0.1)
        checks = vehicle_checks(ctx, 2.0)
        checks.append(Check(name="Payload delivered and released (C4)", ok=bool(deliv and deliv.get("released")), blocking=False,
                            detail="C4 result available" if deliv else "C4 not run in this session"))
        checks.append(Check(name="Rope wound in (nothing hanging below the vehicle)", ok=not hanging,
                            detail=f"winch {winch.get('phase')}, {rope} m out" if deliv else "no delivery record: not checked"))
        checks.append(front_camera_check(ctx, blocking=False))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        g = _group(ctx)
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None:
            ctx.emit("Cannot run D1 without the course frame and a position fix", Sev.ERROR)
            return False
        target = return_alt(ctx)
        tol = alt_tol(ctx)
        climb = float(getattr(cfg, "climb_mps", 0.8))
        clear_m = float(getattr(cfg, "clearance_m", 3.0))
        drift_max = float(getattr(cfg, "max_drift_m", 1.0))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        timeout = float(getattr(cfg, "timeout_s", 60.0))
        h0, src = ctx.height()
        if h0 is None:
            ctx.emit("No height reference available", Sev.ERROR)
            return False
        n0, e0, _ = st.ned
        yaw = st.yaw_deg if st.yaw_deg is not None else course.heading_deg
        f0, r0, _ = course.to_course(*st.ned)
        ctx.metric("height_source", src)
        ctx.metric("start_height_m", round(h0, 2))
        ctx.emit(f"Payload clear: climbing straight up from {h0:.1f} m to the {target:.0f} m return altitude")
        t0 = time.time()
        drift = 0.0
        in_tol_since: float | None = None
        reached = False
        while time.time() - t0 < timeout:
            ctx.check_abort()
            st = ctx.state()
            h, _ = ctx.height()
            if h is None or st.ned is None:
                time.sleep(LOOP_S)
                continue
            drift = max(drift, math.hypot(st.ned[0] - n0, st.ned[1] - e0))
            err = target - h
            step = max(-climb, min(climb, err))
            ctx.link.goto_ned(n0, e0, st.ned[2] - step, yaw_deg=yaw)         # same N/E every time: straight up
            ctx.phase(f"Climbing: height {h:.1f} m -> {target:.0f} m", progress=min(1.0, max(0.0, (h - h0) / max(0.1, target - h0))))
            if abs(err) <= tol:
                in_tol_since = in_tol_since or time.time()
                if time.time() - in_tol_since >= stable_s:
                    reached = True
                    break
            else:
                in_tol_since = None
            time.sleep(LOOP_S)
        climb_s = time.time() - t0
        st = ctx.state()
        h, _ = ctx.height()
        gain = None if h is None else h - h0
        ctx.metric("final_height_m", None if h is None else round(h, 2))
        ctx.metric("climb_s", round(climb_s, 1))
        ctx.metric("sideways_drift_m", round(drift, 2))
        ctx.metric("height_gained_m", None if gain is None else round(gain, 2))
        ctx.snapshot("down", "d1_drop_point_clear")
        ctx.output("ascent", {"drop_point": {"fwd": round(f0, 2), "right": round(r0, 2)}, "height_m": None if h is None else round(h, 2),
                              "climb_s": round(climb_s, 1)})
        criteria = [
            Check(name=f"Return altitude reached ({target:.0f} m AGL)", ok=bool(reached and h is not None and abs(h - target) <= tol),
                  value=None if h is None else round(h, 2), limit=target),
            Check(name=f"Climbed straight up (<= {drift_max:.1f} m sideways)", ok=(drift <= drift_max), value=round(drift, 2), limit=drift_max),
            Check(name=f"Clear of the drop point (>= {clear_m:.0f} m above it before moving)", ok=bool(gain is not None and gain >= min(clear_m, target - h0 - 0.5)),
                  value=None if gain is None else round(gain, 2), limit=clear_m),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"D1 SUCCESS: {_fmt(h)} above the drop point after {climb_s:.0f} s, {drift:.2f} m sideways", Sev.GOOD)
        return success


# ───────────────────────────── D2: orange corridor localisation ─────────────────────────────

class StageD2(Stage):
    id = "D2"
    title = "Orange Corridor Localization"
    rulebook = "Stage D, D2: find the return corridor (orange) and localise its entrance and axis"
    summary = ("Face back toward the start, look for the orange corridor with the front camera (sweeping the heading, then "
               "hopping closer if it is too far to measure), and record where its entrance is and which way it runs.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        h, src = ctx.height()
        target = return_alt(ctx)
        checks = vehicle_checks(ctx, 5.0)
        checks.append(Check(name=f"At the return altitude ({target:.0f} m)", ok=bool(h is not None and abs(h - target) <= alt_tol(ctx) + 1.0),
                            value=None if h is None else round(h, 2), limit=target, detail=f"height {_fmt(h)} from the {src}"))
        checks.append(front_camera_check(ctx))
        checks.append(Check(name="Vision can look for the orange corridor", ok=hasattr(ctx.vision, "set_corridor_colour")))
        checks.append(Check(name="Payload delivered (C4) and cleared (D1)", ok=bool(ctx.mission.get("delivery") and ctx.mission.get("ascent")),
                            blocking=False, detail="" if ctx.mission.get("ascent") else "D1 not run in this session"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None or st.yaw_deg is None:
            ctx.emit("Cannot run D2 without the course frame and a position fix", Sev.ERROR)
            return False
        if not _look_for_orange(ctx):
            ctx.emit("The vision pipeline cannot look for the orange corridor", Sev.ERROR)
            return False
        gimbal = float(getattr(cfg, "gimbal_pitch_deg", -30.0))
        dwell = float(getattr(cfg, "search_dwell_s", 3.0))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        sweep = list(getattr(cfg, "search_headings_deg", [0, -15, 15, -30, 30, -45, 45, -70, 70]))
        hop_m = float(getattr(cfg, "hop_m", 8.0))
        max_hops = int(getattr(cfg, "max_hops", 3))
        axis_tol = float(getattr(cfg, "axis_tol_deg", 30.0))
        width_exp = float(getattr(getattr(getattr(ctx.full_cfg, "vision", None), "banner", None), "corridor_width_m", 3.5))
        prior_cfg = getattr(cfg, "prior", None)
        prior: Pt = (float(prior_cfg[0]), float(prior_cfg[1])) if prior_cfg else (0.0, 0.0)      # default: the take-off point
        target = return_alt(ctx)
        tol = alt_tol(ctx)
        hold_d = course.to_ned(0.0, 0.0, target)[2]
        t_stage = time.time()

        ctx.phase(f"Pitching the front camera to {gimbal:.0f} deg")
        ctx.link.set_gimbal(gimbal, 0.0)
        ctx.wait(lambda s: s.gimbal_pitch_deg is not None and abs(s.gimbal_pitch_deg - gimbal) < 3.0, 8.0, "gimbal at pitch")
        ctx.sleep(1.0)

        meas: dict[str, float] | None = None
        tried: list[float] = []
        hops = 0
        zs = flight = nav = None
        for hop in range(max_hops + 1):
            here = _pos(ctx, course)
            prior_rel = bearing_rel_deg(here, prior)
            ctx.emit(f"Looking for the orange corridor toward the start (course heading {prior_rel:+.0f} deg, "
                     f"{dist(here, prior):.0f} m away)" if hop == 0 else f"Not in measurable range yet: looking again from ({here[0]:.0f}, {here[1]:.0f})")
            hold = ctx.state()
            for rel in [0.0] + [float(x) for x in sweep if float(x) != 0.0]:
                ctx.check_abort()
                yaw = course.abs_heading(prior_rel + rel)
                ctx.phase(f"Looking toward heading {yaw:.0f} deg (prior {rel:+.0f} deg)")
                StageA4._fly_to(ctx, (hold.ned[0], hold.ned[1], hold_d, yaw), 14.0, xy_tol=0.6, yaw_tol=5.0, alt_tol=0.6)
                tried.append(round(prior_rel + rel, 1))
                meas = _acquire(ctx, dwell)
                if meas:
                    break
            if meas:
                break
            if hop == max_hops or dist(here, prior) <= hop_m + 4.0:
                break
            hops += 1
            d = unit(prior[0] - here[0], prior[1] - here[1])
            goal = (here[0] + d[0] * hop_m, here[1] + d[1] * hop_m)
            ctx.emit(f"Moving {hop_m:.0f} m closer ({hops}/{max_hops}) around any red zone")
            if flight is None:
                zs, flight, nav = _nav_rig(ctx, course, target, course.abs_heading(prior_rel))
            flight.heading = course.abs_heading(prior_rel)
            res = nav.go_to(goal, timeout_s=60.0)
            if res not in ("done", "stopped"):
                ctx.emit(f"Could not move closer ({res})", Sev.WARN)
                break
        if meas is None:
            ctx.emit("Orange corridor not found", Sev.ERROR)
            ctx.report.criteria = [Check(name="Orange corridor detected", ok=False, detail=f"no stable detection; headings tried {tried}")]
            ctx.snapshot("front", "d2_corridor_not_found")
            return False
        first = dict(meas)
        ctx.emit(f"Orange corridor seen: entrance {meas['distance_m']:.1f} m ahead, centre line {meas['lateral_m']:+.2f} m, "
                 f"axis {meas['yaw_err_deg']:+.1f} deg, width {meas['width_m']:.2f} m", Sev.GOOD)
        ctx.snapshot("front", "d2_corridor_detected")

        # hold still, keep measuring, and take the median entrance estimate
        ctx.phase(f"Holding to localise the entrance for {stable_s:.0f} s")
        hp = ctx.state()
        est: list[dict[str, float]] = []
        meas_s: list[dict[str, float]] = []
        t_h = time.time()
        last_t = t_h
        while time.time() - t_h < max(stable_s, 1.0) + 1.5:
            ctx.check_abort()
            ctx.link.goto_ned(hp.ned[0], hp.ned[1], hp.ned[2], yaw_deg=hp.yaw_deg)
            cur = ctx.state()
            # every plausible single frame counts here (the entrance is far away and a 3-in-a-row lock flickers); the median
            # of many estimates is what is reported
            for d in ctx.vision.banner_track(8):
                if d.t > last_t and d.t >= t_h and d.found and d.plane_ok and cur.ned is not None:
                    last_t = d.t
                    m = {k: float(getattr(d, k)) for k in ("distance_m", "lateral_m", "yaw_err_deg", "width_m", "bearing_deg", "score")}
                    meas_s.append(m)
                    est.append(entrance_estimate(course, cur.ned, cur.yaw_deg or 0.0, m))
            time.sleep(0.3)
        if not est:
            m = meas
            cur = ctx.state()
            est = [entrance_estimate(course, cur.ned, cur.yaw_deg or 0.0, m)]
            meas_s = [m]
            ctx.emit("No steady measurement while holding: using the first one", Sev.WARN)
        med = lambda k: sorted(e[k] for e in est)[len(est) // 2]          # noqa: E731
        ent = (med("fwd"), med("right"))
        axis_abs = wrap360(sorted(e["axis_heading_deg"] for e in est)[len(est) // 2])
        axis_rel = wrap180(course.rel_heading(axis_abs))
        spread = sorted(dist(ent, (e["fwd"], e["right"])) for e in est)[int(0.9 * (len(est) - 1))]   # 90th percentile: one bad frame is not a drift
        steady_lim = max(0.8, 0.05 * float(first["distance_m"]))                                         # a far entrance measures coarser
        width = sorted(m["width_m"] for m in meas_s)[len(meas_s) // 2]
        fin = meas_s[-1]
        final_state = ctx.state()
        h, _ = ctx.height()
        here = _pos(ctx, course)

        ctx.metric("entrance_course", {"fwd": round(ent[0], 2), "right": round(ent[1], 2)})
        ctx.metric("axis_heading_deg", round(axis_abs, 1))
        ctx.metric("axis_rel_course_deg", round(axis_rel, 1))
        ctx.metric("corridor_width_m", round(width, 2))
        ctx.metric("entrance_spread_m", round(spread, 2))
        ctx.metric("distance_to_entrance_m", round(dist(here, ent), 1))
        ctx.metric("hops", hops)
        ctx.metric("headings_tried", tried)
        ctx.metric("localised_after_s", round(time.time() - t_stage, 1))
        ctx.metric("first_detection", {k: round(v, 2) for k, v in first.items() if k != "t"})
        ctx.snapshot("front", "d2_corridor_localised")
        ctx.output("return_corridor", {
            "colour": "orange",
            "entrance_course": {"fwd": round(ent[0], 2), "right": round(ent[1], 2)},
            "axis_heading_deg": round(axis_abs, 1),
            "axis_rel_course_deg": round(axis_rel, 1),
            "width_m": round(width, 2),
            "seen_from": {"fwd": round(here[0], 2), "right": round(here[1], 2), "alt_m": None if h is None else round(h, 2)},
        })

        criteria = [
            Check(name="Orange corridor detected and confirmed", ok=True, value=f"{_corridor_conf(ctx)} consecutive frames"),
            Check(name=f"Corridor geometry plausible (width ~{width_exp:.1f} m)", ok=abs(width - width_exp) <= 0.6, value=round(width, 2), limit=width_exp),
            Check(name=f"Corridor runs back toward the start (axis within {axis_tol:.0f} deg of the reverse course heading)",
                  ok=abs(ang_diff(axis_rel, 180.0)) <= axis_tol, value=round(axis_rel, 1), limit=180.0),
            Check(name=f"Entrance position steady while holding (<= {steady_lim:.1f} m)", ok=(spread <= steady_lim and len(est) >= 2), value=round(spread, 2), limit=round(steady_lim, 2),
                  detail=f"{len(est)} estimates"),
            Check(name=f"Return altitude held ({target:.0f} m)", ok=bool(h is not None and abs(h - target) <= tol), value=None if h is None else round(h, 2), limit=target),
        ]
        truth = ctx.truth()
        tc = (truth or {}).get("return_corridor") if truth else None
        if tc:
            d_lat = abs(-fin["lateral_m"] - tc["lateral_m"])
            d_yaw = abs(-fin["yaw_err_deg"] - tc["yaw_err_deg"])
            d_dist = abs(fin["distance_m"] - (-tc["along_axis_m"]))
            ctx.metric("truth_dist_to_entrance_m", round(-tc["along_axis_m"], 2))
            criteria.append(Check(name="(sim truth) Vision agrees with the simulator (lateral / yaw / distance)", blocking=False,
                                  ok=(d_lat <= 0.5 and d_yaw <= 5.0 and d_dist <= 1.0),
                                  detail=f"d_lat={d_lat:.2f} m  d_yaw={d_yaw:.1f} deg  d_dist={d_dist:.2f} m"))
        if zs is not None:
            criteria.append(Check(name="Never over a red zone while moving closer", ok=(zs.red_entries == 0), value=zs.red_entries, limit=0))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"D2 SUCCESS: return corridor entrance at course ({ent[0]:.1f}, {ent[1]:.1f}), axis {axis_rel:+.0f} deg, width {width:.2f} m", Sev.GOOD)
        return success


# ───────────────────────────── D3: approach and alignment ─────────────────────────────

class StageD3(Stage):
    id = "D3"
    title = "Approach & Alignment"
    rulebook = "Stage D, D3: fly to the orange corridor and align on its centre line in front of the entrance (return lap)"
    summary = ("Fly to the stand-off point in front of the entrance around the red zones, then refine with the front camera "
               "until the vehicle is on the centre line, along the axis and at the stand-off distance. Altitude held.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        h, src = ctx.height()
        target = return_alt(ctx)
        rc = ctx.mission.get("return_corridor")
        checks = vehicle_checks(ctx, 5.0)
        checks.append(Check(name=f"At the return altitude ({target:.0f} m)", ok=bool(h is not None and abs(h - target) <= alt_tol(ctx) + 1.0),
                            value=None if h is None else round(h, 2), limit=target, detail=f"height {_fmt(h)} from the {src}"))
        checks.append(front_camera_check(ctx))
        checks.append(Check(name="Orange corridor localised (D2)", ok=bool(rc),
                            detail=(f"entrance at ({rc['entrance_course']['fwd']}, {rc['entrance_course']['right']})" if rc else "run D2 first")))
        checks.append(Check(name="Red map from the search (C2)", ok=zone_state(ctx) is not None, blocking=False,
                            detail="" if zone_state(ctx) is not None else "no C2 map: only red zones seen from now on are avoided"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        course = ctx.course
        st = ctx.state()
        rc = ctx.mission.get("return_corridor")
        if course is None or st.ned is None or not rc:
            ctx.emit("Cannot run D3 without the course frame and the corridor from D2", Sev.ERROR)
            return False
        if not _look_for_orange(ctx):
            ctx.emit("The vision pipeline cannot look for the orange corridor", Sev.ERROR)
            return False
        gimbal = float(getattr(cfg, "gimbal_pitch_deg", -35.0))
        standoff = float(getattr(cfg, "standoff_m", 10.0))
        standoff_tol = float(getattr(cfg, "standoff_tol_m", 0.6))
        lat_tol = float(getattr(cfg, "lateral_tol_m", 0.3))
        yaw_tol = float(getattr(cfg, "yaw_tol_deg", 5.0))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        max_iters = int(getattr(cfg, "max_refine_iters", 6))
        approach_timeout = float(getattr(cfg, "approach_timeout_s", 120.0))
        timeout_s = float(getattr(cfg, "timeout_s", 240.0))
        n_conf = _corridor_conf(ctx)
        expected_w = float(getattr(getattr(getattr(ctx.full_cfg, "vision", None), "banner", None), "corridor_width_m", 3.5))
        target = return_alt(ctx)
        tol = alt_tol(ctx)
        hold_d = course.to_ned(0.0, 0.0, target)[2]
        t_stage = time.time()

        ent: Pt = (float(rc["entrance_course"]["fwd"]), float(rc["entrance_course"]["right"]))
        axis_rel = float(rc["axis_rel_course_deg"])
        axis_abs = course.abs_heading(axis_rel)
        goal = standoff_point(ent, axis_rel, standoff)
        ctx.phase(f"Pitching the front camera to {gimbal:.0f} deg")
        ctx.link.set_gimbal(gimbal, 0.0)

        # 1. fly to the stand-off point (heading along the corridor axis the whole way), around the red zones
        zs, flight, nav = _nav_rig(ctx, course, target, axis_abs)
        nav.target_pt = goal
        here = _pos(ctx, course)
        ctx.emit(f"Approaching the corridor: stand-off point ({goal[0]:.1f}, {goal[1]:.1f}), {dist(here, goal):.0f} m away, "
                 f"red zones mapped: {len(zs.grid.red_boxes())}")
        res = nav.go_to(goal, timeout_s=approach_timeout)
        flight.hold()
        arrive = _pos(ctx, course)
        approach_err = dist(arrive, goal)
        ctx.metric("approach_result", res)
        ctx.metric("approach_error_m", round(approach_err, 2))
        ctx.metric("evasions", len(zs.evasions))
        ctx.metric("min_red_distance_m", None if nav.min_red_dist == math.inf else round(nav.min_red_dist, 2))
        if res != "done":
            ctx.emit(f"Approach ended early: {res}", Sev.ERROR)
        ctx.sleep(1.0)
        ctx.wait(lambda s: s.gimbal_pitch_deg is not None and abs(s.gimbal_pitch_deg - gimbal) < 3.0, 6.0, "gimbal at pitch")

        # 2. refine with the camera (the same loop as A4, on the orange corridor, at the return altitude)
        meas = _acquire(ctx, 8.0) if res == "done" else None
        first = dict(meas) if meas else None
        if res == "done" and meas is None:
            ctx.emit("Corridor not in view at the stand-off point: sweeping the heading", Sev.WARN)
            hold = ctx.state()
            for rel in (-20.0, 20.0, -40.0, 40.0):
                ctx.check_abort()
                StageA4._fly_to(ctx, (hold.ned[0], hold.ned[1], hold_d, wrap360(axis_abs + rel)), 12.0, xy_tol=0.6, yaw_tol=5.0, alt_tol=0.6)
                meas = _acquire(ctx, 3.0)
                if meas:
                    first = dict(meas)
                    break
        if meas is not None:
            ctx.snapshot("front", "d3_corridor_in_view")
            for it in range(max_iters):
                ctx.check_abort()
                if time.time() - t_stage > timeout_s:
                    ctx.emit("D3 timed out while aligning", Sev.ERROR)
                    break
                tgt = StageA4._plan(ctx, meas, standoff, hold_d)
                cur = ctx.state()
                travel = math.hypot(tgt[0] - cur.ned[0], tgt[1] - cur.ned[1])
                ctx.phase(f"Aligning ({it + 1}/{max_iters}): moving {travel:.2f} m, yaw {meas['yaw_err_deg']:+.1f} deg", progress=(it + 1) / (max_iters + 1))
                if travel > 0.25 or abs(meas["yaw_err_deg"]) > 2.0:
                    StageA4._fly_to(ctx, tgt, 40.0)
                ctx.sleep(1.0)
                meas = _acquire(ctx, 8.0)
                if meas is None:
                    ctx.emit("Lost the corridor after moving", Sev.ERROR)
                    break
                err_d = meas["distance_m"] - standoff
                ctx.emit(f"Check {it + 1}: lateral {-meas['lateral_m']:+.2f} m, yaw {-meas['yaw_err_deg']:+.1f} deg, "
                         f"entrance {meas['distance_m']:.2f} m (target {standoff:.1f})")
                if abs(meas["lateral_m"]) <= lat_tol * 0.7 and abs(meas["yaw_err_deg"]) <= yaw_tol * 0.7 and abs(err_d) <= standoff_tol * 0.7:
                    break

        # 3. prove it is stable
        fin: dict[str, float] | None = meas
        samples: list[dict[str, float]] = []
        if meas is not None:
            ctx.phase(f"Holding the aligned pose for {stable_s:.0f} s")
            hp = ctx.state()
            t_h = time.time()
            while time.time() - t_h < stable_s:
                ctx.check_abort()
                ctx.link.goto_ned(hp.ned[0], hp.ned[1], hold_d, yaw_deg=hp.yaw_deg)
                m = _confirmed_corridor(ctx, n_conf, t_h)
                if m:
                    samples.append(m)
                time.sleep(0.25)
            fin = samples[-1] if samples else meas
        final_state = ctx.state()
        h, _ = ctx.height()
        ctx.snapshot("front", "d3_aligned_for_return")

        criteria: list[Check] = [
            Check(name="Reached the stand-off point (route flown around the red zones)", ok=(res == "done"), detail=f"route {res}, {approach_err:.1f} m off the point"),
            Check(name=f"Orange corridor in view and confirmed ({n_conf} frames)", ok=bool(fin), value=n_conf),
        ]
        if fin:
            worst_lat = max((abs(m["lateral_m"]) for m in samples), default=abs(fin["lateral_m"]))
            worst_yaw = max((abs(m["yaw_err_deg"]) for m in samples), default=abs(fin["yaw_err_deg"]))
            ctx.metric("final_lateral_offset_m", round(-fin["lateral_m"], 2))
            ctx.metric("final_yaw_error_deg", round(-fin["yaw_err_deg"], 1))
            ctx.metric("final_entrance_distance_m", round(fin["distance_m"], 2))
            ctx.metric("corridor_width_m", round(fin["width_m"], 2))
            ctx.metric("hold_samples", len(samples))
            if first:
                ctx.metric("first_detection", {k: round(v, 2) for k, v in first.items() if k != "t"})
            e2 = entrance_estimate(course, final_state.ned, final_state.yaw_deg or 0.0, fin)
            ctx.output("return_entry_aligned", {
                "entrance_course": {"fwd": round(e2["fwd"], 2), "right": round(e2["right"], 2)},
                "axis_heading_deg": round(e2["axis_heading_deg"], 1), "axis_rel_course_deg": round(e2["axis_rel_deg"], 1),
                "width_m": round(fin["width_m"], 2), "standoff_m": round(fin["distance_m"], 2),
                "alt_m": None if h is None else round(h, 2),
            })
            criteria += [
                Check(name=f"Corridor geometry plausible (width ~{expected_w:.1f} m)", ok=abs(fin["width_m"] - expected_w) <= 0.6, value=round(fin["width_m"], 2), limit=expected_w),
                Check(name="Lateral alignment on the centre line", ok=worst_lat <= lat_tol, value=round(worst_lat, 2), limit=lat_tol),
                Check(name="Heading aligned with the corridor axis", ok=worst_yaw <= yaw_tol, value=round(worst_yaw, 1), limit=yaw_tol),
                Check(name=f"Stand-off before the entrance (~{standoff:.0f} m)", ok=abs(fin["distance_m"] - standoff) <= standoff_tol, value=round(fin["distance_m"], 2), limit=standoff),
                Check(name="Alignment held steady", ok=len(samples) >= 2, value=len(samples), limit=2),
            ]
        criteria += [
            Check(name=f"Return altitude held ({target:.0f} m, no descent yet)", ok=bool(h is not None and abs(h - target) <= tol), value=None if h is None else round(h, 2), limit=target),
            Check(name="Never over a red zone", ok=(zs.red_entries == 0), value=zs.red_entries, limit=0),
            Check(name="Armed and still in GUIDED", ok=bool(final_state.armed and final_state.mode == "GUIDED")),
        ]
        truth = ctx.truth()
        tc = (truth or {}).get("return_corridor") if truth else None
        if tc and fin:
            d_lat = abs(-fin["lateral_m"] - tc["lateral_m"])
            d_yaw = abs(-fin["yaw_err_deg"] - tc["yaw_err_deg"])
            d_dist = abs(fin["distance_m"] - (-tc["along_axis_m"]))
            ctx.metric("truth_lateral_m", tc["lateral_m"])
            ctx.metric("truth_yaw_err_deg", tc["yaw_err_deg"])
            ctx.metric("truth_dist_to_entrance_m", round(-tc["along_axis_m"], 2))
            criteria.append(Check(name="(sim truth) Vision agrees with the simulator (lateral / yaw / distance)", blocking=False,
                                  ok=(d_lat <= 0.25 and d_yaw <= 3.0 and d_dist <= 0.5),
                                  detail=f"d_lat={d_lat:.2f} m  d_yaw={d_yaw:.1f} deg  d_dist={d_dist:.2f} m"))
            criteria.append(Check(name="(sim truth) Vehicle on the centre line / along the axis", blocking=False,
                                  ok=(abs(tc["lateral_m"]) <= lat_tol * 1.5 and abs(tc["yaw_err_deg"]) <= yaw_tol * 1.5),
                                  detail=f"lateral={tc['lateral_m']:+.2f} m yaw_err={tc['yaw_err_deg']:+.1f} deg"))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success and fin:
            ctx.emit(f"D3 SUCCESS: aligned {fin['distance_m']:.1f} m before the orange corridor entrance at {_fmt(h)} "
                     f"(lateral {-fin['lateral_m']:+.2f} m, heading {-fin['yaw_err_deg']:+.1f} deg off the axis)", Sev.GOOD)
        return success
