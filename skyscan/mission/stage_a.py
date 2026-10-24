"""Stage A implementations (A1–A5) for AeroTHON 2026 Pre-Corridor Operations.

A1: Autonomous Takeoff
A2: Climb & Positioning (5m altitude, 1m forward)
A3: Start QR Detection & Decoding (ground QR scan from 5m altitude)
A4: Green Banner Detection & Entry Alignment (AeroTHON 2026 banner, align with corridor axis)
A5: Safety Backup (1 m straight back from the entrance, before the descent to the corridor altitude)
"""
from __future__ import annotations

import math
import time
from typing import Any

from skyscan.geo import ang_diff, CourseFrame, ground_offset_from_pixel, level_to_ned, wrap360
from skyscan.mission.context import Aborted, MissionContext, height_above_ground
from skyscan.mission.stage import Stage
from skyscan.types import Check, Sev
from skyscan.utils.logger import get_logger

log = get_logger("STAGE/A")


# ───────────────────────────── shared: ground QR positions ─────────────────────────────

def qr_sightings(ctx: MissionContext, course: CourseFrame, since_t: float, text: str | None = None,
                 min_height_m: float = 1.5) -> list[tuple[float, float]]:
    """Course-frame ground positions of the QR codes the belly camera decoded since ``since_t`` (only ``text`` when
    given), each projected with the vehicle state saved with its frame."""
    vis = ctx.vision
    if vis is None or not hasattr(vis, "down_since"):
        return []
    out: list[tuple[float, float]] = []
    for obs in vis.down_since(0):
        st = obs.state
        if obs.t < since_t or st is None or st.ned is None or st.yaw_deg is None or obs.qr is None:
            continue
        h, _ = height_above_ground(st, ctx.full_cfg, now=obs.t)
        if h is None or h < min_height_m:
            continue
        dets = [(obs.qr.center, obs.qr.text)] if (obs.qr.found and obs.qr.center) else []
        dets += [(o.get("center"), o.get("text")) for o in (obs.qr.others or [])]
        cam = vis.camera_model("down", obs.w, obs.h)
        for center, txt in dets:
            if center is None or not txt or (text is not None and txt != text):
                continue
            off = ground_offset_from_pixel(cam, center[0], center[1], h, "body_down", -90.0, st.roll_deg or 0.0, st.pitch_deg or 0.0)
            if off is None:
                continue
            n, e, d = level_to_ned(st.ned, st.yaw_deg, off[0], off[1], 0.0)
            f, r, _ = course.to_course(n, e, d)
            out.append((f, r))
    return out


