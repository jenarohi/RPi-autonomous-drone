"""Tests for the shared foundation: geo frames, camera model, bus, config, types."""
import asyncio
import json
import math
import threading

import numpy as np
import pytest

from skyscan import geo
from skyscan.bus import EventBus, jsonable
from skyscan.types import BannerDetection, Check, Sev, StageReport, StageState, VehicleState


# ── geo ──────────────────────────────────────────────────────────────────

def test_wrap_and_diff():
    assert geo.wrap180(190) == pytest.approx(-170)
    assert geo.wrap180(-180) == pytest.approx(-180)
    assert geo.wrap360(-10) == pytest.approx(350)
    assert geo.ang_diff(10, 350) == pytest.approx(20)
    assert geo.ang_diff(350, 10) == pytest.approx(-20)


def test_gz_ned_roundtrip_and_heading():
    assert geo.gz_to_ned(3, 2, 5) == (2, 3, -5)
    assert geo.ned_to_gz(*geo.gz_to_ned(1.5, -2.0, 4.0)) == (1.5, -2.0, 4.0)
    assert geo.gz_yaw_to_heading_deg(0.0) == pytest.approx(90.0)          # facing +x = east
    assert geo.gz_yaw_to_heading_deg(math.pi / 2) == pytest.approx(0.0)   # facing +y = north
    assert geo.heading_deg_to_gz_yaw(90.0) == pytest.approx(0.0)


def test_course_frame_east_facing():
    cf = geo.CourseFrame((10.0, 20.0, -0.2), 90.0)   # start facing east
    # 1 m east of origin = 1 m forward; 1 m south = 1 m right (facing east, right hand points south)
    assert cf.to_course(10.0, 21.0, -0.2) == pytest.approx((1.0, 0.0, 0.0))
    assert cf.to_course(9.0, 20.0, -0.2) == pytest.approx((0.0, 1.0, 0.0))
    assert cf.to_course(10.0, 20.0, -5.2) == pytest.approx((0.0, 0.0, 5.0))
    n, e, d = cf.to_ned(1.0, 2.0, 5.0)
    assert cf.to_course(n, e, d) == pytest.approx((1.0, 2.0, 5.0))
    assert cf.rel_heading(60.0) == pytest.approx(-30.0)
    assert cf.abs_heading(-30.0) == pytest.approx(60.0)
    assert cf.dir_to_ned(1.0, 0.0) == pytest.approx((0.0, 1.0), abs=1e-9)
    assert geo.CourseFrame.from_dict(cf.to_dict()) == cf


def test_course_frame_random_roundtrip():
    rng = np.random.default_rng(1)
    for _ in range(50):
        cf = geo.CourseFrame(tuple(rng.uniform(-50, 50, 3)), float(rng.uniform(0, 360)))
        p = rng.uniform(-30, 30, 3)
        assert cf.to_course(*cf.to_ned(*p)) == pytest.approx(tuple(p), abs=1e-9)


def test_camera_model_from_hfov():
    cam = geo.CameraModel.from_hfov(640, 480, 60.0)
    assert cam.hfov_deg == pytest.approx(60.0)
    assert cam.fx == pytest.approx(320 / math.tan(math.radians(30)))
    assert cam.vfov_deg == pytest.approx(2 * math.degrees(math.atan(240 / cam.fy)))
    assert cam.project((0, 0, 1)) == pytest.approx((320, 240))
    half = cam.scaled(320, 240)
    assert half.hfov_deg == pytest.approx(60.0)


