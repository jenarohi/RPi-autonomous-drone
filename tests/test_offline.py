"""Offline tests - no Gazebo / SITL needed.   cd ~/skyscan && python3 -m pytest -q"""
import math
import os

import cv2
import numpy as np
import pytest

from skyscan import config as C
from skyscan import lidar, vision
from skyscan.geometry import (CorridorAxis, Rect, body_to_world, lawnmower, plan_path, push_out,
                              segment_clear, segment_hits_rect, wrap_pi)
from tests.sim2d import GREEN, ORANGE, run_corridor

TEX = os.path.expanduser("~/gz_ws/src/aerothon_world/textures")
ZONE_SIM = (19.0, 59.0, -15.0, 15.0)        # delivery field of create_world.py (tests only)


# ── geometry ───────────────────────────────────────────────────────────────
def test_wrap_and_body_to_world():
    assert abs(wrap_pi(3 * math.pi) - math.pi) < 1e-9 or abs(wrap_pi(3 * math.pi) + math.pi) < 1e-9
    x, y = body_to_world(0, 0, 0.0, 1.0, 2.0)          # facing east: right = south
    assert (round(x, 6), round(y, 6)) == (1.0, -2.0)
    x, y = body_to_world(0, 0, math.pi, 1.0, 2.0)      # facing west: right = north
    assert (round(x, 6), round(y, 6)) == (-1.0, 2.0)


def test_corridor_axis_round_trip_and_realign():
    ax = CorridorAxis.from_config(ORANGE)              # flown westwards
    assert abs(ax.length - 10) < 1e-9 and abs(abs(ax.heading) - math.pi) < 1e-9
    s, d = ax.to_sd(*ax.from_sd(3.0, 0.5))
    assert abs(s - 3.0) < 1e-9 and abs(d - 0.5) < 1e-9
    s, d = ax.to_sd(11.0, -2.0)                        # 1 m north of centre = right when flying west
    assert abs(s - 5.0) < 1e-9 and abs(d + 1.0) < 1e-9
    moved = ax.realigned((10.0, -2.8), ax.heading)
    assert abs(moved.to_sd(10.0, -2.8)[1]) < 1e-9 and abs(moved.length - 10) < 1e-9


def test_rect_segment_and_planner():
    r = Rect(0, 2, 0, 2)
    assert segment_hits_rect((-1, 1), (3, 1), r)
    assert not segment_hits_rect((-1, 3), (3, 3), r)
    assert not segment_hits_rect((-1, 2), (3, 2), r)       # grazing an edge is fine
    zones = [Rect(24.5, 27.5, 4.5, 7.5).inflate(1.5)]
    path = plan_path((20, 6), (32, 6), zones)
    pts = [(20, 6)] + path
    assert all(segment_clear(a, b, zones) for a, b in zip(pts, pts[1:]))
    assert path[-1] == (32, 6) and len(path) >= 2
    assert plan_path((20, 6), (26, 6), zones) is None       # goal inside a zone
    p = push_out((26, 6.5), zones)
    assert not any(z.contains(p) for z in zones)


def test_lawnmower_covers_zone():
    wps = lawnmower(ZONE_SIM, 8.0, 4.0, 3.0, (17.5, 3.0))
    ys = sorted({y for _, y in wps})
    assert ys[0] - 4.0 <= ZONE_SIM[2] + 1e-6 and ys[-1] + 4.0 >= ZONE_SIM[3] - 1e-6
    assert all(b - a <= 8.0 + 1e-6 for a, b in zip(ys, ys[1:]))
    assert wps[0][0] == ZONE_SIM[0] + 3.0             # starts at the west end


# ── vision ─────────────────────────────────────────────────────────────────
def _scene(png, side_px, centre=(320, 240), blur=1.0, size=(480, 640)):
    img = np.full(size + (3,), 200, np.uint8)
    qr = cv2.imread(os.path.join(TEX, png))
    qr = cv2.resize(qr, (side_px, side_px), interpolation=cv2.INTER_AREA)
    x0, y0 = centre[0] - side_px // 2, centre[1] - side_px // 2
    img[y0:y0 + side_px, x0:x0 + side_px] = qr
    return cv2.GaussianBlur(img, (0, 0), blur) if blur else img


