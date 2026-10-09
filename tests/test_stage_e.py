"""Stage E (E1-E6) in-process: the return lap through the obstacle corridor, home, and the landing.

Same kinematic vehicle and ray-cast lidar as tests/test_stage_b.py, but the vehicle faces back down the course (the
return heading) and flies the corridor from its far end. No simulator, no flight controller.
"""
import math
import threading
import time

import pytest

import test_stage_b as tb
from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.geo import CameraModel, CourseFrame
from skyscan.mission import stage_b, stage_e
from skyscan.mission.context import MissionContext
from skyscan.mission.stage_a import median_pt, qr_sightings
from skyscan.mission.stage_b import FORWARD, RETURN, along_heading, corridor_alt, lap_heading, return_axis_heading
from skyscan.mission.stage_e import StageE1, StageE2, StageE3, StageE4, StageE5, StageE6, drift_correction
from skyscan.types import QRDetection, VehicleState
from skyscan.vision.pipeline import DownObs

from test_corridor_ctrl import OBSTACLES, ORANGE_WALLS, raycast

COURSE = tb.COURSE
RETURN_HEADING = tb.HEADING + 180.0
ALIGNED = {"return_entry_aligned": {"entrance_course": {"fwd": 19.0, "right": 0.0}, "axis_heading_deg": RETURN_HEADING,
                                    "axis_rel_course_deg": 180.0, "width_m": 3.4, "standoff_m": 10.0, "alt_m": 10.0}}


class ReturnVehicle(tb.SimVehicle):
    """The test_stage_b vehicle turned round: nose toward -fwd, so its lidar scan is rotated by 180 deg."""

    def state(self):
        st = super().state()
        st.yaw_deg = RETURN_HEADING
        return st