def test_down_camera_ground_projection():
    cam = geo.CameraModel.from_hfov(640, 480, 60.0)
    # centre pixel straight below
    assert geo.ground_offset_from_pixel(cam, 320, 240, 5.0) == pytest.approx((0.0, 0.0), abs=1e-9)
    # image top = forward, image right = right
    f, r = geo.ground_offset_from_pixel(cam, 320, 240 - cam.fy * 0.2, 5.0)
    assert f == pytest.approx(1.0) and r == pytest.approx(0.0, abs=1e-9)
    f, r = geo.ground_offset_from_pixel(cam, 320 + cam.fx * 0.2, 240, 5.0)
    assert f == pytest.approx(0.0, abs=1e-9) and r == pytest.approx(1.0)
    # nose up 10° → the belly camera looks forward: centre pixel lands ahead
    f, r = geo.ground_offset_from_pixel(cam, 320, 240, 5.0, pitch_deg=10.0)
    assert f == pytest.approx(5.0 * math.tan(math.radians(10.0))) and r == pytest.approx(0.0, abs=1e-9)
    # right wing down (roll +10°) → the belly camera looks left
    f, r = geo.ground_offset_from_pixel(cam, 320, 240, 5.0, roll_deg=10.0)
    assert r == pytest.approx(-5.0 * math.tan(math.radians(10.0)))


def test_gimbal_camera_rays():
    cam = geo.CameraModel.from_hfov(640, 480, 74.5)
    level = geo.cam_to_level("gimbal", cam_pitch_deg=0.0)
    b, e = geo.ray_angles(geo.pixel_ray(cam, 320, 240, level))
    assert (b, e) == pytest.approx((0.0, 0.0), abs=1e-9)
    # a pixel above the centre is above the horizon; right of centre is to the right
    b, e = geo.ray_angles(geo.pixel_ray(cam, 320, 100, level))
    assert e > 0 and b == pytest.approx(0.0, abs=1e-9)
    b, e = geo.ray_angles(geo.pixel_ray(cam, 500, 240, level))
    assert b > 0 and e == pytest.approx(0.0, abs=1e-9)
    # pitched −8°: the centre ray points 8° below the horizon
    b, e = geo.ray_angles(geo.pixel_ray(cam, 320, 240, geo.cam_to_level("gimbal", cam_pitch_deg=-8.0)))
    assert e == pytest.approx(-8.0)
    # nadir gimbal: image top = forward (same as the body-down camera)
    nadir = geo.cam_to_level("gimbal", cam_pitch_deg=-90.0)
    f, r = geo.ground_point(geo.pixel_ray(cam, 320, 200, nadir), 5.0)
    assert f > 0 and r == pytest.approx(0.0, abs=1e-9)
    for R in (level, nadir, geo.cam_to_level("body_down", roll_deg=7, pitch_deg=-4)):
        assert R @ R.T == pytest.approx(np.eye(3), abs=1e-12)
        assert np.linalg.det(R) == pytest.approx(1.0)


def test_level_ned_roundtrip():
    pos = (3.0, -4.0, -5.0)
    n, e, d = geo.level_to_ned(pos, 135.0, 2.0, -1.0, 0.5)
    assert geo.ned_to_level(pos, 135.0, n, e, d) == pytest.approx((2.0, -1.0, 0.5))


# ── types / jsonable ─────────────────────────────────────────────────────

def test_jsonable_sanitises():
    rep = StageReport("A1", "Autonomous Takeoff", state=StageState.RUNNING,
                      checks=[Check("link", True, "ok", value=float("nan"))])
    rep.metrics["x"] = np.float32(1.5)
    rep.metrics["arr"] = np.array([1, 2])
    rep.metrics["inf"] = float("inf")
    d = rep.to_dict()
    json.dumps(d, allow_nan=False)
    assert d["state"] == "running" and d["checks"][0]["value"] is None
    assert d["metrics"] == {"x": 1.5, "arr": [1, 2], "inf": None}
    v = VehicleState(ned=(1.0, 2.0, 3.0)).to_dict()
    assert v["ned"] == [1.0, 2.0, 3.0]
    b = BannerDetection(t=1.0, cam="front", seq=3, found=False).to_dict()
    assert b["found"] is False
    assert jsonable(Sev.WARN) == "warn"
    assert StageState.NOGO.terminal and not StageState.RUNNING.terminal


# ── bus ──────────────────────────────────────────────────────────────────