@pytest.mark.skipif(not os.path.isdir(TEX), reason="QR textures not found")
@pytest.mark.parametrize("alt", [5.0, 10.0])
def test_decode_qr_at_mission_altitudes(alt):
    cam = vision.DownCam(2304, 1296)                  # Pi Cam 3 Wide, binned full-FOV mode
    side = int(round(1.0 / cam.metres_per_px(alt + C.CAM_HEIGHT_OFFSET)))   # 1 m QR
    hits = vision.decode_qrs(_scene("qr_c.png", side, centre=(1400, 300), size=(1296, 2304)))
    assert [h.data for h in hits] == ["C"]
    assert abs(hits[0].u - 1400) < 4 and abs(hits[0].v - 300) < 4
    start = vision.decode_qrs(_scene("qr_start.png", side, centre=(1152, 648), size=(1296, 2304)))
    assert vision.parse_start_qr(start[0].data) == "C"


def test_parse_start_qr():
    assert vision.parse_start_qr("TARGET:C") == "C"
    assert vision.parse_start_qr(" target = b ") == "B"
    assert vision.parse_start_qr("C") is None


def test_pixel_to_ground():
    cam = vision.DownCam()
    f, r = cam.pixel_to_ground(cam.cx, cam.cy - 100, 5.0)          # 100 px up = forward
    assert abs(f - 100 * 5.0 / cam.f) < 1e-9 and abs(r) < 1e-9
    f, r = cam.pixel_to_ground(cam.cx, cam.cy, 5.0, pitch=math.radians(10))   # nose up looks ahead
    assert abs(f - 5.0 * math.tan(math.radians(10))) < 1e-6
    f, r = cam.pixel_to_ground(cam.cx, cam.cy, 5.0, roll=math.radians(10))    # right wing down looks left
    assert r < 0


@pytest.mark.parametrize("offset_m,angle_deg", [(0.0, 0.0), (0.6, 0.0), (-0.4, 5.0), (0.3, -8.0)])
def test_floor_axis_recovers_offset_and_angle(offset_m, angle_deg):
    cam = vision.DownCam()
    h = 5.645
    mpp = cam.metres_per_px(h)
    img = np.full((480, 640, 3), 128, np.uint8)
    # green strip 3.5 m wide whose centre line is offset_m right of the drone and
    # rotated angle_deg to the right of the nose; floor starts 40 px below the top
    a = math.radians(angle_deg)
    for v in range(40, 480):
        fwd = (cam.cy - v) * mpp
        centre = offset_m + fwd * math.tan(a)
        half = 1.75 / math.cos(a)
        u0, u1 = cam.cx + (centre - half) / mpp, cam.cx + (centre + half) / mpp
        img[v, max(0, int(u0)):min(640, int(u1))] = (25, 204, 25)
    fa = vision.floor_axis(img, "green")
    lat, ang, width = vision.floor_measurement(fa, cam, h)
    assert abs(lat - offset_m) < 0.05
    assert abs(math.degrees(ang) - angle_deg) < 1.0
    assert abs(width - 3.5 / math.cos(a)) < 0.15


def test_red_regions():
    img = np.full((480, 640, 3), 200, np.uint8)
    cv2.rectangle(img, (100, 100), (180, 170), (25, 25, 230), -1)
    regs = vision.red_regions(img)
    assert len(regs) == 1
    xs, ys = regs[0][:, 0], regs[0][:, 1]
    assert abs(xs.min() - 100) < 3 and abs(ys.max() - 170) < 3


# ── lidar ──────────────────────────────────────────────────────────────────
def _walls(left=1.65, right=1.65):
    a = np.linspace(-6, 6, 241)
    return np.vstack([np.column_stack((a, np.full_like(a, left))),
                      np.column_stack((a, np.full_like(a, -right)))])


def test_plan_step_centres_in_empty_corridor():
    st = lidar.plan_step(_walls())
    assert abs(st.target) < 0.05 and math.isinf(st.clear)
    st = lidar.plan_step(_walls(left=1.0, right=2.3))   # drone 0.65 m left of centre
    assert st.target < -0.5


def test_plan_step_sidesteps_obstacle():
    obstacle = np.column_stack((np.full(20, 2.0), np.linspace(-0.6, 0.2, 20)))   # 1.45 m gap on the left
    st = lidar.plan_step(np.vstack([_walls(), obstacle]))
    assert abs(st.target) > 0.6 and st.clear < 2.1
    assert lidar.forward_speed(st) < 0.5


