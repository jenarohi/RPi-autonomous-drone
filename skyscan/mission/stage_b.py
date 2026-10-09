"""Stage B implementations (B1-B4): green corridor navigation.

B1: descend to the corridor flight altitude (10 ft, ~3 m)
B2: enter the 3.5 m wide corridor
B3: autonomous static-obstacle traversal (walls + obstacles, lidar-reactive)
B4: corridor exit detection into the delivery zone

Sensors: the 2D lidar (walls, obstacles, entrance and exit) and the flight controller's height reference
(``MissionContext.height()``: a downward lidar/rangefinder when one reports, else the EKF). Simulator ground truth is
never used to fly or to decide a stage's result.

The same four stages fly the return lap back through the orange corridor (Stage E, ``skyscan.mission.stage_e``): a
``Lap`` says which corridor heading to hold, where the settings live and what the products are called. Progress is
measured along the held heading, so the code is the same in both directions.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

from skyscan.geo import CourseFrame, wrap360
from skyscan.lidar import wall_info
from skyscan.mission.context import MissionContext
from skyscan.mission.corridor_ctrl import AvoidParams, CorridorController, NavCmd
from skyscan.mission.stage import Stage
from skyscan.types import Check, LidarScan, Sev
from skyscan.utils.logger import get_logger

log = get_logger("STAGE/B")

LOOP_S = 0.1                 # control loop period (velocity setpoints must keep arriving at >= 2 Hz)
NAV_PUBLISH_S = 0.2


# ───────────────────────────── shared helpers ─────────────────────────────

@dataclass(frozen=True)
class Lap:
    """Which corridor a corridor stage flies."""
    name: str           # "forward" (green, Stage B) | "return" (orange, Stage E)
    group: str          # config group of its stages: mission.<group>.<prefix><n>
    prefix: str         # "b" | "e"
    key: str            # prefix of the mission products it writes ("corridor_entry" / "return_corridor_entry" ...)
    aligned: str        # mission product of the alignment stage before it (A4 / D3)
    aligned_by: str


FORWARD = Lap("forward", "stage_b", "b", "", "corridor_axis", "A4")
RETURN = Lap("return", "stage_e", "e", "return_", "return_entry_aligned", "D3")


def _lap_cfg(ctx: MissionContext, lap: Lap, n: int) -> Any:
    return getattr(getattr(getattr(ctx.full_cfg, "mission", None), lap.group, None), f"{lap.prefix}{n}", {}) or {}


def _stage_b_cfg(ctx: MissionContext, sid: str) -> Any:
    return getattr(getattr(getattr(ctx.full_cfg, "mission", None), "stage_b", None), sid, {}) or {}


def corridor_alt(ctx: MissionContext, lap: Lap = FORWARD) -> float:
    alt = getattr(_lap_cfg(ctx, lap, 1), "corridor_alt_m", None)
    if alt is None:                                          # the return lap flies the same corridor height by default
        alt = getattr(_stage_b_cfg(ctx, "b1"), "corridor_alt_m", 3.0)
    return float(alt)


def axis_heading(ctx: MissionContext, course: CourseFrame) -> float:
    """Heading to hold along the corridor: A4's measured axis when there is one, else the course heading."""
    ax = ctx.mission.get("corridor_axis")
    if isinstance(ax, dict) and ax.get("axis_heading_deg") is not None:
        return float(ax["axis_heading_deg"])
    return float(course.heading_deg)


def return_axis_heading(ctx: MissionContext, course: CourseFrame) -> float:
    """Heading to hold back through the return corridor: D3's refined axis, else D2's, else the reverse course heading."""
    for key in ("return_entry_aligned", "return_corridor"):
        rc = ctx.mission.get(key)
        if isinstance(rc, dict) and rc.get("axis_heading_deg") is not None:
            return float(rc["axis_heading_deg"])
    return wrap360(course.heading_deg + 180.0)


def lap_heading(ctx: MissionContext, course: CourseFrame, lap: Lap = FORWARD) -> float:
    return return_axis_heading(ctx, course) if lap.name == "return" else axis_heading(ctx, course)


def along_heading(course: CourseFrame, heading_deg: float, fwd: float, right: float) -> float:
    """Course-frame point (fwd, right) projected onto the direction ``heading_deg``: progress along a corridor."""
    a = math.radians(course.rel_heading(heading_deg))
    return fwd * math.cos(a) + right * math.sin(a)


def _fmt(v: float | None, unit: str = "m", nd: int = 2) -> str:
    return "n/a" if v is None else f"{v:.{nd}f} {unit}"


