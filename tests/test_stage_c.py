"""Stage C (C1-C4) end to end, in-process: MissionContext + a kinematic drone + a synthetic belly camera (tests/sim_c.py).

The red-zone detector is the real one running on rendered images; QR codes are simulated by geometry. Time runs 4x
faster than the wall clock inside the drone model, so a whole delivery takes about a minute.
"""
import math
import threading
import time

import pytest

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.mission import stage_c
from skyscan.mission.context import MissionContext
from skyscan.mission.stage_c import StageC1, StageC2, StageC3, StageC4, ZoneState, zone_state

from sim_c import COURSE, SIM_QRS, SIM_REDS, SPEED_UP, SimDrone, SimQR, SimVision, build_world, truth_fn_for


@pytest.fixture
def fast_loop(monkeypatch):
    monkeypatch.setattr(stage_c, "LOOP_S", 0.1 / SPEED_UP)


class Rig:
    def __init__(self, start=(20.0, 0.0, 3.0), reds=SIM_REDS, decode_below_m=11.0):
        self.cfg = load_config()
        w = self.cfg.winch                                   # the winch runs on wall-clock time: speed it up like the drone
        w.lower_mps, w.raise_mps = 0.5 * SPEED_UP, 0.5 * SPEED_UP
        w.ground_settle_s, w.release_hold_s = 1.0 / SPEED_UP, 1.5 / SPEED_UP
        self.reds = reds
        self.drone = SimDrone(*start)
        self.vision = SimVision(self.cfg, self.drone, build_world(reds), SimQR(SIM_QRS, decode_below_m=decode_below_m))
        self.truth_fn = truth_fn_for(self.drone, reds, SIM_QRS)
        self.mission = {"_course_frame": COURSE, "origin": COURSE, "qr": {"raw": "DELIVERY-C", "target": "C"},
                        "corridor_exit": {"exit_fwd_m": 19.0}}
        t0 = time.time()
        while self.vision.down_age_s() is None and time.time() - t0 < 3:
            time.sleep(0.02)

    def run(self, cls):
        group = self.cfg.mission.stage_c
        ctx = MissionContext(stage_id=cls.id, title=cls.id, cfg=getattr(group, cls.id.lower()), full_cfg=self.cfg, bus=EventBus(),
                             link=self.drone, vision=self.vision, mission_state=self.mission, abort_event=threading.Event(),
                             truth_fn=self.truth_fn)
        stage = cls()
        pre = stage.preconditions(ctx)
        bad = [(c.name, c.detail) for c in pre if c.blocking and not c.ok]
        assert not bad, f"{cls.id} NO-GO: {bad}"
        ok = stage.run(ctx)
        failed = [(c.name, c.value, c.limit, c.detail) for c in ctx.report.criteria if c.blocking and not c.ok]
        return ok, ctx, failed

    def inside_red(self, margin=0.0):
        """Trace points of the drone (any height) that were over a red rectangle (grown by ``margin``)."""
        bad = []
        for (f, r, u) in self.drone.trace:
            for (rf, rr, sf, sr) in self.reds:
                if abs(f - rf) <= sf / 2 + margin and abs(r - rr) <= sr / 2 + margin:
                    bad.append((round(f, 1), round(r, 1)))
        return bad

    def close(self):
        self.drone.run = False
        self.vision.stop()


@pytest.fixture
def rig_factory():
    rigs = []

    def make(**kw):
        r = Rig(**kw)
        rigs.append(r)
        return r

    yield make
    for r in rigs:
        r.close()


def test_c1_climbs_to_10m_and_holds_the_zone_entry(fast_loop, rig_factory):
    rig = rig_factory()
    ok, ctx, failed = rig.run(StageC1)
    assert ok, failed
    assert abs(rig.drone.p[2] - 10.0) <= 0.5
    assert math.hypot(rig.drone.p[0] - 23.0, rig.drone.p[1] - 0.0) <= 0.6
    assert ctx.mission["zone_entry"]["alt_m"] == pytest.approx(10.0, abs=0.5)
    assert ctx.mission["search_zone"]["fwd"] == [22.0, 62.0]


