"""usage: qr_error.py <log> [<log>...]   QR position error (vs the world truth) by drone speed, from the QRFIX log lines."""
import re, sys, math, statistics as st
sys.path.insert(0, '/home/jena/skyscan')
from worlds import make_worlds as W
cx, cy = 39.0, 0.0                     # dz_ahead field centre, yaw 0
truth = {k.upper(): (cx + v[0], cy + v[1]) for k, v in W.FIELD_QRS.items()}
pat = re.compile(r"QRFIX\s*\]\s+(\S+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+spd=([\d.]+)\s+tilt=([\d.]+)")
for f in sys.argv[1:]:
    rows = []
    for l in open(f, errors='ignore'):
        m = pat.search(l)
        if not m: continue
        d, x, y, spd, tilt = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5))
        key = re.sub(r'[^A-Za-z]', '', d).upper()[-1:]
        # payloads look like 'A', 'DZ-C' ...: take the last letter
        t = truth.get(key)
        if t is None: continue
        rows.append((math.hypot(x - t[0], y - t[1]), spd, tilt))
    print(f"== {f.split('/')[-1]}: {len(rows)} fixes")
    for name, lo, hi in (("hovering  (<0.3 m/s)", 0, 0.3), ("slow      (0.3-2)", 0.3, 2.0), ("moving    (>2 m/s)", 2.0, 99)):
        e = [r[0] for r in rows if lo <= r[1] < hi]
        if e:
            e.sort(); print(f"   {name}: n={len(e):3d}  median {st.median(e):.2f} m  p90 {e[int(0.9*(len(e)-1))]:.2f} m  max {e[-1]:.2f} m")
    tl = [r for r in rows if r[2] > 5]
    if tl: print(f"   tilted >5 deg: n={len(tl)} median err {st.median([r[0] for r in tl]):.2f} m")
