"""Random scenarios: the layout rules, the files written for Gazebo, and the HTTP endpoints (fake simulator)."""
import asyncio
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from aiohttp.test_utils import TestClient, TestServer

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.gz.frames import FrameHub
from skyscan.server.app import Services, create_app
from skyscan.sim import scenario as sc
from skyscan.sim.course import Course
from skyscan.sim.truth import TruthComputer

REPO = Path(__file__).resolve().parents[1]
ZONE = sc.Zone(22.0, 62.0, -12.0, 18.0)


def check_rules(lay: sc.Layout, p: sc.Params) -> None:
    z = lay.zone
    for r in lay.reds:
        assert z.fwd_min + sc.EDGE_M - 1e-6 <= r["fwd"] - r["w"] / 2 and r["fwd"] + r["w"] / 2 <= z.fwd_max - sc.EDGE_M + 1e-6
        assert z.right_min + sc.EDGE_M - 1e-6 <= r["right"] - r["d"] / 2 and r["right"] + r["d"] / 2 <= z.right_max - sc.EDGE_M + 1e-6
    for i, a in enumerate(lay.reds):
        for b in lay.reds[i + 1:]:
            assert sc._boxes_gap(a, b) >= sc.RED_GAP_M - 1e-6
    assert sum(r["w"] * r["d"] for r in lay.reds) <= p.max_red_fraction * z.area + 1e-6
    assert len(lay.qrs) == p.qr_count
    for q in lay.qrs:
        assert z.fwd_min <= q["fwd"] <= z.fwd_max and z.right_min <= q["right"] <= z.right_max
        assert all(sc.box_dist(q["fwd"], q["right"], r) >= p.qr_clear_m - 1e-6 for r in lay.reds)
    for i, a in enumerate(lay.qrs):
        for b in lay.qrs[i + 1:]:
            assert math.hypot(a["fwd"] - b["fwd"], a["right"] - b["right"]) >= p.qr_spacing_m - 1e-6
    assert sorted(q["letter"] for q in lay.qrs) == sorted(p.letters())
    assert lay.target in {q["letter"] for q in lay.qrs}
    fwds = [q["fwd"] for q in lay.qrs]
    assert fwds == sorted(fwds)                                    # letters are listed nearest to farthest


@pytest.mark.parametrize("d", [
    {},
    {"red_count": [4, 8], "red_w": [3, 6], "red_d": [3, 6]},
    {"red_count": [0, 0]},
    {"qr_count": 8, "qr_spacing_m": 4.0},
    {"qr_size": [0.8, 1.2], "red_square": True},
    {"obstacles": True},
])
def test_every_layout_obeys_the_rules(d):
    for seed in range(1, 81):
        p = sc.Params.from_dict({**d, "seed": seed})
        try:
            lay = sc.generate(p, ZONE)
        except sc.ScenarioError:
            continue                                                # an over-full request may be refused, never wrong
        check_rules(lay, p)


def test_same_seed_same_layout_and_missing_seed_is_recorded():
    p = sc.Params.from_dict({"seed": 42})
    assert sc.generate(p, ZONE).to_dict() == sc.generate(p, ZONE).to_dict()
    assert sc.generate(sc.Params.from_dict({"seed": 43}), ZONE).to_dict() != sc.generate(p, ZONE).to_dict()
    lay = sc.generate(sc.Params.from_dict({}), ZONE)
    assert isinstance(lay.seed, int) and sc.generate(sc.Params.from_dict({"seed": lay.seed}), ZONE).to_dict() == lay.to_dict()


def test_everything_really_varies():
    layouts = [sc.generate(sc.Params.from_dict({"seed": s}), ZONE) for s in range(1, 40)]
    assert len({len(l.reds) for l in layouts}) > 1
    assert len({r["w"] for l in layouts for r in l.reds}) > 10
    assert len({l.target for l in layouts}) > 2
    assert len({tuple(q["letter"] for q in l.qrs) for l in layouts}) > 10