def test_scan_to_points_drops_self_hits():
    pts = lidar.scan_to_points([0.2, 1.0, float("inf")], -0.1, 0.1)
    assert len(pts) == 1 and abs(pts[0][0] - 1.0) < 1e-9


@pytest.mark.parametrize("cfg", [GREEN, ORANGE], ids=["green", "orange"])
@pytest.mark.parametrize("offset,yaw", [(0.0, 0.0), (0.7, -6.0), (-0.7, 6.0)])
def test_corridor_kinematic_sim(cfg, offset, yaw):
    """Locked heading off by `yaw`: walls must pull it back, exit must be found by LiDAR."""
    r = run_corridor(cfg, offset, yaw, tau=0.6, noise=0.03)
    assert r["ok"], "exit never detected"
    assert r["min_clear"] > C.DRONE_RADIUS + 0.15
    assert 10.5 < r["exit_s"] < 12.5                 # corridor is 10 m long
    assert abs(r["heading_err"]) < 2.5


def test_wall_angle():
    a = np.linspace(-1.5, 3.0, 60)
    rot = math.radians(6)                            # walls turned 6 deg CCW
    left = np.column_stack((a, 1.6 + a * math.tan(rot)))
    right = np.column_stack((a, -1.7 + a * math.tan(rot)))
    assert abs(math.degrees(lidar.wall_angle(np.vstack([left, right]))) - 6) < 0.3
    blob = np.column_stack((np.full(20, 1.0), np.linspace(0.5, 1.5, 20)))   # obstacle beside us
    # the left side is no longer one straight wall -> ignored, the right wall still gives the angle
    assert abs(math.degrees(lidar.wall_angle(np.vstack([left, blob, right]))) - 6) < 0.3
    assert lidar.wall_angle(np.vstack([left, blob])) is None


def test_front_camera_projection():
    cam = vision.FrontCam()
    f, r = cam.pixel_to_ground(cam.cx, cam.cy, 5.0)  # optical axis 45 deg down
    assert abs(f - 5.0) < 1e-6 and abs(r) < 1e-9
    assert cam.pixel_to_ground(cam.cx, 0, 5.0) is None or cam.pixel_to_ground(cam.cx, 0, 5.0)[0] > 5
    f_up, _ = cam.pixel_to_ground(cam.cx, cam.cy, 5.0, pitch=math.radians(5))
    assert f_up > 5.0                                 # nose up looks further


@pytest.mark.parametrize("offset,angle_deg", [(0.0, 0.0), (0.8, 10.0), (-1.0, -15.0)])
def test_front_camera_finds_corridor(offset, angle_deg):
    """Render a 3.5 m green strip on the ground as the 45 deg camera sees it, then
    recover its centre line from the projected rows."""
    cam = vision.FrontCam()
    h = 5.7
    a = math.radians(angle_deg)
    img = np.full((480, 640, 3), 128, np.uint8)
    for v in range(480):
        for u in range(0, 640, 1):
            g = cam.pixel_to_ground(u, v, h)
            if g is None:
                continue
            f, r = g
            along = f * math.cos(a) + (r - offset) * math.sin(a)
            lat = -f * math.sin(a) + (r - offset) * math.cos(a)
            if 3.0 < along < 13.0 and abs(lat) < 1.75:
                img[v, u] = (25, 204, 25)
    pts = vision.floor_ground_points(img, "green", cam, h, 0.0, 0.0, 3.5)
    assert len(pts) > 30
    c = pts.mean(axis=0)
    d = np.linalg.svd(pts - c)[2][0]
    d = d if d[0] > 0 else -d
    assert abs(math.degrees(math.atan2(d[1], d[0])) - angle_deg) < 1.5
    lat0 = c[1] - c[0] * d[1] / d[0]                 # centre line at forward = 0
    assert abs(lat0 - offset) < 0.15


def test_floor_measurement_compensates_tilt():
    cam = vision.DownCam()
    fa = vision.FloorAxis(u_centre=cam.cx, slope=0.0, width_px=330, rows=50, v_lo=0, v_hi=120)
    lat, ang, _ = vision.floor_measurement(fa, cam, 5.6)
    assert abs(lat) < 1e-9 and abs(ang) < 1e-9
    # right wing down 5 deg: the image centre column looks at the ground to the LEFT
    lat, ang, _ = vision.floor_measurement(fa, cam, 5.6, roll=math.radians(5))
    assert abs(lat + 5.6 * math.tan(math.radians(5))) < 0.03
    assert abs(math.degrees(ang)) < 0.5