def test_c1_is_no_go_without_the_camera_or_a_course(fast_loop, rig_factory):
    rig = rig_factory()
    rig.vision.run = False
    time.sleep(0.5)                                         # the camera stops: its last frame gets old
    rig.mission.pop("_course_frame"), rig.mission.pop("origin")
    ctx = MissionContext(stage_id="C1", title="C1", cfg=rig.cfg.mission.stage_c.c1, full_cfg=rig.cfg, bus=EventBus(), link=rig.drone,
                         vision=rig.vision, mission_state=rig.mission, abort_event=threading.Event())
    bad = {c.name for c in StageC1().preconditions(ctx) if c.blocking and not c.ok}
    assert "Course frame established (A1)" in bad
    rig.vision.hist.clear()
    rig.vision.rx = 0.0
    bad = {c.name for c in StageC1().preconditions(ctx) if c.blocking and not c.ok}
    assert "Belly camera streaming" in bad


def test_stage_c_full_delivery_with_both_red_zones(fast_loop, rig_factory):
    rig = rig_factory()
    for cls in (StageC1, StageC2, StageC3, StageC4):
        ok, ctx, failed = rig.run(cls)
        assert ok, f"{cls.id} failed: {failed} error={ctx.report.error}"
        if cls is StageC2:
            assert ctx.report.metrics["result"] == "stopped"                        # ended as soon as the target was read
            assert ctx.report.metrics["red_zones_mapped"] >= 1
            cands = {c["text"]: c for c in ctx.mission["qr_candidates"]}
            assert "DELIVERY-C" in cands and cands["DELIVERY-C"]["status"] == "match"
        if cls is StageC3:
            tq = ctx.mission["target_qr"]
            assert math.hypot(tq["fwd"] - 41.0, tq["right"] + 2.0) <= 0.5, tq     # the estimate is on the real QR
            assert tq["votes"] >= 5 and not tq["inspected_low"]
            assert abs(rig.drone.p[2] - 10.0) <= 0.5
    d = ctx.mission["delivery"]
    assert d["released"] and d["drop_error_m"] <= 0.5
    f, r, u = rig.drone.p
    assert math.hypot(f - 41.0, r + 2.0) <= 0.5 and abs(u - 5.0) <= 0.4          # hovering 5 m over the QR (truth)
    pwm = [p for _, p in rig.drone.servo]
    assert pwm[0] == 1100 and 1900 in pwm and pwm[-1] == 1500                      # lower, stop, raise, stop
    assert not rig.inside_red(), rig.inside_red()[:5]                              # never over a red rectangle (truth)
    assert ctx.report.metrics.get("sim_drop_error_m", 0.0) <= 0.5


@pytest.mark.slow
def test_c3_lowers_for_a_closer_look_when_the_code_is_not_readable_from_10m(fast_loop, rig_factory):
    rig = rig_factory(start=(23.0, 0.0, 10.0), decode_below_m=7.5)
    ok, ctx, failed = rig.run(StageC2)
    assert ok, failed
    assert ctx.report.metrics["result"] == "done"                                   # nothing read, so the whole zone was swept
    assert ctx.report.metrics["coverage_pct"] >= 95.0
    assert ctx.report.metrics["qr_seen"] == 5 and ctx.report.metrics["qr_decoded"] == 0
    ok, ctx, failed = rig.run(StageC3)
    assert ok, f"{failed} {ctx.report.error}"
    assert ctx.report.metrics["inspected_low"] is True
    tq = ctx.mission["target_qr"]
    assert math.hypot(tq["fwd"] - 41.0, tq["right"] + 2.0) <= 0.5
    assert abs(rig.drone.p[2] - 10.0) <= 0.5                                        # climbed back up
    assert not rig.inside_red()


