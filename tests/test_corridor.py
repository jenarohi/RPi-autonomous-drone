"""Green-corridor detector: real Gazebo frames against simulator truth, plus synthetic geometry with known offsets."""
import json
import math
import time
from pathlib import Path
from types import SimpleNamespace as NS

import cv2
import numpy as np
import pytest

from skyscan.geo import CameraModel, cam_to_level
from skyscan.types import Frame
from skyscan.vision.corridor import CorridorDetector

DATA = Path(__file__).parent / "data" / "a2_front"
CAM = CameraModel.from_hfov(640, 480, 114.59)
HEIGHT_OFFSET = 0.07        # config cameras.front.height_offset_m


def _captures():
    return [json.loads(l) for l in (DATA / "captures.jsonl").read_text().splitlines() if l.strip()]


@pytest.mark.parametrize("cap", _captures(), ids=lambda c: f"pitch{int(c['gimbal_cmd'])}")
def test_real_frames_match_truth(cap):
    img = cv2.imread(str(DATA / f"front_{int(cap['gimbal_cmd'])}.png"))
    tr = cap["truth"]["corridor"]
    det = CorridorDetector(NS()).detect(Frame("front", 1, time.time(), img), CAM, cap["gimbal_reported"],
                                        cap["rel_alt"] + HEIGHT_OFFSET)
    assert det.found and det.plane_ok, det.reason
    assert det.kind == "floor"
    assert abs(det.distance_m - (-tr["along_axis_m"])) < 0.35
    assert abs(det.lateral_m - (-tr["lateral_m"])) < 0.15          # corridor centre line relative to the vehicle
    assert abs(det.yaw_err_deg - (-tr["yaw_err_deg"])) < 1.5       # corridor axis relative to the vehicle heading
    assert 3.0 < det.width_m < 3.8                                  # true width 3.5 m
    assert det.corners and len(det.corners) == 4


def test_no_green_is_not_found():
    img = np.full((480, 640, 3), 128, np.uint8)
    det = CorridorDetector(NS()).detect(Frame("front", 1, time.time(), img), CAM, -25.0, 5.0)
    assert not det.found and "no green" in det.reason


def test_unknown_height_is_not_found():
    img = np.zeros((480, 640, 3), np.uint8)
    det = CorridorDetector(NS()).detect(Frame("front", 1, time.time(), img), CAM, -25.0, None)
    assert not det.found


def _render_floor(pitch_deg, height, offset_right, yaw_deg, entrance=8.0, length=10.0, width=3.5):
    """Draw the corridor floor as the camera would see it, for a vehicle ``offset_right`` m right of the centre line
    (i.e. the centre line is at -offset_right) and heading ``yaw_deg`` clockwise of the corridor axis."""
    R = cam_to_level("gimbal", pitch_deg)
    ya = math.radians(-yaw_deg)          # axis heading relative to the vehicle = -(vehicle heading relative to axis)
    a = np.array([math.cos(ya), math.sin(ya)])
    n = np.array([-a[1], a[0]])
    # vehicle at origin; centre line is at lateral s = -offset_right, entrance along-axis t = entrance
    quad = []
    for t, s in ((entrance + length, -offset_right - width / 2), (entrance + length, -offset_right + width / 2),
                 (entrance, -offset_right + width / 2), (entrance, -offset_right - width / 2)):
        g = a * t + n * s
        p_cam = R.T @ np.array([g[0], g[1], height])
        uv = CAM.project(p_cam)
        assert uv is not None
        quad.append(uv)
    img = np.full((480, 640, 3), 150, np.uint8)
    cv2.fillPoly(img, [np.array(quad, dtype=np.int32)], (40, 200, 40))   # BGR green
    return img


@pytest.mark.parametrize("offset_right,yaw_deg,pitch", [(0.0, 0.0, -25), (1.0, 0.0, -25), (-1.2, 8.0, -30),
                                                        (0.6, -12.0, -20), (1.5, 15.0, -35)])
def test_synthetic_known_offsets(offset_right, yaw_deg, pitch):
    height = 5.07
    img = _render_floor(pitch, height, offset_right, yaw_deg)
    det = CorridorDetector(NS()).detect(Frame("front", 1, time.time(), img), CAM, pitch, height)
    assert det.found and det.plane_ok, det.reason
    # the centre line is `offset_right` to the vehicle's LEFT, perpendicular to the axis
    assert abs(det.yaw_err_deg - (-yaw_deg)) < 1.5
    assert abs(det.lateral_m - (-offset_right)) < 0.25
    assert abs(det.distance_m - 8.0) < 0.5
    assert abs(det.width_m - 3.5) < 0.4


def test_wrong_width_is_rejected():
    height = 5.07
    img = _render_floor(-25, height, 0.0, 0.0, width=7.0)       # a 7 m wide green strip is not our corridor
    det = CorridorDetector(NS()).detect(Frame("front", 1, time.time(), img), CAM, -25.0, height)
    assert det.found and not det.plane_ok and "width" in det.reason
