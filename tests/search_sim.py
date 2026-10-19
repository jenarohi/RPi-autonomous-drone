"""
Offline simulation of the delivery search planner (no Gazebo): QR codes inside the
usable picture of a stop are read; the scout spots codes within its range ahead.
Used by the tests and runnable on its own:  python3 -m tests.search_sim
"""
import math

from skyscan import config as C
from skyscan import vision
from skyscan.searchmap import HeatMap

FIELD_QRS = {"a": (-17, 10), "b": (-9, -8), "c": (-1, 5), "d": (7, -12), "e": (15, 9),
             "f": (-18.5, -13.5), "g": (18.5, -1)}
LAYOUTS = {"dz_ahead": ((39.0, 0.0), 0.0, "c"), "dz_side": ((36.0, 24.0), 0.0, "g"),
           "dz_rot": ((45.0, -4.0), 30.0, "f"), "dz_far": ((58.0, 8.0), -15.0, "e")}
EXIT, EXIT_HDG = (17.4, 3.0), 0.0


def qr_world(centre, yaw_deg):
    a = math.radians(yaw_deg)
    return {k: (centre[0] + x * math.cos(a) - y * math.sin(a), centre[1] + x * math.sin(a) + y * math.cos(a))
            for k, (x, y) in FIELD_QRS.items()}


def in_picture(p, stop, hdg, along, across):
    dx, dy = p[0] - stop[0], p[1] - stop[1]
    f = dx * math.cos(hdg) + dy * math.sin(hdg)
    l = -dx * math.sin(hdg) + dy * math.cos(hdg)
    return abs(f) <= along / 2 and abs(l) <= across / 2


def run(layout, scout=True, max_stops=30):
    centre, yaw, target = LAYOUTS[layout]
    qrs = qr_world(centre, yaw)
    cam = vision.DownCam(2304, 1296)
    along, across = cam.footprint(C.ALT_SEARCH + C.CAM_HEIGHT_OFFSET)
    # codes are read anywhere in the picture except a 1 m edge band (pessimistic)
    ra, rc = along - 2.0, across - 2.0
    hm = HeatMap(EXIT, EXIT_HDG)
    here, hdg, t, read = EXIT, EXIT_HDG, 0.0, set()

    def look(p, h):
        for k, q in qrs.items():
            if k not in read and in_picture(q, p, h, ra, rc):
                read.add(k)
                hm.qr_found(q)
        hm.seen_picture(p, h, along, across)

    look(here, hdg)
    if scout:
        for q in qrs.values():
            u, v = hm.to_uv(q)
            if u >= 1 and math.hypot(u, v) <= C.SCOUT_MAX_RANGE and abs(math.atan2(v, u)) <= math.radians(130):
                hm.pin(q, C.SEARCH_PIN_WEIGHT)
    start = hm.total()
    stops = [here]
    while target not in read and len(stops) <= max_stops:
        best = hm.best_stop(here, hdg, along, across)
        if best is None or best[2] < C.SEARCH_MIN_GAIN:
            break
        p, h, _, _ = best
        leg = math.hypot(p[0] - here[0], p[1] - here[1])
        t += leg / C.SPEED_SEARCH + C.SEARCH_STOP_TIME
        n = int(leg // C.SEARCH_TRANSIT_STEP)          # codes read / ground checked on the way
        for i in range(1, n + 1):
            q = (here[0] + (p[0] - here[0]) * i / (n + 1), here[1] + (p[1] - here[1]) * i / (n + 1))
            hdg_leg = h                                  # yawing to the stop heading on the way
            for k, c in qrs.items():
                if k not in read and in_picture(c, q, hdg_leg, along - 4.0, across - 4.0):
                    read.add(k)
                    hm.qr_found(c)
            hm.seen(q, hdg_leg, along, across, C.SEARCH_TRANSIT_FACTOR)
        here, hdg = p, h
        stops.append(p)
        look(p, h)
    return target in read, len(stops) - 1, t, sorted(read)


if __name__ == "__main__":
    for name in LAYOUTS:
        for scout in (True, False):
            ok, n, t, read = run(name, scout)
            print(f"{name:9s} scout={'on ' if scout else 'off'} -> target {'FOUND' if ok else 'missed'} "
                  f"after {n} stops, ~{t:.0f}s flying+stops, read {read}")
