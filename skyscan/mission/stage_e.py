"""Stage E implementations (E1-E6): back through the return corridor, home to the take-off point, and land.

E1: descend to the corridor height (10 ft, ~3 m) at D3's stand-off point in front of the orange corridor
E2: enter the return corridor
E3: traverse it, avoiding its static obstacles (the orange lane of rulebook Figure 3 has them; the green one does not)
E4: detect the return corridor's exit on the start-area side
E5: climb to 5 m, fly to the start QR, re-find it with the belly camera and correct the EKF's drift, then hold over
    the take-off point
E6: land on the take-off point, disarm, and report the mission time against the rulebook's 15 minutes

Rulebook Mission 2 (p.36-37): "Return Flight: ... navigate back through the corridor while avoiding obstacles, and return
to the take-off location. Landing: the mission concludes once the drone lands safely at the designated take-off point."
Scoring (p.42): 6 Autonomous Return Navigation (20), 7 Safe Autonomous Landing (5), 8 Mission Completion Within Time (15).

E1-E4 are the Stage B corridor stages flown on the return lap: the same lidar code, holding the return corridor's axis
measured by D3 and counting progress along it. Simulator ground truth is read only to cross-check results afterwards.
"""
from __future__ import annotations

import math
import time
from typing import Any

from skyscan.mission.context import MissionContext
from skyscan.mission.stage import Stage
from skyscan.mission.stage_a import StageA4, median_pt, qr_sightings
from skyscan.mission.stage_b import RETURN, StageB1, StageB2, StageB3, StageB4, vehicle_checks
from skyscan.types import Check, Sev
from skyscan.utils.logger import get_logger

log = get_logger("STAGE/E")

LOOP_S = 0.1
MISSION_LIMIT_S = 15 * 60.0          # rulebook p.36: 15 minutes for the whole mission


def _fmt(v: float | None, unit: str = "m", nd: int = 2) -> str:
    return "n/a" if v is None else f"{v:.{nd}f} {unit}"


def _pos(ctx: MissionContext, course: Any) -> tuple[float, float]:
    f, r, _ = course.to_course(*ctx.state().ned)
    return f, r


def landing_point(ctx: MissionContext) -> tuple[float, float]:
    """Where E6 lands, in the course frame: E5's drift-corrected take-off point, else the take-off point itself."""
    lp = ctx.mission.get("landing_point")
    if isinstance(lp, dict) and lp.get("fwd") is not None:
        return float(lp["fwd"]), float(lp["right"])
    return 0.0, 0.0


def drift_correction(recorded: tuple[float, float], measured: tuple[float, float], max_m: float) -> tuple[float, float] | None:
    """How far the EKF frame has slid since A3, from the start QR seen then (``recorded``) and now (``measured``). The QR
    did not move, so the take-off point (0, 0) of the old frame now sits at the returned offset. None when the
    difference is too large to be drift (a misread, or another QR)."""
    d = (measured[0] - recorded[0], measured[1] - recorded[1])
    return d if math.hypot(*d) <= max_m else None


# ───────────────────────────── E1-E4: the corridor stages on the return lap ─────────────────────────────

class StageE1(StageB1):
    id = "E1"
    title = "Descent to Return-Corridor Altitude"
    rulebook = "Return Flight (p.36): fly back through the corridor, corridor height 10 ft (~3 m)"
    summary = "At D3's stand-off point in front of the orange corridor, descend straight down to 3 m and hold, heading along its axis."
    lap = RETURN


class StageE2(StageB2):
    id = "E2"
    title = "Return Corridor Entry"
    rulebook = "Return Flight (p.36): navigate back through the 3.5 m wide corridor"
    summary = "Fly along the return corridor's axis until the lidar sees both walls, continue 1.5 m inside on the centre line."
    lap = RETURN


class StageE3(StageB3):
    id = "E3"
    title = "Return Obstacle Traversal"
    rulebook = "Return Flight (p.36) / Figure 3: back through the corridor while avoiding its static obstacles"
    summary = "Lidar-reactive flight through the orange corridor: slalom round the static obstacles, keep off the walls, hold 3 m."
    lap = RETURN


class StageE4(StageB4):
    id = "E4"
    title = "Return Corridor Exit"
    rulebook = "Return Flight (p.36): complete the corridor on the way back to the take-off location"
    summary = "Keep flying the return corridor until both walls are gone (the exit), clear it by 1 m and hold on the start-area side."
    lap = RETURN


# ───────────────────────────── E5: back to the take-off point ─────────────────────────────

