"""End-to-end SITL test for Stage A (A1-A4) in Gazebo.

Requires the robotics box with Gazebo Harmonic and ArduCopter SITL.
Run with: scripts/dev/box.sh test --sim -- python -m pytest -s tests/test_sitl_stage_a.py -m sitl
"""
import asyncio
import os
import time
import pytest

from skyscan.bus import EventBus
from skyscan.config import load_config, repo_path
from skyscan.fc.link import MavLink
from skyscan.gz.bridge import GzBridge
from skyscan.gz.frames import FrameHub
from skyscan.mission.runner import MissionRunner
from skyscan.recorder import Recorder
from skyscan.sim.course import Course
from skyscan.sim.procman import ProcessManager
from skyscan.sim.truth import TruthComputer
from skyscan.types import StageState
from skyscan.utils.logger import get_logger
from skyscan.vision.pipeline import VisionPipeline

log = get_logger("TEST/SITL")


@pytest.mark.sitl
def test_full_stage_a_sitl(tmp_path):
    async def run_test():
        cfg = load_config(overrides=[
            f"server.runs_dir={tmp_path}",
            "sim.autostart=false",
            "mission.stage_a.a1.ready_timeout_s=90",
            "mission.stage_a.a1.climb_timeout_s=25",
            "mission.stage_a.a2.timeout_s=30",
            "mission.stage_a.a3.timeout_s=40",
            "mission.stage_a.a4.timeout_s=70",
        ])

        bus = EventBus()
        bus.attach_loop(asyncio.get_running_loop())
        hub = FrameHub()

        recorder = Recorder(cfg, bus)
        recorder.start()

        # Build world if missing
        from sim.build_world import build_world
        world_path = repo_path(cfg.sim.world_file)
        if not world_path.exists():
            build_world(out_file=world_path)

        procman = ProcessManager(cfg, bus)
        log.info("Starting simulation via procman...")
        await procman.start_sim()

        # Connect MAVLink
        link = MavLink(cfg.mavlink, bus)
        link.start()

        # Connect GzBridge & Vision
        gz = GzBridge(cfg, bus, hub)
        gz.start()

        vision = VisionPipeline(cfg, bus, hub, state_fn=link.state)
        vision.start()

        course_path = repo_path(cfg.sim.course_file)
        course = Course.from_yaml(course_path) if course_path.exists() else None
        truth_comp = TruthComputer(course)
        truth_fn = lambda: truth_comp.compute(gz.truth())

        runner = MissionRunner(
            cfg=cfg,
            bus=bus,
            link=link,
            vision=vision,
            recorder=recorder,
            truth_fn=truth_fn,
        )

        try:
            # Wait for vehicle link & EKF convergence
            log.info("Waiting for vehicle link and EKF readiness...")
            t0 = time.time()
            ready = False
            while time.time() - t0 < 100:
                st = link.state()
                elapsed = time.time() - t0
                if int(elapsed) % 5 == 0:
                    log.info(f"Readiness [{elapsed:.0f}s]: link={st.link} ekf_ok={st.ekf_ok} prearm={st.prearm_ok} sats={st.gps_sats} last_text='{st.last_text}'")
                if st.link and st.ekf_ok and st.prearm_ok is not False:
                    ready = True
                    log.info(f"Vehicle ready after {elapsed:.1f}s")
                    break
                await asyncio.sleep(1.0)

            assert ready, f"Vehicle failed to achieve EKF and PreArm readiness within 100s (ekf_ok={st.ekf_ok}, prearm={st.prearm_ok}, last_text='{st.last_text}')"

            # Execute Stage A (A1 to A4)
            log.info("Executing Stage A sequence: A1, A2, A3, A4")
            ok, run_msg = runner.run(["A1", "A2", "A3", "A4"])
            assert ok, f"Failed to start mission run: {run_msg}"

            # Wait for mission completion
            t_run = time.time()
            while time.time() - t_run < 240:
                if not runner.busy:
                    break
                await asyncio.sleep(1.0)

            assert not runner.busy, "Mission run timed out"

            # Verify results
            reports = runner._reports
            log.info(f"A1 state: {reports['A1'].state}")
            log.info(f"A2 state: {reports['A2'].state}")
            log.info(f"A3 state: {reports['A3'].state}")
            log.info(f"A4 state: {reports['A4'].state}")

            assert reports["A1"].state == StageState.SUCCESS, f"A1 failed: {reports['A1'].message}"
            assert reports["A2"].state == StageState.SUCCESS, f"A2 failed: {reports['A2'].message}"
            assert reports["A3"].state == StageState.SUCCESS, f"A3 failed: {reports['A3'].message}"
            assert reports["A4"].state == StageState.SUCCESS, f"A4 failed: {reports['A4'].message}"

            # Disarm & land at end of test
            link.land()
            await asyncio.sleep(3.0)

        finally:
            log.info("Cleaning up test and stopping processes...")
            if runner.busy:
                runner.abort("Test cleanup", hold=False, wait_s=1.0)
            vision.stop()
            gz.stop()
            link.stop()
            await procman.stop_sim()
            recorder.stop()

    asyncio.run(run_test())
