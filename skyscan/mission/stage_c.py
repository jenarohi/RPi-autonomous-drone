"""Stage C implementations (C1-C4): the delivery zone.

C1: leave the corridor, climb to the 10 m search altitude and align with the delivery-zone entry point
C2: boustrophedon (lawnmower) search over the zone with the belly camera: find QR codes, avoid red zones
C3: verify that the QR code found is the one the start QR asked for
C4: descend from 10 m to 5 m directly over it, lower the payload on the winch and release it

Rulebook Mission 2 (p.35-37): "ascend to approximately 10 m to identify the correct QR code ... avoid designated
restricted (red) zones ... descend to 5 m, lower and release the payload accurately at the correct QR code".

Sensors: the belly camera (QR codes, red mask), the flight controller's height reference (``MissionContext.height()``)
and the EKF position. Simulator ground truth is read only to cross-check results afterwards, never to fly.

Red-zone evasion protocol (the team's Stage C spec): when red enters the safety margin on the way ahead, halt forward
progress at once, reverse 2 m along the entry vector, sidestep far enough to clear the boundary within 5 s, update the
search grid and resume the sweep without crossing a red boundary.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from skyscan.geo import ground_offset_from_pixel, level_to_ned
from skyscan.mission.context import MissionContext, height_above_ground
from skyscan.mission.search import (Leg, PathFollower, Pt, Strip, Zone, ZoneGrid, dist, footprint_m, make_strips,
                                    plan_evasion, strip_spacing_m, unit)
from skyscan.mission.stage import Stage
from skyscan.payload import Winch
from skyscan.types import Check, Sev
from skyscan.utils.logger import get_logger
from skyscan.vision.qr import parse_qr_payload

log = get_logger("STAGE/C")

LOOP_S = 0.1                 # control loop period (velocity setpoints must keep arriving at >= 2 Hz)
SEARCH_PUBLISH_S = 0.4
NAV_PUBLISH_S = 0.2


# ───────────────────────────── config helpers ─────────────────────────────

def _group(ctx: MissionContext) -> Any:
    return getattr(getattr(ctx.full_cfg, "mission", None), "stage_c", None) or {}


def _gv(ctx: MissionContext, name: str, default: Any = None) -> Any:
    return getattr(_group(ctx), name, default)


def search_alt(ctx: MissionContext) -> float:
    return float(_gv(ctx, "search_alt_m", 10.0))


def deliver_alt(ctx: MissionContext) -> float:
    return float(_gv(ctx, "deliver_alt_m", 5.0))


def zone_of(ctx: MissionContext) -> Zone:
    return Zone.from_cfg(_gv(ctx, "zone"))


def _fmt(v: float | None, unit_: str = "m", nd: int = 2) -> str:
    return "n/a" if v is None else f"{v:.{nd}f} {unit_}"


# ───────────────────────────── target and candidate QR codes ─────────────────────────────

@dataclass
class Target:
    """What the start QR (A3) asked for."""
    raw: str
    target: str | None

    @classmethod
    def from_mission(cls, ctx: MissionContext) -> "Target | None":
        q = ctx.mission.get("qr")
        if not isinstance(q, dict) or not (q.get("raw") or q.get("target")):
            return None
        return cls(str(q.get("raw") or ""), (str(q["target"]) if q.get("target") else None))

    def matches(self, text: str | None) -> bool:
        if not text:
            return False
        if self.raw and text.strip().casefold() == self.raw.strip().casefold():
            return True
        p = parse_qr_payload(text)
        return bool(self.target and p.target and p.target.strip().upper() == self.target.strip().upper())


@dataclass
class Candidate:
    """A QR code seen on the ground: where it is (mean of every sighting) and what it reads."""
    id: int
    n: int = 0
    sf: float = 0.0
    sr: float = 0.0
    sff: float = 0.0
    srr: float = 0.0
    decoded: dict[str, int] = field(default_factory=dict)
    last_t: float = 0.0
    size_px: float | None = None

    @property
    def fwd(self) -> float:
        return self.sf / self.n if self.n else 0.0

    @property
    def right(self) -> float:
        return self.sr / self.n if self.n else 0.0

    @property
    def pt(self) -> Pt:
        return (self.fwd, self.right)

    @property
    def scatter_m(self) -> float:
        if self.n < 2:
            return 0.0
        vf = max(0.0, self.sff / self.n - self.fwd ** 2)
        vr = max(0.0, self.srr / self.n - self.right ** 2)
        return math.sqrt(vf + vr)

    @property
    def text(self) -> str | None:
        return max(self.decoded, key=self.decoded.get) if self.decoded else None

    def add(self, pt: Pt, text: str | None, size_px: float | None, t: float) -> None:
        self.n += 1
        self.sf += pt[0]
        self.sr += pt[1]
        self.sff += pt[0] ** 2
        self.srr += pt[1] ** 2
        self.last_t = t
        if size_px:
            self.size_px = size_px
        if text:
            self.decoded[text] = self.decoded.get(text, 0) + 1


class CandidateRegistry:
    """Every QR code seen so far, clustered by ground position."""

    def __init__(self, target: Target | None, cluster_m: float = 1.5, confirm_decodes: int = 3, min_frames: int = 3) -> None:
        self.target, self.cluster_m = target, float(cluster_m)
        self.confirm, self.min_frames = int(confirm_decodes), int(min_frames)
        self.cands: list[Candidate] = []

    def observe(self, pt: Pt, text: str | None, size_px: float | None, t: float) -> Candidate:
        best: Candidate | None = None
        for c in self.cands:
            d = dist(pt, c.pt)
            if d <= self.cluster_m and (best is None or d < dist(pt, best.pt)):
                best = c
        if best is None:
            best = Candidate(id=len(self.cands) + 1)
            self.cands.append(best)
        best.add(pt, text, size_px, t)
        return best

    def status(self, c: Candidate) -> str:
        """``match`` / ``decoy`` once a text has been read ``confirm`` times, else ``unknown``."""
        txt = c.text
        if txt is None or c.decoded[txt] < self.confirm:
            return "unknown"
        return "match" if (self.target is not None and self.target.matches(txt)) else "decoy"

    def real(self) -> list[Candidate]:
        return [c for c in self.cands if c.n >= self.min_frames]

    def matched(self) -> Candidate | None:
        ms = [c for c in self.real() if self.status(c) == "match"]
        return max(ms, key=lambda c: c.decoded[c.text]) if ms else None

    def to_list(self) -> list[dict[str, Any]]:
        return [{"id": c.id, "fwd": round(c.fwd, 2), "right": round(c.right, 2), "text": c.text, "status": self.status(c),
                 "frames": c.n, "decodes": sum(c.decoded.values()), "scatter_m": round(c.scatter_m, 2)} for c in self.real()]


@dataclass
class LiveQR:
    """A QR sighting in the latest belly-camera frame."""
    t: float
    pt: Pt                         # course frame
    off: Pt                        # (fwd, right) from the vehicle, level frame
    text: str | None
    size_px: float | None


class ZoneState:
    """Everything the C stages share: the zone, the red map, the QR codes seen and how the search went."""

    def __init__(self, ctx: MissionContext) -> None:
        g = _group(ctx)
        red = getattr(g, "red", {}) or {}
        c2 = getattr(g, "c2", {}) or {}
        self.zone = zone_of(ctx)
        self.grid = ZoneGrid(self.zone, res_m=float(getattr(red, "grid_res_m", 0.5)), margin_m=float(getattr(red, "margin_m", 1.5)),
                             confirm_hits=int(getattr(red, "confirm_hits", 2)), fence_inset_m=float(getattr(g, "fence_inset_m", 1.0)))
        self.cands = CandidateRegistry(Target.from_mission(ctx), cluster_m=float(getattr(c2, "cluster_m", 1.5)),
                                       confirm_decodes=int(getattr(c2, "confirm_decodes", 3)), min_frames=int(getattr(c2, "min_frames", 3)))
        self.strips: list[Strip] = []
        self.last_seq = -1
        self.evasions: list[dict[str, Any]] = []
        self.red_entries = 0                     # times the vehicle was over a confirmed red cell (the camera map)


def zone_state(ctx: MissionContext) -> ZoneState | None:
    zs = ctx.mission.get("_zone")
    return zs if isinstance(zs, ZoneState) else None


# ───────────────────────────── camera observations -> ground positions ─────────────────────────────

class ZoneObserver:
    """Turns the belly camera's detections into ground positions in the course frame, using the vehicle state that was
    saved with each frame: red hulls go into the grid, QR codes into the registry, the footprint into the coverage."""

    def __init__(self, ctx: MissionContext, course: Any, zs: ZoneState) -> None:
        self.ctx, self.course, self.zs = ctx, course, zs
        down = getattr(getattr(ctx.full_cfg, "cameras", None), "down", None)
        self.hfov = float(getattr(down, "hfov_deg", 60.0))
        self.live: list[LiveQR] = []              # sightings in the latest frame that had any
        self.live_t = 0.0
        self.new_live: list[LiveQR] = []          # every sighting processed by the latest poll(): each is counted once
        self.frames = 0
        self.red_frames = 0
        self.cover_min_alt = 6.0

    def poll(self) -> int:
        vis = self.ctx.vision
        if vis is None:
            return 0
        obs_list = vis.down_since(self.zs.last_seq)
        self.new_live = []
        for obs in obs_list:
            self.zs.last_seq = obs.seq
            try:
                self._process(obs)
            except Exception as exc:  # noqa: BLE001 - one bad frame must not stop the flight
                log.warn(f"observation {obs.seq} skipped: {type(exc).__name__}: {exc}")
        return len(obs_list)

    def fresh_live(self, max_age_s: float = 0.6) -> list[LiveQR]:
        return self.live if (self.live and time.time() - self.live_t <= max_age_s) else []

    def _ground(self, st: Any, cam: Any, h: float, u: float, v: float) -> tuple[Pt, Pt] | None:
        off = ground_offset_from_pixel(cam, u, v, h, "body_down", -90.0, st.roll_deg or 0.0, st.pitch_deg or 0.0)
        if off is None:
            return None
        n, e, d = level_to_ned(st.ned, st.yaw_deg or 0.0, off[0], off[1], 0.0)
        f, r, _ = self.course.to_course(n, e, d)
        return (f, r), (off[0], off[1])

    def _process(self, obs: Any) -> None:
        st = obs.state
        if st is None or st.ned is None or st.yaw_deg is None:
            return
        h, _ = height_above_ground(st, self.ctx.full_cfg, now=obs.t)
        if h is None or h < 1.0:
            return
        self.frames += 1
        cam = self.ctx.vision.camera_model("down", obs.w, obs.h)
        f0, r0, _ = self.course.to_course(*st.ned)
        grid = self.zs.grid
        if h >= self.cover_min_alt:
            along, across = footprint_m(h, self.hfov, obs.w, obs.h)
            grid.mark_footprint((f0, r0), 0.45 * along, 0.45 * across)       # 90 % of the footprint: edges are unreliable
        if obs.red is not None and obs.red.found:
            self.red_frames += 1
            for blob in obs.red.blobs:
                poly = [g[0] for g in (self._ground(st, cam, h, u, v) for u, v in blob.hull) if g is not None]
                if len(poly) >= 3:
                    grid.add_polygon(poly)
        q = obs.qr
        dets: list[tuple[Any, str | None, float | None]] = []
        if q is not None and q.found and q.center:
            dets.append((q.center, q.text, q.size_px))
        for o in (q.others or []) if q is not None else []:
            dets.append((o["center"], o.get("text"), o.get("size_px")))
        live: list[LiveQR] = []
        for center, text, size in dets:
            g = self._ground(st, cam, h, center[0], center[1])
            if g is None:
                continue
            self.zs.cands.observe(g[0], text, size, obs.t)
            live.append(LiveQR(obs.t, g[0], g[1], text, size))
        if live:
            self.live, self.live_t = live, time.time()
            self.new_live.extend(live)


# ───────────────────────────── flight ─────────────────────────────

class ZoneFlight:
    """Velocity flight in the course frame at a held height, heading held on the course heading (so the belly camera's
    image axes stay aligned with the zone's fwd / right axes)."""

    def __init__(self, ctx: MissionContext, course: Any, h_target: float, nav_cfg: Any) -> None:
        self.ctx, self.course = ctx, course
        self.heading = float(course.heading_deg)
        self.h_target = float(h_target)
        self.kz = float(getattr(nav_cfg, "k_height", 0.8))
        self.vz_max = float(getattr(nav_cfg, "vz_max_mps", 0.8))
        self.max_mps = float(getattr(nav_cfg, "max_mps", 1.2))
        self.max_height_err = 0.0
        self.height_src = "none"
        self.mode = "HOLD"
        self._anchor: tuple[float, float, float] | None = None
        self._last_nav = 0.0

    def pos(self) -> Pt | None:
        st = self.ctx.state()
        if st.ned is None:
            return None
        f, r, _ = self.course.to_course(*st.ned)
        return (f, r)

    def height(self) -> float | None:
        h, src = self.ctx.height()
        self.height_src = src
        return h

    def speed_xy(self) -> float:
        st = self.ctx.state()
        return math.hypot(st.vel_ned[0], st.vel_ned[1]) if st.vel_ned else 0.0

    def height_error(self) -> float | None:
        h = self.height()
        return None if h is None else self.h_target - h

    def _vd(self, track_error: bool = True) -> float:
        err = self.height_error()
        if err is None:
            return 0.0
        if track_error:
            self.max_height_err = max(self.max_height_err, abs(err))
        return -max(-self.vz_max, min(self.vz_max, self.kz * err))

    def velocity(self, vf: float, vr: float, mode: str = "SWEEP", track_error: bool = True) -> None:
        """Command a ground velocity (course fwd, right) while holding height and heading."""
        self._anchor = None
        self.mode = mode
        n = math.hypot(vf, vr)
        if n > self.max_mps:
            vf, vr = vf / n * self.max_mps, vr / n * self.max_mps
        vn, ve = self.course.dir_to_ned(vf, vr)
        self.ctx.link.velocity_ned(vn, ve, self._vd(track_error), yaw_deg=self.heading)
        now = time.time()
        if now - self._last_nav >= NAV_PUBLISH_S:
            self._last_nav = now
            self.ctx.bus.publish("nav", {"stage": self.ctx.stage_id, "mode": mode, "vx": round(vf, 2), "vy": round(vr, 2),
                                         "theta_deg": 0.0, "free_m": 0.0})

    def hold(self) -> None:
        """Stop and hold the current position and height."""
        self.mode = "HOLD"
        if self._anchor is None:
            st = self.ctx.state()
            if st.ned is None:
                return
            err = self.height_error()
            self._anchor = (st.ned[0], st.ned[1], st.ned[2] - (err if err is not None else 0.0))
        self.ctx.link.goto_ned(self._anchor[0], self._anchor[1], self._anchor[2], yaw_deg=self.heading)
        self.ctx.bus.publish("nav", {"stage": self.ctx.stage_id, "mode": "HOLD", "vx": 0.0, "vy": 0.0, "theta_deg": 0.0, "free_m": 0.0})


class TruthWatch:
    """Simulator ground truth about the red zones and QR codes, sampled while flying. For the report only."""

    def __init__(self, ctx: MissionContext) -> None:
        self.ctx = ctx
        self.have = False
        self.min_red_m = math.inf
        self.violations = 0
        self._inside = False
        self._last = 0.0
        # debugging aid (c2.debug_frames_dir): save the raw belly frame whenever the simulator says a QR code is in view,
        # with what the live scanner made of it, to find out why a code that is there was not reported
        self.debug_dir = getattr(getattr(_group(ctx), "c2", None), "debug_frames_dir", None)
        self._dbg_n: dict[str, int] = {}
        self._dbg_t: dict[str, float] = {}

    def sample(self, min_period_s: float = 0.3) -> None:
        now = time.time()
        if now - self._last < min_period_s:
            return
        self._last = now
        t = self.ctx.truth()
        if self.debug_dir and t:
            self._debug_frames(t)
        zones = (t or {}).get("restricted")
        if not zones:
            return
        self.have = True
        self.min_red_m = min(self.min_red_m, min(z["dist_m"] for z in zones))
        inside = any(z["inside"] for z in zones)
        if inside and not self._inside:
            self.violations += 1
        self._inside = inside

    def _debug_frames(self, truth: dict[str, Any]) -> None:
        import os

        import cv2
        vis = self.ctx.vision
        if vis is None:
            return
        now = time.time()
        for q in truth.get("qrs") or []:
            qid = q["id"]
            if abs(q["dfwd"]) > 3.5 or abs(q["dright"]) > 4.5:
                continue
            n = self._dbg_n.get(qid, 0)
            if n >= 8 or now - self._dbg_t.get(qid, 0.0) < 1.2:
                continue
            frame = vis.hub.latest("down")
            if frame is None or frame.img is None:
                continue
            det = vis.qr_latest()
            os.makedirs(self.debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(self.debug_dir, f"{qid}_{n}_df{q['dfwd']:+.1f}_dr{q['dright']:+.1f}.png"), frame.img)
            self._dbg_n[qid], self._dbg_t[qid] = n + 1, now
            log.info(f"debug frame {qid} #{n}: QR is ({q['dfwd']:+.1f}, {q['dright']:+.1f}) m from the vehicle; scanner found="
                     f"{det.found if det else None} text={det.text if det else None} decoder={det.decoder if det else None} "
                     f"others={len(det.others or []) if det else 0}")

    def qr_offset(self, text: str | None) -> float | None:
        """True distance from the vehicle to the delivery-zone QR whose content is ``text`` (or None without truth). The start
        QR carries the same text as the matching zone code, so it is left out; of the rest the nearest counts."""
        t = self.ctx.truth()
        same = [q for q in (t or {}).get("qrs") or [] if q.get("content") == text]
        zone = [q for q in same if not str(q.get("id", "")).startswith("start")]
        pick = zone or same
        return min(float(q["dist_m"]) for q in pick) if pick else None


class ZoneNavigator:
    """Follows a route over the zone with the red-zone protocol running underneath."""

    def __init__(self, ctx: MissionContext, course: Any, zs: ZoneState, flight: ZoneFlight, observer: ZoneObserver) -> None:
        self.ctx, self.course, self.zs, self.flight, self.observer = ctx, course, zs, flight, observer
        g = _group(ctx)
        nav, red = getattr(g, "nav", {}) or {}, getattr(g, "red", {}) or {}
        self.cruise = float(getattr(nav, "cruise_mps", 0.8))
        self.look = float(getattr(nav, "lookahead_m", 1.5))
        self.reach = float(getattr(nav, "reach_m", 0.4))
        self.halt_m = float(getattr(red, "halt_m", 3.0))
        self.reverse_m = float(getattr(red, "reverse_m", 2.0))
        self.evade_mps = float(getattr(red, "evade_mps", 1.0))
        self.offset_budget_s = float(getattr(red, "offset_budget_s", 5.0))
        self.max_lateral_m = float(getattr(red, "max_lateral_m", 6.0))
        self.max_evasions = int(getattr(red, "max_evasions", 6))
        self.stall_s = float(getattr(nav, "stall_s", 10.0))
        self.fence_slack = float(_gv(ctx, "fence_slack_m", 2.5))
        self.current_strip: int | None = None
        self.min_red_dist = math.inf
        self.truth = TruthWatch(ctx)
        self.ui_route: list[Pt] = []
        self.target_pt: Pt | None = None
        self.mode = "HOLD"
        self._was_in_red = False
        self._last_pub = 0.0

    # --- bookkeeping ----------------------------------------------------------------------------------------

    def monitor(self, pos: Pt) -> None:
        """Per-cycle watch: over a red cell? how close to red? coverage; and the UI picture."""
        grid = self.zs.grid
        if grid.zone.contains(pos):
            i, j = grid.cell(pos)
            in_red = bool(grid.red[i, j])
            if in_red and not self._was_in_red:
                self.zs.red_entries += 1
                self.ctx.emit("The vehicle is over a red zone", Sev.ERROR)
            self._was_in_red = in_red
        self.min_red_dist = min(self.min_red_dist, grid.dist_to_red(pos))
        self.truth.sample()
        now = time.time()
        if now - self._last_pub >= SEARCH_PUBLISH_S:
            self._last_pub = now
            self.publish(pos)

    def publish(self, pos: Pt | None = None) -> None:
        zs = self.zs
        pos = pos or self.flight.pos()
        h = self.flight.height()
        self.ctx.bus.publish("search", {
            "stage": self.ctx.stage_id, "mode": self.flight.mode, "zone": zs.zone.to_dict(),
            "pos": None if pos is None else [round(pos[0], 2), round(pos[1], 2)], "alt_m": None if h is None else round(h, 2),
            "strips": [{"right": s.right, "f0": s.f_start, "f1": s.f_end} for s in zs.strips],
            "route": [[round(p[0], 1), round(p[1], 1)] for p in self.ui_route[:80]],
            "red": zs.grid.red_boxes(), "margin_m": zs.grid.margin, "qrs": zs.cands.to_list(),
            "coverage": round(zs.grid.coverage(), 3), "evasions": len(zs.evasions),
            "target": None if self.target_pt is None else [round(self.target_pt[0], 2), round(self.target_pt[1], 2)],
        })

    def fence_breach(self, pos: Pt) -> bool:
        return not self.zs.zone.contains(pos, slack=self.fence_slack)

    # --- moving ---------------------------------------------------------------------------------------------

    def goto(self, p: Pt, speed: float, tol: float, timeout_s: float, mode: str = "EVADE") -> bool:
        """Straight P-controlled move to ``p`` (used by the evasion moves)."""
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            self.ctx.check_abort()
            self.observer.poll()
            pos = self.flight.pos()
            if pos is None:
                time.sleep(LOOP_S)
                continue
            self.monitor(pos)
            d = (p[0] - pos[0], p[1] - pos[1])
            n = math.hypot(*d)
            if n <= tol:
                return True
            v = min(speed, 1.2 * n + 0.15)
            self.flight.velocity(d[0] / n * v, d[1] / n * v, mode)
            time.sleep(LOOP_S)
        return False

    def _evade(self, follower: PathFollower) -> None:
        """Halt, reverse along the entry vector, sidestep clear of the boundary, all while the map keeps updating."""
        ctx, flight, zs = self.ctx, self.flight, self.zs
        t_trig = time.time()
        pos = flight.pos()
        a = follower.pts[min(follower.seg, len(follower.pts) - 1)]
        b = follower.pts[min(follower.seg + 1, len(follower.pts) - 1)]
        travel = unit(b[0] - a[0], b[1] - a[1])
        if travel == (0.0, 0.0):
            st = ctx.state()
            travel = unit(*(st.vel_ned[:2] if st.vel_ned else (1.0, 0.0)))
            travel = unit(*self.course.dir_to_ned(1.0, 0.0)) if travel == (0.0, 0.0) else travel
        red_d = zs.grid.dist_to_red(pos)
        ctx.emit(f"Red zone {red_d:.1f} m from the path ahead: halting", Sev.WARN)
        # 1) halt forward progress at once
        while time.time() - t_trig < 2.5:
            ctx.check_abort()
            flight.hold()
            self.observer.poll()
            p = flight.pos()
            if p is not None:
                self.monitor(p)
            if flight.speed_xy() < 0.15 and time.time() - t_trig > 0.3:
                break
            time.sleep(LOOP_S)
        halt_s = time.time() - t_trig
        p_halt = flight.pos() or pos
        # 2) reverse along the entry vector
        plan = plan_evasion(zs.grid, p_halt, travel, self.reverse_m, self.halt_m, self.max_lateral_m)
        t_r = time.time()
        self.goto(plan.reverse_to, self.evade_mps, 0.4, self.reverse_m / max(0.2, self.evade_mps) + 6.0)
        reverse_s = time.time() - t_r
        p_back = flight.pos() or plan.reverse_to
        # 3) sidestep clear of the boundary (re-planned: the map has grown while we backed off)
        plan2 = plan_evasion(zs.grid, p_back, travel, 0.0, self.halt_m + self.reverse_m, self.max_lateral_m)
        t_o = time.time()
        ok_o = self.goto(plan2.offset_to, self.evade_mps, 0.4, self.offset_budget_s + 4.0)
        offset_s = time.time() - t_o
        ev = {"t": round(t_trig, 2), "at": [round(p_halt[0], 2), round(p_halt[1], 2)], "red_dist_m": round(red_d, 2),
              "halt_s": round(halt_s, 2), "reversed_m": round(dist(p_halt, p_back), 2), "reverse_s": round(reverse_s, 2),
              "side": plan2.side, "lateral_m": round(plan2.lateral_m, 2), "offset_s": round(offset_s, 2),
              "within_budget": bool(ok_o and offset_s <= self.offset_budget_s), "clear": bool(plan2.ok)}
        zs.evasions.append(ev)
        ctx.emit(f"Evasion: halted in {halt_s:.1f} s, reversed {ev['reversed_m']:.1f} m, sidestepped {plan2.side} "
                 f"{plan2.lateral_m:.1f} m in {offset_s:.1f} s", Sev.GOOD if ev["within_budget"] else Sev.WARN)

    def follow(self, route_fn: Callable[[Pt], list[Leg]], stop_fn: Callable[[], bool] | None = None, timeout_s: float = 300.0,
               speed: float | None = None) -> str:
        """Fly the route that ``route_fn(pos)`` gives, re-asking whenever the red map changes. Returns ``done`` (route
        finished), ``stopped`` (``stop_fn`` said so), ``timeout``, ``fence`` or ``lost`` (no position)."""
        ctx, flight, grid = self.ctx, self.flight, self.zs.grid
        speed = speed or self.cruise
        t0 = time.time()
        pos = flight.pos()
        if pos is None:
            return "lost"
        pts, seg_leg = self._build(pos, route_fn(pos))
        follower = PathFollower(pts, self.look, self.reach)
        planned = grid.version
        evasions = 0
        best, t_best, stalls = math.inf, time.time(), 0           # progress watchdog: remaining path must keep shrinking
        while True:
            ctx.check_abort()
            if time.time() - t0 > timeout_s:
                flight.hold()
                return "timeout"
            self.observer.poll()
            pos = flight.pos()
            if pos is None:
                time.sleep(LOOP_S)
                continue
            self.monitor(pos)
            if self.fence_breach(pos):
                flight.hold()
                return "fence"
            if stop_fn is not None and stop_fn():
                flight.hold()
                return "stopped"
            if grid.version != planned:
                # new red cells: if the way we were going now leads into the margin, run the evasion protocol; then re-plan
                blocked = grid.first_blocked_along(follower.ahead(pos), self.halt_m)
                if blocked is not None and not grid.blocked(pos) and evasions < self.max_evasions:
                    self._evade(follower)
                    evasions += 1
                    pos = flight.pos() or pos
                planned = grid.version
                pts, seg_leg = self._build(pos, route_fn(pos))
                follower = PathFollower(pts, self.look, self.reach)
                best, t_best = math.inf, time.time()                  # a new route has a new length: restart the watchdog
                continue
            carrot, remaining = follower.update(pos)
            if follower.done:
                flight.hold()
                return "done"
            if remaining < best - 0.4:
                best, t_best = remaining, time.time()
            elif time.time() - t_best > self.stall_s:
                stalls += 1
                ctx.emit(f"No progress along the route for {self.stall_s:.0f} s ({remaining:.1f} m to go): re-planning", Sev.WARN)
                log.warning(f"stall: pos=({pos[0]:.2f},{pos[1]:.2f}) carrot=({carrot[0]:.2f},{carrot[1]:.2f}) seg={follower.seg}/"
                            f"{len(follower.pts) - 1} speed={flight.speed_xy():.2f} mode={flight.mode} "
                            f"next={[(round(a, 2), round(b, 2)) for a, b in follower.pts[follower.seg:follower.seg + 3]]}")
                if stalls > 3:
                    flight.hold()
                    return "stalled"
                pts, seg_leg = self._build(pos, route_fn(pos))
                follower = PathFollower(pts, self.look, self.reach)
                best, t_best = math.inf, time.time()
                continue
            if seg_leg:
                leg = seg_leg[min(follower.seg, len(seg_leg) - 1)]
                self.current_strip = leg.strip
                mode = "SWEEP" if leg.sweeping else "TRANSIT"
            else:
                mode = "TRANSIT"
            d = unit(carrot[0] - pos[0], carrot[1] - pos[1])
            v = min(speed, max(0.2, 0.8 * remaining))
            flight.velocity(d[0] * v, d[1] * v, mode)
            time.sleep(LOOP_S)

    def _build(self, pos: Pt, legs: list[Leg]) -> tuple[list[Pt], list[Leg]]:
        pts: list[Pt] = [pos]
        seg_leg: list[Leg] = []
        for leg in legs:
            for p in leg.pts:
                pts.append(p)
                seg_leg.append(leg)
        self.ui_route = pts
        return pts, seg_leg

    def go_to(self, goal: Pt, timeout_s: float = 90.0, stop_fn: Callable[[], bool] | None = None) -> str:
        """Fly to ``goal`` around any red keep-out (a goal inside it is moved to the nearest free spot)."""
        grid = self.zs.grid

        def route(pos: Pt) -> list[Leg]:
            plan = grid.plan(pos, goal)
            return [Leg(0, plan.path, False)] if (plan.ok and plan.path) else []

        return self.follow(route, stop_fn=stop_fn, timeout_s=timeout_s)

    # --- hovering over a QR ---------------------------------------------------------------------------------

    def centre(self, over: Pt, tol_m: float, stable_s: float, timeout_s: float, vmax: float = 0.4, k: float = 0.6,
               mode: str = "CENTRE", until: Callable[[list[tuple[Pt, str | None]]], bool] | None = None) -> dict[str, Any]:
        """Hover-correct onto the QR code near ``over``: steer on its camera offset when it is in view, else on the
        position estimate. Done once it has been within ``tol_m`` for ``stable_s`` and ``until(samples)`` (if given) is
        true. Returns the sightings collected (their ground positions and decoded texts)."""
        flight = self.flight
        t0 = time.time()
        stable_since: float | None = None
        samples: list[tuple[Pt, str | None]] = []
        err_m: float | None = None
        seen_t = 0.0
        ok = False
        while time.time() - t0 < timeout_s:
            self.ctx.check_abort()
            self.observer.poll()
            pos = flight.pos()
            if pos is None:
                time.sleep(LOOP_S)
                continue
            self.monitor(pos)
            for q in self.observer.new_live:
                if dist(q.pt, over) <= 1.6:
                    samples.append((q.pt, q.text))
            ours = [q for q in self.observer.fresh_live(0.6) if dist(q.pt, over) <= 1.6]
            if ours:
                q = min(ours, key=lambda x: math.hypot(*x.off))
                off = q.off
                err_m = math.hypot(*off)
                seen_t = time.time()
            else:
                off = (over[0] - pos[0], over[1] - pos[1])
                err_m = None
            n = math.hypot(*off)
            v = min(vmax, k * n)
            flight.velocity(off[0] / n * v if n > 1e-6 else 0.0, off[1] / n * v if n > 1e-6 else 0.0, mode)
            if err_m is not None and err_m <= tol_m:
                stable_since = stable_since or time.time()
                if time.time() - stable_since >= stable_s and (until is None or until(samples)):
                    ok = True
                    break
            else:
                stable_since = None
            time.sleep(LOOP_S)
        return {"ok": ok, "err_m": err_m, "samples": samples, "last_seen_s": (time.time() - seen_t) if seen_t else None}


# ───────────────────────────── shared checks ─────────────────────────────

def vehicle_checks(ctx: MissionContext, min_alt: float = 1.0) -> list[Check]:
    st = ctx.state()
    h, src = ctx.height()
    return [
        Check(name="Course frame established (A1)", ok=(ctx.course is not None), detail="origin recorded" if ctx.course else "run A1 first"),
        Check(name="Vehicle airborne, armed, GUIDED", ok=bool(st.armed and (h or 0.0) > min_alt and st.mode == "GUIDED"),
              detail=f"armed={st.armed} height={_fmt(h)} ({src}) mode={st.mode}"),
    ]


def camera_checks(ctx: MissionContext, blocking: bool = True) -> list[Check]:
    vis = ctx.vision
    age = vis.down_age_s() if (vis is not None and hasattr(vis, "down_age_s")) else None
    return [Check(name="Belly camera streaming", ok=bool(age is not None and age <= 2.0), blocking=blocking,
                  value=None if age is None else round(age, 2), limit=2.0,
                  detail="no belly-camera frame processed yet" if age is None else f"last frame {age:.1f} s ago")]


def height_check(ctx: MissionContext, target: float, tol: float, name: str, blocking: bool = True) -> Check:
    h, src = ctx.height()
    return Check(name=name, ok=bool(h is not None and abs(h - target) <= tol), blocking=blocking, value=None if h is None else round(h, 2),
                 limit=target, detail=f"height {_fmt(h)} from the {src}")


def target_check(ctx: MissionContext) -> Check:
    t = Target.from_mission(ctx)
    return Check(name="Delivery target known (A3 start QR)", ok=t is not None,
                 detail=f"target {t.target!r} ({t.raw!r})" if t else "run A3 first: no start QR payload")


def _flight(ctx: MissionContext, course: Any, h_target: float) -> ZoneFlight:
    return ZoneFlight(ctx, course, h_target, getattr(_group(ctx), "nav", {}) or {})


def _need_state(ctx: MissionContext, need_course: bool = True) -> tuple[Any, ZoneState] | None:
    course, zs = ctx.course, zone_state(ctx)
    if need_course and course is None:
        ctx.emit("Cannot run without the course frame", Sev.ERROR)
        return None
    if zs is None:
        ctx.emit("No search state: run C2 first", Sev.ERROR)
        return None
    return course, zs


# ───────────────────────────── C1: corridor transition and zone entry ─────────────────────────────

class StageC1(Stage):
    id = "C1"
    title = "Corridor Transition & Zone Entry"
    rulebook = "Stage C, C1: leave the corridor, climb to 10 m AGL and align with the delivery-zone entry coordinates"
    summary = "From the corridor exit climb to the 10 m search altitude, fly to the zone entry point and hold, heading along the course."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        zone = zone_of(ctx)
        st = ctx.state()
        course = ctx.course
        checks = vehicle_checks(ctx, 1.5)
        checks += camera_checks(ctx)
        pos = course.to_course(*st.ned)[:2] if (course is not None and st.ned is not None) else None
        checks.append(Check(name="Near the delivery zone", ok=bool(pos is not None and zone.contains(pos, slack=8.0)),
                            detail="outside the zone by more than 8 m" if pos is not None else "no position"))
        ex = ctx.mission.get("corridor_exit")
        checks.append(Check(name="Corridor exit detected earlier (B4)", ok=bool(ex), blocking=False,
                            detail="B4 result available" if ex else "B4 not run in this session"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        g = _group(ctx)
        course = ctx.course
        st = ctx.state()
        if course is None or st.ned is None:
            ctx.emit("Cannot run C1 without the course frame and a position fix", Sev.ERROR)
            return False
        target = search_alt(ctx)
        tol = float(getattr(g, "alt_tol_m", 0.5))
        climb = float(getattr(cfg, "climb_mps", 0.8))
        entry: Pt = (float(cfg.entry[0]), float(cfg.entry[1]))
        entry_tol = float(getattr(cfg, "entry_tol_m", 0.6))
        stable_s = float(getattr(cfg, "stable_s", 2.0))
        head_tol = float(getattr(cfg, "heading_tol_deg", 8.0))
        timeout = float(getattr(cfg, "timeout_s", 90.0))
        zone = zone_of(ctx)
        flight = _flight(ctx, course, target)
        heading = course.heading_deg
        h0, src0 = ctx.height()
        if h0 is None:
            ctx.emit("No height reference available", Sev.ERROR)
            return False
        ctx.metric("height_source", src0)
        ctx.metric("start_height_m", round(h0, 2))
        t0 = time.time()

        # 1) straight up to the search altitude (we are just past the corridor exit: nothing above us)
        n0, e0, _ = st.ned
        ctx.emit(f"Climbing from {h0:.1f} m to the {target:.0f} m search altitude")
        in_tol_since: float | None = None
        while time.time() - t0 < timeout:
            ctx.check_abort()
            st = ctx.state()
            h, src = ctx.height()
            if h is None or st.ned is None:
                time.sleep(LOOP_S)
                continue
            err = target - h
            step = max(-climb, min(climb, err))
            ctx.link.goto_ned(n0, e0, st.ned[2] - step, yaw_deg=heading)
            ctx.phase(f"Climbing: height {h:.1f} m -> {target:.0f} m ({src})", progress=min(0.5, max(0.0, (h - h0) / max(0.1, target - h0)) * 0.5))
            if abs(err) <= tol:
                in_tol_since = in_tol_since or time.time()
                if time.time() - in_tol_since >= 1.0:
                    break
            else:
                in_tol_since = None
            time.sleep(LOOP_S)
        else:
            ctx.emit("Climb to the search altitude timed out", Sev.ERROR)

        # 2) fly to the zone entry point at the search altitude
        ctx.emit(f"Flying to the zone entry point (fwd {entry[0]:.1f}, right {entry[1]:.1f})")
        at_since: float | None = None
        p_start = flight.pos() or (0.0, 0.0)
        n_start = max(1.0, dist(p_start, entry))
        while time.time() - t0 < timeout:
            ctx.check_abort()
            pos = flight.pos()
            if pos is None:
                time.sleep(LOOP_S)
                continue
            d = (entry[0] - pos[0], entry[1] - pos[1])
            n = math.hypot(*d)
            if n <= entry_tol:
                at_since = at_since or time.time()
                flight.hold()
                if time.time() - at_since >= stable_s:
                    break
            else:
                at_since = None
                v = min(float(getattr(getattr(g, "nav", {}), "cruise_mps", 0.8)), 0.6 * n + 0.15)
                flight.velocity(d[0] / n * v, d[1] / n * v, "TRANSIT")
            ctx.phase(f"To the zone entry: {n:.1f} m to go", progress=0.5 + 0.5 * max(0.0, 1.0 - n / n_start))
            time.sleep(LOOP_S)
        flight.hold()
        ctx.sleep(0.5)

        st = ctx.state()
        h, src = ctx.height()
        pos = flight.pos() or (0.0, 0.0)
        err_entry = dist(pos, entry)
        yaw_err = abs(((st.yaw_deg or heading) - heading + 180.0) % 360.0 - 180.0)
        vis = ctx.vision
        age = vis.down_age_s() if (vis is not None and hasattr(vis, "down_age_s")) else None
        ctx.metric("height_m", None if h is None else round(h, 2))
        ctx.metric("height_source", src)
        ctx.metric("entry_error_m", round(err_entry, 2))
        ctx.metric("heading_error_deg", round(yaw_err, 1))
        ctx.metric("climb_and_entry_s", round(time.time() - t0, 1))
        ctx.snapshot("down", "c1_zone_entry")
        ctx.output("zone_entry", {"fwd": round(pos[0], 2), "right": round(pos[1], 2), "alt_m": None if h is None else round(h, 2)})
        ctx.output("search_zone", zone_of(ctx).to_dict())
        criteria = [
            Check(name=f"Search altitude reached ({target:.0f} m AGL)", ok=bool(h is not None and abs(h - target) <= tol),
                  value=None if h is None else round(h, 2), limit=target),
            Check(name=f"At the zone entry point (+-{entry_tol:.1f} m)", ok=(err_entry <= entry_tol), value=round(err_entry, 2), limit=entry_tol),
            Check(name="Inside the delivery-zone geo-fence", ok=zone.contains(pos), detail=f"({pos[0]:.1f}, {pos[1]:.1f})"),
            Check(name=f"Heading along the course (+-{head_tol:.0f} deg)", ok=(yaw_err <= head_tol), value=round(yaw_err, 1), limit=head_tol),
            Check(name="Belly camera streaming", ok=bool(age is not None and age <= 2.0), value=None if age is None else round(age, 2), limit=2.0),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"C1 SUCCESS: at {_fmt(h)} over the zone entry, {err_entry:.2f} m from the entry point", Sev.GOOD)
        return success


# ───────────────────────────── C2: boustrophedon search ─────────────────────────────

class StageC2(Stage):
    id = "C2"
    title = "Boustrophedon Search & Red-Zone Evasion"
    rulebook = "Stage C, C2: lawnmower search of the delivery zone at 10 m, red-zone masking and the evasion protocol"
    summary = ("Sweep the zone in strips (30 % overlap), find the QR codes with the belly camera, keep out of red zones "
               "(halt, back off 2 m, sidestep, re-plan).")

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        zone = zone_of(ctx)
        g = _group(ctx)
        tol = float(getattr(g, "alt_tol_m", 0.5))
        course, st = ctx.course, ctx.state()
        pos = course.to_course(*st.ned)[:2] if (course is not None and st.ned is not None) else None
        checks = vehicle_checks(ctx, 5.0)
        checks.append(height_check(ctx, search_alt(ctx), tol + 1.0, "At the search altitude (C1)"))
        checks += camera_checks(ctx)
        checks.append(target_check(ctx))
        checks.append(Check(name="Inside the delivery zone", ok=bool(pos is not None and zone.contains(pos, slack=2.0)),
                            detail="outside the zone: run C1" if pos is not None else "no position"))
        checks.append(Check(name="Red-zone detector present", ok=bool(getattr(ctx.vision, "red_detector", None) is not None),
                            detail="vision pipeline has no red-zone detector"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        g = _group(ctx)
        course = ctx.course
        st = ctx.state()
        target = Target.from_mission(ctx)
        if course is None or st.ned is None or target is None:
            ctx.emit("Cannot run C2 without the course frame, a position fix and the start QR payload", Sev.ERROR)
            return False
        h_search = search_alt(ctx)
        alt_tol = float(getattr(g, "alt_tol_m", 0.5))
        timeout = float(getattr(cfg, "timeout_s", 480.0))
        overlap = float(getattr(cfg, "overlap", 0.30))
        cov_min = float(getattr(cfg, "coverage_min", 0.95))
        stop_on_match = bool(getattr(cfg, "stop_on_match", True))
        fence = float(getattr(g, "fence_inset_m", 1.0))
        zs = ZoneState(ctx)                                   # a new search starts with a clean map and no QR codes
        ctx.mission["_zone"] = zs
        flight = _flight(ctx, course, h_search)
        observer = ZoneObserver(ctx, course, zs)
        nav = ZoneNavigator(ctx, course, zs, flight, observer)
        pos0 = flight.pos() or (zs.zone.fwd_min, 0.0)
        spacing_cfg = getattr(cfg, "strip_spacing_m", None)
        spacing = float(spacing_cfg) if spacing_cfg else strip_spacing_m(h_search, observer.hfov, overlap)
        zs.strips = make_strips(zs.zone, spacing, inset_m=fence, start=pos0)
        strip_len = sum(s.length_m for s in zs.strips)
        ctx.metric("strips", len(zs.strips))
        ctx.metric("strip_spacing_m", round(zs.zone.width_m / max(1, len(zs.strips)), 2))
        ctx.metric("planned_sweep_m", round(strip_len, 1))
        ctx.output("search_plan", {"strips": len(zs.strips), "spacing_m": round(zs.zone.width_m / max(1, len(zs.strips)), 2),
                                   "overlap": overlap, "altitude_m": h_search})
        ctx.emit(f"Sweeping the zone: {len(zs.strips)} strips, {strip_len:.0f} m, looking for {target.raw!r}")

        def route(pos: Pt) -> list[Leg]:
            first = nav.current_strip if nav.current_strip is not None else 0
            return zs.grid.route(pos, zs.strips, first)

        def matched() -> bool:
            m = zs.cands.matched()
            return bool(stop_on_match and m is not None and m.decoded.get(m.text, 0) >= zs.cands.confirm)

        t0 = time.time()

        def watch() -> bool:
            k, tot = nav.current_strip or 0, len(zs.strips)
            ctx.phase(f"Sweeping strip {k + 1}/{tot}, coverage {zs.grid.coverage() * 100:.0f} %, "
                      f"{len(zs.cands.real())} QR seen, {len(zs.evasions)} evasion(s)", progress=min(1.0, (k + 0.5) / max(1, tot)))
            return matched()

        result = nav.follow(route, stop_fn=watch, timeout_s=timeout)
        flight.hold()
        duration = time.time() - t0
        match = zs.cands.matched()
        real = zs.cands.real()
        if match is not None:
            nav.target_pt = match.pt
            ctx.emit(f"Matching QR read at ({match.fwd:.1f}, {match.right:.1f}): {match.text!r}", Sev.GOOD)
            ctx.snapshot("down", "c2_match_in_view")
        nav.publish()
        h, src = ctx.height()
        st = ctx.state()
        grid = zs.grid
        cov = grid.coverage()
        n_evade = len(zs.evasions)
        late = [e for e in zs.evasions if not e["within_budget"]]
        ctx.metric("result", result)
        ctx.metric("sweep_s", round(duration, 1))
        ctx.metric("coverage_pct", round(cov * 100, 1))
        ctx.metric("qr_seen", len(real))
        ctx.metric("qr_decoded", sum(1 for c in real if c.text))
        ctx.metric("red_zones_mapped", len(grid.red_boxes()))
        ctx.metric("evasions", n_evade)
        ctx.metric("min_red_distance_m", None if not math.isfinite(nav.min_red_dist) or nav.min_red_dist >= 20.0 else round(nav.min_red_dist, 2))
        ctx.metric("max_height_error_m", round(flight.max_height_err, 2))
        ctx.metric("height_source", src)
        ctx.metric("frames_seen", observer.frames)
        if nav.truth.have:
            ctx.metric("sim_min_red_distance_m", round(nav.truth.min_red_m, 2))
            ctx.metric("sim_red_violations", nav.truth.violations)
        ctx.output("qr_candidates", zs.cands.to_list())
        ctx.output("red_map", {"zones": grid.red_boxes(), "margin_m": grid.margin})
        ctx.output("search", {"result": result, "coverage": round(cov, 3), "evasions": zs.evasions})
        full_sweep = result == "done"
        criteria = [
            Check(name="Search flown over the zone", ok=(result in ("done", "stopped")), detail=f"ended: {result}"),
            Check(name="A QR code was found", ok=bool(real), value=len(real), limit=1),
            Check(name="Target QR read at the search altitude", ok=(match is not None), blocking=False,
                  detail="decoded as the target" if match else "not read from 10 m: C3 inspects the located codes"),
            Check(name=f"Stayed out of every red zone (camera map, margin {grid.margin:.1f} m)", ok=(zs.red_entries == 0),
                  value=zs.red_entries, limit=0, detail=f"{len(grid.red_boxes())} zone(s) mapped"),
            Check(name=f"Evasion protocol finished within {nav.offset_budget_s:.0f} s", ok=(not late), blocking=(n_evade > 0),
                  value=n_evade, detail=("no red zone had to be evaded" if n_evade == 0 else
                                          "; ".join(f"{e['side']} {e['lateral_m']} m in {e['offset_s']} s" for e in zs.evasions))),
            Check(name=f"Zone coverage >= {cov_min * 100:.0f} % (full sweep)", ok=(cov >= cov_min or not full_sweep), blocking=full_sweep,
                  value=round(cov * 100, 1), limit=cov_min * 100, detail="" if full_sweep else "sweep ended early on the target: not required"),
            Check(name=f"Search altitude held (+-{alt_tol:.1f} m)", ok=(flight.max_height_err <= alt_tol + 0.3),
                  value=round(flight.max_height_err, 2), limit=alt_tol),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        if nav.truth.have:
            criteria.append(Check(name="(sim truth) Never over a red zone", ok=(nav.truth.violations == 0), blocking=False,
                                  value=nav.truth.violations, limit=0, detail=f"closest {nav.truth.min_red_m:.2f} m to a red zone"))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"C2 SUCCESS: {len(real)} QR code(s) found in {duration:.0f} s, {n_evade} evasion(s), coverage {cov * 100:.0f} %", Sev.GOOD)
        return success


# ───────────────────────────── C3: target QR verification ─────────────────────────────

class StageC3(Stage):
    id = "C3"
    title = "Target QR Verification"
    rulebook = "Stage C, C3: verify the QR code in the delivery zone against the start QR (Target Identification, 10 m)"
    summary = "Hover over the candidate, read it repeatedly (lowering for a closer look if needed), compare with the start QR, fix its position."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        g = _group(ctx)
        tol = float(getattr(g, "alt_tol_m", 0.5))
        zs = zone_state(ctx)
        checks = vehicle_checks(ctx, 5.0)
        checks.append(height_check(ctx, search_alt(ctx), tol + 1.0, "At the search altitude (C1/C2)"))
        checks += camera_checks(ctx)
        checks.append(target_check(ctx))
        n = len(zs.cands.real()) if zs is not None else 0
        checks.append(Check(name="QR candidates from the search (C2)", ok=(n > 0), value=n, limit=1,
                            detail=f"{n} QR code(s) seen" if zs is not None else "run C2 first"))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        g = _group(ctx)
        got = _need_state(ctx)
        target = Target.from_mission(ctx)
        if got is None or target is None:
            ctx.emit("Cannot run C3 without the search state and the start QR payload", Sev.ERROR)
            return False
        course, zs = got
        zs.cands.target = target
        votes_needed = int(getattr(cfg, "verify_votes", 5))
        verify_s = float(getattr(cfg, "verify_timeout_s", 8.0))
        inspect_alts = [float(a) for a in (getattr(cfg, "inspect_alts_m", None) or [])]
        tol = float(getattr(cfg, "centre_tol_m", 0.3))
        stable_s = float(getattr(cfg, "stable_s", 1.5))
        scatter_max = float(getattr(cfg, "scatter_max_m", 0.4))
        max_cands = int(getattr(cfg, "max_candidates", 4))
        timeout = float(getattr(cfg, "timeout_s", 240.0))
        h_search = search_alt(ctx)
        alt_tol = float(getattr(g, "alt_tol_m", 0.5))
        flight = _flight(ctx, course, h_search)
        observer = ZoneObserver(ctx, course, zs)
        nav = ZoneNavigator(ctx, course, zs, flight, observer)
        t0 = time.time()

        cands = [c for c in zs.cands.real() if zs.cands.status(c) != "decoy"]
        pos = flight.pos() or (0.0, 0.0)
        order = sorted(cands, key=lambda c: (zs.cands.status(c) != "match", dist(pos, c.pt)))
        ctx.emit(f"Verifying {len(order[:max_cands])} candidate QR code(s) against {target.raw!r}")
        verified: dict[str, Any] | None = None
        log_rows: list[dict[str, Any]] = []
        inspected_low = False
        for cand in order[:max_cands]:
            ctx.check_abort()
            if time.time() - t0 > timeout:
                break
            ctx.phase(f"Over candidate #{cand.id} at ({cand.fwd:.1f}, {cand.right:.1f})")
            nav.target_pt = cand.pt
            res = nav.go_to(cand.pt, timeout_s=max(30.0, timeout - (time.time() - t0)))
            if res not in ("done", "stopped"):
                log_rows.append({"id": cand.id, "result": f"could not reach it ({res})"})
                continue
            texts: dict[str, int] = {}
            pts: list[Pt] = []

            def tally(samples: list[tuple[Pt, str | None]]) -> int:
                for p, tx in samples:
                    if tx:
                        texts[tx] = texts.get(tx, 0) + 1
                        if target.matches(tx):
                            pts.append(p)
                return sum(n for tx, n in texts.items() if target.matches(tx))

            def enough(samples: list[tuple[Pt, str | None]]) -> bool:
                return sum(1 for _, tx in samples if target.matches(tx)) >= votes_needed

            r = nav.centre(cand.pt, tol, stable_s, verify_s + stable_s, mode="VERIFY", until=enough)
            votes = tally(r["samples"])
            low = False
            for alt in inspect_alts:                                    # not read yet: lower for a closer look
                if votes >= votes_needed or (texts and not any(target.matches(t) for t in texts) and sum(texts.values()) >= 3):
                    break
                low = inspected_low = True
                flight.h_target = alt
                ctx.emit(f"Not read from {flight.height() or h_search:.1f} m: lowering to {alt:.1f} m for a closer look")
                r = nav.centre(cand.pt, tol, stable_s, verify_s + 12.0, mode="INSPECT", until=enough)
                votes = tally(r["samples"])
            flight.h_target = h_search
            if low:                                                     # back up to the search altitude before going on
                tb = time.time()
                while time.time() - tb < 25.0 and abs(flight.height_error() or 0.0) > 0.4:
                    ctx.check_abort()
                    observer.poll()
                    nav.centre(cand.pt, tol, 0.2, 0.5, mode="CLIMB")
            read_texts = ", ".join(f"{tx!r} x{n}" for tx, n in texts.items()) or "nothing"
            row = {"id": cand.id, "fwd": round(cand.fwd, 2), "right": round(cand.right, 2), "read": read_texts, "votes": votes}
            if votes >= votes_needed and pts:
                mf = sum(p[0] for p in pts) / len(pts)
                mr = sum(p[1] for p in pts) / len(pts)
                scatter = math.sqrt(sum((p[0] - mf) ** 2 + (p[1] - mr) ** 2 for p in pts) / len(pts))
                verified = {"fwd": round(mf, 2), "right": round(mr, 2), "text": next(tx for tx in texts if target.matches(tx)),
                            "votes": votes, "scatter_m": round(scatter, 2), "candidate": cand.id, "inspected_low": low}
                row["result"] = "TARGET"
                log_rows.append(row)
                ctx.emit(f"Candidate #{cand.id} reads {verified['text']!r}: this is the delivery target", Sev.GOOD)
                break
            row["result"] = "decoy" if (texts and not any(target.matches(t) for t in texts)) else "unreadable"
            log_rows.append(row)
            ctx.emit(f"Candidate #{cand.id}: {row['result']} (read {read_texts})", Sev.INFO)

        flight.hold()
        ctx.sleep(0.8)
        h, src = ctx.height()
        st = ctx.state()
        nav.publish()
        ctx.metric("candidates_checked", len(log_rows))
        ctx.metric("verify_s", round(time.time() - t0, 1))
        ctx.metric("inspected_low", inspected_low)
        ctx.metric("height_m", None if h is None else round(h, 2))
        ctx.output("verification", log_rows)
        sim_err = None
        if verified is not None:
            nav.target_pt = (verified["fwd"], verified["right"])
            ctx.output("target_qr", verified)
            ctx.snapshot("down", "c3_target_verified")
            ctx.metric("target_fwd_m", verified["fwd"])
            ctx.metric("target_right_m", verified["right"])
            ctx.metric("target_votes", verified["votes"])
            ctx.metric("target_scatter_m", verified["scatter_m"])
            sim_err = nav.truth.qr_offset(verified["text"])
            safe = not zs.grid.blocked((verified["fwd"], verified["right"]))
            ctx.metric("delivery_point_clear_of_red", safe)
            if sim_err is not None:
                ctx.metric("sim_hover_error_to_target_m", round(sim_err, 2))
        else:
            safe = False
        criteria = [
            Check(name="Matching QR identified", ok=(verified is not None), detail="; ".join(f"#{r['id']} {r['result']}" for r in log_rows if 'result' in r) or "no candidate verified"),
            Check(name=f"Read {votes_needed}+ times as the start-QR target", ok=bool(verified and verified["votes"] >= votes_needed),
                  value=verified["votes"] if verified else 0, limit=votes_needed),
            Check(name=f"Position estimate tight (<= {scatter_max:.1f} m scatter)", ok=bool(verified and verified["scatter_m"] <= scatter_max),
                  value=verified["scatter_m"] if verified else None, limit=scatter_max),
            Check(name="Delivery point clear of every red keep-out", ok=safe, detail="the QR is within the red-zone safety margin" if (verified and not safe) else ""),
            Check(name=f"Back at the search altitude ({h_search:.0f} m)", ok=bool(h is not None and abs(h - h_search) <= alt_tol), value=None if h is None else round(h, 2), limit=h_search),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        if sim_err is not None:
            criteria.append(Check(name="(sim truth) Hovering within 1 m of the real QR", ok=(sim_err <= 1.0), blocking=False, value=round(sim_err, 2), limit=1.0))
        ctx.report.criteria = criteria
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"C3 SUCCESS: target QR {verified['text']!r} at ({verified['fwd']:.1f}, {verified['right']:.1f}), {verified['votes']} reads", Sev.GOOD)
        return success


# ───────────────────────────── C4: precision descent and payload release ─────────────────────────────

class StageC4(Stage):
    id = "C4"
    title = "Precision Descent & Payload Release"
    rulebook = "Stage C, C4: descend from 10 m to 5 m directly over the target QR, lower the payload on the winch and release it"
    summary = "Centre on the QR, descend to 5 m holding over it, lower the payload to the ground, release, wind the rope in."

    def preconditions(self, ctx: MissionContext) -> list[Check]:
        g = _group(ctx)
        tol = float(getattr(g, "alt_tol_m", 0.5))
        zs = zone_state(ctx)
        tq = ctx.mission.get("target_qr")
        w = Winch(getattr(ctx.full_cfg, "winch", {}) or {}, ctx.link)
        need = deliver_alt(ctx) + w.slack_m
        checks = vehicle_checks(ctx, 5.0)
        checks.append(height_check(ctx, search_alt(ctx), tol + 1.0, "At the search altitude (C3)"))
        checks += camera_checks(ctx)
        checks.append(Check(name="Target QR verified (C3)", ok=bool(tq), detail=f"at ({tq['fwd']}, {tq['right']})" if tq else "run C3 first"))
        safe = bool(tq and zs is not None and not zs.grid.blocked((float(tq["fwd"]), float(tq["right"]))))
        checks.append(Check(name="Delivery point clear of red zones", ok=safe,
                            detail="" if safe else ("inside a red keep-out (or outside the fence)" if tq else "no target")))
        checks.append(Check(name="Winch rope reaches the ground", ok=(w.rope_length_m >= need), value=w.rope_length_m, limit=round(need, 2),
                            detail=f"{w.backend} backend, channel {w.channel}"))
        checks.append(Check(name="Payload not delivered yet", ok=not ctx.mission.get("delivery"), blocking=False,
                            detail="already delivered in this session" if ctx.mission.get("delivery") else ""))
        return checks

    def run(self, ctx: MissionContext) -> bool:
        cfg = ctx.cfg
        g = _group(ctx)
        got = _need_state(ctx)
        tq = ctx.mission.get("target_qr")
        if got is None or not tq:
            ctx.emit("Cannot run C4 without the search state and a verified target QR", Sev.ERROR)
            return False
        course, zs = got
        descent = float(getattr(cfg, "descent_mps", 0.5))
        alt_tol = float(getattr(cfg, "alt_tol_m", 0.25))
        align_tol = float(getattr(cfg, "align_tol_m", 0.3))
        drop_tol = float(getattr(cfg, "drop_tol_m", 0.5))
        pause_err = float(getattr(cfg, "pause_err_m", 1.0))
        hold_s = float(getattr(cfg, "hold_s", 2.0))
        stable_xy = float(getattr(cfg, "stable_xy_m", 0.6))
        stable_z = float(getattr(cfg, "stable_z_m", 0.5))
        timeout = float(getattr(cfg, "timeout_s", 180.0))
        h_search, h_deliver = search_alt(ctx), deliver_alt(ctx)
        qpt: Pt = (float(tq["fwd"]), float(tq["right"]))
        flight = _flight(ctx, course, h_search)
        observer = ZoneObserver(ctx, course, zs)
        nav = ZoneNavigator(ctx, course, zs, flight, observer)
        nav.target_pt = qpt
        winch = Winch(getattr(ctx.full_cfg, "winch", {}) or {}, ctx.link)
        t0 = time.time()
        err_msg: str | None = None

        # 1) over the QR at the search altitude
        ctx.emit(f"Aligning over the target QR at ({qpt[0]:.1f}, {qpt[1]:.1f})")
        if dist(flight.pos() or qpt, qpt) > 1.0:
            nav.go_to(qpt, timeout_s=60.0)
        c = nav.centre(qpt, align_tol, 2.0, 25.0, mode="ALIGN")
        if not c["ok"]:
            err_msg = "Could not centre over the target QR"

        # 2) descend to the delivery altitude, staying over it
        max_err = 0.0
        paused_s = 0.0
        in_tol_since: float | None = None
        lost_since: float | None = None
        err_now: float | None = c["err_m"]
        h_cmd = flight.height() or h_search
        t_loop = time.time()
        while err_msg is None and time.time() - t0 < timeout:
            ctx.check_abort()
            observer.poll()
            pos = flight.pos()
            h = flight.height()
            if pos is None or h is None:
                time.sleep(LOOP_S)
                continue
            nav.monitor(pos)
            ours = [q for q in observer.fresh_live(0.6) if dist(q.pt, qpt) <= 1.6]
            if ours:
                q = min(ours, key=lambda x: math.hypot(*x.off))
                off, err_now, lost_since = q.off, math.hypot(*q.off), None
            else:
                off, err_now = (qpt[0] - pos[0], qpt[1] - pos[1]), None
                lost_since = lost_since or time.time()
            n = math.hypot(*off)
            v = min(0.4, 0.6 * n)
            now = time.time()
            dt, t_loop = now - t_loop, now
            if err_now is not None:
                max_err = max(max_err, err_now)
            # the target height ramps down, pausing while we are off the QR (or cannot see it for a while)
            off_qr = (err_now is not None and err_now > pause_err) or (lost_since is not None and now - lost_since > 3.0)
            if off_qr:
                paused_s += dt
            elif h_cmd > h_deliver:
                h_cmd = max(h_deliver, h_cmd - descent * dt)
            flight.h_target = max(h_cmd, h_deliver)
            flight.velocity(off[0] / n * v if n > 1e-6 else 0.0, off[1] / n * v if n > 1e-6 else 0.0, "DESCEND")
            ctx.phase(f"Descending over the QR: {h:.1f} m -> {h_deliver:.0f} m, off by {_fmt(err_now)}",
                      progress=min(0.6, max(0.0, (h_search - h) / max(0.1, h_search - h_deliver)) * 0.6))
            if lost_since is not None and now - lost_since > 12.0:
                err_msg = "Lost sight of the target QR for 12 s during the descent"
                break
            if abs(h - h_deliver) <= alt_tol and err_now is not None and err_now <= drop_tol:
                in_tol_since = in_tol_since or now
                if now - in_tol_since >= hold_s:
                    break
            else:
                in_tol_since = None
            time.sleep(LOOP_S)
        else:
            if err_msg is None:
                err_msg = f"Timed out after {timeout:.0f} s before reaching the delivery altitude"
        h_arrive = flight.height()
        ctx.snapshot("down", "c4_at_delivery_altitude")

        # 3) lower the payload, release it, wind the rope in -- holding over the QR the whole time
        lowered = released = retracted = False
        lower_s = 0.0
        xy_dev = z_dev = 0.0
        err_release: float | None = None
        sim_err: float | None = None
        if err_msg is None:
            depth = max(0.5, h_arrive if h_arrive is not None else h_deliver)
            ctx.emit(f"At {_fmt(h_arrive)}: lowering the payload ({depth + winch.slack_m:.1f} m of rope)")
            if not winch.start_lower(depth):
                err_msg = winch.error or "Winch refused to lower"
            t_w = time.time()
            wait_limit = (depth + winch.slack_m) / max(0.05, winch.lower_mps) * 1.5 + 8.0
            stage_phase = "lowering"
            while err_msg is None and time.time() - t0 < timeout + 60.0:
                ctx.check_abort()
                observer.poll()
                pos = flight.pos()
                h = flight.height()
                if pos is not None and h is not None:
                    nav.monitor(pos)
                    ours = [q for q in observer.fresh_live(0.6) if dist(q.pt, qpt) <= 1.6]
                    if ours:
                        q = min(ours, key=lambda x: math.hypot(*x.off))
                        off, err_now = q.off, math.hypot(*q.off)
                    else:
                        off, err_now = (qpt[0] - pos[0], qpt[1] - pos[1]), None
                    n = math.hypot(*off)
                    v = min(0.3, 0.5 * n)
                    flight.h_target = h_deliver
                    flight.velocity(off[0] / n * v if n > 1e-6 else 0.0, off[1] / n * v if n > 1e-6 else 0.0, "DELIVER")
                    if err_now is not None:
                        xy_dev = max(xy_dev, err_now)
                    z_dev = max(z_dev, abs(h - h_deliver))
                phase = winch.tick()
                if winch.phase == "fault":
                    err_msg = winch.error or "Winch fault"
                    break
                ctx.phase(f"Winch {phase}: rope {winch.rope_out_m:.1f} m", progress=0.6 + 0.4 * min(1.0, winch.rope_out_m / max(0.1, depth + winch.slack_m)))
                if phase == "down" and stage_phase == "lowering":
                    lowered, lower_s, stage_phase = True, time.time() - t_w, "down"
                    err_release = err_now if err_now is not None else (dist(pos, qpt) if pos else None)
                    sim_err = nav.truth.qr_offset(tq.get("text"))
                    ctx.emit(f"Payload on the ground after {lower_s:.1f} s, {_fmt(err_release)} from the QR centre", Sev.GOOD)
                if stage_phase == "down" and winch.phase == "down":
                    if winch.release():
                        ctx.emit("Releasing the payload")
                if winch.phase == "released" and stage_phase == "down":
                    released, stage_phase = True, "released"
                    ctx.snapshot("down", "c4_payload_released")
                    winch.start_raise()
                if winch.phase == "stowed" and stage_phase == "released":
                    retracted = True
                    break
                if time.time() - t_w > wait_limit + (winch.rope_length_m / max(0.05, winch.raise_mps) + 6.0):
                    err_msg = f"Winch did not finish (phase {winch.phase})"
                    break
                time.sleep(LOOP_S)
            if winch.phase not in ("stowed", "released"):
                winch.stop()
        flight.hold()
        h_end, src = ctx.height()
        st = ctx.state()
        nav.publish()
        if err_msg:
            ctx.emit(err_msg, Sev.ERROR)
        ctx.metric("descent_height_reached_m", None if h_arrive is None else round(h_arrive, 2))
        ctx.metric("max_error_during_descent_m", round(max_err, 2))
        ctx.metric("descent_paused_s", round(paused_s, 1))
        ctx.metric("lowering_s", round(lower_s, 1))
        ctx.metric("drop_error_m", None if err_release is None else round(err_release, 2))
        ctx.metric("max_xy_deviation_lowering_m", round(xy_dev, 2))
        ctx.metric("max_height_deviation_lowering_m", round(z_dev, 2))
        ctx.metric("winch_backend", winch.backend)
        ctx.metric("servo_commands", len(winch.commands))
        ctx.metric("servo_commands_refused", winch.acks_failed)
        ctx.metric("total_s", round(time.time() - t0, 1))
        if sim_err is not None:
            ctx.metric("sim_drop_error_m", round(sim_err, 2))
        ctx.output("delivery", {"released": released, "drop_error_m": None if err_release is None else round(err_release, 2),
                                "height_m": None if h_arrive is None else round(h_arrive, 2), "winch": winch.status()})
        criteria = [
            Check(name=f"Descended to the delivery altitude ({h_deliver:.0f} m)", ok=bool(h_arrive is not None and abs(h_arrive - h_deliver) <= alt_tol + 0.1),
                  value=None if h_arrive is None else round(h_arrive, 2), limit=h_deliver),
            Check(name=f"Directly over the QR at release (<= {drop_tol:.1f} m)", ok=bool(err_release is not None and err_release <= drop_tol),
                  value=None if err_release is None else round(err_release, 2), limit=drop_tol),
            Check(name="Payload lowered to the ground", ok=lowered, value=round(lower_s, 1), detail=f"{lower_s:.1f} s of winch"),
            Check(name="Payload released only after reaching the ground", ok=bool(released and lowered)),
            Check(name=f"Stable while lowering (<= {stable_xy:.1f} m sideways, {stable_z:.1f} m vertically)", ok=bool(lowered and xy_dev <= stable_xy and z_dev <= stable_z),
                  value=f"{xy_dev:.2f} / {z_dev:.2f}", limit=f"{stable_xy} / {stable_z}"),
            Check(name="Winch commands accepted by the flight controller", ok=(winch.acks_failed == 0),
                  value=len(winch.commands), detail=f"{winch.backend} backend" + (" (simulated: no hardware)" if winch.simulated else "")),
            Check(name="Rope wound back in", ok=retracted),
            Check(name="Never over a red zone", ok=(zs.red_entries == 0), value=zs.red_entries, limit=0),
            Check(name="Armed and still in GUIDED", ok=bool(st.armed and st.mode == "GUIDED")),
        ]
        if sim_err is not None:
            criteria.append(Check(name="(sim truth) Payload within 0.5 m of the real QR", ok=(sim_err <= 0.5), blocking=False, value=round(sim_err, 2), limit=0.5))
        ctx.report.criteria = criteria
        if err_msg:
            ctx.report.error = err_msg
        success = all(c.ok for c in criteria if c.blocking)
        if success:
            ctx.emit(f"C4 SUCCESS: payload delivered {_fmt(err_release)} from the QR centre at {_fmt(h_arrive)}; holding at {_fmt(h_end)}", Sev.GOOD)
        return success
