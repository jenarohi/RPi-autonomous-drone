"""Stage D (D1-D3): the geometry of the return lap, and D1 end to end on the in-process drone (tests/sim_c.py).

D2 and D3 fly on the front camera, which only the simulator provides: they are checked in SITL (docs/STAGE_D.md). Here
the maths they stand on is tested against independently computed numbers.
"""
import math
import threading
import time

import pytest

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.geo import CourseFrame
from skyscan.mission import stage_d
from skyscan.mission.context import MissionContext
from skyscan.mission.stage_d import StageD1, StageD2, StageD3, bearing_rel_deg, entrance_estimate, standoff_point

from sim_c import COURSE, SIM_QRS, SIM_REDS, SPEED_UP, SimDrone, SimQR, SimVision, build_world, truth_fn_for


def test_bearing_back_to_the_start():
    assert bearing_rel_deg((41.0, -2.0), (0.0, 0.0)) == pytest.approx(177.2, abs=0.1)
    assert bearing_rel_deg((0.0, 0.0), (10.0, 0.0)) == 0.0
    assert bearing_rel_deg((0.0, 0.0), (0.0, 5.0)) == 90.0            # to the right of the course heading


def test_standoff_point_is_before_the_entrance_on_the_centre_line():
    p = standoff_point((19.0, 6.0), 180.0, 10.0)                      # corridor runs back toward the start (west)
    assert p == pytest.approx((29.0, 6.0), abs=1e-9)
    q = standoff_point((20.0, 4.0), 150.0, 6.0)
    assert math.hypot(q[0] - 20.0, q[1] - 4.0) == pytest.approx(6.0)
    a = (math.cos(math.radians(150)), math.sin(math.radians(150)))
    assert (20.0 - q[0]) * a[1] - (4.0 - q[1]) * a[0] == pytest.approx(0.0, abs=1e-9)   # q is on the axis line through the entrance


@pytest.mark.parametrize("veh,heading_rel,alt", [((30.0, 0.0), 180.0, 10.0), ((41.0, -2.0), 172.0, 10.0), ((29.0, 6.0), 190.0, 9.5)])
def test_entrance_estimate_round_trip(veh, heading_rel, alt):
    """Build the measurement a perfect detector would give for the real entrance (19, 6) running back along 180 deg,
    from independent trigonometry, and check that the estimate returns the entrance."""
    course = CourseFrame(origin_ned=(2.99, -3.0, -0.19), heading_deg=90.8)
    ent, axis_rel = (19.0, 6.0), 180.0
    th = math.radians(heading_rel)
    df, dr = ent[0] - veh[0], ent[1] - veh[1]
    vf, vr = df * math.cos(th) + dr * math.sin(th), -df * math.sin(th) + dr * math.cos(th)    # entrance in the vehicle level frame
    yaw_err = axis_rel - heading_rel                                                          # axis heading minus vehicle heading
    y = math.radians(yaw_err)
    a, n = (math.cos(y), math.sin(y)), (-math.sin(y), math.cos(y))
    meas = {"distance_m": vf * a[0] + vr * a[1], "lateral_m": vf * n[0] + vr * n[1], "yaw_err_deg": yaw_err}
    ned = course.to_ned(veh[0], veh[1], alt)
    est = entrance_estimate(course, ned, course.abs_heading(heading_rel), meas)
    assert (est["fwd"], est["right"]) == pytest.approx(ent, abs=0.01)
    assert abs(((est["axis_rel_deg"] - axis_rel + 180.0) % 360.0) - 180.0) < 0.01
    assert est["axis_heading_deg"] == pytest.approx(course.abs_heading(axis_rel) % 360.0, abs=0.01)


# ── D1 on the in-process drone ─────────────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fast_loop(monkeypatch):
    monkeypatch.setattr(stage_d, "LOOP_S", 0.1 / SPEED_UP)


class Rig:
    def __init__(self, delivery, start=(41.0, -2.0, 5.0)):
        self.cfg = load_config()
        self.drone = SimDrone(*start)
        self.vision = SimVision(self.cfg, self.drone, build_world(SIM_REDS), SimQR(SIM_QRS))
        self.mission = {"_course_frame": COURSE, "origin": COURSE}
        if delivery is not None:
            self.mission["delivery"] = delivery
        t0 = time.time()
        while self.vision.down_age_s() is None and time.time() - t0 < 3:
            time.sleep(0.02)

    def ctx(self, cls):
        return MissionContext(stage_id=cls.id, title=cls.id, cfg=getattr(self.cfg.mission.stage_d, cls.id.lower()), full_cfg=self.cfg, bus=EventBus(),
                              link=self.drone, vision=self.vision, mission_state=self.mission, abort_event=threading.Event(),
                              truth_fn=truth_fn_for(self.drone, SIM_REDS, SIM_QRS))

    def stop(self):
        self.vision.stop()


DELIVERED = {"released": True, "winch": {"phase": "stowed", "rope_out_m": 0.0}}


def test_d1_climbs_straight_up_to_the_return_altitude(fast_loop):
    rig = Rig(DELIVERED)
    try:
        ctx = rig.ctx(StageD1)
        stage = StageD1()
        assert not [c for c in stage.preconditions(ctx) if c.blocking and not c.ok]
        assert stage.run(ctx)
        crit = {c.name: c for c in ctx.report.criteria}
        assert all(c.ok for c in ctx.report.criteria), [(c.name, c.value) for c in ctx.report.criteria if not c.ok]
        st = rig.drone.state()
        f, r, up = COURSE.to_course(*st.ned)
        assert abs(up - 10.0) <= 0.5 and math.hypot(f - 41.0, r + 2.0) <= 1.0
        assert ctx.mission["ascent"]["drop_point"] == {"fwd": pytest.approx(41.0, abs=0.2), "right": pytest.approx(-2.0, abs=0.2)}
    finally:
        rig.stop()


def test_d1_refuses_while_the_rope_is_still_out():
    rig = Rig({"released": True, "winch": {"phase": "down", "rope_out_m": 5.2}})
    try:
        bad = [c.name for c in StageD1().preconditions(rig.ctx(StageD1)) if c.blocking and not c.ok]
        assert any("Rope" in n for n in bad)
    finally:
        rig.stop()


def test_d1_without_a_delivery_record_is_not_blocked_but_says_so():
    rig = Rig(None)
    try:
        checks = {c.name: c for c in StageD1().preconditions(rig.ctx(StageD1))}
        assert checks["Rope wound in (nothing hanging below the vehicle)"].ok
        assert not checks["Payload delivered and released (C4)"].ok and not checks["Payload delivered and released (C4)"].blocking
    finally:
        rig.stop()


def test_d2_and_d3_need_their_inputs():
    rig = Rig(DELIVERED, start=(41.0, -2.0, 10.0))
    try:
        d3 = {c.name: c for c in StageD3().preconditions(rig.ctx(StageD3))}
        assert not d3["Orange corridor localised (D2)"].ok            # D3 cannot start before D2 has localised the corridor
        d2 = {c.name: c for c in StageD2().preconditions(rig.ctx(StageD2))}
        assert not d2["Vision can look for the orange corridor"].ok   # the in-process vision rig has no front camera
    finally:
        rig.stop()