# ── green ground map (corridor search) ─────────────────────────────────────
def _render_ground(cam, x, y, alt, heading, rects):
    """Front-camera image of flat coloured rectangles (cx, cy, length, width, yaw_deg)
    on a grey ground, drone at (x, y, alt) facing `heading`."""
    vs, us = np.mgrid[0:480, 0:640]
    f, r, ok = cam.ground_points(us.ravel().astype(float), vs.ravel().astype(float),
                                 alt + C.FRONT_CAM_HEIGHT_OFFSET)
    c, s = math.cos(heading), math.sin(heading)
    wx, wy = x + f * c + r * s, y + f * s - r * c
    img = np.full((480 * 640, 3), 128, np.uint8)
    for cx, cy, L, W, yaw in rects:
        a = math.radians(yaw)
        along = (wx - cx) * math.cos(a) + (wy - cy) * math.sin(a)
        lat = -(wx - cx) * math.sin(a) + (wy - cy) * math.cos(a)
        img[ok & (np.abs(along) < L / 2) & (np.abs(lat) < W / 2)] = (25, 204, 25)
    return img.reshape(480, 640, 3)


def _feed(gmap, cam, x, y, alt, headings, rects, frames=2):
    for hdg in headings:
        img = _render_ground(cam, x, y, alt, math.radians(hdg), rects)
        g = vision.colour_ground_samples(img, "green", cam, alt + C.FRONT_CAM_HEIGHT_OFFSET, 0, 0, 25.0)
        h = math.radians(hdg)
        for _ in range(frames):
            gmap.add(np.column_stack([x + g[:, 0] * math.cos(h) + g[:, 1] * math.sin(h),
                                      y + g[:, 0] * math.sin(h) - g[:, 1] * math.cos(h)]))


def test_ground_map_finds_rotated_corridor_from_the_side():
    from skyscan.groundmap import GroundMap
    cam = vision.FrontCam()
    yaw = 12.0                                         # corridor rotated 12 deg, entrance at (6, 3)
    a = math.radians(yaw)
    corridor = (6 + 5 * math.cos(a), 3 + 5 * math.sin(a), 10.0, 3.5, yaw)
    start = (-3.0, -4.0)
    gm = GroundMap(start)
    _feed(gm, cam, *start, 7.0, [0, 45], [corridor])
    strips, _, notes = gm.strips(3.5, C.BANNER_MIN_LENGTH, start)
    assert len(strips) == 1, notes
    s = strips[0]
    assert dist_ok(s.entry, (6.0, 3.0), 0.6)
    assert abs(math.degrees(s.heading) - yaw) < 4.0
    assert 2.8 < s.width < 4.3


def test_ground_map_rejects_grass_and_mats():
    from skyscan.groundmap import GroundMap
    cam = vision.FrontCam()
    grass = (6.0, 0.0, 10.0, 8.0, 0.0)                 # big green patch
    mat = (6.0, 9.0, 5.0, 1.5, 70.0)                   # narrow tarp
    gm = GroundMap((0.0, 0.0))
    _feed(gm, cam, 0.0, 0.0, 10.0, [0, 45], [grass, mat])
    strips, _, notes = gm.strips(3.5, C.BANNER_MIN_LENGTH, (0.0, 0.0))
    assert strips == [], [s.describe() for s in strips]
    assert any("too wide" in n for n in notes) and any("narrow" in n or "partly" in n for n in notes)


