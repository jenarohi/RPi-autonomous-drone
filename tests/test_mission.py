"""Mission runner and stage execution unit tests."""
import threading
import time

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.mission.context import MissionContext
from skyscan.mission.runner import MissionRunner
from skyscan.mission.stage import Stage
from skyscan.types import Check, StageState, VehicleState


class MockLink:
    def __init__(self):
        self._st = VehicleState(link=True, armed=False, mode="GUIDED", ekf_ok=True, ned=(0.0, 0.0, 0.0), yaw_deg=90.0)

    def state(self):
        return self._st

    def set_mode(self, mode, timeout=5.0):
        self._st.mode = mode
        return True

    def arm(self, timeout=8.0):
        self._st.armed = True
        return True, "Armed"

    def disarm(self, force=False, timeout=5.0):
        self._st.armed = False
        return True

    def takeoff(self, alt):
        self._st.rel_alt_m = alt
        return 0

    def goto_ned(self, n, e, d, yaw_deg=None):
        self._st.ned = (n, e, d)
        if yaw_deg is not None:
            self._st.yaw_deg = yaw_deg

    def hold(self, force_guided=False):
        return True

    def set_gimbal(self, pitch_deg, yaw_deg=0.0):
        self._st.gimbal_pitch_deg = pitch_deg
        return True


class MockVision:
    def qr_reset(self):
        return 1

    def qr_status(self):
        from skyscan.types import QRPayload, QRStatus
        return QRStatus(confirmed="TARGET-C", payload=QRPayload(raw="TARGET-C", target="C", valid=True))

    def qr_latest(self):
        return None

    def banner_latest(self):
        from skyscan.types import BannerDetection
        return BannerDetection(t=time.time(), cam="front", seq=1, found=True, score=0.9, plane_ok=True, distance_m=4.0, lateral_m=0.0, yaw_err_deg=0.0)


def test_runner_executes_stages():
    cfg = load_config()
    bus = EventBus()
    link = MockLink()
    vision = MockVision()

    runner = MissionRunner(cfg, bus, link, vision)
    assert [s.id for s in runner.stages] == ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3",
                                              "E1", "E2", "E3", "E4", "E5", "E6"]
    desc = runner.describe()
    assert len(desc) == 22 and desc[0]["id"] == "A1" and desc[4]["id"] == "A5" and desc[5]["id"] == "B1" and desc[9]["id"] == "C1" and desc[13]["id"] == "D1"
    assert desc[5]["config"]["corridor_alt_m"] == 3.0       # stage_b config group is wired to B1..B4
    assert desc[9]["config"]["entry"] == [23.0, 0.0]        # stage_c config group is wired to C1..C4
    assert desc[13]["config"]["clearance_m"] == 3.0         # stage_d config group is wired to D1..D3
    assert desc[17]["config"]["max_search_m"] == 14.0       # stage_e config group is wired to E1..E6
    assert desc[21]["config"]["handover_alt_m"] == 1.0

    # Run A1
    ok, msg = runner.run(["A1"])
    assert ok
    time.sleep(1.0)
    runner.abort("test", hold=False, wait_s=1.0)
    assert not runner.busy


def test_preview_is_an_instant_go_nogo_per_stage():
    runner = MissionRunner(load_config(), EventBus(), MockLink(), MockVision())
    t0 = time.time()
    pre = runner.preview()
    assert time.time() - t0 < 1.0, "preview must never wait for the vehicle"
    assert list(pre) == ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3",
                                              "E1", "E2", "E3", "E4", "E5", "E6"]

    def go(sid):
        return all(c.ok for c in pre[sid] if c.blocking)

    assert go("A1")                      # on the ground, EKF ok, disarmed
    assert not go("A2")                  # no course frame yet
    assert not go("A3") and not go("A4") and not go("A5")
    assert not go("B1") and not go("B2") and not go("B3") and not go("B4")   # nothing flying, no lidar
    assert not go("C1") and not go("C2") and not go("C3") and not go("C4")   # nothing flying, no camera frames, no start QR
    assert not go("D1") and not go("D2") and not go("D3")                    # nothing flying, no course frame
    assert not any(go(f"E{i}") for i in range(1, 7))                         # nothing flying, no course frame
    assert any(c.name.startswith("Course frame") and not c.ok for c in pre["A2"])


def test_partial_run_keeps_the_reports_of_the_other_stages():
    runner = MissionRunner(load_config(), EventBus(), MockLink(), MockVision())
    runner._reports["A1"].state = StageState.SUCCESS
    runner._reports["A1"].message = "took off"
    ok, _ = runner.run(["A3"])          # NO-GO (no course frame) but must not touch A1
    assert ok
    while runner.busy:
        time.sleep(0.05)
    assert runner._reports["A1"].state == StageState.SUCCESS and runner._reports["A1"].message == "took off"
    assert runner._reports["A3"].state == StageState.NOGO