def test_specific_target_and_order_are_honoured():
    p = sc.Params.from_dict({"seed": 5, "target_mode": "specific", "target": "d", "order_mode": "specific", "order": "C A E B D"})
    lay = sc.generate(p, ZONE)
    assert lay.target == "D" and [q["letter"] for q in lay.qrs] == ["C", "A", "E", "B", "D"]
    p2 = sc.Params.from_dict({"seed": 5, "order_mode": "specific", "order": ["B", "A", "C", "D", "E"]})
    assert [q["letter"] for q in sc.generate(p2, ZONE).qrs] == list("BACDE")


@pytest.mark.parametrize("bad", [
    {"target_mode": "specific", "target": "Z"},
    {"order_mode": "specific", "order": "A B C"},
    {"order_mode": "specific", "order": "A A C D E"},
    {"qr_count": 99},
    {"red_w": [0.1, 2]},
    {"seed": "abc"},
    {"target_mode": "sometimes"},
])
def test_bad_parameters_say_why(bad):
    with pytest.raises(sc.ScenarioError):
        sc.Params.from_dict(bad)


def test_impossible_requests_are_refused_not_faked():
    p = sc.Params.from_dict({"qr_count": 8, "qr_spacing_m": 15.0, "seed": 1})
    with pytest.raises(sc.ScenarioError):
        sc.generate(p, ZONE)


def test_written_world_matches_the_layout(tmp_path):
    p = sc.Params.from_dict({"seed": 9, "target_mode": "specific", "target": "B", "obstacles": True})
    lay = sc.generate(p, ZONE)
    files = sc.write(lay, REPO / "sim" / "course.yaml", tmp_path / "scenario")
    course = Course.from_yaml(files["course"])
    reds = [o for o in course.objects if o.type == "restricted"]
    qrs = [o for o in course.objects if o.type == "qr" and o.id != "start_qr"]
    assert len(reds) == len(lay.reds) and len(qrs) == len(lay.qrs)
    assert {o.extras["content"] for o in qrs} == {f"DELIVERY-{q['letter']}" for q in lay.qrs}
    assert course.get_object("start_qr").extras["content"] == "DELIVERY-B"
    for o in qrs:
        assert (files["dir"] / "textures" / o.extras["texture"]).is_file()
    assert (files["dir"] / "textures" / "qr_start.png").is_file()
    # the corridors, walls and zone floor of the canonical course are all still there
    base = Course.from_yaml(REPO / "sim" / "course.yaml")
    keep = {o.id for o in base.objects if o.type not in ("restricted", "qr")}
    assert keep <= {o.id for o in course.objects}
    # the world is well-formed SDF with one model per object, and its textures resolve next to it
    root = ET.parse(files["world"]).getroot()
    names = {m.get("name") for m in root.iter("model")}
    assert {o.id for o in course.objects} <= names
    for tex in root.iter("albedo_map"):
        assert (files["world"].parent / tex.text).is_file()
    # red zone size in the SDF is what the layout asked for (gz box x = fwd extent, y = right extent)
    red = next(m for m in root.iter("model") if m.get("name") == "red1")
    sx, sy, _ = (float(v) for v in red.find(".//box/size").text.split())
    assert (sx, sy) == (lay.reds[0]["w"], lay.reds[0]["d"])


def test_obstacles_keep_a_passage(tmp_path):
    for seed in range(1, 30):
        lay = sc.generate(sc.Params.from_dict({"seed": seed, "obstacles": True}), ZONE)
        obs = sorted(lay.obstacles, key=lambda o: o["fwd"])
        assert len(obs) == 3 and all(10.0 <= o["fwd"] <= 18.0 for o in obs)
        assert all(obs[i + 1]["fwd"] - obs[i]["fwd"] >= 2.5 - 1e-6 for i in range(2))
        for o in obs:
            lo, hi = o["right"] - o["width"] / 2, o["right"] + o["width"] / 2
            assert lo >= sc.ORANGE_WALL_L - 1e-6 and hi <= sc.ORANGE_WALL_R + 1e-6
            assert min(lo - sc.ORANGE_WALL_L, sc.ORANGE_WALL_R - hi) <= 0.3 + 1e-6      # hugs a wall
            assert max(lo - sc.ORANGE_WALL_L, sc.ORANGE_WALL_R - hi) >= 1.8             # >= 1.8 m free on the other side


