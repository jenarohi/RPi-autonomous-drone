"""
SkyScan - AeroTHON 2026 Mission 2 (autonomous) state machine.

Phase 1 (perception driven - no course coordinates are used):
 TAKEOFF            arm in GUIDED, climb to 5 m
 SCAN_START_QR      at 5 m: move ~1 m forward, find + decode the start QR ("TARGET:C"),
                    creeping forward, then a ring, then wider rings
 FIND_BANNER        at 5 m. Down camera already sees the corridor -> done. Otherwise
                    spin 360 with the front camera (every frame projected into a green
                    ground map); nothing -> search points on rings, spinning at each.
                    DECIDE on the strip that looks like the corridor, lock heading on
                    it, approach re-looking each leg, hand over when the DOWN camera
                    sees the corridor floor at the entrance
 ALIGN_FORWARD      down camera, 5 m, outside the entrance: lateral + heading + distance
 CORRIDOR_FORWARD   descend to 3 m, fly through on LiDAR: centre between the
                    walls, heading corrected from the wall lines, entry and exit
                    detected from the walls

Phase 2 (--full; still uses the delivery-zone geofence + return-corridor survey):
 SEARCH             climb to 10 m, lawnmower the delivery zone avoiding red zones
 DELIVER            centre over the target QR, descend to 5 m, lower + release
 TO_RETURN_CORRIDOR climb to 10 m, fly (around red zones) to the return corridor
 ALIGN_RETURN       align on the orange corridor floor
 CORRIDOR_RETURN    descend to 3 m, fly back through with obstacle avoidance
 HOME_LAND          fly to the take-off point and LAND

Every stage returns Result.SUCCESS / TIMEOUT / FAILED. A failed stage is
retried once; ALIGN / CORRIDOR failures then climb clear and go back to
FIND_BANNER (a green strip without walls is rejected first), up to
MAX_FALLBACKS times. Only then RTL (climbs to RTL_ALT, clear of the 5 m walls).
A pilot mode change or the 14 min limit aborts immediately.
"""
import math
import threading
import time
from enum import Enum
from typing import Callable, Optional

import cv2
import numpy as np

from . import config as C
from . import lidar, vision
from .geometry import (CorridorAxis, Rect, body_to_world, clamp, dist,
                       plan_path, push_out, segment_clear, wrap_pi)
from .groundmap import GroundMap, Strip
from .searchmap import HeatMap


class Result(Enum):
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"


class Abort(Exception):
    def __init__(self, reason: str, pilot: bool = False):
        super().__init__(reason)
        self.pilot = pilot