def lidar_checks(ctx: MissionContext, blocking: bool = True) -> list[Check]:
    """Is the lidar there and streaming fast enough?"""
    lcfg = getattr(ctx.full_cfg, "lidar", None)
    min_hz = float(getattr(lcfg, "min_hz", 2.0))
    fresh_s = float(getattr(lcfg, "fresh_s", 1.0))
    if ctx.lidar is None:
        return [Check(name="Lidar streaming", ok=False, blocking=blocking, detail="no lidar source in this profile")]
    stats = ctx.lidar.stats()
    ok = bool(stats["age_s"] is not None and stats["age_s"] <= fresh_s and stats["hz"] >= min_hz)
    return [Check(name="Lidar streaming", ok=ok, blocking=blocking, value=stats["hz"], limit=min_hz,
                  detail=f"{stats['hz']} Hz, {stats['n']} rays, age {stats['age_s']} s" if stats["age_s"] is not None else "no scan received")]


def vehicle_checks(ctx: MissionContext, min_alt: float = 1.0) -> list[Check]:
    st = ctx.state()
    h, src = ctx.height()
    return [
        Check(name="Course frame established (A1)", ok=(ctx.course is not None), detail="origin recorded" if ctx.course else "run A1 first"),
        Check(name="Vehicle airborne, armed, GUIDED", ok=bool(st.armed and (h or 0.0) > min_alt and st.mode == "GUIDED"),
              detail=f"armed={st.armed} height={_fmt(h)} ({src}) mode={st.mode}"),
    ]


def height_check(ctx: MissionContext, target: float, tol: float, name: str) -> Check:
    h, src = ctx.height()
    return Check(name=name, ok=bool(h is not None and abs(h - target) <= tol), value=None if h is None else round(h, 2),
                 limit=target, detail=f"height {_fmt(h)} from the {src}")


class CorridorFlight:
    """Velocity-controlled flight along the corridor axis: lidar controller for sideways + speed, height from
    ``ctx.height()``, heading held on the axis. One ``step()`` per control tick."""

    def __init__(self, ctx: MissionContext, course: CourseFrame, speed_mps: float, avoid_cfg: Any, h_target: float,
                 heading: float | None = None) -> None:
        self.ctx, self.course, self.h_target = ctx, course, h_target
        self.heading = axis_heading(ctx, course) if heading is None else float(heading)
        params = AvoidParams.from_cfg(avoid_cfg)
        params.cruise_mps = float(speed_mps)
        self.ctrl = CorridorController(params)
        self.kz, self.vz_max = 0.8, 0.5
        self.cmd = NavCmd()
        self.scan: LidarScan | None = None
        self.last_scan_t = time.time()
        self.last_nav_pub = 0.0
        self.last_seq: int | None = None
        self.new_scan = False
        self.min_clearance = math.inf
        self.max_height_err = 0.0
        self.height_src = "none"
        self._anchor: tuple[float, float, float] | None = None

    def fwd(self) -> float:
        st = self.ctx.state()
        return self.course.to_course(*st.ned)[0] if st.ned else 0.0

    def right(self) -> float:
        st = self.ctx.state()
        return self.course.to_course(*st.ned)[1] if st.ned else 0.0

    def along(self) -> float:
        """Position along the held heading: corridor progress, the same on the forward and the return lap."""
        st = self.ctx.state()
        if not st.ned:
            return 0.0
        f, r, _ = self.course.to_course(*st.ned)
        return along_heading(self.course, self.heading, f, r)

    def _vd(self) -> float:
        h, src = self.ctx.height()
        self.height_src = src
        if h is None:
            return 0.0
        err = self.h_target - h
        self.max_height_err = max(self.max_height_err, abs(err))
        return -max(-self.vz_max, min(self.vz_max, self.kz * err))

    def step(self, speed_scale: float = 1.0) -> NavCmd:
        """Read the latest scan, compute the command, send it. Holds still (zero velocity) if the scan is stale."""
        ctx = self.ctx
        self._anchor = None                                     # moving again: the next hold() pins a new spot
        scan = ctx.scan()
        self.new_scan = bool(scan is not None and scan.seq != self.last_seq)
        if scan is None:
            self.cmd = NavCmd(0.0, 0.0, "HOLD")
            self.scan = None
        else:
            self.last_scan_t = time.time()
            if self.new_scan:
                self.last_seq = scan.seq
                self.scan = scan
                self.cmd = self.ctrl.step(scan, speed_scale)
                self.min_clearance = min(self.min_clearance, self.cmd.nearest_m)
        c = self.cmd
        h = math.radians(self.heading)
        vn = c.vx * math.cos(h) - c.vy * math.sin(h)           # body (forward, right) -> NED
        ve = c.vx * math.sin(h) + c.vy * math.cos(h)
        ctx.link.velocity_ned(vn, ve, self._vd(), yaw_deg=self.heading)
        now = time.time()
        if now - self.last_nav_pub >= NAV_PUBLISH_S:
            self.last_nav_pub = now
            ctx.bus.publish("nav", {"stage": ctx.stage_id, **c.to_dict()})
        return c

    def stale_s(self) -> float:
        return time.time() - self.last_scan_t

    def hold(self) -> None:
        """Stop and hold the current position and height."""
        if self._anchor is None:
            st = self.ctx.state()
            if st.ned is None:
                return
            self._anchor = (st.ned[0], st.ned[1], st.ned[2])
        self.ctx.link.goto_ned(self._anchor[0], self._anchor[1], self._anchor[2], yaw_deg=self.heading)
        self.ctx.bus.publish("nav", {"stage": self.ctx.stage_id, "mode": "HOLD", "vx": 0.0, "vy": 0.0, "theta_deg": 0.0, "free_m": 0.0})