# ── HTTP endpoints with a fake simulator ───────────────────────────────────────────────────────────────────────────

class FakeProc:
    def __init__(self, world):
        self.world_file = world
        self.restarts = 0

    async def restart_sim(self):
        self.restarts += 1


class FakeRunner:
    busy = False

    def __init__(self):
        self.resets = 0

    def reset(self):
        self.resets += 1

    def describe(self):
        return []


def test_endpoints(tmp_path):
    async def main():
        world_dir = tmp_path / "worlds"
        world_dir.mkdir()
        world = world_dir / "aerothon_mission.sdf"
        world.write_text("<sdf/>")
        cfg = load_config(overrides=[f"server.runs_dir={tmp_path / 'runs'}", f"sim.course_file={REPO / 'sim' / 'course.yaml'}"])
        base = Course.from_yaml(REPO / "sim" / "course.yaml")
        truth = TruthComputer(base)
        proc, runner = FakeProc(world), FakeRunner()
        svc = Services(cfg, EventBus(), FrameHub(), runner=runner, procman=proc, course=base.to_dict(), truth_comp=truth)
        async with TestClient(TestServer(create_app(svc))) as client:
            r = await client.get("/api/scenario")
            j = await r.json()
            assert j["available"] and not j["active"] and j["zone"] == {"fwd": [22.0, 62.0], "right": [-12.0, 18.0]}

            params = {"seed": 11, "target_mode": "specific", "target": "E"}
            r = await client.post("/api/scenario/preview", json={"params": params})
            prev = (await r.json())["layout"]
            assert r.status == 200 and prev["target"] == "E" and prev["seed"] == 11 and proc.restarts == 0
            assert svc.course == base.to_dict()                        # a preview changes nothing

            r = await client.post("/api/scenario/preview", json={"params": {"target_mode": "specific", "target": "Q"}})
            assert r.status == 400 and "target" in (await r.json())["error"]
            r = await client.post("/api/scenario/preview", data="not json", headers={"Content-Type": "text/plain"})
            assert r.status == 415

            runner.busy = True
            r = await client.post("/api/scenario/apply", json={"params": params})
            assert r.status == 409 and proc.restarts == 0              # never mid-run
            runner.busy = False

            r = await client.post("/api/scenario/apply", json={"params": params})
            out = await r.json()
            assert r.status == 200 and out["layout"]["reds"] == prev["reds"] and out["layout"]["qrs"] == prev["qrs"]
            await asyncio.sleep(0.05)
            assert proc.restarts == 1 and runner.resets == 1
            assert proc.world_file == world_dir / "scenario" / "aerothon_mission.sdf" and proc.world_file.is_file()
            assert {o["id"] for o in svc.course["objects"] if o["type"] == "restricted"} == {f"red{i}" for i in range(1, len(prev["reds"]) + 1)}
            assert truth.course.get_object("start_qr").extras["content"] == "DELIVERY-E"
            assert svc.scenario["layout"]["target"] == "E"
            assert (await (await client.get("/api/scenario")).json())["active"]
            hello = None
            ws = await client.ws_connect("/ws")
            hello = await ws.receive_json(timeout=3)
            assert hello["scenario"]["target"] == "E" and hello["course"] == svc.course

            r = await client.post("/api/scenario/reset")
            assert r.status == 200
            await asyncio.sleep(0.05)
            assert proc.world_file == world and svc.scenario is None and proc.restarts == 2
            assert svc.course == base.to_dict() and truth.course.get_object("qr_c") is not None
            await ws.close()

    asyncio.run(main())
