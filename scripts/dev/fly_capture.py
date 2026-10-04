#!/usr/bin/env python3
"""Fly the first Stage A stages in the real sim, then park and capture camera frames + state (calibration / fixtures).

    scripts/dev/box.sh cap --sim -- python scripts/dev/fly_capture.py --stages A1,A2 --gimbal=-15,-25,-35 --out /tmp/cap

For every gimbal pitch it writes <out>/front_<pitch>.png, down.png, overview.png and one line per capture in
<out>/captures.jsonl: vehicle state (NED, heading, altitude, reported gimbal pitch) and the simulator truth.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2  # noqa: E402

from skyscan.bus import EventBus  # noqa: E402
from skyscan.config import load_config  # noqa: E402
from skyscan.fc.link import MavLink  # noqa: E402
from skyscan.gz.bridge import GzBridge  # noqa: E402
from skyscan.gz.frames import FrameHub  # noqa: E402
from skyscan.mission.runner import MissionRunner  # noqa: E402
from skyscan.recorder import Recorder  # noqa: E402
from skyscan.sim.course import Course  # noqa: E402
from skyscan.sim.procman import ProcessManager  # noqa: E402
from skyscan.sim.truth import TruthComputer  # noqa: E402
from skyscan.vision.pipeline import VisionPipeline  # noqa: E402
from skyscan.config import repo_path  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="A1,A2")
    ap.add_argument("--gimbal", default="-25")
    ap.add_argument("--out", default="/tmp/cap")
    ap.add_argument("--settle", type=float, default=4.0, help="seconds to wait after each gimbal move")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--keep-flying", action="store_true", help="do not land at the end")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = load_config(None, overrides=[f"server.runs_dir={out}/runs", *args.set])
    bus, hub = EventBus(), FrameHub()
    bus.attach_loop(asyncio.get_running_loop())
    rec = Recorder(cfg, bus)
    rec.start()
    pm = ProcessManager(cfg, bus)
    await pm.start_sim()
    link = MavLink(cfg.mavlink, bus)
    link.start()
    gz = GzBridge(cfg, bus, hub)
    gz.start()
    vision = VisionPipeline(cfg, bus, hub, state_fn=link.state)
    vision.start()
    course = Course.from_yaml(repo_path(cfg.sim.course_file))
    tc = TruthComputer(course)
    runner = MissionRunner(cfg=cfg, bus=bus, link=link, vision=vision, recorder=rec, truth_fn=lambda: tc.compute(gz.truth()))

    try:
        t0 = time.time()
        while time.time() - t0 < 120:
            st = link.state()
            if st.link and st.ekf_ok and st.prearm_ok is not False:
                break
            await asyncio.sleep(1.0)
        print(f"vehicle ready after {time.time() - t0:.0f}s", flush=True)
        stages = [s for s in args.stages.split(",") if s]
        if stages:
            ok, msg = runner.run(stages)
            print("run:", ok, msg, flush=True)
            while runner.busy:
                await asyncio.sleep(1.0)
            for sid, rep in runner._reports.items():
                print(f"  {sid}: {rep.state}  {rep.message or ''}", flush=True)
        for pitch in [float(p) for p in args.gimbal.split(",") if p]:
            link.set_gimbal(pitch, 0.0)
            await asyncio.sleep(args.settle)
            st = link.state()
            for cam in ("front", "down", "overview"):
                f = hub.latest(cam)
                if f is not None:
                    name = f"front_{int(pitch)}.png" if cam == "front" else f"{cam}_{int(pitch)}.png"
                    cv2.imwrite(str(out / name), f.img)
            rec_line = {
                "gimbal_cmd": pitch,
                "gimbal_reported": st.gimbal_pitch_deg,
                "ned": st.ned,
                "heading": st.yaw_deg,
                "rel_alt": st.rel_alt_m,
                "roll": getattr(st, "roll_deg", None),
                "pitch": getattr(st, "pitch_deg", None),
                "truth": tc.compute(gz.truth()),
                "front_stats": hub.stats("front"),
            }
            print(json.dumps(rec_line, default=str), flush=True)
            with open(out / "captures.jsonl", "a") as fh:
                fh.write(json.dumps(rec_line, default=str) + "\n")
        if not args.keep_flying:
            link.land()
            await asyncio.sleep(2.0)
    finally:
        vision.stop()
        gz.stop()
        link.stop()
        await pm.stop_sim()
        rec.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
