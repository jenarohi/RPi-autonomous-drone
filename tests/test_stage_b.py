"""Stage B (B1-B4) end to end, in-process: MissionContext + a kinematic vehicle + the lidar fed by a ray-caster.

Time runs 4x faster than the wall clock inside the vehicle model (and the control loop is shortened to match), so the
whole corridor flight takes seconds. No simulator, no flight controller.
"""
import math
import threading
import time

import pytest

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.geo import CourseFrame
from skyscan.lidar import LidarHub
from skyscan.mission import stage_b
from skyscan.mission.context import MissionContext
from skyscan.mission.stage_b import StageB1, StageB2, StageB3, StageB4
from skyscan.types import LidarScan, VehicleState

from test_corridor_ctrl import GREEN, OBSTACLES, ORANGE_WALLS, raycast

SPEED_UP = 4.0
HEADING = 90.0                       # course heading (east)
COURSE = CourseFrame(origin_ned=(0.0, 0.0, 0.0), heading_deg=HEADING)


class SimVehicle:
    """Point-mass vehicle in the course frame (fwd, y-left, up) with first-order velocity tracking."""

    def __init__(self, world, fwd=5.0, left=0.0, up=5.0, with_range=False):
        self.world, self.fwd, self.left, self.up = world, fwd, left, up
        self.v = [0.0, 0.0, 0.0]                        # NED
        self.target = None                              # position target (n, e, d)
        self.vel_cmd = None
        self.with_range = with_range
        self.lock = threading.Lock()
        self.run = True
        self.hub = LidarHub()
        self.seq = 0
        threading.Thread(target=self._loop, daemon=True).start()

    def _ned(self):
        n, e, d = COURSE.to_ned(self.fwd, -self.left, self.up)
        return (n, e, d)

    def state(self):
        n, e, d = self._ned()
        now = time.time()
        st = VehicleState(link=True, armed=True, mode="GUIDED", ekf_ok=True, ned=(n, e, d), yaw_deg=HEADING,
                          rel_alt_m=self.up, vel_ned=tuple(self.v))
        if self.with_range:
            st.range_m, st.range_t, st.range_min_m, st.range_max_m = self.up, now, 0.1, 30.0
        return st

    def velocity_ned(self, vn, ve, vd, yaw_deg=None):
        with self.lock:
            self.vel_cmd, self.target = (vn, ve, vd), None

    def goto_ned(self, n, e, d, yaw_deg=None):
        with self.lock:
            self.target, self.vel_cmd = (n, e, d), None

    def hold(self, force_guided=False):
        return True

    def _loop(self):
        t_prev, t_scan = time.time(), 0.0
        while self.run:
            time.sleep(0.01)
            now = time.time()
            dt = (now - t_prev) * SPEED_UP
            t_prev = now
            with self.lock:
                vel, tgt = self.vel_cmd, self.target
            n, e, d = self._ned()
            if vel is not None:
                want = list(vel)
            elif tgt is not None:                       # P-controlled position target, 1 m/s limit
                err = [tgt[0] - n, tgt[1] - e, tgt[2] - d]
                want = [max(-1.0, min(1.0, 1.0 * x)) for x in err]
            else:
                want = [0.0, 0.0, 0.0]
            for i in range(3):
                self.v[i] += (want[i] - self.v[i]) * min(1.0, dt * 3.0)
            # NED velocity -> course frame
            h = math.radians(HEADING)
            self.fwd += (self.v[0] * math.cos(h) + self.v[1] * math.sin(h)) * dt
            right = (-self.v[0] * math.sin(h) + self.v[1] * math.cos(h))
            self.left -= right * dt
            self.up -= self.v[2] * dt
            if now - t_scan > 0.05:
                t_scan = now
                self.seq += 1
                s = raycast(self.fwd, self.left, self.world)
                self.hub.put(LidarScan(t=now, seq=self.seq, angle_min_deg=s.angle_min_deg, angle_step_deg=s.angle_step_deg,
                                       ranges=s.ranges, range_min=s.range_min, range_max=s.range_max))


@pytest.fixture
def fast_loop(monkeypatch):
    monkeypatch.setattr(stage_b, "LOOP_S", 0.1 / SPEED_UP)


def make_ctx(stage_id, veh, mission=None):
    cfg = load_config()
    state = {"_course_frame": COURSE, "origin": COURSE}
    state.update(mission or {})
    group = getattr(cfg.mission, "stage_b")
    ctx = MissionContext(stage_id=stage_id, title=stage_id, cfg=getattr(group, stage_id.lower()), full_cfg=cfg, bus=EventBus(),
                         link=veh, vision=None, mission_state=state, abort_event=threading.Event(), lidar=veh.hub)
    return ctx, cfg


def wait_lidar(veh):
    t0 = time.time()
    while veh.hub.stats()["hz"] < 5.0 and time.time() - t0 < 3:
        time.sleep(0.02)


