"""Stage A5 (Safety Backup): 1 m straight back along the corridor axis before B1, on the in-process drone (tests/sim_c.py)."""
import dataclasses
import math
import threading

import pytest

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.mission.context import MissionContext
from skyscan.mission.stage_a import StageA5

from sim_c import COURSE, SIM_QRS, SIM_REDS, SimDrone, SimQR, SimVision, build_world, truth_fn_for


class YawingDrone(SimDrone):
    """The point-mass sim drone never yaws; this one reports the last commanded heading."""
    yaw = None

    def goto_ned(self, n, e, d, yaw_deg=None):
        if yaw_deg is not None:
            self.yaw = yaw_deg
        super().goto_ned(n, e, d, yaw_deg)

    def state(self):
        st = super().state()
        return st if self.yaw is None else dataclasses.replace(st, yaw_deg=self.yaw)


def _rig(start, axis=True, axis_rel=0.0):
    cfg = load_config()
    drone = YawingDrone(*start)
    vision = SimVision(cfg, drone, build_world(SIM_REDS), SimQR(SIM_QRS))
    mission = {"_course_frame": COURSE, "origin": COURSE}
    if axis:
        mission["corridor_axis"] = {"axis_heading_deg": round(COURSE.abs_heading(axis_rel) % 360.0, 1)}
    ctx = MissionContext(stage_id="A5", title="A5", cfg=cfg.mission.stage_a.a5, full_cfg=cfg, bus=EventBus(), link=drone,
                         vision=vision, mission_state=mission, abort_event=threading.Event(),
                         truth_fn=truth_fn_for(drone, SIM_REDS, SIM_QRS))
    return drone, vision, ctx


@pytest.mark.parametrize("axis_rel", [0.0, 12.0])
def test_a5_backs_up_one_metre_along_the_axis(axis_rel):
    drone, vision, ctx = _rig((5.0, 0.0, 5.0), axis_rel=axis_rel)
    try:
        stage = StageA5()
        assert not [c for c in stage.preconditions(ctx) if c.blocking and not c.ok]
        f0, r0, up0 = COURSE.to_course(*drone.state().ned)
        assert stage.run(ctx)
        assert all(c.ok for c in ctx.report.criteria if c.blocking), [(c.name, c.value) for c in ctx.report.criteria if not c.ok]
        f1, r1, up1 = COURSE.to_course(*drone.state().ned)
        a = math.radians(axis_rel)
        back = -((f1 - f0) * math.cos(a) + (r1 - r0) * math.sin(a))
        side = -(f1 - f0) * math.sin(a) + (r1 - r0) * math.cos(a)
        assert back == pytest.approx(1.0, abs=0.25) and abs(side) <= 0.3 and abs(up1 - up0) <= 0.4
        assert ctx.mission["safety_backup"]["back_m"] == pytest.approx(1.0, abs=0.25)
    finally:
        vision.stop()


def test_a5_needs_the_corridor_axis_from_a4():
    drone, vision, ctx = _rig((5.0, 0.0, 5.0), axis=False)
    try:
        checks = {c.name: c for c in StageA5().preconditions(ctx)}
        assert not checks["Corridor axis measured (A4)"].ok and checks["Corridor axis measured (A4)"].blocking
        assert not StageA5().run(ctx)
    finally:
        vision.stop()