class StageE5(Stage):
    id = "E5"
    title = "Return to the Take-off Point"
    rulebook = "Return Flight (p.36): return to the take-off location"
    summary = ("Climb to 5 m, fly to the start QR and read it again with the belly camera to correct the position drift "
               "since take-off, then hold over the take-off point, facing the take-off heading.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        qr = ctx.mission.get("start_qr_pos")
        ex = ctx.mission.get("return_corridor_exit")
        checks = vehicle_checks(ctx)
        checks.append(Check(name="Return corridor exited (E4)", ok=bool(ex), blocking=False,
                            detail="E4 result available" if ex else "E4 not run in this session"))
        checks.append(Check(name="Start QR position known (A3)", ok=bool(qr), blocking=False,
                            detail=(f"at ({qr['fwd']}, {qr['right']})" if qr else "A3 not run: landing on the EKF position only")))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None:
            ctx.emit("Cannot run E5 without the course frame and a position fix", Sev.ERROR)
            return False
        alt = float(getattr(cfg, "approach_alt_m", 5.0))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.4))
        over_tol = float(getattr(cfg, "over_tol_m", 0.3))
        dwell = float(getattr(cfg, "qr_dwell_s", 4.0))
        min_reads = int(getattr(cfg, "min_qr_reads", 3))
        max_corr = float(getattr(cfg, "max_correction_m", 3.0))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        transit_timeout = float(getattr(cfg, "transit_timeout_s", 90.0))
        heading = course.heading_deg                             # land facing the way the vehicle took off
        d_alt = course.to_ned(0.0, 0.0, alt)[2]
        t0 = time.time()

        # 1. straight up to the approach height (clear of the 10 ft corridor walls before any sideways move)
        start = _pos(ctx, course)
        ctx.emit(f"Climbing to {alt:.0f} m before flying home from ({start[0]:.1f}, {start[1]:.1f})")
        ctx.phase(f"Climbing to {alt:.0f} m")
        climbed = StageA4._fly_to(ctx, (st.ned[0], st.ned[1], d_alt, st.yaw_deg or heading), 30.0, xy_tol=0.6, yaw_tol=180.0, alt_tol=alt_tol)
        if not climbed:
            ctx.emit(f"Did not reach {alt:.0f} m", Sev.ERROR)

        # 2. over the start QR (it is next to the take-off point) and read it again
        qr_rec = ctx.mission.get("start_qr_pos")
        qr_text = (ctx.mission.get("qr") or {}).get("raw")
        recorded = (float(qr_rec["fwd"]), float(qr_rec["right"])) if isinstance(qr_rec, dict) else None
        corr: tuple[float, float] | None = None
        reads = 0
        measured: tuple[float, float] | None = None
        if recorded is not None and climbed:
            ctx.link.set_gimbal(-90.0, 0.0)
            n, e, _ = course.to_ned(recorded[0], recorded[1], alt)
            ctx.emit(f"Flying to the start QR at ({recorded[0]:.1f}, {recorded[1]:.1f}) to check the position drift")
            ctx.phase("Flying to the start QR")
            if StageA4._fly_to(ctx, (n, e, d_alt, heading), transit_timeout, xy_tol=0.4, yaw_tol=5.0, alt_tol=alt_tol):
                ctx.phase(f"Reading the start QR for {dwell:.0f} s")
                t_r = time.time()
                while time.time() - t_r < dwell:
                    ctx.check_abort()
                    ctx.link.goto_ned(n, e, d_alt, yaw_deg=heading)
                    time.sleep(0.2)
                seen = qr_sightings(ctx, course, t_r, qr_text)
                reads = len(seen)
                if reads >= min_reads:
                    measured = median_pt(seen)
                    corr = drift_correction(recorded, measured, max_corr)
                    if corr is None:
                        ctx.emit(f"Start QR seen {math.hypot(measured[0] - recorded[0], measured[1] - recorded[1]):.1f} m from where "
                                 f"A3 saw it: too far to be drift, ignoring it", Sev.WARN)
                    else:
                        ctx.emit(f"Start QR read {reads} times: position drift since take-off {math.hypot(*corr):.2f} m "
                                 f"(fwd {corr[0]:+.2f}, right {corr[1]:+.2f})", Sev.GOOD)
                else:
                    ctx.emit(f"Start QR read only {reads} time(s): landing on the EKF position", Sev.WARN)
            else:
                ctx.emit("Could not reach the start QR", Sev.WARN)
        elif recorded is None:
            ctx.emit("Start QR position unknown (A3 not run): landing on the EKF position", Sev.WARN)

        # 3. over the take-off point
        lp = corr if corr is not None else (0.0, 0.0)
        n, e, _ = course.to_ned(lp[0], lp[1], alt)
        ctx.emit(f"Moving over the take-off point ({lp[0]:+.2f}, {lp[1]:+.2f})")
        ctx.phase("Moving over the take-off point")
        over = StageA4._fly_to(ctx, (n, e, d_alt, heading), transit_timeout, xy_tol=over_tol, yaw_tol=5.0, alt_tol=alt_tol)
        samples: list[float] = []
        if over:
            ctx.phase(f"Holding over the take-off point for {stable_s:.0f} s")
            t_h = time.time()
            while time.time() - t_h < stable_s:
                ctx.check_abort()
                ctx.link.goto_ned(n, e, d_alt, yaw_deg=heading)
                f, r = _pos(ctx, course)
                samples.append(math.hypot(f - lp[0], r - lp[1]))
                time.sleep(0.2)
        st = ctx.state()
        h, src = ctx.height()
        f, r = _pos(ctx, course)
        err = math.hypot(f - lp[0], r - lp[1])
        worst = max(samples, default=err)
        ctx.snapshot("down", "e5_over_takeoff_point")
        ctx.metric("transit_s", round(time.time() - t0, 1))
        ctx.metric("qr_reads", reads)
        ctx.metric("drift_correction", None if corr is None else {"fwd": round(corr[0], 2), "right": round(corr[1], 2)})
        ctx.metric("position_error_m", round(err, 2))
        ctx.metric("height_m", None if h is None else round(h, 2))
        ctx.output("landing_point", {"fwd": round(lp[0], 2), "right": round(lp[1], 2), "qr_reads": reads,
                                     "corrected": corr is not None, "alt_m": None if h is None else round(h, 2)})
        criteria = [
            Check(name=f"Approach height reached ({alt:.0f} m)", ok=bool(climbed and h is not None and abs(h - alt) <= alt_tol + 0.1),
                  value=None if h is None else round(h, 2), limit=alt, detail=f"height from the {src}"),
            Check(name=f"Holding over the take-off point (<= {over_tol:.1f} m)", ok=bool(over and worst <= over_tol + 0.1),
                  value=round(worst, 2), limit=over_tol),
            Check(name="Start QR re-read to correct the drift", ok=corr is not None, blocking=False,
                  value=reads, detail="" if corr is not None else "landing on the EKF position"),
            Check(name="Facing the take-off heading", ok=abs(((st.yaw_deg or 0.0) - heading + 180.0) % 360.0 - 180.0) <= 8.0, blocking=False,
                  value=None if st.yaw_deg is None else round(st.yaw_deg, 1), limit=round(heading, 1)),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        truth = ctx.truth()
        tc = (truth or {}).get("course") if truth else None
        if tc:
            d_true = math.hypot(tc["fwd"], tc["right"])
            ctx.metric("truth_dist_to_takeoff_m", round(d_true, 2))
            criteria.append(Check(name="(sim truth) Over the real take-off point (<= 0.5 m)", blocking=False, ok=d_true <= 0.5,
                                  value=round(d_true, 2), limit=0.5))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"E5 SUCCESS: holding {_fmt(h)} over the take-off point ({err:.2f} m off), "
                     f"{'drift corrected from the start QR' if corr is not None else 'EKF position'}", Sev.GOOD)
        return success


