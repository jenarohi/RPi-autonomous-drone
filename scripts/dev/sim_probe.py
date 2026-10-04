#!/usr/bin/env python3
"""Start Gazebo (headless) + SITL through ProcessManager, grab one frame per camera, print RTF/truth, stop.

    scripts/dev/box.sh probe --sim -- python scripts/dev/sim_probe.py --out /tmp/probe [--hold 20]

Handy to eyeball the world and the cameras without running the whole mission-control server.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import cv2  # noqa: E402

from skyscan.bus import EventBus  # noqa: E402
from skyscan.config import load_config  # noqa: E402
from skyscan.gz.bridge import GzBridge  # noqa: E402
from skyscan.gz.frames import FrameHub  # noqa: E402
from skyscan.sim.procman import ProcessManager  # noqa: E402


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/probe")
    ap.add_argument("--hold", type=float, default=15.0, help="seconds to let the sim run before grabbing frames")
    ap.add_argument("--link", action="store_true", help="hold a MAVLink connection to SITL (like the real app does)")
    ap.add_argument("--set", action="append", default=[])
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cfg = load_config(None, overrides=args.set)
    bus, hub = EventBus(), FrameHub()
    lines: list[str] = []
    bus.add_listener(lambda m: lines.extend(f"[{m.get('src')}] {t}" for t in m.get("lines", [])) if m.get("t") == "log" else None)
    pm = ProcessManager(cfg, bus)
    gz = GzBridge(cfg, bus, hub)
    gz.start()
    t0 = time.time()
    await pm.start_sim()
    if args.link:
        import threading
        from pymavlink import mavutil

        def hold() -> None:
            m = mavutil.mavlink_connection("tcp:127.0.0.1:5760", source_system=245)
            m.wait_heartbeat(timeout=30)
            print("  MAVLink heartbeat ok", flush=True)
            while time.time() < t0 + args.hold + 20:
                m.recv_match(blocking=True, timeout=1)
        threading.Thread(target=hold, daemon=True).start()
    print(f"sim state={pm.status()['sim']} detail={pm.status()['detail']} after {time.time() - t0:.1f}s")
    t_end = time.time() + args.hold
    while time.time() < t_end:
        await asyncio.sleep(2.0)
        print(f"  t+{time.time() - t0:5.1f}s  stats={gz.world_stats()}  down={hub.stats('down')['seq']}", flush=True)
    for cam in ("down", "front", "overview"):
        f = hub.latest(cam)
        if f is None:
            print(f"{cam}: NO FRAME")
            continue
        cv2.imwrite(str(out / f"{cam}.png"), f.img)
        print(f"{cam}: {f.w}x{f.h} seq={f.seq} stats={hub.stats(cam)}")
    print("world stats:", gz.world_stats())
    print("truth:", gz.truth())
    await pm.stop_sim()
    gz.stop()
    print("---- last process output ----")
    print("\n".join(lines[-60:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