def _quiet_s(ctx: MissionContext, seconds: float, hold: CorridorFlight) -> None:
    """Hold position for a while (abortable)."""
    t0 = time.time()
    while time.time() - t0 < seconds:
        ctx.check_abort()
        hold.hold()
        time.sleep(LOOP_S)


# ───────────────────────────── B1: Descent to corridor altitude ─────────────────────────────

class StageB1(Stage):
    id = "B1"
    title = "Descent to Corridor Altitude"
    rulebook = "Stage B, B1: descend to the corridor flight altitude of 10 ft (~3 m)"
    summary = "From the stand-off point in front of the corridor, descend to 3 m (10 ft) and hold position, height read from the height reference."
    lap = FORWARD

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        cfg = getattr(ctx.cfg, "b1", ctx.cfg)
        target = corridor_alt(ctx, self.lap)
        tol = float(getattr(cfg, "alt_tol_m", 0.25))
        h, src = ctx.height()
        axis = ctx.mission.get(self.lap.aligned)
        checks = vehicle_checks(ctx)
        checks += [
            Check(name="At or above the corridor altitude", ok=bool(h is not None and h >= target - tol), value=None if h is None else round(h, 2),
                  limit=target, detail=f"height {_fmt(h)} ({src}); B1 descends to {target:.1f} m"),
            Check(name="Height reference is the lidar/rangefinder", ok=(src == "lidar"), blocking=False,
                  detail=("downward lidar reporting" if src == "lidar" else f"using the {src}: no downward lidar/rangefinder is reporting")),
        ]
        checks += lidar_checks(ctx, blocking=False)
        checks.append(Check(name=f"Corridor aligned earlier ({self.lap.aligned_by})", ok=bool(axis), blocking=False,
                            detail="axis measured" if axis else f"{self.lap.aligned_by} not run in this session"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "b1", ctx.cfg)
        target = corridor_alt(ctx, self.lap)
        tol = float(getattr(cfg, "alt_tol_m", 0.25))
        rate = float(getattr(cfg, "descent_mps", 0.5))
        hold_s = float(getattr(cfg, "hold_s", 2.0))
        max_drift = float(getattr(cfg, "max_drift_m", 0.6))
        timeout = float(getattr(cfg, "timeout_s", 40.0))
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None:
            ctx.emit(f"Cannot run {self.id} without the course frame and a position fix", Sev.ERROR)
            return False
        heading = lap_heading(ctx, course, self.lap)
        n0, e0, d0 = st.ned
        h0, src0 = ctx.height()
        if h0 is None:
            ctx.emit("No height reference available", Sev.ERROR)
            return False
        ctx.metric("height_source", src0)
        ctx.metric("start_height_m", round(h0, 2))
        ctx.emit(f"Descending from {h0:.2f} m to {target:.1f} m, height from the {src0}")

        t0 = time.time()
        in_tol_since: float | None = None
        done = False
        max_height_err_after = 0.0
        while time.time() - t0 < timeout:
            ctx.check_abort()
            st = ctx.state()
            h, src = ctx.height()
            if h is None or st.ned is None:
                time.sleep(LOOP_S)
                continue
            err = target - h                                    # negative while above the target
            # EKF z at which the true height would be `target`: lidar corrects the EKF's idea of the ground
            step = max(-rate, min(rate, err))                   # <= descent_mps worth of travel per second
            d_cmd = st.ned[2] - step
            ctx.link.goto_ned(n0, e0, d_cmd, yaw_deg=heading)
            ctx.phase(f"Descending: height {h:.2f} m -> {target:.1f} m ({src})",
                      progress=min(1.0, max(0.0, (h0 - h) / max(0.1, h0 - target))))
            if abs(err) <= tol:
                in_tol_since = in_tol_since or time.time()
                if time.time() - in_tol_since >= hold_s:
                    done = True
                    break
            else:
                in_tol_since = None
            time.sleep(LOOP_S)

        st = ctx.state()
        h, src = ctx.height()
        final_h = h if h is not None else float("nan")
        drift = math.hypot(st.ned[0] - n0, st.ned[1] - e0) if st.ned else float("nan")
        ctx.metric("final_height_m", round(final_h, 2))
        ctx.metric("descent_time_s", round(time.time() - t0, 1))
        ctx.metric("drift_m", round(drift, 2))
        ctx.metric("height_source_final", src)
        ctx.snapshot("front", f"{self.id.lower()}_corridor_altitude")
        ctx.output(self.lap.key + "corridor_altitude", {"height_m": round(final_h, 2), "source": src})

        criteria = [
            Check(name=f"Corridor altitude reached ({target:.1f} m / 10 ft)", ok=bool(done and abs(final_h - target) <= tol),
                  value=round(final_h, 2), limit=target),
            Check(name=f"Held within +-{tol:.2f} m for {hold_s:.0f} s", ok=done, value=round(time.time() - (in_tol_since or time.time()), 1), limit=hold_s),
            Check(name="Horizontal drift while descending", ok=(drift <= max_drift), value=round(drift, 2), limit=max_drift),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
            Check(name="Height read from the lidar/rangefinder (not the EKF)", ok=(src == "lidar"), blocking=False,
                  detail=f"height source: {src}"),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"{self.id} SUCCESS: holding {final_h:.2f} m (target {target:.1f} m), drift {drift:.2f} m, height from the {src}", Sev.GOOD)
        return success


# ───────────────────────────── B2: Corridor entry ─────────────────────────────

class StageB2(Stage):
    id = "B2"
    title = "Corridor Entry"
    rulebook = "Stage B, B2: enter the 3.5 m wide navigation corridor"
    summary = "Fly forward at corridor altitude until the lidar sees both walls (the entrance), continue 1.5 m inside on the centre line."
    lap = FORWARD

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        cfg = getattr(ctx.cfg, "b2", ctx.cfg)
        tol = float(getattr(cfg, "alt_tol_m", 0.4))
        checks = vehicle_checks(ctx)
        checks.append(height_check(ctx, corridor_alt(ctx, self.lap), tol + 0.2, f"At the corridor altitude ({self.lap.prefix.upper()}1)"))
        checks += lidar_checks(ctx)
        scan = ctx.scan()
        w = wall_info(scan) if scan is not None else None
        checks.append(Check(name="Corridor entrance not yet crossed", ok=bool(w is not None and not w.both), blocking=False,
                            detail="side walls visible: already inside" if (w is not None and w.both) else "open air to both sides"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "b2", ctx.cfg)
        speed = float(getattr(cfg, "speed_mps", 0.5))
        depth_m = float(getattr(cfg, "depth_m", 1.5))
        max_search = float(getattr(cfg, "max_search_m", 7.0))
        confirm = int(getattr(cfg, "confirm_scans", 3))
        width_tol = float(getattr(cfg, "width_tol_m", 0.8))
        centre_tol = float(getattr(cfg, "centre_tol_m", 0.5))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.4))
        timeout = float(getattr(cfg, "timeout_s", 60.0))
        nominal_w = float(getattr(getattr(getattr(ctx.full_cfg, "vision", None), "banner", None), "corridor_width_m", 3.5))
        course = ctx.course
        if course is None or ctx.state().ned is None:
            ctx.emit(f"Cannot run {self.id} without the course frame and a position fix", Sev.ERROR)
            return False
        h_target = corridor_alt(ctx, self.lap)
        flight = CorridorFlight(ctx, course, speed, getattr(cfg, "avoid", None), h_target, lap_heading(ctx, course, self.lap))
        start_fwd = flight.along()
        entrance_fwd: float | None = None
        first_both_fwd = start_fwd
        both_run = 0
        t0 = time.time()
        ctx.emit(f"Flying forward to the corridor entrance at {h_target:.1f} m")
        ctx.phase("Searching for the corridor walls")

        while time.time() - t0 < timeout:
            ctx.check_abort()
            cmd = flight.step()
            if flight.stale_s() > 3.0:
                flight.hold()
                ctx.emit("Lidar data lost for 3 s: holding", Sev.ERROR)
                ctx.report.criteria = [Check(name="Lidar stayed available", ok=False)]
                return False
            if flight.new_scan and cmd.walls is not None:
                if cmd.walls.both:
                    if both_run == 0:
                        first_both_fwd = flight.along()
                    both_run += 1
                else:
                    both_run = 0
                if entrance_fwd is None and both_run >= confirm:
                    # the 45-degree side rays hit each wall about half a corridor-width AHEAD of the vehicle, so the
                    # entrance line is that far beyond the point where both walls first appeared
                    entrance_fwd = first_both_fwd + 0.5 * cmd.walls.width_m
                    ctx.emit(f"Corridor walls seen on both sides: entrance line at {entrance_fwd:.2f} m forward "
                             f"(width {_fmt(cmd.walls.width_m)})", Sev.GOOD)
            fwd = flight.along()
            if entrance_fwd is None:
                ctx.phase(f"Searching for the corridor walls ({fwd - start_fwd:.1f} m flown, {cmd.mode})",
                          progress=min(0.5, (fwd - start_fwd) / max_search * 0.5))
                if fwd - start_fwd > max_search:
                    flight.hold()
                    ctx.emit(f"Both corridor walls were not seen within {max_search:.0f} m", Sev.ERROR)
                    ctx.report.criteria = [Check(name="Corridor entrance detected by the lidar", ok=False,
                                                 detail=f"no wall pair within {max_search:.0f} m of the start")]
                    return False
            else:
                inside = fwd - entrance_fwd
                ctx.phase(f"Entering: {inside:.1f} m / {depth_m:.1f} m inside ({cmd.mode})",
                          progress=0.5 + 0.5 * min(1.0, inside / max(0.1, depth_m)))
                if inside >= depth_m:
                    break
            time.sleep(LOOP_S)
        else:
            flight.hold()
            ctx.emit(f"{self.id} timed out", Sev.ERROR)
            ctx.report.criteria = [Check(name="Entered the corridor in time", ok=False, limit=timeout)]
            return False

        # stop and measure the walls for a moment
        flight.hold()
        samples = []
        t_m = time.time()
        while time.time() - t_m < 1.5:
            ctx.check_abort()
            flight.hold()
            scan = ctx.scan()
            if scan is not None:
                w = wall_info(scan)
                if w.both:
                    samples.append(w)
            time.sleep(0.2)
        h, src = ctx.height()
        st = ctx.state()
        width = sorted(w.width_m for w in samples)[len(samples) // 2] if samples else None
        offset = sorted(w.offset_m for w in samples)[len(samples) // 2] if samples else None
        align = [w.turn_to_align_deg for w in samples if w.turn_to_align_deg is not None]
        misalign = sorted(align)[len(align) // 2] if align else None
        depth_done = flight.along() - entrance_fwd
        ctx.metric("entrance_fwd_m", round(entrance_fwd, 2))
        ctx.metric("depth_inside_m", round(depth_done, 2))
        ctx.metric("wall_width_m", None if width is None else round(width, 2))
        ctx.metric("centre_offset_m", None if offset is None else round(offset, 2))
        ctx.metric("wall_misalignment_deg", None if misalign is None else round(misalign, 1))
        ctx.metric("height_m", None if h is None else round(h, 2))
        ctx.metric("height_source", src)
        ctx.snapshot("front", f"{self.id.lower()}_inside_corridor")
        ctx.output(self.lap.key + "corridor_entry", {"entrance_fwd_m": round(entrance_fwd, 2), "width_m": None if width is None else round(width, 2),
                                                     "offset_m": None if offset is None else round(offset, 2)})

        # A4 / D3 measured the entrance with the camera: the two should agree
        ax = ctx.mission.get(self.lap.aligned)
        ec = ax.get("entrance_course") if isinstance(ax, dict) else None
        vis_fwd = (along_heading(course, flight.heading, float(ec["fwd"]), float(ec["right"]))
                   if isinstance(ec, dict) and ec.get("fwd") is not None else None)
        # lidar-measured width is the inner clear width: nominal centre-to-centre width minus the wall thickness
        criteria = [
            Check(name="Lidar sees both corridor walls (entrance crossed)", ok=bool(samples), value=len(samples), limit=1),
            Check(name=f"Corridor width plausible (~{nominal_w:.1f} m)", ok=bool(width is not None and abs(width - nominal_w) <= width_tol),
                  value=None if width is None else round(width, 2), limit=nominal_w),
            Check(name="On the corridor centre line", ok=bool(offset is not None and abs(offset) <= centre_tol),
                  value=None if offset is None else round(offset, 2), limit=centre_tol),
            Check(name=f"Inside by at least {depth_m:.1f} m", ok=(depth_done >= depth_m - 0.3), value=round(depth_done, 2), limit=depth_m),
            Check(name="Corridor altitude held", ok=bool(h is not None and abs(h - h_target) <= alt_tol),
                  value=None if h is None else round(h, 2), limit=h_target),
            Check(name="Heading along the walls (lidar)", ok=bool(misalign is None or abs(misalign) <= 10.0), blocking=False,
                  value=None if misalign is None else round(misalign, 1), limit=10.0),
            Check(name=f"Entrance agrees with the {self.lap.aligned_by} camera estimate (+-1.5 m)", ok=bool(vis_fwd is not None and abs(entrance_fwd - float(vis_fwd)) <= 1.5),
                  blocking=False, detail=f"lidar {entrance_fwd:.2f} m vs camera {vis_fwd:.2f} m" if vis_fwd is not None else f"{self.lap.aligned_by} estimate not available"),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"{self.id} SUCCESS: {depth_done:.1f} m inside, width {_fmt(width)}, centre offset {_fmt(offset)}", Sev.GOOD)
        return success


# ───────────────────────────── B3: Static obstacle traversal ─────────────────────────────

class StageB3(Stage):
    id = "B3"
    title = "Autonomous Static Obstacle Traversal"
    rulebook = "Stage B, B3: forward through the corridor, autonomously detecting and avoiding static obstacles and side walls"
    summary = "Lidar-reactive flight along the corridor: stay centred between the walls, slide round any obstacle, hold 3 m."
    lap = FORWARD

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        cfg = getattr(ctx.cfg, "b3", ctx.cfg)
        tol = float(getattr(cfg, "alt_tol_m", 0.5))
        p = self.lap.prefix.upper()
        checks = vehicle_checks(ctx)
        checks.append(height_check(ctx, corridor_alt(ctx, self.lap), tol + 0.2, f"At the corridor altitude ({p}1)"))
        checks += lidar_checks(ctx)
        scan = ctx.scan()
        w = wall_info(scan) if scan is not None else None
        checks.append(Check(name="Inside the corridor (both walls seen)", ok=bool(w is not None and w.both),
                            detail=(f"width {_fmt(w.width_m)}, offset {_fmt(w.offset_m)}" if (w is not None and w.both)
                                    else ("no scan" if w is None else f"walls not seen on both sides: run {p}2"))))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "b3", ctx.cfg)
        speed = float(getattr(cfg, "speed_mps", 0.6))
        traverse_m = float(getattr(cfg, "traverse_m", 6.0))
        min_clear = float(getattr(cfg, "min_clearance_m", 0.35))
        centre_tol = float(getattr(cfg, "centre_tol_m", 0.8))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.5))
        blocked_timeout = float(getattr(cfg, "blocked_timeout_s", 12.0))
        timeout = float(getattr(cfg, "timeout_s", 120.0))
        course = ctx.course
        if course is None or ctx.state().ned is None:
            ctx.emit(f"Cannot run {self.id} without the course frame and a position fix", Sev.ERROR)
            return False
        h_target = corridor_alt(ctx, self.lap)
        flight = CorridorFlight(ctx, course, speed, getattr(cfg, "avoid", None), h_target, lap_heading(ctx, course, self.lap))
        start_fwd = flight.along()
        t0 = time.time()
        blocked_since: float | None = None
        blocked_total = 0.0
        avoid_events = 0
        prev_mode = "CRUISE"
        max_offset = 0.0
        no_walls_since: float | None = None
        exited_early = False
        err_msg: str | None = None
        ctx.emit(f"Traversing the corridor at {speed:.1f} m/s, {h_target:.1f} m altitude")

        while time.time() - t0 < timeout:
            ctx.check_abort()
            cmd = flight.step()
            if flight.stale_s() > 3.0:
                err_msg = "Lidar data lost for 3 s"
                break
            progress = flight.along() - start_fwd
            ctx.phase(f"Traversing: {progress:.1f} m / {traverse_m:.1f} m, {cmd.mode}, free {cmd.free_m:.1f} m, "
                      f"clearance {_fmt(flight.min_clearance if math.isfinite(flight.min_clearance) else None)}",
                      progress=min(1.0, progress / max(0.1, traverse_m)))
            if cmd.mode == "AVOID" and prev_mode != "AVOID":
                avoid_events += 1
                ctx.emit(f"Obstacle ahead ({cmd.free_m:.1f} m): sliding {'left' if cmd.theta_deg > 0 else 'right'}", Sev.INFO)
            prev_mode = cmd.mode
            if cmd.walls is not None and cmd.walls.both:
                max_offset = max(max_offset, abs(cmd.walls.offset_m))
            if cmd.mode == "BLOCKED":
                blocked_since = blocked_since or time.time()
                if time.time() - blocked_since > blocked_timeout:
                    err_msg = f"No gap: blocked for {blocked_timeout:.0f} s"
                    break
            elif blocked_since is not None:
                blocked_total += time.time() - blocked_since
                blocked_since = None
            if cmd.walls is not None and not cmd.walls.any:        # walls ended before traverse_m: the exit is here
                no_walls_since = no_walls_since or time.time()
                if time.time() - no_walls_since > 1.0:
                    exited_early = True
                    break
            else:
                no_walls_since = None
            if progress >= traverse_m:
                break
            time.sleep(LOOP_S)
        else:
            err_msg = f"Timed out after {timeout:.0f} s"

        flight.hold()
        if err_msg:
            ctx.emit(err_msg, Sev.ERROR)
        dist = flight.along() - start_fwd
        h, src = ctx.height()
        st = ctx.state()
        clearance = flight.min_clearance if math.isfinite(flight.min_clearance) else None
        ctx.metric("distance_m", round(dist, 2))
        ctx.metric("duration_s", round(time.time() - t0, 1))
        ctx.metric("min_clearance_m", None if clearance is None else round(clearance, 2))
        ctx.metric("max_centre_offset_m", round(max_offset, 2))
        ctx.metric("avoid_manoeuvres", avoid_events)
        ctx.metric("blocked_s", round(blocked_total, 1))
        ctx.metric("max_height_error_m", round(flight.max_height_err, 2))
        ctx.metric("height_source", src)
        ctx.snapshot("front", f"{self.id.lower()}_traversal_end")
        ctx.output(self.lap.key + "traverse", {"distance_m": round(dist, 2), "min_clearance_m": None if clearance is None else round(clearance, 2),
                                "avoid_manoeuvres": avoid_events})
        criteria = [
            Check(name=f"Traversed {traverse_m:.0f} m of corridor", ok=bool(err_msg is None and (dist >= traverse_m - 0.5 or exited_early)),
                  value=round(dist, 2), limit=traverse_m, detail="walls ended early" if exited_early else ""),
            Check(name=f"Clearance to walls/obstacles >= {min_clear:.2f} m", ok=bool(clearance is None or clearance >= min_clear),
                  value=None if clearance is None else round(clearance, 2), limit=min_clear),
            Check(name=f"Stayed within {centre_tol:.1f} m of the centre line", ok=(max_offset <= centre_tol), value=round(max_offset, 2), limit=centre_tol),
            Check(name=f"Corridor altitude held (+-{alt_tol:.1f} m)", ok=(flight.max_height_err <= alt_tol), value=round(flight.max_height_err, 2), limit=alt_tol),
            Check(name="Never stuck without a gap", ok=(blocked_total < blocked_timeout and not (err_msg or "").startswith("No gap")),
                  value=round(blocked_total, 1), limit=blocked_timeout),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        if err_msg:
            ctx.report.error = err_msg
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"{self.id} SUCCESS: {dist:.1f} m flown, closest approach {_fmt(clearance)}, {avoid_events} avoidance manoeuvre(s)", Sev.GOOD)
        return success


