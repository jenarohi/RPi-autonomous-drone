#!/usr/bin/env python3
"""
SkyScan - AeroTHON 2026 Mission 2 (autonomous).

  python3 run_mission.py --check        # link + sensors only, no arming
  python3 run_mission.py --view         # phase 1: QR -> green banner -> corridor, then RTL
  python3 run_mission.py --full --view  # + search, delivery, return corridor, landing
  python3 run_mission.py --stop-after FIND_BANNER   # stop earlier, then RTL
"""
import argparse
import math
import os
import sys

import numpy as np

from skyscan import config as C
from skyscan import vision
from skyscan.mission import Mission
from skyscan.missionlog import MissionLog
from skyscan.sensors import GzSensors
from skyscan.vehicle import Vehicle

STAGES = ["TAKEOFF", "SCAN_START_QR", "FIND_BANNER", "ALIGN_FORWARD", "CORRIDOR_FORWARD", "SEARCH", "DELIVER",
          "TO_RETURN_CORRIDOR", "ALIGN_RETURN", "CORRIDOR_RETURN"]


def check(vehicle: Vehicle, sensors: GzSensors, log):
    st = vehicle.state()
    log("CHECK", f"mode {st.mode}, armed {st.armed}, heading {math.degrees(st.heading):.0f} deg (ENU), "
                 f"alt {st.alt:.2f} m, on ground {vehicle.on_ground()}")
    img, _, _ = sensors.frame()
    log("CHECK", f"down camera {img.shape[1]}x{img.shape[0]}, QR codes in view: "
                 f"{[h.data for h in vision.decode_qrs(img)]}")
    log.snapshot("check_down_camera", img)
    front, _, _ = sensors.frame("front")
    green = int((vision.colour_mask(front, C.BANNER_COLOUR) > 0).sum())
    log("CHECK", f"front camera {front.shape[1]}x{front.shape[0]}, green pixels in view: {green}")
    log.snapshot("check_front_camera", front)
    pts, _, _ = sensors.scan()
    ang = np.degrees(np.arctan2(pts[:, 1], pts[:, 0])) if len(pts) else np.zeros(0)
    rng = np.hypot(pts[:, 0], pts[:, 1]) if len(pts) else np.zeros(0)
    for name, lo, hi in (("front", -20, 20), ("left", 70, 110), ("right", -110, -70)):
        sel = rng[(ang >= lo) & (ang <= hi)]
        log("CHECK", f"lidar {name:5s}: {sel.min():.2f} m" if sel.size else f"lidar {name:5s}: clear")
    log("CHECK", "OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=C.MAVLINK_URL, help="MAVLink connection (default %(default)s)")
    ap.add_argument("--check", action="store_true", help="check link + sensors, do not fly")
    ap.add_argument("--view", action="store_true", help="show the down camera with detections")
    ap.add_argument("--full", action="store_true",
                    help="fly the whole mission (default: phase 1 up to the green corridor exit)")
    ap.add_argument("--stop-after", choices=STAGES, help="end after this stage with RTL")
    ap.add_argument("--home", type=float, nargs=2, metavar=("X", "Y"),
                    help="world (x, y) of the take-off spot, only to label logs (default %s)" % (C.HOME_XY,))
    args = ap.parse_args()
    if args.home:
        C.HOME_XY = tuple(args.home)

    log = MissionLog(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
    log("MAIN", f"logs -> {log.dir}")
    vehicle = Vehicle(args.url, log)
    sensors = GzSensors(log)
    try:
        vehicle.connect()       # first: SITL only steps Gazebo once a client is connected
        sensors.start()
        if args.check:
            check(vehicle, sensors, log)
            return 0
        ok = Mission(vehicle, sensors, log, view=args.view).run(stop_after=args.stop_after, full=args.full)
        return 0 if ok else 1
    finally:
        vehicle.close()
        log.close()


if __name__ == "__main__":
    sys.exit(main())