def median_pt(pts: list[tuple[float, float]]) -> tuple[float, float]:
    fs, rs = sorted(p[0] for p in pts), sorted(p[1] for p in pts)
    return fs[len(fs) // 2], rs[len(rs) // 2]


# ───────────────────────────── A1: Takeoff ─────────────────────────────

class StageA1(Stage):
    id = "A1"
    title = "Autonomous Takeoff"
    rulebook = "Rulebook §4.2.4 (Takeoff)"
    summary = "Take off autonomously from ground start point, establish course frame and stable hover."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        st = ctx.state()
        cfg = getattr(ctx.cfg, "a1", ctx.cfg)
        timeout = float(getattr(cfg, "ready_timeout_s", 120.0))

        # Wait for vehicle ready during checking phase
        ctx.phase("Pre-flight checks: link and EKF convergence")
        t0 = time.time()
        while time.time() - t0 < timeout:
            ctx.check_abort()
            st = ctx.state()
            if st.link and st.ekf_ok and st.prearm_ok is not False:
                break
            time.sleep(0.5)

        return self._checks(st)

    def preview(self, ctx: MissionContext) -> list[Check]:
        return self._checks(ctx.state())            # no waiting for the vehicle: the UI polls this

    @staticmethod
    def _checks(st: Any) -> list[Check]:
        return [
            Check(name="Telemetry link active", ok=bool(st.link), detail=f"hb_age={st.hb_age_s:.1f}s" if st.hb_age_s else "no hb"),
            Check(name="EKF converged & position valid", ok=bool(st.ekf_ok), detail=f"flags=0x{st.ekf_flags:X}" if st.ekf_flags else "none"),
            Check(name="Pre-arm checks passing", ok=(st.prearm_ok is not False), detail="prearm ok" if st.prearm_ok else "prearm failing"),
            Check(name="Vehicle currently disarmed", ok=(not st.armed), detail=f"armed={st.armed}"),
            Check(name="Local NED position available", ok=(st.ned is not None), detail=str(st.ned)),
        ]

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "a1", ctx.cfg)
        takeoff_alt = float(getattr(cfg, "takeoff_alt_m", 2.5))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.3))
        climb_timeout = float(getattr(cfg, "climb_timeout_s", 30.0))
        settle_s = float(getattr(cfg, "settle_s", 2.0))
        max_drift = float(getattr(cfg, "max_drift_m", 0.6))

        # 1. Capture ground origin and start heading
        ctx.phase("Recording ground origin and course frame")
        st = ctx.state()
        if st.ned is None or st.yaw_deg is None:
            ctx.emit("Missing initial position or heading", Sev.ERROR)
            return False

        origin_ned = st.ned
        start_heading = st.yaw_deg
        course = CourseFrame(origin_ned=origin_ned, heading_deg=start_heading)
        ctx.set_course(course)
        ctx.metric("origin_ned", list(origin_ned))
        ctx.metric("start_heading_deg", start_heading)

        # 2. Switch to GUIDED
        ctx.phase("Switching flight mode to GUIDED")
        if not ctx.link.set_mode("GUIDED", timeout=5.0):
            ctx.emit("Failed to enter GUIDED mode", Sev.ERROR)
            return False

        # 3. Arm motors
        ctx.phase("Arming motors")
        armed, reason = ctx.link.arm(timeout=float(getattr(cfg, "arm_timeout_s", 10.0)))
        if not armed:
            ctx.emit(f"Arming failed: {reason}", Sev.ERROR)
            return False

        # 4. Command takeoff
        ctx.phase(f"Commanding takeoff to {takeoff_alt:.1f} m")
        ctx.link.takeoff(takeoff_alt)

        # 5. Monitor climb
        t_takeoff = time.time()
        ctx.mission["_t_takeoff"] = t_takeoff               # the rulebook's 15-minute mission clock (E6 reports it)
        reached = False
        while time.time() - t_takeoff < climb_timeout:
            ctx.check_abort()
            st = ctx.state()
            rel_alt = st.rel_alt_m or 0.0
            ctx.phase(f"Climbing: alt={rel_alt:.2f} m / target={takeoff_alt:.1f} m", progress=min(1.0, rel_alt / takeoff_alt))
            if rel_alt >= (takeoff_alt - alt_tol):
                reached = True
                break
            time.sleep(0.2)

        if not reached:
            ctx.emit(f"Takeoff climb timed out after {climb_timeout}s", Sev.ERROR)
            return False

        # 6. Settle hover
        ctx.phase(f"Settling hover for {settle_s:.1f} s")
        ctx.sleep(settle_s)

        st = ctx.state()
        final_alt = st.rel_alt_m or 0.0
        final_ned = st.ned or (0.0, 0.0, 0.0)
        dx = final_ned[0] - origin_ned[0]
        dy = final_ned[1] - origin_ned[1]
        drift = math.sqrt(dx * dx + dy * dy)

        ctx.metric("final_alt_m", round(final_alt, 2))
        ctx.metric("drift_m", round(drift, 2))

        # Snapshot
        ctx.snapshot("down", "takeoff_hover")

        criteria = [
            Check(name="Target takeoff altitude reached", ok=(final_alt >= takeoff_alt - alt_tol), value=final_alt, limit=takeoff_alt),
            Check(name="Horizontal drift within tolerance", ok=(drift <= max_drift), value=drift, limit=max_drift),
            Check(name="Motors remain armed in GUIDED", ok=(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"A1 Takeoff SUCCESS: hover at {final_alt:.2f} m, drift {drift:.2f} m", Sev.GOOD)
        return success


# ───────────────────────────── A2: Climb & Positioning ─────────────────────────────

class StageA2(Stage):
    id = "A2"
    title = "Climb & Positioning"
    rulebook = "Rulebook §4.2.4 (QR Code Scan prep)"
    summary = "Ascend to 5-meter altitude and move forward 1-meter in the course frame."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        st = ctx.state()
        course = ctx.course
        checks = [
            Check(name="Course frame established from A1", ok=(course is not None), detail="origin set" if course else "missing A1 origin"),
            Check(name="Vehicle airborne and armed", ok=bool(st.armed and (st.rel_alt_m or 0.0) > 1.0), detail=f"alt={st.rel_alt_m}m"),
            Check(name="Flight mode GUIDED", ok=(st.mode == "GUIDED"), detail=f"mode={st.mode}"),
        ]
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "a2", ctx.cfg)
        target_alt = float(getattr(cfg, "target_alt_m", 5.0))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.25))
        forward_m = float(getattr(cfg, "forward_m", 1.0))
        pos_tol = float(getattr(cfg, "pos_tol_m", 0.25))
        timeout = float(getattr(cfg, "timeout_s", 45.0))
        settle_s = float(getattr(cfg, "settle_s", 2.0))

        course = ctx.course
        if course is None:
            ctx.emit("Cannot run A2 without course frame from A1", Sev.ERROR)
            return False

        # Target in CourseFrame: fwd = 1.0, right = 0.0, up = 5.0 m
        target_ned = course.to_ned(forward_m, 0.0, target_alt)
        target_yaw = course.heading_deg

        ctx.phase(f"Climbing to {target_alt:.1f} m and moving forward {forward_m:.1f} m")
        ctx.emit(f"Navigating to course position (fwd={forward_m}m, up={target_alt}m, yaw={target_yaw:.1f}°)")

        t0 = time.time()
        reached = False

        while time.time() - t0 < timeout:
            ctx.check_abort()
            # Constantly push position target to SITL
            ctx.link.goto_ned(target_ned[0], target_ned[1], target_ned[2], yaw_deg=target_yaw)

            st = ctx.state()
            if st.ned is not None and st.rel_alt_m is not None:
                c_fwd, c_right, c_up = course.to_course(st.ned[0], st.ned[1], st.ned[2])
                dist_xy = math.sqrt((c_fwd - forward_m) ** 2 + c_right ** 2)
                alt_err = abs(st.rel_alt_m - target_alt)

                ctx.phase(
                    f"Positioning: fwd={c_fwd:.2f}m (tgt {forward_m}m), alt={st.rel_alt_m:.2f}m (tgt {target_alt}m)",
                    progress=min(1.0, max(0.0, (time.time() - t0) / timeout))
                )

                if dist_xy <= pos_tol and alt_err <= alt_tol:
                    reached = True
                    break
            time.sleep(0.2)

        if not reached:
            ctx.emit("Timeout reaching A2 climb & positioning target", Sev.ERROR)
            return False

        ctx.phase(f"Hover settling for {settle_s:.1f} s")
        ctx.sleep(settle_s)

        st = ctx.state()
        c_fwd, c_right, c_up = course.to_course(st.ned[0], st.ned[1], st.ned[2])
        final_alt = st.rel_alt_m or 0.0
        yaw_err = abs(ang_diff(st.yaw_deg or 0.0, target_yaw))

        ctx.metric("final_course_fwd_m", round(c_fwd, 2))
        ctx.metric("final_course_right_m", round(c_right, 2))
        ctx.metric("final_alt_m", round(final_alt, 2))
        ctx.metric("yaw_error_deg", round(yaw_err, 1))

        ctx.snapshot("down", "a2_5m_position")

        criteria = [
            Check(name="Altitude reaches 5-meter", ok=(abs(final_alt - target_alt) <= alt_tol), value=final_alt, limit=target_alt),
            Check(name="Forward 1-meter position reached", ok=(abs(c_fwd - forward_m) <= pos_tol), value=c_fwd, limit=forward_m),
            Check(name="Heading aligned with course", ok=(yaw_err <= 10.0), value=yaw_err, limit=10.0),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"A2 Positioning SUCCESS: at fwd={c_fwd:.2f}m, alt={final_alt:.2f}m", Sev.GOOD)
        return success