def test_ground_map_partial_and_rejected():
    from skyscan.groundmap import GroundMap
    cam = vision.FrontCam()
    stub = (14.0, 0.0, 2.5, 3.5, 0.0)                  # only 2.5 m of strip visible
    gm = GroundMap((0.0, 0.0))
    _feed(gm, cam, 0.0, 0.0, 5.5, [0], [stub])
    strips, partial, _ = gm.strips(3.5, C.BANNER_MIN_LENGTH, (0.0, 0.0))
    assert strips == [] and len(partial) == 1 and dist_ok(partial[0], (14.0, 0.0), 0.8)
    full = (16.0, 0.0, 10.0, 3.5, 0.0)
    gm = GroundMap((0.0, 0.0))
    _feed(gm, cam, 0.0, 0.0, 7.0, [0], [full])
    strips, _, _ = gm.strips(3.5, C.BANNER_MIN_LENGTH, (0.0, 0.0))
    assert len(strips) == 1
    strips, _, notes = gm.strips(3.5, C.BANNER_MIN_LENGTH, (0.0, 0.0), rejected=[strips[0].entry])
    assert strips == [] and any("rejected earlier" in n for n in notes)


def dist_ok(p, q, tol):
    return math.hypot(p[0] - q[0], p[1] - q[1]) < tol


@pytest.mark.parametrize("ahead,offset,angle_deg", [(0.7, 0.0, 0.0), (1.2, 0.5, 8.0), (0.9, -0.6, -12.0)])
def test_entrance_edge_from_outside(ahead, offset, angle_deg):
    """Down camera at 5 m outside a corridor: the near floor edge gives the entrance
    centre (ahead / right) and the corridor direction."""
    cam = vision.DownCam()
    h = 5.0 + C.CAM_HEIGHT_OFFSET
    a = math.radians(angle_deg)                       # axis to the RIGHT of the nose
    vs, us = np.mgrid[0:480, 0:640]
    f, r, ok = cam.ground_points(us.ravel().astype(float), vs.ravel().astype(float), h)
    t = (math.cos(a), math.sin(a))                    # (fwd, right) along the axis
    along = (f - ahead) * t[0] + (r - offset) * t[1]
    lat = -(f - ahead) * t[1] + (r - offset) * t[0]
    img = np.full((480 * 640, 3), 128, np.uint8)
    img[ok & (along > 0) & (along < 10) & (np.abs(lat) < 1.65)] = (25, 204, 25)
    e = vision.entrance_edge(img.reshape(480, 640, 3), "green", cam, h)
    assert e is not None
    assert abs(e.fwd - ahead) < 0.08 and abs(e.right - offset) < 0.08
    assert abs(math.degrees(e.angle) - angle_deg) < 1.5
    assert abs(e.width - 3.3) < 0.15


def test_snap_grid_covers_zone_with_few_stops():
    from skyscan.geometry import snap_grid
    cam = vision.DownCam(2304, 1296)
    along, across = cam.footprint(10.0 + C.CAM_HEIGHT_OFFSET)
    assert 24 < across < 26 and 13 < along < 15           # Pi Cam 3 Wide from 10 m
    zone = (19.0, 59.0, -15.0, 15.0)
    pts, hdg = snap_grid(zone, C.SEARCH_USABLE * across, C.SEARCH_USABLE * along, (17.0, 3.0))
    assert len(pts) == 6 and abs(hdg - math.pi / 2) < 1e-9
    assert pts[0][0] < 39 and pts[0][1] > 0                # starts at the corner nearest the entry
    fx, fy = C.SEARCH_USABLE * across, C.SEARCH_USABLE * along     # heading north: width along x
    for x in np.linspace(19, 59, 41):                      # every point of the zone is in a footprint
        for y in np.linspace(-15, 15, 31):
            assert any(abs(x - px) <= fx / 2 + 1e-6 and abs(y - py) <= fy / 2 + 1e-6 for px, py in pts)


def test_red_vote_map_gives_true_size():
    """3 x 3 m red square seen from 10 m by the wide down camera, from three spots and
    with a little attitude error: the voted box stays close to the real square."""
    from skyscan.groundmap import GroundMap
    cam = vision.DownCam(640, 360)
    h = 10.0 + C.CAM_HEIGHT_OFFSET
    zone = (24.5, 27.5, 4.5, 7.5)
    gm = GroundMap((26.0, 6.0), half_size=30.0, res=0.25)
    vs, us = np.mgrid[0:360, 0:640]
    for (x, y), roll in (((24.0, 4.0), 0.01), ((28.0, 6.0), -0.01), ((26.0, 9.0), 0.0)):
        f, r, ok = cam.ground_points(us.ravel().astype(float), vs.ravel().astype(float), h, roll, 0.0)
        wx, wy = x + f * 0.0 + r * 1.0, y + f * 1.0 - r * 0.0          # heading north
        img = np.full((360 * 640, 3), 128, np.uint8)
        img[ok & (wx > zone[0]) & (wx < zone[1]) & (wy > zone[2]) & (wy < zone[3])] = (25, 25, 230)
        g = vision.colour_ground_samples(img.reshape(360, 640, 3), 'red', cam, h, 0.0, 0.0, h, step=3)
        gm.add(np.column_stack([x + g[:, 1], y + g[:, 0]]))
    boxes = gm.boxes(3, 0.5)
    assert len(boxes) == 1
    b = boxes[0]
    assert all(abs(b[i] - zone[i]) < 0.5 for i in range(4)), b