def run_stage(cls, veh, mission=None):
    ctx, _ = make_ctx(cls.id, veh, mission)
    wait_lidar(veh)
    stage = cls()
    checks = stage.preconditions(ctx)
    bad = [c for c in checks if c.blocking and not c.ok]
    assert not bad, [(c.name, c.detail) for c in bad]
    ok = stage.run(ctx)
    return ok, ctx


def test_b1_descends_to_3m_and_holds(fast_loop):
    veh = SimVehicle(GREEN, fwd=5.0, up=5.0)
    try:
        ok, ctx = run_stage(StageB1, veh)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert abs(veh.up - 3.0) < 0.25 and abs(veh.fwd - 5.0) < 0.6
        assert ctx.report.metrics["height_source"] == "ekf"          # no rangefinder in this vehicle model
        assert not [c for c in ctx.report.criteria if not c.ok and c.blocking]
    finally:
        veh.run = False


def test_b1_uses_the_lidar_height_when_it_reports(fast_loop):
    veh = SimVehicle(GREEN, fwd=5.0, up=5.0, with_range=True)
    try:
        ok, ctx = run_stage(StageB1, veh)
        assert ok and ctx.report.metrics["height_source"] == "lidar"
        assert [c for c in ctx.report.criteria if c.name.startswith("Height read from")][0].ok
    finally:
        veh.run = False


def test_b1_is_no_go_below_the_corridor_altitude(fast_loop):
    veh = SimVehicle(GREEN, fwd=5.0, up=2.0)
    try:
        ctx, _ = make_ctx("B1", veh)
        checks = StageB1().preconditions(ctx)
        assert any(c.name.startswith("At or above") and not c.ok for c in checks)
    finally:
        veh.run = False


def test_b2_b3_b4_fly_the_empty_green_corridor(fast_loop):
    veh = SimVehicle(GREEN, fwd=5.0, up=3.0)                       # 4 m before the entrance (x = 9), at corridor altitude
    mission = {}
    try:
        ok, ctx = run_stage(StageB2, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert abs(ctx.report.metrics["entrance_fwd_m"] - 9.0) < 0.5            # the entrance line, from the lidar alone
        mission.update(ctx.mission)
        ok, ctx = run_stage(StageB3, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert ctx.report.metrics["avoid_manoeuvres"] == 0 and ctx.report.metrics["min_clearance_m"] > 1.0
        mission.update(ctx.mission)
        ok, ctx = run_stage(StageB4, veh, mission)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        # the corridor really ends at x = 19: the lidar-measured exit must land close to it, and the length near 10 m
        assert abs(ctx.report.metrics["exit_fwd_m"] - 19.0) < 1.0, ctx.report.metrics
        assert abs(ctx.report.metrics["corridor_length_measured_m"] - 10.0) < 1.0
        assert veh.fwd > 19.0
    finally:
        veh.run = False


def test_b3_goes_round_the_three_obstacles(fast_loop):
    veh = SimVehicle(ORANGE_WALLS + OBSTACLES, fwd=10.0, up=3.0)    # already inside, B3 must cross obstacles 1..3
    try:
        ctx, _ = make_ctx("B3", veh)
        ctx.cfg.traverse_m = 8.0                                    # reach x = 18, past obstacle 3
        wait_lidar(veh)
        ok = StageB3().run(ctx)
        assert ok, [(c.name, c.ok, c.value) for c in ctx.report.criteria]
        assert ctx.report.metrics["avoid_manoeuvres"] >= 2
        assert ctx.report.metrics["min_clearance_m"] >= 0.35
        assert veh.fwd > 17.5
    finally:
        veh.run = False


def test_b2_fails_when_there_are_no_walls(fast_loop):
    veh = SimVehicle([], fwd=0.0, up=3.0)                           # open field: the entrance never appears
    try:
        ctx, _ = make_ctx("B2", veh)
        ctx.cfg.max_search_m = 2.0
        wait_lidar(veh)
        assert StageB2().run(ctx) is False
        assert any(c.name.startswith("Corridor entrance detected") and not c.ok for c in ctx.report.criteria)
    finally:
        veh.run = False


def test_b3_preconditions_need_the_lidar_and_both_walls(fast_loop):
    veh = SimVehicle(GREEN, fwd=3.0, up=3.0)                        # outside the walls
    try:
        ctx, _ = make_ctx("B3", veh)
        wait_lidar(veh)
        checks = StageB3().preconditions(ctx)
        assert any(c.name.startswith("Inside the corridor") and not c.ok for c in checks)
        ctx2, _ = make_ctx("B3", veh)
        ctx2.lidar = None
        assert any(c.name == "Lidar streaming" and not c.ok for c in StageB3().preconditions(ctx2))
    finally:
        veh.run = False