class LandingVehicle(tb.SimVehicle):
    """The test_stage_b vehicle with a LAND mode: descends to the ground, then reports on-ground and disarms."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.armed, self.mode, self.landed = True, "GUIDED", False

    def land(self):
        n, e, _ = self._ned()
        self.mode = "LAND"
        self.goto_ned(n, e, 0.0)
        return True

    def disarm(self, force=False):
        self.armed = False
        return True

    def state(self):
        st = super().state()
        if self.mode == "LAND" and self.up <= 0.05:
            self.landed, self.armed = True, False
        st.armed, st.mode, st.landed_state = self.armed, self.mode, (1 if self.landed else 2)
        return st


@pytest.fixture
def fast_loop(monkeypatch):
    monkeypatch.setattr(stage_b, "LOOP_S", 0.1 / tb.SPEED_UP)
    monkeypatch.setattr(stage_e, "LOOP_S", 0.1 / tb.SPEED_UP)


@pytest.fixture
def facing_back(monkeypatch):
    monkeypatch.setattr(tb, "raycast", lambda px, py, rects: raycast(px, py, rects, yaw=180.0))


def make_ctx(stage_id, veh, mission=None, vision=None):
    cfg = load_config()
    state = {"_course_frame": COURSE, "origin": COURSE}
    state.update(mission or {})
    ctx = MissionContext(stage_id=stage_id, title=stage_id, cfg=getattr(cfg.mission.stage_e, stage_id.lower()), full_cfg=cfg,
                         bus=EventBus(), link=veh, vision=vision, mission_state=state, abort_event=threading.Event(), lidar=veh.hub)
    return ctx


def run_stage(cls, veh, mission=None):
    ctx = make_ctx(cls.id, veh, mission)
    tb.wait_lidar(veh)
    stage = cls()
    bad = [c for c in stage.preconditions(ctx) if c.blocking and not c.ok]
    assert not bad, [(c.name, c.detail) for c in bad]
    return stage.run(ctx), ctx


# ── pure helpers ─────────────────────────────────────────────────────────────────────────────────────────────

def test_return_lap_heading_and_progress():
    mission = {}
    ctx = MissionContext("E2", "E2", {}, load_config(), EventBus(), None, None, mission, threading.Event())
    assert return_axis_heading(ctx, COURSE) == pytest.approx(RETURN_HEADING % 360.0)     # nothing measured: reverse course
    mission["return_corridor"] = {"axis_heading_deg": 272.0}
    assert return_axis_heading(ctx, COURSE) == 272.0                                       # D2
    mission["return_entry_aligned"] = {"axis_heading_deg": 269.0}
    assert lap_heading(ctx, COURSE, RETURN) == 269.0                                       # D3 wins
    assert lap_heading(ctx, COURSE, FORWARD) == COURSE.heading_deg
    # progress back down the course grows as fwd shrinks
    assert along_heading(COURSE, 270.0, 19.0, 6.0) == pytest.approx(-19.0)
    assert along_heading(COURSE, 270.0, 9.0, 6.0) - along_heading(COURSE, 270.0, 19.0, 6.0) == pytest.approx(10.0)
    assert corridor_alt(ctx, RETURN) == 3.0 and corridor_alt(ctx, FORWARD) == 3.0


def test_drift_correction():
    assert drift_correction((3.0, 0.0), (3.4, -0.3), 3.0) == pytest.approx((0.4, -0.3))   # EKF slid 0.5 m: land there
    assert drift_correction((3.0, 0.0), (9.0, 0.0), 3.0) is None                          # 6 m is a misread, not drift


def test_qr_sightings_project_the_qr_onto_the_course():
    class Vis:
        def __init__(self, obs):
            self.obs = obs

        def down_since(self, seq):
            return [o for o in self.obs if o.seq > seq]

        def camera_model(self, cam, w, h):
            return CameraModel.from_hfov(w, h, 90.0)

    now = time.time()
    n, e, d = COURSE.to_ned(3.0, 0.5, 5.0)
    st = VehicleState(ned=(n, e, d), yaw_deg=tb.HEADING, rel_alt_m=5.0, roll_deg=0.0, pitch_deg=0.0)
    hit = QRDetection(t=now, cam="down", seq=1, found=True, text="DELIVERY-C", center=(320.0, 240.0))
    other = QRDetection(t=now, cam="down", seq=2, found=True, text="DELIVERY-A", center=(320.0, 240.0))
    old = QRDetection(t=now - 100, cam="down", seq=3, found=True, text="DELIVERY-C", center=(320.0, 240.0))
    vis = Vis([DownObs(1, now, 640, 480, hit, None, st), DownObs(2, now, 640, 480, other, None, st),
               DownObs(3, now - 100, 640, 480, old, None, st)])
    ctx = MissionContext("A3", "A3", {}, load_config(), EventBus(), None, vis, {}, threading.Event())
    seen = qr_sightings(ctx, COURSE, now - 1.0, "DELIVERY-C")
    assert len(seen) == 1                                       # the other code and the stale frame are left out
    f, r = median_pt(seen)
    assert f == pytest.approx(3.0, abs=0.05) and r == pytest.approx(0.5, abs=0.05)      # image centre = straight below


# ── the return corridor, flown backwards through the three obstacles ─────────────────────────────────────────

def test_e1_descends_to_the_corridor_height_facing_back(fast_loop, facing_back):
    veh = ReturnVehicle(ORANGE_WALLS + OBSTACLES, fwd=29.0, up=10.0)                       # D3's stand-off, 10 m up
    try:
        ok, ctx = run_stage(StageE1, veh, dict(ALIGNED))
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert abs(veh.up - 3.0) < 0.25 and abs(veh.fwd - 29.0) < 0.6
        assert ctx.mission["return_corridor_altitude"]["height_m"] == pytest.approx(3.0, abs=0.25)
    finally:
        veh.run = False


def test_e2_e3_e4_fly_back_through_the_obstacle_corridor(fast_loop, facing_back):
    veh = ReturnVehicle(ORANGE_WALLS + OBSTACLES, fwd=27.0, up=3.0)                        # 8 m before the far end (x = 19)
    mission = dict(ALIGNED)
    try:
        ok, ctx = run_stage(StageE2, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert abs(-ctx.report.metrics["entrance_fwd_m"] - 19.0) < 0.5                      # progress runs along the return heading
        assert any(c.name.startswith("Entrance agrees with the D3") and c.ok for c in ctx.report.criteria)
        mission.update(ctx.mission)
        ok, ctx = run_stage(StageE3, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert ctx.report.metrics["avoid_manoeuvres"] >= 2
        assert ctx.report.metrics["min_clearance_m"] >= 0.35
        mission.update(ctx.mission)
        assert "return_traverse" in mission and "traverse" not in mission                  # the forward-lap products stay untouched
        ok, ctx = run_stage(StageE4, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert abs(-ctx.report.metrics["exit_fwd_m"] - 9.0) < 1.0, ctx.report.metrics       # the corridor ends at x = 9
        assert abs(ctx.report.metrics["corridor_length_measured_m"] - 10.0) < 1.0
        assert veh.fwd < 9.0
    finally:
        veh.run = False


# ── home and land ────────────────────────────────────────────────────────────────────────────────────────────

def test_e5_flies_home_and_holds_over_the_takeoff_point(fast_loop):
    veh = LandingVehicle([], fwd=7.5, left=-6.0, up=3.0)                                   # just out of the return corridor
    try:
        ctx = make_ctx("E5", veh, {"return_corridor_exit": {"exit_fwd_m": -9.0}})
        ok = StageE5().run(ctx)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert math.hypot(veh.fwd, veh.left) < 0.4 and abs(veh.up - 5.0) < 0.5
        assert ctx.mission["landing_point"] == {"fwd": 0.0, "right": 0.0, "qr_reads": 0, "corrected": False,
                                                "alt_m": pytest.approx(5.0, abs=0.5)}
    finally:
        veh.run = False


def test_e6_lands_on_the_takeoff_point_and_reports_the_mission_time(fast_loop):
    veh = LandingVehicle([], fwd=0.1, left=0.1, up=5.0)
    try:
        ctx = make_ctx("E6", veh, {"landing_point": {"fwd": 0.0, "right": 0.0}, "_t_takeoff": time.time() - 600.0})
        ok = StageE6().run(ctx)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert veh.landed and not veh.armed and veh.up < 0.1
        assert ctx.report.metrics["landing_error_m"] < 1.0
        assert 600.0 <= ctx.report.metrics["mission_time_s"] < 700.0
        assert [c for c in ctx.report.criteria if c.name.startswith("Mission completed within")][0].ok
        assert "_allowed_modes" not in ctx.mission                       # LAND is allowed only while E6 hands over
    finally:
        veh.run = False


def test_e6_says_when_the_mission_ran_over_15_minutes(fast_loop):
    veh = LandingVehicle([], fwd=0.0, left=0.0, up=2.0)
    try:
        ctx = make_ctx("E6", veh, {"_t_takeoff": time.time() - 1000.0})
        assert StageE6().run(ctx)                                       # the landing itself is fine ...
        late = [c for c in ctx.report.criteria if c.name.startswith("Mission completed within")][0]
        assert not late.ok and not late.blocking                        # ... the time is reported, not a crash
    finally:
        veh.run = False