class Mission:
    def __init__(self, vehicle, sensors, log, view: bool = False):
        self.v, self.s, self.log = vehicle, sensors, log
        self.view = view
        self.cam = vision.DownCam()          # model of the small working copy (colour work)
        self.cam_full = vision.DownCam()     # model of the full frame (QR codes)
        self._last_full = None               # last full-resolution down frame
        self.search_heading = C.SEARCH_HEADING
        self.unread = []                     # world spots that looked like a QR but did not read
        self.heat: Optional[HeatMap] = None  # delivery search: where QR codes probably are
        self._transit_mark = None            # last spot where transit coverage was marked
        self.exit_xy = None                  # green corridor exit (start of the delivery search)
        self.exit_heading = None
        self.front = vision.FrontCam()
        self.stage = "INIT"
        self.target_id: Optional[str] = None
        self.target_xy = None
        self.qr_obs = {}                     # payload -> list of world points
        self.red_zones = [Rect(*r) for r in C.KNOWN_RED_ZONES]
        self.axes = {}                       # corridor name -> aligned CorridorAxis
        self.gmap: Optional[GroundMap] = None    # green floor seen so far (created at take-off)
        self.red_map: Optional[GroundMap] = None # red zone votes (created at take-off)
        self.start_ref = None                # start QR (or take-off) position: corridor entrance = nearer end
        self.corr_name = C.FORWARD_CORRIDOR_NAME   # corridor being searched for now (green, later orange)
        self.corr_colour = C.BANNER_COLOUR
        self.map_red_while_searching = False       # return search: keep mapping red zones
        self.rejected = []                   # entrances of green strips that turned out not to be the corridor
        self._frame_seq = {"down": 0, "front": 0}
        self._frame_t = {"down": 0.0, "front": 0.0}      # arrival time of the newest frame of each camera
        self._last_img = None                # last down-camera frame
        self._last_front = None              # last front-camera frame
        self._overlay = []                   # (u, v, text) drawn in the viewer
        self._map_shown = 0.0
        self._leg_goal = None
        self._search_deadline = 0.0
        self._return_map_started = False
        self.degraded = []                    # stages that failed but were skipped to still score the return
        self._speed = C.SPEED_TRANSIT
        self._guided = False
        self._t_flight = None
        self._tele_run = False

    # ══ plumbing ═══════════════════════════════════════════════════════════
    def st(self):
        return self.v.state()

    def check(self):
        if self._guided and self.v.mode != "GUIDED":
            raise Abort(f"flight mode changed to {self.v.mode} - pilot has control", pilot=True)
        if self._t_flight and time.monotonic() - self._t_flight > C.ABORT_AT:
            raise Abort("mission time limit reached")
        if self.st().age > 3 * C.TELEMETRY_MAX_AGE:
            raise Abort("telemetry lost")

    def sleep(self, dt: float):
        self.check()
        if self.view and self._last_img is not None:
            img = self._last_img.copy()
            k = img.shape[1] / self._last_full.shape[1]       # overlay is in full-frame pixels
            for u, v, text in self._overlay:
                cv2.circle(img, (int(u * k), int(v * k)), 8, (0, 0, 255), 2)
                cv2.putText(img, text, (int(u * k) + 10, int(v * k)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 0, 255), 1)
            cv2.putText(img, self.stage, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.imshow("SkyScan down camera", img)
        if self.view and self._last_front is not None:
            cv2.imshow("SkyScan front camera", self._last_front)
        if self.view and self.gmap is not None and time.monotonic() - self._map_shown > 1.0:
            self._map_shown = time.monotonic()
            if self.heat is not None:
                qrs = [tuple(np.median(np.array(v), axis=0)) for v in self.qr_obs.values()]
                cv2.imshow("SkyScan delivery heat map", self.heat.render((), self.st().xy, qrs))
            else:
                cv2.imshow("SkyScan green map", self.gmap.render(marks=[self.st().xy]))
        if self.view:
            cv2.waitKey(1)
        time.sleep(dt)

    def set_speed(self, mps: float):
        self._speed = mps
        self.v.set_speed(mps)

    def new_frame(self, which: str = "down"):
        """Latest frame of camera `which` if it has not been processed yet, else None."""
        img, t_frame, seq = self.s.frame(which)
        if img is None or seq == self._frame_seq[which]:
            return None
        self._frame_seq[which] = seq
        self._frame_t[which] = t_frame
        if which == "down":
            H, W = img.shape[:2]
            self.cam_full.resize(W, H)
            self._last_full = img
            if W > C.DOWN_WORK_WIDTH:
                img = cv2.resize(img, (C.DOWN_WORK_WIDTH, int(round(H * C.DOWN_WORK_WIDTH / W))),
                                 interpolation=cv2.INTER_AREA)
            self.cam.resize(img.shape[1], img.shape[0])
            self._last_img = img
        else:
            self.front.resize(img.shape[1], img.shape[0])
            self._last_front = img
        return img

    def frame_state(self, which: str = "down"):
        """Drone pose at the EXPOSURE time of the newest frame of camera `which`: arrival time minus the
        camera latency, looked up in the telemetry history. Pair every image measurement with this, not
        with the latest pose - while the drone moves or tilts they differ."""
        t = self._frame_t[which]
        return self.v.state_at(t - C.CAM_LATENCY_S) if t > 0 else self.st()

    def cam_height(self, st) -> float:
        return max(0.3, st.alt + C.CAM_HEIGHT_OFFSET)

    def front_height(self, st) -> float:
        return max(0.3, st.alt + C.FRONT_CAM_HEIGHT_OFFSET)

    def pixel_to_world(self, st, u: float, v: float):
        """FULL-frame down-camera pixel (QR hits) -> world point."""
        fwd, right = self.cam_full.pixel_to_ground(u, v, self.cam_height(st), st.roll, st.pitch)
        return body_to_world(st.x, st.y, st.heading, fwd, right)

    def no_fly(self):
        return [z.inflate(C.RED_MARGIN) for z in self.red_zones]

    def _telemetry_loop(self):
        while self._tele_run:
            try:
                self.log.telemetry(self.stage, self.st())
            except Exception:
                pass
            time.sleep(0.2)

    # ══ movement ═══════════════════════════════════════════════════════════
    def fly_to(self, x: float, y: float, alt: float, heading: float, tol: float = 0.5,
               stop: bool = True, timeout: Optional[float] = None,
               on_tick: Optional[Callable] = None) -> str:
        """ArduPilot position control to a WORLD point. Returns 'arrived', 'timeout'
        or whatever on_tick(state) returned (e.g. 'found', 'replan')."""
        gx = C.GEOFENCE
        if not (gx[0] <= x <= gx[1] and gx[2] <= y <= gx[3]):
            raise Abort(f"target ({x:.1f}, {y:.1f}) is outside the geofence")
        st = self.st()
        d3 = math.hypot(dist(st.xy, (x, y)), alt - st.alt)
        t_end = time.monotonic() + (timeout or 15.0 + 3.0 * d3 / max(self._speed, 0.5))
        last_send = 0.0
        while time.monotonic() < t_end:
            if time.monotonic() - last_send > 0.5:
                self.v.goto(x, y, alt, heading)
                last_send = time.monotonic()
            st = self.st()
            close = dist(st.xy, (x, y)) < tol and abs(st.alt - alt) < 0.35
            if close and (not stop or (math.hypot(st.vx, st.vy) < 0.4 and
                                       abs(wrap_pi(st.heading - heading)) < math.radians(8))):
                return "arrived"
            if on_tick:
                r = on_tick(st)
                if r:
                    return r
            self.sleep(0.1)
        return "timeout"

    def hold(self, seconds: float, heading: float, on_tick: Optional[Callable] = None) -> Optional[str]:
        st = self.st()
        t_end = time.monotonic() + seconds
        while time.monotonic() < t_end:
            self.v.goto(st.x, st.y, st.alt, heading)
            if on_tick:
                r = on_tick(self.st())
                if r:
                    return r
            self.sleep(0.1)
        return None

    def travel(self, goal, alt: float, heading: float, on_tick=None, tol: float = 1.0) -> str:
        """Fly to goal at `alt`, routing around (inflated) red zones and
        re-planning whenever on_tick reports a newly seen zone ('replan')."""
        for _ in range(12):
            zones = self.no_fly()
            start = self.st().xy
            if any(z.contains(start) for z in zones):
                esc = push_out(start, zones)
                self.log("NAV", f"inside a red-zone margin - stepping out to ({esc[0]:.1f}, {esc[1]:.1f})")
                self.fly_to(*esc, alt, heading, tol=0.5, stop=False)
                start = esc
            path = plan_path(start, push_out(goal, zones), zones)
            if path is None:
                self.log("NAV", f"no path to ({goal[0]:.1f}, {goal[1]:.1f})")
                return "unreachable"
            if len(path) > 1:
                self.log("NAV", "detour " + " -> ".join(f"({p[0]:.1f},{p[1]:.1f})" for p in path))
            result = "arrived"
            for i, p in enumerate(path):
                self._leg_goal = p
                last = i == len(path) - 1
                result = self.fly_to(*p, alt, heading, tol=tol if last else 1.0, stop=last, on_tick=on_tick)
                if result != "arrived":
                    break
            self._leg_goal = None
            if result == "arrived":
                # the red-zone map may have grown while we flew (a zone only partly seen when
                # this goal was chosen): never stay inside a zone + margin
                here = self.st().xy
                zones = self.no_fly()
                if any(z.contains(here) for z in zones):
                    esc = push_out(here, zones)
                    self.log("NAV", f"arrived inside a red-zone margin (zone grew) - moving out to "
                                    f"({esc[0]:.1f}, {esc[1]:.1f})")
                    self.fly_to(*esc, alt, heading, tol=0.5)
            if result != "replan":
                return result
        return "timeout"

    # ══ perception helpers ═════════════════════════════════════════════════
    def record_qr(self, data: str, p, pose=None) -> bool:
        """Store a delivery-zone QR sighting. True when the target just got confirmed."""
        cur = self.st()
        tilt = math.degrees(max(abs(pose.roll), abs(pose.pitch))) if pose else math.degrees(max(abs(cur.roll), abs(cur.pitch)))
        self.log("QRFIX", f"{data} {p[0]:.2f} {p[1]:.2f} spd={math.hypot(cur.vx, cur.vy):.2f} tilt={tilt:.1f}")
        obs = self.qr_obs.setdefault(data, [])
        obs.append(p)
        if len(obs) == 1:
            tag = "TARGET" if self.target_id and vision.same_id(data, self.target_id) else "other"
            self.log("QR", f"'{data}' seen at ({p[0]:.1f}, {p[1]:.1f})  [{tag}]")
            self.log.snapshot(f"qr_{data}", self._last_img)
            if self.heat is not None:
                self.heat.qr_found(p)                # the other codes of the field are near it
        if self.target_id and vision.same_id(data, self.target_id) and len(obs) >= C.QR_CONFIRMATIONS:
            pts = np.array(obs[-10:])
            self.target_xy = tuple(np.median(pts, axis=0))
            return True
        return False

    def _map_red(self, st, img) -> bool:
        """Red pixels of a (small) down frame -> red vote map -> red zone rectangles.
        Only steady views vote: drone near level, and only ground within RED_VIEW_ANGLE
        of straight down (small attitude/timing errors stay small there). A cell is red
        after RED_MAP_VOTES frames, so one bad frame cannot grow a zone.
        True if a zone appeared or grew."""
        if self.red_map is None or max(abs(st.roll), abs(st.pitch)) > C.RED_MAX_TILT:
            return False
        h = self.cam_height(st)
        g = vision.colour_ground_samples(img, "red", self.cam, h, st.roll, st.pitch,
                                         h * math.tan(C.RED_VIEW_ANGLE), step=3)
        c, s = math.cos(st.heading), math.sin(st.heading)
        self.red_map.add(np.column_stack([st.x + g[:, 0] * c + g[:, 1] * s,
                                          st.y + g[:, 0] * s - g[:, 1] * c]) if len(g) else g)
        zones = [Rect(*b) for b in self.red_map.boxes(C.RED_MAP_VOTES, C.RED_MIN_AREA)]
        zones += [Rect(*r) for r in C.KNOWN_RED_ZONES]
        changed = False
        for z in zones:
            old = [o for o in self.red_zones if o.overlaps(z, gap=0.5)]
            if not old:
                self.log("RED", f"NEW red zone at x {z.xmin:.1f}..{z.xmax:.1f}, y {z.ymin:.1f}..{z.ymax:.1f}")
                self.log.snapshot("red_zone", self._last_img)
                changed = True
            elif any((z.xmax - z.xmin) + (z.ymax - z.ymin) > (o.xmax - o.xmin) + (o.ymax - o.ymin) + 0.5
                     for o in old):
                self.log("RED", f"red zone now x {z.xmin:.1f}..{z.xmax:.1f}, y {z.ymin:.1f}..{z.ymax:.1f}")
                changed = True
        self.red_zones = zones
        return changed

    def _scan_tick(self, st) -> Optional[str]:
        """Per-frame work while flying over the delivery zone."""
        img = self.new_frame()
        if img is None:
            return None
        result = None
        sf = self.frame_state("down")
        if self._map_red(sf, img) and self._leg_goal and not segment_clear(st.xy, self._leg_goal, self.no_fly()):
            result = "replan"
        if (self.heat is not None and st.alt > C.ALT_SEARCH - 1.5
                and max(abs(st.roll), abs(st.pitch)) < math.radians(8)
                and (self._transit_mark is None or dist(st.xy, self._transit_mark) >= C.SEARCH_TRANSIT_STEP)):
            self._transit_mark = st.xy               # this strip was looked at on the way
            along, across = self.cam_full.footprint(self.cam_height(st))
            self.heat.seen(st.xy, st.heading, along, across, C.SEARCH_TRANSIT_FACTOR)
        self._overlay = []
        had_target = self.target_xy is not None
        for hit in vision.decode_qrs(self._last_full):
            self._overlay.append((hit.u, hit.v, hit.data))
            if vision.parse_start_qr(hit.data) is None:
                if self.record_qr(hit.data, self.pixel_to_world(sf, hit.u, hit.v), sf) and not had_target:
                    result = "found"
        return result

    def settle(self, heading: float, timeout: float = 4.0):
        """Hold position until yaw is on `heading` and the drone is still and level."""
        st0 = self.st()
        t_end = time.monotonic() + timeout
        while time.monotonic() < t_end:
            self.v.goto(st0.x, st0.y, st0.alt, heading)
            st = self.st()
            if (abs(wrap_pi(st.heading - heading)) < math.radians(1.5) and math.hypot(st.vx, st.vy) < 0.15
                    and abs(st.roll) < math.radians(1.5) and abs(st.pitch) < math.radians(1.5)):
                return
            self.sleep(0.1)

    def measure_floor(self, prior: CorridorAxis, frames: int = 5, timeout: float = 3.0):
        """Corridor axis seen by the camera, in WORLD coordinates. Every frame is
        converted with the pose at that moment, then the median is taken.
        If the near end of the floor (the entrance edge) is in the image, the entry is
        also moved along the axis to where it really is.
        Returns (CorridorAxis, floor width m, image) or None."""
        got, img_used = [], None
        t_end = time.monotonic() + timeout
        while len(got) < frames and time.monotonic() < t_end:
            img = self.new_frame()
            st = self.frame_state("down") if img is not None else self.st()
            if img is not None:
                H = img.shape[0]
                fa = vision.floor_axis(img, prior.colour)
                if fa is not None and fa.v_hi - fa.v_lo >= C.ALIGN_MIN_FLOOR_ROWS * H:
                    h = self.cam_height(st)
                    lat, ang, width = vision.floor_measurement(fa, self.cam, h, st.roll, st.pitch)
                    if 0.6 * C.CORRIDOR_WIDTH < width < 1.5 * C.CORRIDOR_WIDTH:
                        seen = prior.realigned(body_to_world(st.x, st.y, st.heading, 0.0, lat),
                                               wrap_pi(st.heading - ang))
                        s_edge = math.nan
                        if fa.v_hi < H - 6:                  # entrance edge visible
                            g = self.cam.pixel_to_ground(fa.u_centre + fa.slope * (fa.v_hi - self.cam.cy),
                                                         fa.v_hi, h, st.roll, st.pitch)
                            if g is not None:
                                s_edge = seen.to_sd(*body_to_world(st.x, st.y, st.heading, *g))[0]
                        got.append((seen.entry[0], seen.entry[1],
                                    wrap_pi(seen.heading - prior.heading), width, s_edge))
                        img_used = img
            self.sleep(0.05)
        if len(got) < 3:
            return None
        G = np.array(got)
        ex, ey, dh, width = np.median(G[:, :4], axis=0)
        axis = prior.realigned((ex, ey), prior.heading + dh)
        edges = G[:, 4][~np.isnan(G[:, 4])]
        if len(edges) >= 2 and abs(np.median(edges)) < C.ALIGN_MAX_CORRECTION:
            s = float(np.median(edges))
            t = axis.t
            axis = CorridorAxis(axis.name, (axis.entry[0] + s * t[0], axis.entry[1] + s * t[1]),
                                (axis.exit[0] + s * t[0], axis.exit[1] + s * t[1]), axis.colour)
            axis.edge_shift = s
        return axis, float(width), img_used

    def edge_ok(self, e) -> bool:
        w = C.CORRIDOR_WIDTH - 0.2                       # floor between the 0.2 m walls
        return e is not None and 0.8 * w < e.width < 1.2 * w

    def measure_entrance(self, prior: CorridorAxis, frames: int = 5, timeout: float = 3.0):
        """Entrance seen by the DOWN camera from outside (vision.entrance_edge), as a WORLD
        axis through the entrance centre. Median over a few frames, each converted with the
        pose at that moment. Returns (CorridorAxis, edge width m, image) or None."""
        got, img_used = [], None
        t_end = time.monotonic() + timeout
        while len(got) < frames and time.monotonic() < t_end:
            img = self.new_frame()
            st = self.frame_state("down") if img is not None else self.st()
            if img is not None:
                e = vision.entrance_edge(img, prior.colour, self.cam, self.cam_height(st), st.roll, st.pitch)
                if self.edge_ok(e):
                    p = body_to_world(st.x, st.y, st.heading, e.fwd, e.right)
                    got.append((p[0], p[1], wrap_pi(st.heading - e.angle - prior.heading), e.width))
                    img_used = vision.draw_entrance(img, e)
            self.sleep(0.05)
        if len(got) < 3:
            return None
        ex, ey, dh, width = np.median(np.array(got), axis=0)
        h = prior.heading + dh
        far = (ex + prior.length * math.cos(h), ey + prior.length * math.sin(h))
        return CorridorAxis(prior.name, (ex, ey), far, prior.colour), float(width), img_used

    def green_below(self) -> bool:
        """Latest down frame: is there corridor colour in the half of the image behind the
        camera centre (i.e. under / behind the drone)?"""
        img = self._last_img
        if img is None:
            return False
        mask = vision.colour_mask(img[img.shape[0] // 2:], self.corr_colour)
        return (mask > 0).mean() > 0.05

    # ── green corridor: ground map built from every look ──────────────────
    def feed_map(self, st, which: str = "front", heading: Optional[float] = None) -> bool:
        """Vote the newest frame of camera `which` into the green ground map. Skipped
        while the drone is still yawing towards `heading` (pose would not match)."""
        if self.gmap is None:
            return False
        img = self.new_frame(which)
        if img is None:
            return False
        st = self.frame_state(which)                 # pose when this frame was exposed
        if heading is not None and abs(wrap_pi(st.heading - heading)) > math.radians(3.0):
            return False
        cam, h = (self.front, self.front_height(st)) if which == "front" else (self.cam, self.cam_height(st))
        g = vision.colour_ground_samples(img, self.corr_colour, cam, h, st.roll, st.pitch,
                                         min(C.BANNER_MAX_RANGE, C.BANNER_RANGE_PER_M * h))
        c, s = math.cos(st.heading), math.sin(st.heading)
        self.gmap.add(np.column_stack([st.x + g[:, 0] * c + g[:, 1] * s,
                                       st.y + g[:, 0] * s - g[:, 1] * c]) if len(g) else g)
        return True

    def look(self, heading: float, frames: int = C.BANNER_LOOK_FRAMES):
        """Turn to `heading`, hold still, vote a few front frames (+ one down frame) into the map."""
        self.settle(heading)
        n, t_end = 0, time.monotonic() + 3.0
        while n < frames and time.monotonic() < t_end:
            if self.feed_map(self.st(), "front", heading):
                n += 1
            self.sleep(0.05)
        self.feed_map(self.st(), "down", heading)

    def corridor_strips(self, log: bool = False):
        """Corridor candidates in the map (nearest to the drone first) + partly seen blobs."""
        strips, partial, notes = self.gmap.strips(C.CORRIDOR_WIDTH, C.BANNER_MIN_LENGTH, self.start_ref,
                                                  C.BANNER_MAP_VOTES, self.rejected,
                                                  narrow_partial=self.map_red_while_searching)
        if log:
            for note in notes[:6]:
                self.log("MAP", note)
        here = self.st().xy
        strips.sort(key=lambda s: dist(s.entry, here))
        return strips, partial

    def map_snapshot(self, name: str, strips=(), marks=()):
        self.log.snapshot(name, self.gmap.render(strips, list(marks) + [self.st().xy]))

    def spin360(self):
        """Full 360 deg turn on the spot at the current altitude, the front camera voting
        every heading into the green map."""
        h0 = self.st().heading
        n = int(round(2 * math.pi / C.BANNER_YAW_STEP))
        self.log("BANNER", f"spinning 360 deg ({n} looks) to find the green corridor")
        for k in range(n):
            self.look(wrap_pi(h0 + k * C.BANNER_YAW_STEP))
        self.look(h0, frames=1)                    # back to where we started

    def blocked_ahead(self) -> bool:
        """LiDAR: anything within BANNER_BLOCKED_DIST in front (+-35 deg)?"""
        pts, t_scan, _ = self.s.scan()
        if pts is None or len(pts) == 0 or time.monotonic() - t_scan > 1.0:
            return False
        ang = np.arctan2(pts[:, 1], pts[:, 0])
        rng = np.hypot(pts[:, 0], pts[:, 1])
        return bool(np.any((np.abs(ang) < math.radians(35)) & (rng < C.BANNER_BLOCKED_DIST)))

    def _search_tick(self, st, hdg: float) -> Optional[str]:
        self.feed_map(st, "front", hdg)
        if self.map_red_while_searching:
            img = self.new_frame()
            if (img is not None and self._map_red(st, img) and self._leg_goal
                    and not segment_clear(st.xy, self._leg_goal, self.no_fly())):
                return "replan"
        if self.blocked_ahead():
            self.v.velocity(0, 0, 0, hdg)
            self.log("BANNER", "something close ahead on the LiDAR - stopping this leg")
            return "blocked"
        return None

    def inside_fence(self, p, margin: float = 2.0) -> bool:
        g = C.GEOFENCE
        return g[0] + margin <= p[0] <= g[1] - margin and g[2] + margin <= p[1] <= g[3] - margin

    def go_and_spin(self, p):
        """Fly to `p` at 5 m facing the direction of travel (front camera feeding the map), then spin."""
        st = self.st()
        hdg = math.atan2(p[1] - st.y, p[0] - st.x)
        self.settle(hdg)
        self.travel(p, C.ALT_ALIGN, hdg, on_tick=lambda s: self._search_tick(s, hdg), tol=1.0)
        self.spin360()

    def investigate(self, p):
        """A green blob that could be part of the corridor: get closer, facing it, and look."""
        st = self.st()
        hdg = math.atan2(p[1] - st.y, p[0] - st.x)
        d = dist(st.xy, p)
        self.log("BANNER", f"green blob at ({p[0]:.1f}, {p[1]:.1f}), {d:.0f} m away, only partly seen "
                           f"- going closer to look")
        if d > C.BANNER_INVESTIGATE_DIST:
            k = (d - C.BANNER_INVESTIGATE_DIST) / d
            goal = (st.x + k * (p[0] - st.x), st.y + k * (p[1] - st.y))
            if self.inside_fence(goal):
                self.settle(hdg)
                self.travel(goal, C.ALT_ALIGN, hdg, on_tick=lambda s: self._search_tick(s, hdg), tol=1.0)
        for off in (0.0, 45.0, -45.0):
            self.look(wrap_pi(hdg + math.radians(off)))
        if not self.map_red_while_searching:
            return
        # Tall walls hide the floor when seen from the side: go round the blob in 45 deg steps
        # (a straight jump to the far side would cut through the walls) and look at it from
        # every side; along the corridor axis the floor is visible through the opening.
        st = self.st()
        b0 = math.atan2(st.y - p[1], st.x - p[0])
        for k in range(1, 8):
            if self.corridor_strips()[0] or time.monotonic() > self._search_deadline:
                return
            b = b0 + k * math.pi / 4
            q = (p[0] + C.RETURN_ORBIT_R * math.cos(b), p[1] + C.RETURN_ORBIT_R * math.sin(b))
            if not self.inside_fence(q):
                continue
            face = math.atan2(p[1] - q[1], p[0] - q[0])
            self.log("BANNER", f"circling the blob: looking from ({q[0]:.1f}, {q[1]:.1f})")
            self.travel(q, C.ALT_ALIGN, face, on_tick=lambda s: self._search_tick(s, face), tol=1.0)
            self.look(face)

    def go_and_look(self, p, face):
        """Fly to p at 5 m facing `face` (front camera feeding the map on the way), then look
        straight ahead and 25 deg to each side."""
        self.travel(p, C.ALT_ALIGN, face, on_tick=lambda s: self._search_tick(s, face), tol=1.0)
        for off in (0.0, 25.0, -25.0):
            self.look(wrap_pi(face + math.radians(off)))

    def return_search_plan(self):
        """Search for the return corridor using the course layout (rulebook Fig. 3): it lies beside
        the forward corridor, parallel to it, with its entrance on the delivery-zone side, roughly
        level with the forward corridor's exit. Looking back at the corridor mouths from the
        delivery-zone side, along their axis, shows the floor through the opening (tall walls hide
        it from the side). Stops nearest first, far lateral ones last; the generic search follows
        if none of them finds the corridor. Yields (description, action)."""
        if self.exit_xy is None or self.exit_heading is None:
            yield from self.search_plan(C.HOME_XY)
            return
        h = self.exit_heading
        t, n = (math.cos(h), math.sin(h)), (-math.sin(h), math.cos(h))
        face = wrap_pi(h + math.pi)
        here = self.st().xy
        stops = []
        for d in C.RETURN_STAGE_LATERAL:
            p = (self.exit_xy[0] + C.RETURN_STAGE_AHEAD * t[0] + d * n[0],
                 self.exit_xy[1] + C.RETURN_STAGE_AHEAD * t[1] + d * n[1])
            if self.inside_fence(p):
                stops.append((d, p))
        near = sorted([x for x in stops if abs(x[0]) <= 10.0], key=lambda x: dist(x[1], here))
        far = sorted([x for x in stops if abs(x[0]) > 10.0], key=lambda x: dist(x[1], here))
        for d, p in near + far:
            yield (f"looking back at the corridor mouths from {C.RETURN_STAGE_AHEAD:.0f} m beyond the "
                   f"forward exit, {d:+.0f} m to the side", lambda p=p: self.go_and_look(p, face))
        yield from self.search_plan(C.HOME_XY)

    def search_plan(self, toward=None):
        """Escalating search from where we are now, always at 5 m: spin 360 here ->
        move out on rings, spinning 360 at each point. Yields (description, action)."""
        st = self.st()
        o, h0 = st.xy, st.heading
        yield "spin 360 here", self.spin360
        if toward is not None:                       # the corridor lies somewhere on the way home
            d = dist(o, toward)
            b = math.atan2(toward[1] - o[1], toward[0] - o[0])
            k = 1
            while k * C.RETURN_SEARCH_STEP < d - 6.0:
                p = (o[0] + k * C.RETURN_SEARCH_STEP * math.cos(b), o[1] + k * C.RETURN_SEARCH_STEP * math.sin(b))
                if self.inside_fence(p):
                    yield (f"moving {k * C.RETURN_SEARCH_STEP:.0f} m towards home to look again",
                           lambda p=p: self.go_and_spin(p))
                k += 1
        n = C.BANNER_SEARCH_BEARINGS
        order = [0] + [k for i in range(1, n // 2 + 1) for k in (i, -i)][:n - 1]
        for r in C.BANNER_SEARCH_RINGS:
            for k in order:
                b = h0 + k * 2 * math.pi / n
                p = (o[0] + r * math.cos(b), o[1] + r * math.sin(b))
                if self.inside_fence(p):
                    yield (f"moving to search point {r:.0f} m out at bearing {math.degrees(wrap_pi(b)):.0f} deg",
                           lambda p=p: self.go_and_spin(p))

    # ══ stages ═════════════════════════════════════════════════════════════
    def takeoff(self) -> Result:
        st = self.st()
        if st.armed or st.alt > 0.5:
            self.log("TAKEOFF", "vehicle must start disarmed on the ground")
            return Result.FAILED
        if not self.v.set_mode("GUIDED"):
            return Result.FAILED
        self.log("TAKEOFF", "GUIDED - arming (waits for pre-arm checks)")
        if not self.v.arm(90.0):
            self.log("TAKEOFF", "arming failed")
            return Result.FAILED
        self.v.capture_home()          # after arming: pre-arm checks guarantee a settled EKF/GPS
        self.gmap = GroundMap(self.st().xy)
        self.red_map = GroundMap(self.st().xy, half_size=90.0, res=0.25)
        self.start_ref = self.st().xy
        if self.v.mode != "GUIDED" and not self.v.set_mode("GUIDED"):   # can drop out before GPS is ready
            self.log("TAKEOFF", f"could not get GUIDED after arming (mode {self.v.mode})")
            return Result.FAILED
        self._guided = True
        self._t_flight = time.monotonic()
        self.v.takeoff(C.ALT_QR)
        t_end = time.monotonic() + 30.0
        while time.monotonic() < t_end:
            if self.st().alt >= C.ALT_QR - 0.3:
                self.log("TAKEOFF", f"at {self.st().alt:.1f} m")
                return Result.SUCCESS
            self.sleep(0.2)
        return Result.TIMEOUT

    def scan_start_qr(self) -> Result:
        """Rulebook: at 5 m move forward ~1 m and read the start QR. If it is not under
        the camera yet, keep creeping forward, then search a ring around that spot.
        Everything is relative to where we took off."""
        st = self.st()
        hdg = st.heading
        self.set_speed(C.SPEED_SCAN)
        ahead = [body_to_world(st.x, st.y, hdg, d, 0.0)
                 for d in np.arange(C.START_QR_FORWARD_STEP, C.START_QR_MAX_FORWARD + 0.01, 1.0)]
        q = body_to_world(st.x, st.y, hdg, C.START_QR_RING_CENTRE, 0.0)
        ring = [(q[0] + C.START_QR_RING * math.cos(hdg + a), q[1] + C.START_QR_RING * math.sin(hdg + a))
                for a in np.radians(np.arange(180, -180, -45))]
        high = [(q[0] + r * math.cos(hdg + a), q[1] + r * math.sin(hdg + a))
                for r in C.START_QR_SPIRAL for a in np.radians(np.arange(0, 360, 45))]
        path = ahead + ring + high
        votes = {}

        def tick(s):
            self.feed_map(s, "front", hdg)       # free look at the course while we scan
            img = self.new_frame()
            if img is None:
                return None
            self._overlay = []
            for hit in vision.decode_qrs(self._last_full):
                self._overlay.append((hit.u, hit.v, hit.data))
                tgt = vision.parse_start_qr(hit.data)
                if tgt is None:
                    continue
                votes[tgt] = votes.get(tgt, 0) + 1
                if votes[tgt] >= C.QR_CONFIRMATIONS:
                    self.target_id = tgt
                    p = self.pixel_to_world(self.frame_state("down"), hit.u, hit.v)
                    self.start_ref = p
                    self.log("QR", f"START QR '{hit.data}' at ({p[0]:.1f}, {p[1]:.1f}) -> deliver to '{tgt}'")
                    self.log.snapshot("start_qr", img)
                    return "found"
            return None

        for i, p in enumerate(path):
            if i == len(ahead):
                self.log("QR", "not under the camera ahead - searching a ring")
            if i == len(ahead) + len(ring):
                self.log("QR", "still not found - searching wider rings")
            if self.fly_to(*p, C.ALT_QR, hdg, tol=0.3, on_tick=tick) == "found":
                return Result.SUCCESS
            if self.hold(1.0, hdg, on_tick=tick) == "found":
                return Result.SUCCESS
        self.log("QR", f"start QR not decoded (votes {votes})")
        return Result.FAILED

    def down_cam_corridor(self) -> Optional[CorridorAxis]:
        """Does the DOWN camera already show the corridor floor with its entrance edge
        ahead of us? Then no search is needed. None otherwise."""
        st = self.st()
        guess = CorridorAxis(self.corr_name, st.xy, body_to_world(st.x, st.y, st.heading, 10.0, 0.0),
                             self.corr_colour)
        m = self.measure_entrance(guess)
        if m is None:
            return None
        axis = m[0]
        t = axis.t
        if (axis.entry[0] - self.start_ref[0]) * t[0] + (axis.entry[1] - self.start_ref[1]) * t[1] < -1.0:
            return None                      # we would be flying back towards the start: not the entrance
        return axis

    def find_banner(self, toward=None, timeout: Optional[float] = None, planner=None) -> Result:
        """Find the green corridor and get to its entrance at 5 m, deciding from what is seen:
          down cam: already shows the corridor + entrance edge -> straight to ALIGN
          search  : spin 360 with the front camera -> if nothing, search points on rings,
                    spinning at each; green blobs only partly seen are investigated closer
          decide  : the map strip ~CORRIDOR_WIDTH wide, long enough, mostly filled,
                    not rejected before; its end nearer the start is the entrance.
                    Heading locked towards it.
          approach: legs towards the entrance, re-looking after each leg; the candidate
                    is updated, or dropped (back to searching) if it stops looking right
          handover: the DOWN camera sees the corridor floor near the entrance -> ALIGN
        Loops until the stage timeout."""
        deadline = time.monotonic() + (timeout or C.BANNER_SEARCH_TIMEOUT)
        self._search_deadline = deadline
        self.set_speed(C.SPEED_TRANSIT)
        self.settle(self.st().heading)
        axis = self.down_cam_corridor()
        if axis is not None:
            self.log("BANNER", f"DOWN camera already sees the green corridor (heading "
                               f"{math.degrees(axis.heading):.1f} deg) - no spin needed")
            self.axes[axis.name] = axis
            return Result.SUCCESS
        self.log("BANNER", "down camera does not see the green corridor")
        make_plan = planner or (lambda: self.search_plan(toward))
        plan = make_plan()
        visited = []
        while time.monotonic() < deadline:
            strips, partial = self.corridor_strips(log=True)
            if strips:
                strip = strips[0]
                st = self.st()
                bearing = math.atan2(strip.entry[1] - st.y, strip.entry[0] - st.x)
                self.log("BANNER", f"DECIDED: {strip.describe()} -> heading LOCKED at "
                                   f"{math.degrees(bearing):.0f} deg towards the entrance")
                self.map_snapshot("green_map_decided", strips)
                r = self.approach(strip, deadline)
                if r == "ready":
                    return Result.SUCCESS
                if r == "timeout":
                    break
                self.log("BANNER", "candidate lost on the way in - searching again from here")
                self.map_snapshot("green_map_lost")
                plan = make_plan()
                continue
            todo = [p for p in partial if all(dist(p, v) > 3.0 for v in visited)]
            if todo:
                p = min(todo, key=lambda q: dist(q, self.st().xy))
                visited.append(p)
                self.investigate(p)
                continue
            step = next(plan, None)
            if step is None:
                self.log("BANNER", "search pattern finished - no green corridor found")
                self.map_snapshot("green_map_failed")
                return Result.FAILED
            desc, action = step
            self.log("BANNER", f"no corridor in the map yet ({self.gmap.frames} frames) - {desc}")
            action()
        self.map_snapshot("green_map_timeout")
        return Result.TIMEOUT

    def approach(self, strip: Strip, deadline: float) -> str:
        """Fly towards the entrance of `strip` in legs. Returns 'ready' (down camera has the
        corridor, or we are at the entrance), 'lost' or 'timeout'."""
        name = self.corr_name
        self.set_speed(C.BANNER_APPROACH_SPEED)
        lost, hand = 0, {"n": 0}
        for _ in range(40):
            if time.monotonic() > deadline:
                return "timeout"
            axis = strip.axis(name, self.corr_colour)
            goal = axis.from_sd(-C.APPROACH_DIST, 0.0)
            st = self.st()
            togo = dist(st.xy, goal)
            near = togo < C.BANNER_APPROACH_STEP + 0.5
            # 5 m all the way; only after a recovery climb (above the walls) stay up
            # until ALIGN has us outside the entrance, where it descends
            alt = st.alt if st.alt > C.ALT_ALIGN + 0.5 else C.ALT_ALIGN
            if near:
                wp, hdg = goal, axis.heading
            else:
                k = C.BANNER_APPROACH_STEP / togo
                wp = (st.x + k * (goal[0] - st.x), st.y + k * (goal[1] - st.y))
                hdg = math.atan2(axis.entry[1] - st.y, axis.entry[0] - st.x)   # keep the entrance in view
            self.log("BANNER", f"entrance {dist(st.xy, axis.entry):.1f} m away, corridor heading "
                               f"{math.degrees(axis.heading):.1f} deg, {togo:.1f} m to the alignment point")
            self.settle(hdg)
            hand["n"] = 0
            r = self.fly_to(*wp, alt, hdg, tol=0.3 if near else 0.6,
                            on_tick=lambda s: self._approach_tick(s, hdg, goal, hand))
            if r == "down_sees" or (near and r == "arrived"):
                self.v.goto(*self.st().xy, self.st().alt, hdg)
                if r == "down_sees":
                    self.log("BANNER", "DOWN camera sees the corridor entrance edge - handing over to alignment")
                else:
                    self.log("BANNER", "at the alignment point (down camera not sure yet) - handing over")
                self.log.snapshot("handover_down", self._last_img)
                self.axes[name] = axis
                return "ready"
            if r == "blocked":
                return "lost"
            self.look(hdg)
            strips, _ = self.corridor_strips()
            same = [s for s in strips if dist(s.entry, axis.entry) < 3.0 and
                    abs(wrap_pi(s.heading - axis.heading)) < math.radians(30)]
            if same:
                lost, strip = 0, same[0]
            else:
                lost += 1
                self.log("BANNER", f"corridor not confirmed from here ({lost}/2)")
                if lost >= 2:
                    return "lost"
        return "lost"

    def _approach_tick(self, st, hdg: float, goal, hand) -> Optional[str]:
        if dist(st.xy, goal) > C.HANDOVER_DIST and self._search_tick(st, hdg):
            return "blocked"
        self.feed_map(st, "front", hdg)
        img = self.new_frame("down")
        if img is None or dist(st.xy, goal) > C.HANDOVER_DIST:
            return None
        sf = self.frame_state("down")
        e = vision.entrance_edge(img, self.corr_colour, self.cam, self.cam_height(sf), sf.roll, sf.pitch)
        hand["n"] = hand["n"] + 1 if self.edge_ok(e) else 0
        return "down_sees" if hand["n"] >= C.HANDOVER_FRAMES else None

    def align(self, prior: CorridorAxis) -> Result:
        """Down camera alignment at ALT_ALIGN (5 m), hovering OUTSIDE the entrance with the
        entrance edge ALIGN_EDGE_AHEAD in front of the drone. While the floor is not in the
        down camera yet, creep forward (it sees ~2 m ahead, so a 0.8 m step cannot pass the
        entrance). Rulebook: align first, then descend (CORRIDOR_* descends to 3 m here).
        `prior` comes from the front camera map (or the survey, return lap)."""
        name, axis = prior.name, prior
        st = self.st()
        self.set_speed(C.SPEED_TRANSIT)
        start = axis.from_sd(-C.APPROACH_DIST, 0.0)
        alt0 = max(C.ALT_ALIGN, st.alt)              # after a recovery climb: get outside first, then descend
        if self.fly_to(*start, alt0, axis.heading, tol=0.4) != "arrived":
            return Result.TIMEOUT
        if alt0 > C.ALT_ALIGN + 0.3:
            self.fly_to(*start, C.ALT_ALIGN, axis.heading, tol=0.3)
        self.set_speed(C.SPEED_SCAN)
        crept = 0.0
        rejected = []
        for attempt in range(1, C.ALIGN_ATTEMPTS + 2):
            self.settle(axis.heading)
            st = self.st()
            m = self.measure_entrance(axis)
            if m is None:
                if self.green_below():
                    self.log("ALIGN", f"#{attempt}: green under the drone, entrance edge not ahead - backing off")
                    self.fly_to(*body_to_world(st.x, st.y, axis.heading, -0.6, 0.0), C.ALT_ALIGN, axis.heading,
                                tol=0.15)
                    continue
                if crept >= C.ALIGN_CREEP_MAX:
                    self.log("ALIGN", f"#{attempt}: {name} floor still not in the down camera after "
                                      f"creeping {crept:.1f} m")
                    break
                crept += C.ALIGN_CREEP_STEP
                self.log("ALIGN", f"#{attempt}: {name} floor not in the down camera yet - creeping "
                                  f"{C.ALIGN_CREEP_STEP:.1f} m forward")
                self.fly_to(*body_to_world(st.x, st.y, axis.heading, C.ALIGN_CREEP_STEP, 0.0), C.ALT_ALIGN,
                            axis.heading, tol=0.15)
                continue
            seen, width, img = m
            self.log.snapshot(f"align_{name}_{attempt}", img)
            moved = dist(seen.entry, axis.entry)
            dyaw = wrap_pi(seen.heading - axis.heading)
            if moved > C.ALIGN_MAX_CORRECTION + 1.0 or abs(dyaw) > C.ALIGN_MAX_YAW_CORRECTION:
                # a coarse prior (front-camera map of a half-hidden corridor) can be well off; the
                # down camera at 5 m is sharper. The SAME odd measurement again and again is not noise.
                same = [r for r in rejected if dist(r[0], seen.entry) < 0.3 and abs(wrap_pi(r[1] - seen.heading)) < math.radians(4)]
                rejected.append((seen.entry, seen.heading))
                if len(same) < C.ALIGN_TRUST_AFTER:
                    self.log("ALIGN", f"#{attempt}: rejected (entrance {moved:.2f} m / {math.degrees(dyaw):+.1f} deg "
                                      f"off the estimate)")
                    continue
                self.log("ALIGN", f"#{attempt}: same measurement {len(same) + 1}x ({moved:.2f} m / "
                                  f"{math.degrees(dyaw):+.1f} deg off the estimate) - trusting the down camera")
            axis = seen
            st = self.st()
            s_now, d = axis.to_sd(*st.xy)
            yaw_err = wrap_pi(st.heading - axis.heading)
            self.log("ALIGN", f"#{attempt}: entrance edge {width:.2f} m wide, moved {moved:.2f} m / "
                              f"{math.degrees(dyaw):+.1f} deg; drone {d:+.2f} m lateral, yaw "
                              f"{math.degrees(yaw_err):+.1f} deg, entrance {-s_now:.2f} m ahead")
            if (abs(d) < C.ALIGN_LAT_TOL and abs(yaw_err) < C.ALIGN_YAW_TOL
                    and abs(-s_now - C.ALIGN_EDGE_AHEAD) < 0.35):
                self.axes[name] = axis
                self.log("ALIGN", f"ALIGNED with the {name} corridor (heading {math.degrees(axis.heading):.1f} deg), "
                                  f"entrance {-s_now:.2f} m ahead -> descend and go in")
                return Result.SUCCESS
            self.fly_to(*axis.from_sd(-C.ALIGN_EDGE_AHEAD, 0.0), C.ALT_ALIGN, axis.heading, tol=0.1)
        if C.ALIGN_FALLBACK_TO_PRIOR:
            self.axes[prior.name] = axis
            self.log("ALIGN", "WARNING: alignment not confirmed - continuing on the best axis estimate")
            return Result.SUCCESS
        return Result.FAILED

    def traverse(self, name: str) -> Result:
        """LiDAR corridor flight on a locked heading. Centres between the walls and
        steers round obstacles (lidar.plan_step), corrects the heading from the wall
        lines, and decides inside / exited from the walls appearing and disappearing.
        The aligned axis only gives the initial heading."""
        heading = self.axes[name].heading
        st = self.st()
        self.set_speed(C.SPEED_SCAN)
        # descend where ALIGN left us (aligned, at the entrance line) - rulebook: align, then descend
        if self.fly_to(st.x, st.y, C.ALT_CORRIDOR, heading, tol=0.3) != "arrived":
            return Result.TIMEOUT
        self.log("CORRIDOR", f"{name}: heading locked at {math.degrees(heading):.1f} deg, flying in on LiDAR")
        start = self.st().xy
        t0 = time.monotonic()
        inside, n_in, n_out, last_seq = False, 0, 0, -1
        entry_xy = None
        best, t_progress, last_log = -math.inf, t0, 0.0
        while True:
            now = time.monotonic()
            st = self.st()
            along = (st.x - start[0]) * math.cos(heading) + (st.y - start[1]) * math.sin(heading)
            if now - t0 > C.CORRIDOR_TIMEOUT:
                self.v.velocity(0, 0, 0, heading)
                return Result.TIMEOUT
            if along > C.CORRIDOR_MAX_LENGTH:
                self.v.velocity(0, 0, 0, heading)
                self.log("CORRIDOR", f"flew {along:.0f} m without finding the exit")
                return Result.FAILED
            if not inside and along > C.APPROACH_DIST + 6.0:
                self.v.velocity(0, 0, 0, heading)
                self.log("CORRIDOR", "no walls on both sides - this green strip is NOT the corridor, "
                                     "rejecting it")
                self.rejected.append(self.axes[name].entry)
                return Result.FAILED
            if along > best + 0.3:
                best, t_progress = along, now
            elif now - t_progress > C.CORRIDOR_STUCK_S:
                self.v.velocity(0, 0, 0, heading)
                self.log("CORRIDOR", f"no progress for {C.CORRIDOR_STUCK_S:.0f}s")
                return Result.FAILED

            pts, t_scan, seq = self.s.scan()
            if now - t_scan > C.LIDAR_STALE_S:
                self.v.velocity(0, 0, 0, heading)
                if now - t_scan > 3.0:
                    self.log("CORRIDOR", "LiDAR stopped publishing")
                    return Result.FAILED
                self.sleep(0.05)
                continue
            pc = lidar.to_corridor_frame(pts, wrap_pi(st.heading - heading))
            step = lidar.plan_step(pc)
            if seq != last_seq:                              # once per new scan
                last_seq = seq
                wa = lidar.wall_angle(pc)
                if inside and wa is not None and abs(wa) < math.radians(15):
                    heading = wrap_pi(heading + C.HEADING_FROM_WALLS_GAIN * wa)
                n_in = n_in + 1 if lidar.walls_both_sides(step) else 0
                n_out = n_out + 1 if (inside and lidar.walls_none(step)) else 0
                if not inside and n_in >= C.WALL_CONFIRM_SCANS:
                    inside, entry_xy = True, st.xy
                    self.log("CORRIDOR", f"walls on both sides - INSIDE the {name} corridor")
                if inside and n_out >= C.EXIT_CONFIRM_SCANS:
                    self.log("CORRIDOR", f"walls gone - EXIT after {dist(entry_xy, st.xy):.1f} m inside, "
                                         f"{now - t0:.1f}s, heading {math.degrees(heading):.1f} deg")
                    clear = body_to_world(st.x, st.y, heading, C.EXIT_MARGIN, 0.0)
                    self.fly_to(*clear, C.ALT_CORRIDOR, heading, tol=0.4)
                    if name == C.FORWARD_CORRIDOR_NAME:      # the delivery search starts from here
                        self.exit_xy, self.exit_heading = clear, heading
                    return Result.SUCCESS

            if step is None:
                v_fwd = v_lat = 0.0
            else:
                v_fwd = lidar.forward_speed(step)
                v_lat = clamp(C.CORRIDOR_K_LAT * step.target, -C.CORRIDOR_MAX_LAT, C.CORRIDOR_MAX_LAT)
            if abs(st.alt - C.ALT_CORRIDOR) > 0.5:
                v_fwd = 0.0                                # get to corridor height first
            vz = clamp(1.0 * (C.ALT_CORRIDOR - st.alt), -0.7, 0.7)
            t = (math.cos(heading), math.sin(heading))
            n = (-t[1], t[0])
            self.v.velocity(v_fwd * t[0] + v_lat * n[0], v_fwd * t[1] + v_lat * n[1], vz, heading)
            if now - last_log > 1.0:
                last_log = now
                if step:
                    wl, wr = step.walls
                    self.log("CORRIDOR", f"{'IN ' if inside else 'out'} {along:5.1f} m | walls L {wl or 0:.2f} "
                                         f"R {wr or 0:.2f} | hdg {math.degrees(heading):6.1f} | ahead "
                                         f"{min(step.clear, 99):.1f} m | steer {step.target:+.2f} | "
                                         f"v {v_fwd:.2f}/{v_lat:+.2f}")
                else:
                    self.log("CORRIDOR", f"{along:5.1f} m | boxed in - holding")
            self.sleep(0.1)

    def near_decoded(self, p, r: float = 1.5) -> bool:
        return any(dist(p, tuple(np.median(np.array(obs), axis=0))) < r for obs in self.qr_obs.values())

    def snap(self, label: str) -> bool:
        """Stop-and-snap: hold still and level, read SEARCH_SNAP_FRAMES fresh FULL frames.
        Every QR (text + ground position), red zone and QR-looking spot that did not read
        goes into the map. True when the target just got confirmed."""
        self.settle(self.search_heading)
        n, t_end, found, seen = 0, time.monotonic() + 4.0, False, set()
        spots = []
        while n < C.SEARCH_SNAP_FRAMES and time.monotonic() < t_end:
            st = self.st()
            img = self.new_frame()
            if img is None:
                self.sleep(0.05)
                continue
            n += 1
            st = self.frame_state("down")
            self._map_red(st, img)
            had = self.target_xy is not None
            hits = vision.decode_qrs(self._last_full)
            self._overlay = [(h.u, h.v, h.data) for h in hits]
            for hit in hits:
                if vision.parse_start_qr(hit.data) is None:
                    seen.add(hit.data)
                    if self.record_qr(hit.data, self.pixel_to_world(st, hit.u, hit.v), st) and not had:
                        found = True
            expect = self.cam_full.f / self.cam_height(st)            # px of a 1 m QR at the centre
            spots += [self.pixel_to_world(st, u, v)
                      for u, v in vision.unread_qr_spots(self._last_full, hits, expect)]
        for p in spots:
            if not self.near_decoded(p) and all(dist(p, q) > 1.5 for q in self.unread):
                self.unread.append(p)
        if self.heat is not None:                     # what this picture covered is now checked
            st = self.st()
            along, across = self.cam_full.footprint(self.cam_height(st))
            self.heat.seen_picture(st.xy, self.search_heading, along, across)
        self.log("SEARCH", f"{label}: read {sorted(seen) or 'nothing'}"
                           + (f", {len(spots)} QR-looking spot(s) did not read" if spots else ""))
        self.log.snapshot(f"search_{label.split()[0]}_{label.split()[-1].replace('/', 'of')}", self._annotated())
        return found

    def _annotated(self):
        img = self._last_img.copy()
        k = img.shape[1] / self._last_full.shape[1]
        for u, v, text in self._overlay:
            cv2.circle(img, (int(u * k), int(v * k)), 10, (0, 0, 255), 2)
            cv2.putText(img, text, (int(u * k) + 12, int(v * k)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return img

    def scout(self, hdg0: float):
        """FRONT camera at the corridor exit, 10 m up: QR-looking squares up to
        SCOUT_MAX_RANGE away become hot pins in the heat map (seen in 2+ frames)."""
        pins = []                                       # [x, y, frames]
        for off in C.SCOUT_LOOKS:
            look = wrap_pi(hdg0 + math.radians(off))
            self.settle(look)
            n, t_end = 0, time.monotonic() + 3.0
            while n < 2 and time.monotonic() < t_end:
                img = self.new_frame("front")
                st = self.frame_state("front") if img is not None else self.st()
                if img is None or abs(wrap_pi(st.heading - look)) > math.radians(3):
                    self.sleep(0.05)
                    continue
                n += 1
                for f, r in vision.qr_scout(img, self.front, self.front_height(st), st.roll, st.pitch,
                                            C.SCOUT_MAX_RANGE):
                    p = body_to_world(st.x, st.y, st.heading, f, r)
                    if self.heat.to_uv(p)[0] < 1.0:
                        continue                         # behind the exit: not the delivery field
                    near = [q for q in pins if math.hypot(q[0] - p[0], q[1] - p[1]) < 2.0]
                    if near:
                        q = near[0]
                        q[0], q[1], q[2] = (q[0] * q[2] + p[0]) / (q[2] + 1), (q[1] * q[2] + p[1]) / (q[2] + 1), q[2] + 1
                    else:
                        pins.append([p[0], p[1], 1])
        good = [(q[0], q[1]) for q in pins if q[2] >= 2]
        for p in good:
            self.heat.pin(p, C.SEARCH_PIN_WEIGHT)
        return good

    def heat_snapshot(self, name: str, stops=(), pins=()):
        qrs = [tuple(np.median(np.array(v), axis=0)) for v in self.qr_obs.values()]
        self.log.snapshot(name, self.heat.render(stops, self.st().xy, qrs, pins))

    def search(self) -> Result:
        """Find the target QR WITHOUT any zone coordinates.
          1. at the corridor exit climb to 10 m, take the first picture
          2. scout: front camera looks ahead / to the sides for QR-looking squares
          3. heat map: warm ahead of the exit, zero behind it, hot at scout pins
          4. loop: fly to the stop whose picture covers the most heat per second of
             flying, hold still, read 2 full frames; covered ground goes cold, ground
             near every code read gets warmer (the field's codes are close together)
          5. ends when the target reads twice, nothing is left worth a look, or time is up
        QR-looking spots that did not read get a look from right above (10 m, 7 m).
        Red zones are mapped from every frame and every leg goes around them."""
        t0 = time.monotonic()
        deadline = t0 + C.SEARCH_TIMEOUT
        self.set_speed(C.SPEED_SEARCH)
        st = self.st()
        origin = self.exit_xy if self.exit_xy is not None else st.xy
        hdg0 = self.exit_heading if self.exit_heading is not None else st.heading
        self.heat = HeatMap(origin, hdg0)
        self.search_heading = hdg0
        along, across = self.cam_full.footprint(C.ALT_SEARCH + C.CAM_HEIGHT_OFFSET)
        self.log("SEARCH", f"looking for '{self.target_id}' with NO zone coordinates: one picture covers "
                           f"{across:.1f} x {along:.1f} m from {C.ALT_SEARCH:.0f} m; searching ahead of the "
                           f"corridor exit ({origin[0]:.1f}, {origin[1]:.1f}), heading {math.degrees(hdg0):.0f} deg")
        stops, pins = [self.st().xy], []
        if self.fly_to(st.x, st.y, C.ALT_SEARCH, hdg0, tol=0.8, on_tick=self._scan_tick) != "found" \
                and not self.snap("look 0"):
            pins = self.scout(hdg0)
            self.log("SEARCH", f"scout: {len(pins)} QR-looking spot(s) ahead: "
                               + ", ".join(f"({p[0]:.0f}, {p[1]:.0f})" for p in pins))
            self.heat_snapshot("heat_start", stops, pins)
            start_total = self.heat.total()

            def blocked(p):
                return any(z.contains(p) for z in self.no_fly()) or not self.inside_fence(p)

            k = 0
            while self.target_xy is None and time.monotonic() < deadline:
                here = self.st()
                best = self.heat.best_stop(here.xy, here.heading, along, across, blocked)
                total = self.heat.total()
                if best is None or best[2] < C.SEARCH_MIN_GAIN * start_total:
                    self.log("SEARCH", "nothing left that is worth a look")
                    break
                p, hdg, gain, why = best
                k += 1
                self.search_heading = hdg
                self.log("SEARCH", f"look {k}: ({p[0]:.1f}, {p[1]:.1f}), {dist(here.xy, p):.0f} m away, camera "
                                   f"{math.degrees(wrap_pi(hdg)):.0f} deg - covers {100 * gain / total:.0f}% of "
                                   f"the remaining heat ({why})")
                r = self.travel(p, C.ALT_SEARCH, hdg, on_tick=self._scan_tick, tol=0.8)
                stops.append(p)
                if r == "found":
                    break
                if r == "unreachable":
                    self.heat.seen_picture(p, hdg, along, across)     # do not pick it again
                    continue
                if self.snap(f"look {k}"):
                    break
            self.heat_snapshot("heat_end", stops, pins)
        looks = 0
        while self.target_xy is None and looks < C.SEARCH_FOLLOWUP_MAX and time.monotonic() < deadline:
            todo = [p for p in self.unread if not self.near_decoded(p)]
            if not todo:
                break
            p = min(todo, key=lambda q: dist(q, self.st().xy))
            self.unread.remove(p)
            looks += 1
            self.log("SEARCH", f"QR-looking spot at ({p[0]:.1f}, {p[1]:.1f}) did not read - looking from above")
            for alt in (C.ALT_SEARCH, C.SEARCH_FOLLOWUP_ALT):
                r = self.travel(push_out(p, self.no_fly()), alt, self.search_heading, on_tick=self._scan_tick,
                                tol=0.4)
                if r == "found" or self.snap(f"closer {looks} at {alt:.0f}m") or self.near_decoded(p):
                    break
        codes = {k: tuple(round(c, 1) for c in np.median(np.array(v), axis=0)) for k, v in self.qr_obs.items()}
        self.log("SEARCH", f"{time.monotonic() - t0:.0f}s, {len(stops) - 1} stop(s); QR codes found: {codes}; "
                           f"red zones: {len(self.red_zones)}")
        if self.target_xy is None:
            self.log("SEARCH", f"target '{self.target_id}' not found")
            return Result.FAILED
        self.log("SEARCH", f"TARGET '{self.target_id}' at ({self.target_xy[0]:.1f}, {self.target_xy[1]:.1f})")
        return Result.SUCCESS

    def centre_on_target(self, alt: float, tol: float, hold_s: Optional[float] = None,
                         timeout: float = 40.0) -> Result:
        """Visual servo over the target QR at `alt`. With hold_s: keep centring that
        long (payload lowering) and always return SUCCESS unless the QR is lost."""
        est = self.target_xy
        t0 = t_seen = time.monotonic()
        settled, worst = 0, 0.0
        while time.monotonic() - t0 < (hold_s or timeout):
            st = self.st()
            img = self.new_frame()
            if img is not None:
                self._overlay = []
                sf = self.frame_state("down")
                for hit in vision.decode_qrs(self._last_full):
                    self._overlay.append((hit.u, hit.v, hit.data))
                    if vision.same_id(hit.data, self.target_id):
                        p = self.pixel_to_world(sf, hit.u, hit.v)
                        est = (0.5 * est[0] + 0.5 * p[0], 0.5 * est[1] + 0.5 * p[1])
                        t_seen = time.monotonic()
            if time.monotonic() - t_seen > C.CENTRE_LOST_S:
                self.log("DELIVER", "target QR lost")
                return Result.FAILED
            ex, ey = est[0] - st.x, est[1] - st.y
            e = math.hypot(ex, ey)
            sp = min(C.CENTRE_MAX_SPEED, C.CENTRE_K * e)
            vx, vy = (ex / e * sp, ey / e * sp) if e > 1e-3 else (0.0, 0.0)
            vz = clamp(0.8 * (alt - st.alt), -1.0, 1.0)
            self.v.velocity(vx, vy, vz, self.search_heading)
            self.target_xy = est
            if hold_s:
                worst = max(worst, e)
            elif e < tol and abs(alt - st.alt) < 0.3:
                settled += 1
                if settled >= C.CENTRE_SETTLE_FRAMES:
                    self.log("DELIVER", f"centred at {st.alt:.1f} m, error {e:.2f} m")
                    return Result.SUCCESS
            else:
                settled = 0
            self.sleep(0.1)
        if hold_s:
            self.log("DELIVER", f"held {hold_s:.0f}s over the target, worst error {worst:.2f} m")
            return Result.SUCCESS
        return Result.TIMEOUT

    def deliver(self) -> Result:
        self.set_speed(C.SPEED_TRANSIT)
        r = self.travel(self.target_xy, C.ALT_SEARCH, self.search_heading, on_tick=self._scan_tick, tol=0.8)
        if r == "timeout":
            return Result.TIMEOUT
        for alt, tol in ((C.ALT_SEARCH, C.CENTRE_TOL_HIGH), (C.ALT_DELIVERY, C.CENTRE_TOL_LOW)):
            r = self.centre_on_target(alt, tol)
            if r is not Result.SUCCESS:
                return r
        self.log("PAYLOAD", f"lowering payload over '{self.target_id}' at {self.st().alt:.1f} m")
        if self.centre_on_target(C.ALT_DELIVERY, C.CENTRE_TOL_LOW, hold_s=C.PAYLOAD_LOWER_S) is not Result.SUCCESS:
            return Result.FAILED
        if C.PAYLOAD_SERVO:
            self.v.set_servo(*C.PAYLOAD_SERVO)
        st = self.st()
        self.log("PAYLOAD", f"RELEASED at ({st.x:.2f}, {st.y:.2f}), alt {st.alt:.1f} m, "
                            f"{dist(st.xy, self.target_xy):.2f} m from the QR estimate")
        self.log.snapshot("delivery", self._last_img)
        return Result.SUCCESS

    def find_return(self) -> Result:
        """Find the orange (return) corridor with the cameras - no coordinates. Same method
        as the green one (front-camera ground map, 360 spin, search points), but from the
        delivery zone: the entrance is the strip end nearest to us, and the first search
        points lie on the way home. Red zones stay mapped and avoided meanwhile."""
        ret = C.RETURN_CORRIDOR
        self.corr_name, self.corr_colour = ret["name"], ret["colour"]
        if not self._return_map_started:                 # a retry keeps what was already seen / rejected
            self.gmap = GroundMap(self.st().xy)
            self.start_ref = self.st().xy
            self.rejected = []
            self._return_map_started = True
        self.map_red_while_searching = True
        self.set_speed(C.SPEED_TRANSIT)
        st = self.st()
        if abs(st.alt - C.ALT_ALIGN) > 0.5 and st.alt < C.ALT_ALIGN + 0.5:
            self.fly_to(st.x, st.y, C.ALT_ALIGN, st.heading, tol=0.6)
        left = C.ABORT_AT - (time.monotonic() - self._t_flight) - C.RETURN_RESERVE_S
        if left < 20.0:
            self.log("MISSION", f"only {left:.0f} s of search budget left - cannot look for the corridor")
            return Result.TIMEOUT
        r = self.find_banner(timeout=min(C.RETURN_SEARCH_TIMEOUT, left), planner=self.return_search_plan)
        self.map_red_while_searching = False
        if r is not Result.SUCCESS and C.RETURN_FALLBACK_TO_SURVEY:
            self.log("MISSION", "return corridor not found by camera - using the surveyed axis")
            self.axes[ret["name"]] = CorridorAxis.from_config(ret)
            return self.to_return_corridor()
        return r

    def to_return_corridor(self) -> Result:
        axis = CorridorAxis.from_config(C.RETURN_CORRIDOR)
        self.set_speed(C.SPEED_TRANSIT)
        st = self.st()
        if st.alt < C.ALT_SEARCH - 0.5:
            self.fly_to(st.x, st.y, C.ALT_SEARCH, self.search_heading, tol=0.8)
        r = self.travel(axis.from_sd(-C.APPROACH_DIST, 0.0), C.ALT_SEARCH, axis.heading,
                        on_tick=self._scan_tick, tol=0.5)
        return Result.SUCCESS if r == "arrived" else Result.TIMEOUT

    def _time_is_short(self) -> bool:
        """Not enough flight time left to try the return corridor (reserve for corridor + landing)."""
        return (self._t_flight is not None and
                time.monotonic() - self._t_flight > C.ABORT_AT - C.RETURN_RESERVE_S)

    def drop_at_estimate(self):
        """Last resort when visual centring on the target failed twice: release over the best estimate of the
        target. The accuracy marks are proportional, a rough drop still scores; skipping it scores nothing."""
        self.log("DELIVER", "centring failed - releasing at the best estimate instead")
        self.set_speed(C.SPEED_TRANSIT)
        r = self.travel(self.target_xy, C.ALT_DELIVERY, self.search_heading, on_tick=self._scan_tick, tol=0.8)
        if r != "arrived":
            self.log("DELIVER", f"could not get over the estimate ({r}) - not releasing")
            return
        self.hold(C.PAYLOAD_LOWER_S, self.search_heading)
        if C.PAYLOAD_SERVO:
            self.v.set_servo(*C.PAYLOAD_SERVO)
        st = self.st()
        self.log("PAYLOAD", f"RELEASED (blind) at ({st.x:.2f}, {st.y:.2f}), alt {st.alt:.1f} m")

    def home_land(self) -> Result:
        self.set_speed(C.SPEED_TRANSIT)
        st = self.st()
        self.fly_to(st.x, st.y, C.ALT_HOME, st.heading, tol=0.5)
        if self.fly_to(*C.HOME_XY, C.ALT_HOME, st.heading, tol=0.3) != "arrived":
            return Result.TIMEOUT
        t_end = time.monotonic() + 12.0
        while self.st().alt > C.LAND_FAST_TO_ALT and time.monotonic() < t_end:
            st = self.st()
            self.v.velocity(clamp(0.5 * (C.HOME_XY[0] - st.x), -0.4, 0.4), clamp(0.5 * (C.HOME_XY[1] - st.y), -0.4, 0.4),
                            -C.LAND_FAST_SPEED, st.heading)
            self.sleep(0.1)
        self.log("LAND", "over the take-off point - LAND")
        self._guided = False
        self.v.set_mode("LAND")
        t_end = time.monotonic() + 60.0
        while self.v.armed and time.monotonic() < t_end:
            time.sleep(0.5)
        st = self.st()
        self.log("LAND", f"{'disarmed' if not st.armed else 'STILL ARMED'}, "
                         f"{dist(st.xy, C.HOME_XY):.2f} m from the take-off point")
        return Result.SUCCESS if not st.armed else Result.TIMEOUT

    # ══ runner ═════════════════════════════════════════════════════════════
    def recover(self):
        """Before going back to an earlier stage: stop, then climb straight up - to 5 m
        normally, but clear of the walls (RECOVER_ALT) if the LiDAR shows we are between
        them (at 5 m we could not fly out over 5 m walls). Straight up is always safe."""
        st = self.st()
        self.v.velocity(0, 0, 0, st.heading)
        self.set_speed(C.SPEED_SCAN)
        pts, _, _ = self.s.scan()
        step = lidar.plan_step(lidar.to_corridor_frame(pts, 0.0)) if pts is not None and len(pts) else None
        between = step is not None and lidar.walls_both_sides(step)
        alt = max(C.RECOVER_ALT if between else C.ALT_ALIGN, st.alt)
        if between:
            self.log("MISSION", f"between walls - climbing to {alt:.0f} m to get out over them")
        self.fly_to(st.x, st.y, alt, st.heading, tol=0.6)

    def abort(self, reason: str, pilot: bool):
        self.log("ABORT", reason)
        if pilot:
            self.log("ABORT", "not commanding the vehicle - pilot has control")
            return
        self._guided = False
        if not self.v.armed:
            return
        self.v.set_mode("RTL")
        self.log("ABORT", "RTL (climbs to RTL_ALT, returns, lands)")
        t_end = time.monotonic() + 180.0
        while self.v.armed and time.monotonic() < t_end:
            time.sleep(1.0)
        st = self.st()
        self.log("ABORT", f"{'landed' if not st.armed else 'still armed'} at ({st.x:.1f}, {st.y:.1f})")

    def run(self, stop_after: Optional[str] = None, full: bool = False) -> bool:
        R = C.STAGE_RETRIES
        fwd = C.FORWARD_CORRIDOR_NAME
        ret = C.RETURN_CORRIDOR["name"]
        # (stage, function, retries in place, stage to go back to when it still fails)
        plan = [
            ("TAKEOFF", self.takeoff, 0, None),
            ("SCAN_START_QR", self.scan_start_qr, R, None),
            ("FIND_BANNER", self.find_banner, R, None),
            ("ALIGN_FORWARD", lambda: self.align(self.axes[fwd]), R, "FIND_BANNER"),
            ("CORRIDOR_FORWARD", lambda: self.traverse(fwd), 0, "FIND_BANNER"),
        ]
        if full:
            plan += [
                ("SEARCH", self.search, 0, None, "FIND_RETURN"),   # loops internally until SEARCH_TIMEOUT
                ("DELIVER", self.deliver, R, None, "FIND_RETURN"),
                ("FIND_RETURN", self.find_return, 0, None),
                ("ALIGN_RETURN", lambda: self.align(self.axes[ret]), R, "FIND_RETURN"),
                ("CORRIDOR_RETURN", lambda: self.traverse(ret), R, "FIND_RETURN"),
                ("HOME_LAND", self.home_land, 0, None),
            ]
        else:
            stop_after = stop_after or "CORRIDOR_FORWARD"
        names = [p[0] for p in plan]
        self._tele_run = True
        threading.Thread(target=self._telemetry_loop, daemon=True).start()
        try:
            i, fallbacks = 0, 0
            while i < len(plan):
                name, fn, retries, back, *rest = plan[i]
                skip = rest[0] if rest else None
                self.stage = name
                for attempt in range(retries + 1):
                    t = time.monotonic()
                    self.log("MISSION", f"=== {name}" + (f" (retry {attempt})" if attempt else ""))
                    res = fn()
                    flight = time.monotonic() - self._t_flight if self._t_flight else 0.0
                    self.log("MISSION", f"=== {name} -> {res.value} in {time.monotonic() - t:.1f}s "
                                        f"(flight time {flight:.0f}s)")
                    if res is Result.SUCCESS:
                        break
                else:
                    if back and fallbacks < C.MAX_FALLBACKS:
                        fallbacks += 1
                        self.log("MISSION", f"{name} still failing - climbing clear and going back to {back} "
                                            f"(loop {fallbacks}/{C.MAX_FALLBACKS})")
                        self.recover()
                        i = names.index(back)
                        continue
                    if skip and not self._time_is_short():
                        if name == "DELIVER" and self.target_xy is not None:
                            self.drop_at_estimate()
                        self.degraded.append(name)
                        self.log("MISSION", f"{name} failed - skipping on to {skip} (the return through the corridor "
                                            f"and the landing still score)")
                        i = names.index(skip)
                        continue
                    raise Abort(f"{name} failed")
                if name == stop_after and name != "HOME_LAND":
                    self.abort(f"stopping after {name} as requested", pilot=False)
                    return True
                i += 1
            flight = time.monotonic() - self._t_flight
            self.log("MISSION", f"MISSION COMPLETE - flight time {flight:.0f}s ({flight / 60:.1f} min), "
                                + (f"delivered to '{self.target_id}'" if not self.degraded
                                   else f"DEGRADED, failed and skipped: {', '.join(self.degraded)}"))
            return True
        except Abort as e:
            self.abort(str(e), e.pilot)
            return False
        except KeyboardInterrupt:
            self.abort("Ctrl-C", pilot=False)
            return False
        except Exception as e:
            self.abort(f"internal error: {e!r}", pilot=False)
            raise
        finally:
            self._tele_run = False