def test_bus_snapshot_and_fanout():
    async def main():
        bus = EventBus()
        bus.attach_loop()
        bus.publish("telem", {"v": {"armed": False}})
        bus.event("SYS", "hello", Sev.GOOD, foo=1)
        bus.log_lines("sitl", ["a", "b"])
        sub = bus.subscribe()
        snap = bus.snapshot()
        assert snap["seq"] == 3
        assert [m["t"] for m in snap["latest"]] == ["telem"]
        assert snap["events"][0]["msg"] == "hello" and snap["events"][0]["data"] == {"foo": 1}
        assert snap["logs"] == {"sitl": ["a", "b"]}

        # publishes from another thread; telem coalesces, events queue in order
        def worker():
            for i in range(50):
                bus.publish("telem", {"v": {"i": i}})
            for i in range(5):
                bus.event("FC", f"e{i}")
            bus.publish("vision", {"key": "down", "seq": 1})
            bus.publish("vision", {"key": "front", "seq": 1})
        th = threading.Thread(target=worker)
        th.start()
        th.join()
        await asyncio.sleep(0.05)
        batch = await sub.next_batch(timeout=1.0)
        # stale messages from before the snapshot may arrive; clients filter seq <= snap seq
        live = [m for m in batch if m["seq"] > snap["seq"]]
        events = [m["msg"] for m in live if m["t"] == "event"]
        telem = [m for m in live if m["t"] == "telem"]
        vision = sorted(m["key"] for m in live if m["t"] == "vision")
        assert events == [f"e{i}" for i in range(5)]
        assert len(telem) == 1 and telem[0]["v"] == {"i": 49}
        assert vision == ["down", "front"]
        assert bus.latest("vision", "front")["key"] == "front"
        assert await sub.next_batch(timeout=0.05) == []
        bus.unsubscribe(sub)
        assert await sub.next_batch(timeout=0.05) == []

    asyncio.run(main())


def test_bus_reserved_keys_and_listener():
    bus = EventBus()
    seen = []
    bus.add_listener(seen.append)
    m = bus.publish("stage", {"key": "A1", "t": "spoof", "ts": 0, "report": {"x": float("nan")}})
    assert m["t"] == "stage" and m["ts"] > 0 and m["report"] == {"x": None}
    assert seen and seen[0]["seq"] == m["seq"]
    bus.add_listener(lambda msg: 1 / 0)   # broken listener must not break publishing
    bus.event("SYS", "still works")
    assert bus.snapshot()["events"][-1]["msg"] == "still works"


def test_bus_fifo_overflow_counts_drops():
    async def main():
        bus = EventBus()
        bus.attach_loop()
        sub = bus.subscribe(fifo_max=10)
        for i in range(25):
            bus.event("SYS", f"m{i}")
        await asyncio.sleep(0.05)
        batch = await sub.next_batch(timeout=1.0)
        assert [m["msg"] for m in batch] == [f"m{i}" for i in range(15, 25)]
        assert sub.dropped == 15

    asyncio.run(main())


# ── config ───────────────────────────────────────────────────────────────

def test_config_loads_and_expands(cfg):
    assert cfg.mission.stage_a.a2.target_alt_m == pytest.approx(5.0)
    assert cfg.mission.stage_a.a2.forward_m == pytest.approx(1.0)
    assert "{world}" not in cfg.cameras.down.topic and cfg.sim.world_name in cfg.cameras.down.topic
    assert cfg.get_path("vision.qr.confirm_votes") == 3
    assert cfg.get_path("nope.nothing", 7) == 7
    with pytest.raises(AttributeError):
        _ = cfg.not_a_key


def test_config_overrides(tmp_path):
    from skyscan.config import load_config
    p = tmp_path / "c.yaml"
    p.write_text("sim: {world_name: w1, model_name: m1}\ncameras: {down: {topic: '/world/{world}/model/{model}/x'}}\n"
                 "a: {b: 1}\n")
    (tmp_path / "c.local.yaml").write_text("a: {c: 2}\n")
    cfg = load_config(p, overrides=["a.b=5", "sim.world_name=w2"])
    assert cfg.a.b == 5 and cfg.a.c == 2
    assert cfg.cameras.down.topic == "/world/w2/model/m1/x"