# ───────────────────────────── B4: Corridor exit detection ─────────────────────────────

class StageB4(Stage):
    id = "B4"
    title = "Corridor Exit Detection"
    rulebook = "Stage B, B4: complete the forward corridor flight and detect the exit into the delivery zone"
    summary = "Keep flying the corridor until the lidar loses both walls (the exit), clear it by 1 m and hold at the delivery-zone edge."
    lap = FORWARD

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        cfg = getattr(ctx.cfg, "b4", ctx.cfg)
        tol = float(getattr(cfg, "alt_tol_m", 0.5))
        p = self.lap.prefix.upper()
        trav = ctx.mission.get(self.lap.key + "traverse")
        checks = vehicle_checks(ctx)
        checks.append(height_check(ctx, corridor_alt(ctx, self.lap), tol + 0.2, f"At the corridor altitude ({p}1)"))
        checks += lidar_checks(ctx)
        scan = ctx.scan()
        w = wall_info(scan) if scan is not None else None
        checks.append(Check(name="Inside the corridor (a wall is seen)", ok=bool(w is not None and w.any),
                            detail=("walls: left " + _fmt(w.left_m) + ", right " + _fmt(w.right_m)) if w is not None else "no scan"))
        checks.append(Check(name=f"Corridor traversed earlier ({p}3)", ok=bool(trav), blocking=False,
                            detail=f"{p}3 result available" if trav else f"{p}3 not run in this session"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "b4", ctx.cfg)
        speed = float(getattr(cfg, "speed_mps", 0.5))
        nominal_len = float(getattr(cfg, "corridor_length_m", 10.0))
        len_tol = float(getattr(cfg, "length_tol_m", 3.5))
        confirm_s = float(getattr(cfg, "exit_confirm_s", 1.0))
        clear_m = float(getattr(cfg, "clear_m", 1.0))
        max_search = float(getattr(cfg, "max_search_m", 8.0))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.5))
        timeout = float(getattr(cfg, "timeout_s", 60.0))
        min_clear = float(getattr(_lap_cfg(ctx, self.lap, 3), "min_clearance_m", 0.35))
        course = ctx.course
        if course is None or ctx.state().ned is None:
            ctx.emit(f"Cannot run {self.id} without the course frame and a position fix", Sev.ERROR)
            return False
        h_target = corridor_alt(ctx, self.lap)
        flight = CorridorFlight(ctx, course, speed, getattr(cfg, "avoid", None), h_target, lap_heading(ctx, course, self.lap))
        start_fwd = flight.along()
        t0 = time.time()
        walls_seen = False
        last_wall_fwd: float | None = None
        last_wall_dist = 1.65
        gone_since: float | None = None
        gone_fwd: float | None = None
        exit_fwd: float | None = None
        confirmed_fwd: float | None = None
        err_msg: str | None = None
        ctx.emit("Flying on to the corridor exit")

        while time.time() - t0 < timeout:
            ctx.check_abort()
            cmd = flight.step()
            if flight.stale_s() > 3.0:
                err_msg = "Lidar data lost for 3 s"
                break
            fwd = flight.along()
            w = cmd.walls
            if w is not None and flight.new_scan:
                if w.any:
                    walls_seen = True
                    last_wall_fwd = fwd
                    last_wall_dist = w.left_m if w.left_m is not None else (w.right_m if w.right_m is not None else last_wall_dist)
                    gone_since = gone_fwd = None
                elif walls_seen and gone_since is None:
                    gone_since, gone_fwd = time.time(), fwd
            if exit_fwd is None:
                ctx.phase(f"Looking for the exit: {fwd - start_fwd:.1f} m flown, walls {'seen' if walls_seen else 'not yet seen'} ({cmd.mode})",
                          progress=min(0.6, (fwd - start_fwd) / max_search * 0.6))
                if gone_since is not None and time.time() - gone_since >= confirm_s:
                    # the 45..135 deg side sectors still see a wall up to ~wall-distance behind the vehicle, so the walls end
                    # that far behind the point where they disappeared
                    exit_fwd = (gone_fwd if gone_fwd is not None else fwd) - last_wall_dist
                    confirmed_fwd = fwd
                    ctx.emit(f"Both walls gone: corridor exit at {exit_fwd:.2f} m forward", Sev.GOOD)
                if fwd - start_fwd > max_search:
                    err_msg = f"No corridor exit within {max_search:.0f} m"
                    break
            else:
                beyond = fwd - confirmed_fwd
                ctx.phase(f"Clearing the exit: {beyond:.1f} m / {clear_m:.1f} m", progress=0.6 + 0.4 * min(1.0, beyond / max(0.1, clear_m)))
                if beyond >= clear_m:
                    break
            time.sleep(LOOP_S)
        else:
            err_msg = f"Timed out after {timeout:.0f} s"

        flight.hold()
        if err_msg:
            ctx.emit(err_msg, Sev.ERROR)
        _quiet_s(ctx, 1.5, flight)
        h, src = ctx.height()
        st = ctx.state()
        speed_end = math.hypot(*(st.vel_ned[:2])) if st.vel_ned else 0.0
        clearance = flight.min_clearance if math.isfinite(flight.min_clearance) else None
        entry = ctx.mission.get(self.lap.key + "corridor_entry")
        entrance_fwd = float(entry["entrance_fwd_m"]) if isinstance(entry, dict) and entry.get("entrance_fwd_m") is not None else None
        length = (exit_fwd - entrance_fwd) if (exit_fwd is not None and entrance_fwd is not None) else None
        ctx.metric("exit_fwd_m", None if exit_fwd is None else round(exit_fwd, 2))
        ctx.metric("corridor_length_measured_m", None if length is None else round(length, 2))
        ctx.metric("distance_m", round(flight.along() - start_fwd, 2))
        ctx.metric("min_clearance_m", None if clearance is None else round(clearance, 2))
        ctx.metric("max_height_error_m", round(flight.max_height_err, 2))
        ctx.metric("height_source", src)
        ctx.snapshot("front", f"{self.id.lower()}_corridor_exit")
        if exit_fwd is not None:
            ctx.output(self.lap.key + "corridor_exit", {"exit_fwd_m": round(exit_fwd, 2), "length_m": None if length is None else round(length, 2)})
        criteria = [
            Check(name="Corridor exit detected (both walls gone)", ok=bool(exit_fwd is not None and walls_seen),
                  detail=err_msg or "side walls disappeared"),
            Check(name=f"Measured corridor length ~{nominal_len:.0f} m (+-{len_tol:.1f})",
                  ok=bool(length is None or abs(length - nominal_len) <= len_tol), blocking=(length is not None),
                  value=None if length is None else round(length, 2), limit=nominal_len,
                  detail=f"entrance not measured ({self.lap.prefix.upper()}2 not run): length unchecked" if length is None else ""),
            Check(name=f"Clearance to walls >= {min_clear:.2f} m", ok=bool(clearance is None or clearance >= min_clear),
                  value=None if clearance is None else round(clearance, 2), limit=min_clear),
            Check(name=f"Corridor altitude held (+-{alt_tol:.1f} m)", ok=(flight.max_height_err <= alt_tol), value=round(flight.max_height_err, 2), limit=alt_tol),
            Check(name="Stopped and holding at the exit", ok=(speed_end < 0.3), value=round(speed_end, 2), limit=0.3),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        if err_msg:
            ctx.report.error = err_msg
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            where = "the delivery-zone edge" if self.lap.name == "forward" else "the start-area side"
            ctx.emit(f"{self.id} SUCCESS: corridor exit detected{'' if length is None else f' after a {length:.1f} m corridor'}; holding at {where}", Sev.GOOD)
        return success