# ───────────────────────────── E6: landing ─────────────────────────────

class StageE6(Stage):
    id = "E6"
    title = "Precision Landing at the Take-off Point"
    rulebook = "Landing (p.36): the mission concludes once the drone lands safely at the designated take-off point"
    summary = ("Descend over the take-off point to 1 m holding position, hand over to the flight controller's LAND, wait "
               "for touchdown and disarm. Reports the landing error and the mission time against 15 minutes.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        lp = ctx.mission.get("landing_point")
        checks = vehicle_checks(ctx)
        checks.append(Check(name="Over the take-off point (E5)", ok=bool(lp), blocking=False,
                            detail=f"landing point ({lp['fwd']}, {lp['right']})" if lp else "E5 not run: landing on the take-off point by EKF"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None:
            ctx.emit("Cannot run E6 without the course frame and a position fix", Sev.ERROR)
            return False
        rate = float(getattr(cfg, "descent_mps", 0.6))
        handover = float(getattr(cfg, "handover_alt_m", 1.0))
        tol = float(getattr(cfg, "landing_tol_m", 1.0))
        land_timeout = float(getattr(cfg, "land_timeout_s", 45.0))
        disarm_timeout = float(getattr(cfg, "disarm_timeout_s", 15.0))
        descent_timeout = float(getattr(cfg, "descent_timeout_s", 30.0))
        heading = course.heading_deg
        lp = landing_point(ctx)
        n, e, _ = course.to_ned(lp[0], lp[1], 0.0)
        h0, src0 = ctx.height()
        if h0 is None:
            ctx.emit("No height reference available", Sev.ERROR)
            return False
        t0 = time.time()
        max_xy = 0.0

        # 1. controlled descent over the point (position held by us) down to the hand-over height
        ctx.emit(f"Descending over the take-off point from {h0:.1f} m to {handover:.1f} m")
        while time.time() - t0 < descent_timeout:
            ctx.check_abort()
            st = ctx.state()
            h, _ = ctx.height()
            if h is None or st.ned is None:
                time.sleep(LOOP_S)
                continue
            f, r, _ = course.to_course(*st.ned)
            max_xy = max(max_xy, math.hypot(f - lp[0], r - lp[1]))
            step = max(-rate, min(rate, handover - h))
            ctx.link.goto_ned(n, e, st.ned[2] - step, yaw_deg=heading)
            ctx.phase(f"Descending: {h:.2f} m -> {handover:.1f} m", progress=0.6 * min(1.0, max(0.0, (h0 - h) / max(0.1, h0 - handover))))
            if h <= handover + 0.15:
                break
            time.sleep(LOOP_S)

        # 2. touchdown with the flight controller's LAND mode (it detects the ground and disarms)
        ctx.mission["_allowed_modes"] = ["LAND"]                # the safety monitor must not read this as a takeover
        landed = disarmed = False
        t_land = time.time()
        try:
            ctx.phase("Touchdown (LAND mode)", progress=0.7)
            if not ctx.link.land():
                ctx.emit("The flight controller did not accept LAND", Sev.ERROR)
            else:
                ctx.emit("LAND engaged: touching down on the take-off point")
                on_ground_since: float | None = None
                while time.time() - t_land < land_timeout:
                    ctx.check_abort()
                    st = ctx.state()
                    if st.ned is not None:
                        f, r, _ = course.to_course(*st.ned)
                        max_xy = max(max_xy, math.hypot(f - lp[0], r - lp[1]))
                    if not st.armed:
                        landed = disarmed = True
                        break
                    if st.landed_state == 1:                        # MAV_LANDED_STATE_ON_GROUND
                        landed = True
                        on_ground_since = on_ground_since or time.time()
                        if time.time() - on_ground_since > disarm_timeout:
                            ctx.emit("On the ground but still armed: disarming", Sev.WARN)
                            disarmed = ctx.link.disarm()
                            break
                    h, _ = ctx.height()
                    ctx.phase(f"Touchdown: height {_fmt(h)}", progress=0.8)
                    time.sleep(0.2)
        finally:
            ctx.mission.pop("_allowed_modes", None)
        land_s = time.time() - t_land
        st = ctx.state()
        f, r, _ = course.to_course(*st.ned) if st.ned else (float("nan"), float("nan"), 0.0)
        err_point = math.hypot(f - lp[0], r - lp[1])
        err_takeoff = math.hypot(f, r)
        t_takeoff = ctx.mission.get("_t_takeoff")
        mission_s = (time.time() - float(t_takeoff)) if t_takeoff else None
        ctx.snapshot("front", "e6_landed")
        ctx.metric("descent_s", round(t_land - t0, 1))
        ctx.metric("touchdown_s", round(land_s, 1))
        ctx.metric("touchdown_course", {"fwd": round(f, 2), "right": round(r, 2)})
        ctx.metric("landing_error_m", round(err_point, 2))
        ctx.metric("distance_from_takeoff_ekf_m", round(err_takeoff, 2))
        ctx.metric("max_drift_during_landing_m", round(max_xy, 2))
        ctx.metric("mission_time_s", None if mission_s is None else round(mission_s, 1))
        ctx.output("landing", {"landed": landed, "disarmed": disarmed, "touchdown": {"fwd": round(f, 2), "right": round(r, 2)},
                               "error_m": round(err_point, 2), "mission_time_s": None if mission_s is None else round(mission_s, 1)})
        criteria = [
            Check(name="Touched down (on the ground)", ok=landed, detail=f"after {land_s:.0f} s of LAND"),
            Check(name="Motors disarmed", ok=disarmed),
            Check(name=f"Landed on the take-off point (<= {tol:.1f} m)", ok=bool(landed and err_point <= tol), value=round(err_point, 2), limit=tol),
            Check(name="Mission completed within 15 minutes", ok=bool(mission_s is not None and mission_s <= MISSION_LIMIT_S), blocking=False,
                  value=None if mission_s is None else round(mission_s, 0), limit=MISSION_LIMIT_S,
                  detail="" if mission_s is not None else "A1 not run in this session: mission time unknown"),
        ]
        truth = ctx.truth()
        tc = (truth or {}).get("course") if truth else None
        if tc:
            d_true = math.hypot(tc["fwd"], tc["right"])
            ctx.metric("truth_dist_to_takeoff_m", round(d_true, 2))
            criteria.append(Check(name=f"(sim truth) On the real take-off point (<= {tol:.1f} m)", blocking=False, ok=d_true <= tol,
                                  value=round(d_true, 2), limit=tol))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            mt = "" if mission_s is None else f", mission time {int(mission_s // 60)} min {mission_s % 60:02.0f} s"
            ctx.emit(f"E6 SUCCESS: landed {err_point:.2f} m from the take-off point and disarmed{mt}", Sev.GOOD)
        return success