def test_red_zone_evasion_protocol_on_a_zone_nobody_expected(fast_loop, rig_factory):
    """A red patch right on the first strip, with nothing in the grid beforehand: halt, back off 2 m, sidestep, carry on."""
    reds = SIM_REDS + [(31.0, -9.5, 3.0, 3.0)]
    rig = rig_factory(start=(23.0, 0.0, 10.0), reds=reds)
    ok, ctx, failed = rig.run(StageC2)
    assert ok, failed
    zs = zone_state(ctx)
    assert zs.evasions, "the red patch on the strip should have triggered the evasion protocol"
    ev = zs.evasions[0]
    assert ev["reversed_m"] == pytest.approx(2.0, abs=0.6)                          # backed off 2 m along the entry vector
    assert ev["offset_s"] * SPEED_UP <= 5.0 and ev["within_budget"]                 # sidestepped within 5 s (simulated seconds)
    assert ev["lateral_m"] > 0.5
    assert zs.red_entries == 0
    assert not rig.inside_red(), rig.inside_red()[:5]                               # truth: no point of the flight over red
    assert not rig.inside_red(margin=0.5), "kept at least 0.5 m clear of the boundary"
    assert ctx.report.metrics["sim_red_violations"] == 0
    boxes = ctx.mission["red_map"]["zones"]
    assert any(b[0] <= 30.2 and b[1] >= 31.8 and b[2] <= -10.8 and b[3] >= -8.2 for b in boxes), boxes   # the new zone is mapped


def test_c4_is_no_go_when_the_target_is_inside_a_red_keep_out(fast_loop, rig_factory):
    rig = rig_factory(start=(41.0, -2.0, 10.0))
    ctx = MissionContext(stage_id="C4", title="C4", cfg=rig.cfg.mission.stage_c.c4, full_cfg=rig.cfg, bus=EventBus(), link=rig.drone,
                         vision=rig.vision, mission_state=rig.mission, abort_event=threading.Event())
    zs = ZoneState(ctx)
    for _ in range(2):
        zs.grid.add_polygon([(40.0, -3.0), (43.0, -3.0), (43.0, 0.0), (40.0, 0.0)])
    rig.mission["_zone"] = zs
    rig.mission["target_qr"] = {"fwd": 41.0, "right": -2.0, "text": "DELIVERY-C", "votes": 9, "scatter_m": 0.05}
    bad = {c.name for c in StageC4().preconditions(ctx) if c.blocking and not c.ok}
    assert bad == {"Delivery point clear of red zones"}


def test_c2_is_no_go_without_a_start_qr(fast_loop, rig_factory):
    rig = rig_factory(start=(23.0, 0.0, 10.0))
    rig.mission.pop("qr")
    ctx = MissionContext(stage_id="C2", title="C2", cfg=rig.cfg.mission.stage_c.c2, full_cfg=rig.cfg, bus=EventBus(), link=rig.drone,
                         vision=rig.vision, mission_state=rig.mission, abort_event=threading.Event())
    bad = {c.name for c in StageC2().preconditions(ctx) if c.blocking and not c.ok}
    assert bad == {"Delivery target known (A3 start QR)"}


def test_truth_check_ignores_the_start_qr_that_carries_the_same_text():
    """The start QR and the matching zone QR both read DELIVERY-C: the cross-check must measure to the one in the zone."""
    from skyscan.mission.stage_c import TruthWatch
    truth = {"qrs": [{"id": "start_qr", "content": "DELIVERY-C", "dist_m": 38.0},
                     {"id": "qr_a", "content": "DELIVERY-A", "dist_m": 17.0},
                     {"id": "qr_c", "content": "DELIVERY-C", "dist_m": 0.6}]}
    watch = TruthWatch.__new__(TruthWatch)
    watch.ctx = type("Ctx", (), {"truth": lambda self: truth})()
    assert watch.qr_offset("DELIVERY-C") == 0.6
    assert watch.qr_offset("DELIVERY-A") == 17.0
    assert watch.qr_offset("DELIVERY-Z") is None
