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


def _render_floor(pitch_deg, height, offset_right, yaw_deg, entrance=8.0, length=10.0, width=3.5, bgr=(40, 200, 40)):
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
    cv2.fillPoly(img, [np.array(quad, dtype=np.int32)], bgr)   # BGR, green unless asked otherwise
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


# ── the orange return corridor (Stage D): same geometry, other colour ────────────────────────────────────────────
ORANGE_BGR = (13, 140, 242)         # the sim floor rgb (0.95, 0.55, 0.05)
RED_BGR = (26, 26, 230)             # the sim no-land zones rgb (0.9, 0.1, 0.1)


def test_orange_corridor_is_measured_like_the_green_one():
    height, pitch = 10.07, -35
    img = _render_floor(pitch, height, 0.8, 6.0, entrance=10.0, bgr=ORANGE_BGR)
    det = CorridorDetector(NS())
    assert not det.detect(Frame("front", 1, time.time(), img), CAM, pitch, height).found     # green detector ignores orange
    assert det.set_colour("orange") and det.colour == "orange"
    d = det.detect(Frame("front", 2, time.time(), img), CAM, pitch, height)
    assert d.found and d.plane_ok, d.reason
    assert abs(d.distance_m - 10.0) < 0.5
    assert abs(d.lateral_m - (-0.8)) < 0.25
    assert abs(d.yaw_err_deg - (-6.0)) < 2.0
    assert 3.0 < d.width_m < 4.0
    assert det.set_colour("green") and not det.detect(Frame("front", 3, time.time(), img), CAM, pitch, height).found


def test_red_zone_is_not_mistaken_for_the_orange_corridor():
    img = _render_floor(-35, 10.07, 0.0, 0.0, entrance=10.0, bgr=RED_BGR)
    det = CorridorDetector(NS())
    det.set_colour("orange")
    d = det.detect(Frame("front", 1, time.time(), img), CAM, -35, 10.07)
    assert not d.found and "no orange" in d.reason


def test_unknown_colour_is_refused():
    det = CorridorDetector(NS())
    assert not det.set_colour("purple") and det.colour == "green"


# ── walls hiding part of the floor (return lap, seen from 10 m) ──────────────────────────────────────────────────
def _render_walled(pitch_deg, height, offset_right, yaw_deg, entrance, length=10.0, width=3.5, wall_h=5.0):
    """``_render_floor`` plus the two 5 m walls drawn over the floor, so the wall nearer the camera hides part of it."""
    R = cam_to_level("gimbal", pitch_deg)
    ya = math.radians(-yaw_deg)
    a = np.array([math.cos(ya), math.sin(ya)])
    n = np.array([-a[1], a[0]])

    def px(t, s, z=0.0):
        g = a * t + n * s
        return CAM.project(R.T @ np.array([g[0], g[1], height - z]))

    c = -offset_right
    img = _render_floor(pitch_deg, height, offset_right, yaw_deg, entrance=entrance, length=length, width=width,
                        bgr=ORANGE_BGR)
    for s in (c - width / 2, c + width / 2):
        wall = [px(entrance, s), px(entrance + length, s), px(entrance + length, s, wall_h), px(entrance, s, wall_h)]
        cv2.fillPoly(img, [np.array(wall, dtype=np.int32)], (110, 110, 110))
    return img


@pytest.mark.parametrize("offset_right,yaw_deg,entrance,pitch", [(3.62, -19.1, 10.0, -35), (4.0, -30.0, 14.0, -30),
                                                                 (-3.0, 20.0, 12.0, -35), (-2.5, 12.0, 10.0, -35),
                                                                 (0.0, 0.0, 10.0, -35)])
def test_walls_hiding_the_floor_do_not_bend_the_axis(offset_right, yaw_deg, entrance, pitch):
    # from off the centre line the near wall hides a wedge of floor whose edge points back at the camera; fitting
    # that edge as a wall base made D3 align 19 deg off the axis and 3.6 m off the centre line
    height = 10.07
    det = CorridorDetector(NS())
    det.set_colour("orange")
    img = _render_walled(pitch, height, offset_right, yaw_deg, entrance)
    d = det.detect(Frame("front", 1, time.time(), img), CAM, pitch, height)
    assert d.found and d.plane_ok, d.reason
    assert abs(d.yaw_err_deg - (-yaw_deg)) < 2.0
    assert abs(d.lateral_m - (-offset_right)) < 0.3
    assert abs(d.distance_m - entrance) < 0.5


def test_real_return_corridor_frame_seen_from_the_side():
    # live sim frame, D3 stand-off after a bad D2 axis: truth lateral +3.61 m, yaw -19.2 deg, 9.8 m to the entrance
    img = cv2.imread(str(Path(__file__).parent / "data" / "d3_orange" / "front_offset.jpg"))
    det = CorridorDetector(NS())
    det.set_colour("orange")
    d = det.detect(Frame("front", 1, time.time(), img), CAM, -35.0, 10.0 + HEIGHT_OFFSET)
    assert d.found and d.plane_ok, d.reason
    assert abs(d.lateral_m - (-3.61)) < 0.4
    assert abs(d.yaw_err_deg - 19.2) < 2.5
    assert abs(d.distance_m - 9.8) < 0.5