def _render_front_qrs(cam, alt, qrs, reds=()):
    """Front-camera image from (0, 0, alt) facing +x of flat 1 m QR textures at (x, y)
    (forward, LEFT) and 3 m red squares, on grey ground. Texture is point-sampled."""
    tex = cv2.imread(os.path.join(TEX, "qr_c.png"))
    vs, us = np.mgrid[0:cam.h, 0:cam.w]
    f, r, ok = cam.ground_points(us.ravel().astype(float), vs.ravel().astype(float),
                                 alt + C.FRONT_CAM_HEIGHT_OFFSET)
    img = np.full((cam.h * cam.w, 3), 128, np.uint8)
    for x, y in qrs:
        lx, ly = f - (x - 0.5), (-r) - (y - 0.5)            # world left = -right
        inside = ok & (lx >= 0) & (lx < 1) & (ly >= 0) & (ly < 1)
        ti = np.clip((lx[inside] * tex.shape[0]).astype(int), 0, tex.shape[0] - 1)
        tj = np.clip((ly[inside] * tex.shape[1]).astype(int), 0, tex.shape[1] - 1)
        img[inside] = tex[ti, tj]
    for x, y in reds:
        img[ok & (np.abs(f - x) < 1.5) & (np.abs(-r - y) < 1.5)] = (25, 25, 230)
    return img.reshape(cam.h, cam.w, 3)


@pytest.mark.skipif(not os.path.isdir(TEX), reason="QR textures not found")
def test_qr_scout_spots_codes_far_away():
    cam = vision.FrontCam()
    qrs = [(12.0, 2.0), (18.0, -5.0), (24.0, 6.0)]
    img = _render_front_qrs(cam, 10.0, qrs, reds=[(15.0, 6.0)])
    pins = vision.qr_scout(img, cam, 10.0 + C.FRONT_CAM_HEIGHT_OFFSET)
    found = [p for p in pins]
    for x, y in qrs:                                         # every code spotted within ~2 m
        assert any(math.hypot(fx - x, -fr - y) < 2.0 for fx, fr in found), (x, y, found)
    assert not any(math.hypot(fx - 15.0, -fr - 6.0) < 2.5 for fx, fr in found)   # red zone ignored
    assert len(found) <= len(qrs) + 1


# ── delivery search without zone coordinates ──────────────────────────────
def test_heat_map_basics():
    from skyscan.searchmap import HeatMap
    hm = HeatMap((17.4, 3.0), 0.0)
    H = hm.heat()
    assert abs(H.sum() - 1.0) < 1e-3                       # probability of a code's place
    assert H[hm.U < 1.0].sum() == 0.0                      # never behind the corridor exit
    cam = vision.DownCam(2304, 1296)
    along, across = cam.footprint(10.15)
    p, hdg, gain, _ = hm.best_stop((17.4, 3.0), 0.0, along, across)
    assert hm.to_uv(p)[0] > 5.0 and gain > 0.05            # first look: ahead of the exit
    hm.seen_picture(p, hdg, along, across)                 # looked there, found nothing ...
    p2, _, _, _ = hm.best_stop(p, hdg, along, across)
    assert math.hypot(p2[0] - p[0], p2[1] - p[1]) > 8.0    # ... so the next look is elsewhere


@pytest.mark.parametrize("layout,max_stops", [("dz_ahead", 4), ("dz_side", 9), ("dz_rot", 8), ("dz_far", 12)])
def test_search_finds_field_without_coordinates(layout, max_stops):
    from tests.search_sim import run
    ok, stops, t, _ = run(layout)
    assert ok and stops <= max_stops and t < C.SEARCH_TIMEOUT, (stops, t)