# ───────────────────────────── A3: Start QR Scan ─────────────────────────────

class StageA3(Stage):
    id = "A3"
    title = "Start QR Detection & Decoding"
    rulebook = "Rulebook §4.2.4 (QR Code Scan)"
    summary = "Scan start QR code from 5m altitude, confirm decode votes, and parse delivery target."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        st = ctx.state()
        course = ctx.course
        checks = [
            Check(name="Course frame established", ok=(course is not None)),
            Check(name="Altitude near 5m scan height", ok=bool(st.rel_alt_m and abs(st.rel_alt_m - 5.0) <= 1.0), detail=f"alt={st.rel_alt_m}m"),
            Check(name="Vision pipeline active", ok=(ctx.vision is not None)),
        ]
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "a3", ctx.cfg)
        dwell_s = float(getattr(cfg, "dwell_s", 6.0))
        timeout_s = float(getattr(cfg, "timeout_s", 90.0))
        center_over_qr = bool(getattr(cfg, "center_over_qr", True))
        search_offsets = list(getattr(cfg, "search_offsets_m", [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [2, 0]]))
        gimbal_pitch = float(getattr(cfg, "gimbal_pitch_deg", -90.0))
        scan_alt = float(getattr(cfg, "scan_alt_m", 5.0))

        course = ctx.course
        if course is None:
            ctx.emit("Cannot run A3 without course frame", Sev.ERROR)
            return False

        # Search offsets are relative to where A3 starts (normally the A2 point), not to a hard-coded spot.
        st0 = ctx.state()
        if st0.ned is None:
            ctx.emit("Cannot run A3 without a position fix", Sev.ERROR)
            return False
        base_fwd, base_right, _ = course.to_course(*st0.ned)

        # Reset vision QR session
        ctx.vision.qr_reset()
        ctx.link.set_gimbal(gimbal_pitch, 0.0)

        t_start = time.time()
        confirmed_status = None

        for idx, (fwd_off, right_off) in enumerate(search_offsets):
            ctx.check_abort()
            if time.time() - t_start > timeout_s:
                break

            target_fwd = base_fwd + fwd_off
            target_right = base_right + right_off
            target_ned = course.to_ned(target_fwd, target_right, scan_alt)
            target_yaw = course.heading_deg

            ctx.phase(f"Search point {idx + 1}/{len(search_offsets)}: offset ({fwd_off}m, {right_off}m)")
            ctx.link.goto_ned(target_ned[0], target_ned[1], target_ned[2], yaw_deg=target_yaw)

            # Dwell at search point
            t_point = time.time()
            while time.time() - t_point < dwell_s:
                ctx.check_abort()
                ctx.link.goto_ned(target_ned[0], target_ned[1], target_ned[2], yaw_deg=target_yaw)

                status = ctx.vision.qr_status()
                det = ctx.vision.qr_latest()

                if status.confirmed:
                    confirmed_status = status
                    break

                # If QR located but not confirmed, adjust position over it
                if center_over_qr and det and det.found and det.ground_fwd_m and det.ground_right_m:
                    if abs(det.ground_fwd_m) > 0.3 or abs(det.ground_right_m) > 0.3:
                        st = ctx.state()
                        if st.ned:
                            # Apply small correction
                            adj_n, adj_e, _ = level_to_ned(st.ned, st.yaw_deg or 0.0, det.ground_fwd_m * 0.5, det.ground_right_m * 0.5)
                            ctx.link.goto_ned(adj_n, adj_e, target_ned[2], yaw_deg=target_yaw)

                time.sleep(0.2)

            if confirmed_status:
                break

        if not confirmed_status or not confirmed_status.confirmed:
            ctx.emit("Failed to decode start QR code within search pattern", Sev.ERROR)
            ctx.report.criteria = [
                Check(name="Start QR confirmed decode", ok=False, detail="QR decode timed out"),
            ]
            return False

        payload = confirmed_status.payload
        ctx.output("qr", payload.to_dict() if payload else {})
        ctx.metric("qr_text", confirmed_status.confirmed)
        ctx.metric("qr_target", payload.target if payload else None)
        # where the start QR lies, in the course frame: the landing (E5) finds it again to correct the EKF's drift
        seen = qr_sightings(ctx, course, t_start, confirmed_status.confirmed)
        if seen:
            pos = median_pt(seen)
            ctx.output("start_qr_pos", {"fwd": round(pos[0], 2), "right": round(pos[1], 2), "sightings": len(seen)})
            ctx.metric("start_qr_course", {"fwd": round(pos[0], 2), "right": round(pos[1], 2)})

        ctx.snapshot("down", "start_qr_confirmed")

        criteria = [
            Check(name="Start QR code confirmed", ok=True, value=confirmed_status.confirmed),
            Check(name="Delivery location parsed from payload", ok=bool(payload and payload.valid), detail=payload.note if payload else ""),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"A3 QR Scan SUCCESS: Target={payload.target if payload else 'valid'} ({confirmed_status.confirmed})", Sev.GOOD)
        return success


