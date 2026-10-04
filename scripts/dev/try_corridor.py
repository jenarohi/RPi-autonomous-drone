import json, sys, time
from pathlib import Path
import cv2
sys.path.insert(0, ".")
from skyscan.geo import CameraModel
from skyscan.types import Frame
from skyscan.vision.corridor import CorridorDetector
from types import SimpleNamespace as NS

det = CorridorDetector(NS())
cam = CameraModel.from_hfov(640, 480, 114.59)
for line in open("tests/data/a2_front/captures.jsonl"):
    c = json.loads(line)
    pitch = c["gimbal_cmd"]
    img = cv2.imread(f"tests/data/a2_front/front_{int(pitch)}.png")
    tr = c["truth"]["corridor"]
    for off in (0.0, 0.07, 0.19):
        d = det.detect(Frame("front", 1, time.time(), img), cam, c["gimbal_reported"], c["rel_alt"] + off)
        print(f"pitch {pitch:5.0f} h+{off:4.2f}: found={d.found} dist={d.distance_m} (truth {-tr['along_axis_m']:.2f}) lat={d.lateral_m} (truth {-tr['lateral_m']:.2f}) yaw={d.yaw_err_deg} (truth {-tr['yaw_err_deg']:.1f}) width={d.width_m} clip={d.near_clipped} vis_len={d.length_visible_m} | {d.reason}")
    out = img.copy()
    if d.corners:
        import numpy as np
        cv2.polylines(out, [np.array(d.corners, dtype=np.int32)], True, (0,0,255), 1)
    cv2.imwrite(f"/tmp/try_{int(pitch)}.png", out)
