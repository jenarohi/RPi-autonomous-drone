"""SkyScan mission control entry point.

Usage:
    python -m skyscan
    python -m skyscan --config config/skyscan.yaml --profile sim
    python -m skyscan --set mission.stage_a.a2.target_alt_m=5.0
"""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys
import time

from aiohttp import web

from skyscan import __version__
from skyscan.bus import EventBus
from skyscan.config import Cfg, load_config, repo_path
from skyscan.fc.link import MavLink
from skyscan.gz.bridge import GzBridge
from skyscan.gz.frames import FrameHub
from skyscan.mission.runner import MissionRunner
from skyscan.recorder import Recorder
from skyscan.server.app import Services, create_app
from skyscan.sim.course import Course
from skyscan.sim.procman import ProcessManager
from skyscan.sim.truth import TruthComputer
from skyscan.types import Sev
from skyscan.utils.logger import get_logger
from skyscan.vision.pipeline import VisionPipeline

log = get_logger("MAIN")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="skyscan",
        description="SkyScan Mission Control (AeroTHON 2026)",
    )
    parser.add_argument("--config", "-c", help="Path to config YAML (default: config/skyscan.yaml)")
    parser.add_argument("--profile", "-p", choices=["sim", "hw"], help="Override profile (sim|hw)")
    parser.add_argument("--set", "-s", action="append", default=[], help="Override tunables, e.g. --set server.port=8081")
    parser.add_argument("--no-browser", action="store_true", help="Do not launch browser UI")
    parser.add_argument("--version", action="version", version=f"SkyScan v{__version__}")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    overrides = list(args.set)
    if args.profile:
        overrides.append(f"profile={args.profile}")

    log.info(f"SkyScan v{__version__} starting up")
    cfg = load_config(args.config, overrides=overrides)
    profile = str(getattr(cfg, "profile", "sim"))
    log.info(f"Active profile: {profile.upper()}")

    bus = EventBus()
    hub = FrameHub()

    # Run recorder
    recorder = Recorder(cfg, bus)
    recorder.start()

    # MAVLink flight controller connection
    link = MavLink(cfg.mavlink, bus)
    link.start()

    # Vision processing pipeline
    vision = VisionPipeline(cfg, bus, hub, state_fn=link.state)
    vision.start()

    # Course layout & ground-truth computer
    course_path = repo_path(getattr(cfg.sim, "course_file", "sim/course.yaml"))
    course = Course.from_yaml(course_path) if course_path.exists() else None
    truth_comp = TruthComputer(course)

    procman: ProcessManager | None = None
    gz: GzBridge | None = None
    truth_fn = None

    if profile == "sim":
        procman = ProcessManager(cfg, bus)
        gz = GzBridge(cfg, bus, hub)
        gz.start()
        truth_fn = lambda: truth_comp.compute(gz.truth())

    runner = MissionRunner(
        cfg=cfg,
        bus=bus,
        link=link,
        vision=vision,
        recorder=recorder,
        truth_fn=truth_fn,
    )

    services = Services(
        cfg=cfg,
        bus=bus,
        hub=hub,
        link=link,
        runner=runner,
        vision=vision,
        procman=procman,
        gz=gz,
        recorder=recorder,
        course=course.to_dict() if course else None,
        truth_fn=truth_fn,
        profile=profile,
    )

    app = create_app(services)

    # Autostart simulation if configured
    if profile == "sim" and getattr(cfg.sim, "autostart", False) and procman:
        async def autostart_sim(app: web.Application) -> None:
            log.info("Autostarting simulation stack...")
            asyncio.create_task(procman.start_sim())
        app.on_startup.append(autostart_sim)

    # Clean shutdown
    async def cleanup(app: web.Application) -> None:
        log.info("Shutdown sequence initiated")
        if runner.busy:
            runner.abort("Server shutdown", hold=True, wait_s=1.0)
        vision.stop()
        link.stop()
        if gz:
            gz.stop()
        if procman:
            await procman.stop_sim()
        recorder.stop()
        log.info("SkyScan shutdown complete")

    app.on_cleanup.append(cleanup)

    host = str(cfg.server.host)
    port = int(cfg.server.port)
    log.info(f"Serving SkyScan Mission Control at http://{host}:{port}")
    bus.event("SYS", f"SkyScan v{__version__} server ready on http://{host}:{port}", Sev.GOOD)

    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    main()