# ───────────────────────────── A4: Green Corridor Detection & Entry Alignment ─────────────────────────────

def _confirmed_corridor(ctx: MissionContext, n: int, since_t: float, max_age_s: float = 4.0) -> dict[str, float] | None:
    """Median of the last ``n`` consecutive plausible corridor detections taken after ``since_t`` (None if not stable)."""
    track = [d for d in ctx.vision.banner_track(max(n, 1)) if d.t >= since_t]
    track = track[-n:]
    if len(track) < n or time.time() - track[-1].t > max_age_s:
        return None
    if not all(d.found and d.plane_ok for d in track):
        return None
    med = lambda attr: float(sorted(getattr(d, attr) for d in track)[len(track) // 2])  # noqa: E731
    out = {k: med(k) for k in ("distance_m", "lateral_m", "yaw_err_deg", "width_m", "bearing_deg", "score")}
    spread = (
        max(d.lateral_m for d in track) - min(d.lateral_m for d in track),
        max(d.yaw_err_deg for d in track) - min(d.yaw_err_deg for d in track),
        max(d.distance_m for d in track) - min(d.distance_m for d in track),
    )
    if spread[0] > 0.5 or spread[1] > 4.0 or spread[2] > 1.0:   # detections disagree: not a stable lock yet
        return None
    out["t"] = track[-1].t
    return out


class StageA4(Stage):
    id = "A4"
    title = "Green Corridor Detection & Entry Alignment"
    rulebook = "Rulebook §4.2.4 (Corridor Entry Detection, forward lap)"
    summary = ("Find the green corridor (the AeroTHON 'green banner' of this world), measure its entrance and axis "
               "from the front camera, and align on the centre line in front of the entrance. No descent.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        st = ctx.state()
        course = ctx.course
        alt = st.rel_alt_m or 0.0
        cam = ctx.vision.hub.stats("front") if (ctx.vision is not None and hasattr(ctx.vision, "hub")) else {}
        age = cam.get("age_s")
        det = ctx.vision.banner_latest() if ctx.vision is not None else None
        qr = ctx.mission.get("qr")
        return [
            Check(name="Course frame established (A1)", ok=(course is not None),
                  detail="origin recorded" if course else "run A1 first"),
            Check(name="Vehicle airborne, armed, GUIDED",
                  ok=bool(st.armed and alt > 1.0 and st.mode == "GUIDED"),
                  detail=f"armed={st.armed} alt={alt:.1f} m mode={st.mode}"),
            Check(name="Altitude at the scan height (>= 3 m)", ok=alt >= 3.0, detail=f"alt={alt:.2f} m", value=round(alt, 2), limit=3.0),
            Check(name="Front camera streaming", ok=bool(age is not None and age < 3.0 and cam.get("fps", 0) > 0),
                  detail=f"fps={cam.get('fps')} age={age}s", value=cam.get("fps")),
            Check(name="Gimbal reports its pitch", ok=(st.gimbal_pitch_deg is not None), blocking=False,
                  detail=f"pitch={st.gimbal_pitch_deg}"),
            Check(name="Corridor visible from here", ok=bool(det and det.found), blocking=False,
                  detail=(det.reason if det else "no front-camera detection yet")),
            Check(name="Start QR decoded earlier (A3)", ok=bool(qr), blocking=False,
                  detail=f"target={qr.get('target')}" if isinstance(qr, dict) and qr else "A3 not run in this session"),
        ]

    # ── helpers ─────────────────────────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _plan(ctx: MissionContext, meas: dict[str, float], standoff: float, hold_ned_d: float) -> tuple[float, float, float, float]:
        """Target (N, E, D, heading) that puts the vehicle ``standoff`` m before the entrance, on the centre line,
        heading along the corridor axis. Computed from one measurement and the current pose."""
        st = ctx.state()
        yaw = math.radians(meas["yaw_err_deg"])
        a = (math.cos(yaw), math.sin(yaw))                  # corridor axis in the vehicle level frame (fwd, right)
        n = (-math.sin(yaw), math.cos(yaw))                 # to the right of the axis
        along = meas["distance_m"] - standoff
        d_fwd = a[0] * along + n[0] * meas["lateral_m"]
        d_right = a[1] * along + n[1] * meas["lateral_m"]
        tn, te, _ = level_to_ned(st.ned, st.yaw_deg, d_fwd, d_right, 0.0)
        return tn, te, hold_ned_d, wrap360(st.yaw_deg + meas["yaw_err_deg"])

    @staticmethod
    def _fly_to(ctx: MissionContext, tgt: tuple[float, float, float, float], timeout: float,
                xy_tol: float = 0.3, yaw_tol: float = 3.0, alt_tol: float = 0.4) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            ctx.check_abort()
            ctx.link.goto_ned(tgt[0], tgt[1], tgt[2], yaw_deg=tgt[3])
            st = ctx.state()
            if st.ned:
                dxy = math.hypot(st.ned[0] - tgt[0], st.ned[1] - tgt[1])
                if (dxy <= xy_tol and abs(ang_diff(st.yaw_deg or 0.0, tgt[3])) <= yaw_tol
                        and abs(st.ned[2] - tgt[2]) <= alt_tol):
                    return True
            time.sleep(0.2)
        return False

    # ── run ─────────────────────────────────────────────────────────────────────────────────────────────────
    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "a4", ctx.cfg)
        bcfg = getattr(getattr(ctx.full_cfg, "vision", None), "banner", None)
        gimbal_pitch = float(getattr(cfg, "gimbal_pitch_deg", -25.0))
        hold_alt = float(getattr(cfg, "hold_alt_m", 5.0))
        standoff = float(getattr(cfg, "standoff_m", 4.0))
        standoff_tol = float(getattr(cfg, "standoff_tol_m", 0.5))
        lat_tol = float(getattr(cfg, "lateral_tol_m", 0.3))
        yaw_tol = float(getattr(cfg, "yaw_tol_deg", 5.0))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        max_iters = int(getattr(cfg, "max_refine_iters", 6))
        max_travel = float(getattr(cfg, "max_travel_m", 15.0))
        timeout_s = float(getattr(cfg, "timeout_s", 150.0))
        dwell = float(getattr(cfg, "search_dwell_s", 3.0))
        n_conf = int(getattr(bcfg, "confirm_frames", getattr(cfg, "confirm_frames", 3)))
        expected_w = float(getattr(bcfg, "corridor_width_m", 3.5))
        t_stage = time.time()

        course = ctx.course
        if course is None:
            ctx.emit("Cannot run A4 without the course frame from A1", Sev.ERROR)
            return False
        st = ctx.state()
        if st.ned is None or st.yaw_deg is None:
            ctx.emit("Cannot run A4 without a position fix", Sev.ERROR)
            return False
        hold_d = course.to_ned(0.0, 0.0, hold_alt)[2]
        start_fwd, start_right, _ = course.to_course(*st.ned)
        if hasattr(ctx.vision, "set_corridor_colour"):
            ctx.vision.set_corridor_colour("green")             # the return lap (Stage D) switches the detector to orange

        # 1. point the front camera down the corridor and wait for it to get there
        ctx.phase(f"Pitching the front camera to {gimbal_pitch:.0f} deg")
        ctx.link.set_gimbal(gimbal_pitch, 0.0)
        ctx.wait(lambda s: s.gimbal_pitch_deg is not None and abs(s.gimbal_pitch_deg - gimbal_pitch) < 3.0, 8.0, "gimbal at pitch")
        ctx.sleep(1.0)

        # 2. acquire: hold position, then sweep the heading if the corridor is not in view
        def acquire(window_s: float, since: float) -> dict[str, float] | None:
            t0 = time.time()
            while time.time() - t0 < window_s:
                ctx.check_abort()
                m = _confirmed_corridor(ctx, n_conf, since)
                if m:
                    return m
                time.sleep(0.2)
            return None

        ctx.phase("Looking for the green corridor")
        hold = ctx.state()
        meas = acquire(dwell + 2.0, time.time())
        if meas is None:
            ctx.emit("Corridor not in view from the current heading, sweeping the heading", Sev.WARN)
            for rel in list(getattr(cfg, "search_headings_deg", [0, -20, 20, -40, 40])):
                ctx.check_abort()
                yaw = course.abs_heading(float(rel))
                ctx.phase(f"Sweeping to heading {yaw:.0f} deg (course {rel:+.0f} deg)")
                self._fly_to(ctx, (hold.ned[0], hold.ned[1], hold_d, yaw), 12.0, xy_tol=0.5, yaw_tol=4.0)
                meas = acquire(dwell, time.time())
                if meas:
                    break
        if meas is None:
            ctx.emit("Green corridor not found", Sev.ERROR)
            ctx.report.criteria = [Check(name="Green corridor detected", ok=False, detail="no stable detection in any search heading")]
            ctx.snapshot("front", "a4_corridor_not_found")
            return False
        ctx.emit(f"Corridor located: entrance {meas['distance_m']:.1f} m ahead, centre line {meas['lateral_m']:+.2f} m, "
                 f"axis {meas['yaw_err_deg']:+.1f} deg, width {meas['width_m']:.2f} m", Sev.GOOD)
        ctx.snapshot("front", "a4_corridor_detected")
        first = dict(meas)

        # 3. move to the stand-off point on the centre line, heading along the corridor axis
        for it in range(max_iters):
            ctx.check_abort()
            if time.time() - t_stage > timeout_s:
                ctx.emit("A4 timed out while aligning", Sev.ERROR)
                break
            tgt = self._plan(ctx, meas, standoff, hold_d)
            cur = ctx.state()
            travel = math.hypot(tgt[0] - cur.ned[0], tgt[1] - cur.ned[1])
            tf, tr, _ = course.to_course(tgt[0], tgt[1], tgt[2])
            if math.hypot(tf, tr) > max_travel + math.hypot(start_fwd, start_right):
                ctx.emit(f"Alignment target is {math.hypot(tf, tr):.1f} m from the start, beyond the {max_travel:.0f} m limit", Sev.ERROR)
                ctx.report.criteria = [Check(name="Alignment target within travel limit", ok=False, value=round(math.hypot(tf, tr), 1), limit=max_travel)]
                return False
            ctx.phase(f"Aligning ({it + 1}/{max_iters}): moving {travel:.2f} m, yaw {meas['yaw_err_deg']:+.1f} deg",
                      progress=(it + 1) / (max_iters + 1))
            if travel > 0.25 or abs(meas["yaw_err_deg"]) > 2.0:
                self._fly_to(ctx, tgt, 40.0)
            ctx.sleep(1.0)
            # re-measure from the new pose and check against the tolerances
            since = time.time()
            meas = acquire(8.0, since)
            if meas is None:
                ctx.emit("Lost the corridor after moving", Sev.ERROR)
                break
            err_d = meas["distance_m"] - standoff
            ctx.emit(f"Check {it + 1}: lateral {-meas['lateral_m']:+.2f} m, yaw {-meas['yaw_err_deg']:+.1f} deg, "
                     f"entrance {meas['distance_m']:.2f} m (target {standoff:.1f})")
            if abs(meas["lateral_m"]) <= lat_tol * 0.7 and abs(meas["yaw_err_deg"]) <= yaw_tol * 0.7 and abs(err_d) <= standoff_tol * 0.7:
                break

        # 4. prove it is stable: hold still and keep measuring for stable_s
        ctx.phase(f"Holding the aligned pose for {stable_s:.0f} s")
        hold_pose = ctx.state()
        samples: list[dict[str, float]] = []
        t_hold = time.time()
        while time.time() - t_hold < stable_s:
            ctx.check_abort()
            ctx.link.goto_ned(hold_pose.ned[0], hold_pose.ned[1], hold_d, yaw_deg=hold_pose.yaw_deg)
            m = _confirmed_corridor(ctx, n_conf, t_hold)
            if m:
                samples.append(m)
            time.sleep(0.25)
        fin = samples[-1] if samples else (meas or first)
        if not samples:
            ctx.emit("No steady corridor measurement while holding the aligned pose", Sev.WARN)
        worst_lat = max((abs(m["lateral_m"]) for m in samples), default=abs(fin["lateral_m"]))
        worst_yaw = max((abs(m["yaw_err_deg"]) for m in samples), default=abs(fin["yaw_err_deg"]))
        final_state = ctx.state()
        final_alt = final_state.rel_alt_m or 0.0
        ctx.snapshot("front", "a4_corridor_entry_aligned")

        # 5. results
        ctx.metric("first_detection", {k: round(v, 2) for k, v in first.items() if k != "t"})
        ctx.metric("final_lateral_offset_m", round(-fin["lateral_m"], 2))        # vehicle relative to the centre line, + = right of it
        ctx.metric("final_yaw_error_deg", round(-fin["yaw_err_deg"], 1))         # vehicle heading relative to the axis, + = right of it
        ctx.metric("final_entrance_distance_m", round(fin["distance_m"], 2))
        ctx.metric("corridor_width_m", round(fin["width_m"], 2))
        ctx.metric("hold_samples", len(samples))
        ctx.metric("final_alt_m", round(final_alt, 2))

        axis_heading = wrap360((final_state.yaw_deg or 0.0) + fin["yaw_err_deg"])
        ent_n, ent_e, _ = level_to_ned(final_state.ned, final_state.yaw_deg or 0.0,
                                       math.cos(math.radians(fin["yaw_err_deg"])) * fin["distance_m"] - math.sin(math.radians(fin["yaw_err_deg"])) * fin["lateral_m"],
                                       math.sin(math.radians(fin["yaw_err_deg"])) * fin["distance_m"] + math.cos(math.radians(fin["yaw_err_deg"])) * fin["lateral_m"], 0.0)
        ef, er, _ = course.to_course(ent_n, ent_e, final_state.ned[2])
        ctx.output("corridor_axis", {
            "entrance_course": {"fwd": round(ef, 2), "right": round(er, 2)},
            "entrance_ned": [round(ent_n, 2), round(ent_e, 2)],
            "axis_heading_deg": round(axis_heading, 1),
            "axis_rel_course_deg": round(course.rel_heading(axis_heading), 1),
            "width_m": round(fin["width_m"], 2),
            "standoff_m": round(fin["distance_m"], 2),
        })

        criteria = [
            Check(name="Green corridor detected and confirmed", ok=bool(samples or meas), value=f"{n_conf} consecutive frames"),
            Check(name=f"Corridor geometry plausible (width ~{expected_w:.1f} m)", ok=abs(fin["width_m"] - expected_w) <= 0.6,
                  value=round(fin["width_m"], 2), limit=expected_w),
            Check(name="Lateral alignment on the centre line", ok=worst_lat <= lat_tol, value=round(worst_lat, 2), limit=lat_tol),
            Check(name="Heading aligned with the corridor axis", ok=worst_yaw <= yaw_tol, value=round(worst_yaw, 1), limit=yaw_tol),
            Check(name=f"Stand-off before the entrance (~{standoff:.1f} m)", ok=abs(fin["distance_m"] - standoff) <= standoff_tol,
                  value=round(fin["distance_m"], 2), limit=standoff),
            Check(name="Alignment held steady", ok=len(samples) >= 2, value=len(samples), limit=2),
            Check(name="Altitude held (no descent yet)", ok=abs(final_alt - hold_alt) <= 0.5, value=round(final_alt, 2), limit=hold_alt),
        ]
        truth = ctx.truth()
        tc = (truth or {}).get("corridor") if truth else None
        if tc:
            d_lat = abs(-fin["lateral_m"] - tc["lateral_m"])
            d_yaw = abs(-fin["yaw_err_deg"] - tc["yaw_err_deg"])
            d_dist = abs(fin["distance_m"] - (-tc["along_axis_m"]))
            ctx.metric("truth_lateral_m", tc["lateral_m"])
            ctx.metric("truth_yaw_err_deg", tc["yaw_err_deg"])
            ctx.metric("truth_dist_to_entrance_m", round(-tc["along_axis_m"], 2))
            criteria.append(Check(name="Vision agrees with simulator truth (lateral / yaw / distance)",
                                  ok=(d_lat <= 0.25 and d_yaw <= 3.0 and d_dist <= 0.5), blocking=False,
                                  detail=f"d_lat={d_lat:.2f} m  d_yaw={d_yaw:.1f} deg  d_dist={d_dist:.2f} m"))
            criteria.append(Check(name="Truth: vehicle on the centre line / along the axis", ok=(abs(tc["lateral_m"]) <= lat_tol * 1.5 and abs(tc["yaw_err_deg"]) <= yaw_tol * 1.5),
                                  blocking=False, detail=f"lateral={tc['lateral_m']:+.2f} m yaw_err={tc['yaw_err_deg']:+.1f} deg"))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"A4 SUCCESS: aligned {fin['distance_m']:.1f} m before the corridor entrance "
                     f"(lateral {-fin['lateral_m']:+.2f} m, heading {-fin['yaw_err_deg']:+.1f} deg off the axis)", Sev.GOOD)
        return success


# ───────────────────────────── A5: Safety Backup ─────────────────────────────

class StageA5(Stage):
    id = "A5"
    title = "Safety Backup"
    rulebook = "Team safety step (not a rulebook stage): clear the entry arch before the descent to the corridor altitude"
    summary = ("After A4, fly straight back 1 m along the corridor axis, facing the corridor, at the same altitude, so nothing "
               "(entry arch, banner board, wall end) is in front of the vehicle when B1 descends. Then hold and check the new spot.")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        cfg = getattr(ctx.cfg, "a5", ctx.cfg)
        st = ctx.state()
        alt = st.rel_alt_m or 0.0
        axis = ctx.mission.get("corridor_axis")
        have_axis = isinstance(axis, dict) and axis.get("axis_heading_deg") is not None
        return [
            Check(name="Course frame established (A1)", ok=(ctx.course is not None), detail="origin recorded" if ctx.course else "run A1 first"),
            Check(name="Vehicle airborne, armed, GUIDED", ok=bool(st.armed and alt > 1.0 and st.mode == "GUIDED"),
                  detail=f"armed={st.armed} alt={alt:.1f} m mode={st.mode}"),
            Check(name="Corridor axis measured (A4)", ok=have_axis,
                  detail=f"axis heading {axis['axis_heading_deg']:.1f} deg" if have_axis else "run A4 first"),
            Check(name=f"Backs up {float(getattr(cfg, 'back_m', 1.0)):.1f} m", ok=True, blocking=False,
                  detail="straight back along the corridor axis"),
        ]

    def run(self, ctx: MissionContext) -> bool:
        cfg = getattr(ctx.cfg, "a5", ctx.cfg)
        back = float(getattr(cfg, "back_m", 1.0))
        back_tol = float(getattr(cfg, "back_tol_m", 0.25))
        lat_tol = float(getattr(cfg, "lateral_tol_m", 0.3))
        yaw_tol = float(getattr(cfg, "yaw_tol_deg", 5.0))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.4))
        hold_s = float(getattr(cfg, "hold_s", 1.5))
        timeout = float(getattr(cfg, "timeout_s", 25.0))
        course = ctx.course
        st = ctx.state()
        axis = ctx.mission.get("corridor_axis")
        if course is None or st.ned is None or st.yaw_deg is None:
            ctx.emit("Cannot run A5 without the course frame and a position fix", Sev.ERROR)
            return False
        if not (isinstance(axis, dict) and axis.get("axis_heading_deg") is not None):
            ctx.emit("Cannot run A5 without the corridor axis from A4", Sev.ERROR)
            return False
        heading = float(axis["axis_heading_deg"])
        ax = (math.cos(math.radians(heading)), math.sin(math.radians(heading)))      # corridor axis, NED (north, east)
        n0, e0, d0 = st.ned
        truth0 = ((ctx.truth() or {}).get("corridor")) if ctx.truth else None
        tgt = (n0 - back * ax[0], e0 - back * ax[1], d0, heading)
        ctx.emit(f"Backing up {back:.1f} m along the corridor axis ({heading:.1f} deg), facing the corridor")
        ctx.phase(f"Backing up {back:.1f} m")

        reached = StageA4._fly_to(ctx, tgt, timeout, xy_tol=0.15, yaw_tol=yaw_tol * 0.6, alt_tol=alt_tol)
        t_hold = time.time()
        while reached and time.time() - t_hold < hold_s:                              # hold the new spot
            ctx.check_abort()
            ctx.link.goto_ned(tgt[0], tgt[1], tgt[2], yaw_deg=tgt[3])
            time.sleep(0.2)

        fin = ctx.state()
        dn, de = fin.ned[0] - n0, fin.ned[1] - e0
        moved_back = -(dn * ax[0] + de * ax[1])                                       # progress away from the corridor
        cross = -dn * ax[1] + de * ax[0]                                              # sideways drift from the axis line
        yaw_err = abs(ang_diff(fin.yaw_deg or 0.0, heading))
        d_alt = abs(fin.ned[2] - d0)
        ctx.metric("moved_back_m", round(moved_back, 2))
        ctx.metric("lateral_drift_m", round(cross, 2))
        ctx.metric("heading_error_deg", round(yaw_err, 1))
        ctx.metric("altitude_change_m", round(d_alt, 2))
        ctx.snapshot("front", "a5_safety_backup")
        ctx.output("safety_backup", {"back_m": round(moved_back, 2), "axis_heading_deg": round(heading, 1),
                                     "ned": [round(fin.ned[0], 2), round(fin.ned[1], 2)]})

        criteria = [
            Check(name=f"Moved straight back {back:.1f} m", ok=bool(reached and abs(moved_back - back) <= back_tol),
                  value=round(moved_back, 2), limit=back),
            Check(name="Stayed on the corridor axis line", ok=(abs(cross) <= lat_tol), value=round(abs(cross), 2), limit=lat_tol),
            Check(name="Still facing along the corridor axis", ok=(yaw_err <= yaw_tol), value=round(yaw_err, 1), limit=yaw_tol),
            Check(name="Altitude held (no descent yet)", ok=(d_alt <= alt_tol), value=round(d_alt, 2), limit=alt_tol),
            Check(name="Armed and still in GUIDED", ok=bool(fin.armed and fin.mode == "GUIDED")),
        ]
        truth1 = ((ctx.truth() or {}).get("corridor")) if ctx.truth else None
        if truth0 and truth1:
            grew = (-truth1["along_axis_m"]) - (-truth0["along_axis_m"])
            ctx.metric("truth_entrance_distance_change_m", round(grew, 2))
            criteria.append(Check(name="Truth: entrance is now further away by the backup distance",
                                  ok=(abs(grew - back) <= back_tol + 0.15), blocking=False,
                                  detail=f"entrance distance grew {grew:.2f} m (backup {back:.1f} m)"))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"A5 SUCCESS: backed up {moved_back:.2f} m along the axis (drift {cross:+.2f} m, "
                     f"heading error {yaw_err:.1f} deg); B1 can descend", Sev.GOOD)
        return success
