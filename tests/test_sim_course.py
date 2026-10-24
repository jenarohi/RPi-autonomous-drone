"""Course layout and truth computer tests."""
from pathlib import Path

from skyscan.sim.course import Course
from skyscan.sim.truth import TruthComputer
from skyscan.types import Truth


def test_course_loading_and_conversion(tmp_path):
    yaml_content = """
name: test_course
origin:
  gz: [0.0, 0.0, 0.0]
  heading_deg: 90.0
objects:
  - id: start_pad
    type: pad
    label: "Pad"
    fwd: 0.0
    right: 0.0
    up: 0.01
    yaw_deg: 0.0
    size: [2.0, 2.0, 0.02]
corridors:
  forward:
    entrance: [8.0, 0.0]
    axis_yaw_deg: 0.0
    width_m: 3.5
    length_m: 10.0
"""
    p = tmp_path / "course.yaml"
    p.write_text(yaml_content)

    c = Course.from_yaml(p)
    assert c.name == "test_course"
    assert len(c.objects) == 1

    # Coordinate transform test
    # Course frame fwd=+x, right=-y, up=+z
    gx, gy, gz = c.course_to_gz(10.0, 2.0, 3.0)
    assert gx == 10.0 and gy == -2.0 and gz == 3.0

    fwd, right, up = c.gz_to_course(gx, gy, gz)
    assert fwd == 10.0 and right == 2.0 and up == 3.0

    # Truth computer test
    tc = TruthComputer(c)
    raw_truth = Truth(
        t=100.0,
        pos_gz=(10.0, -2.0, 3.0),
        yaw_gz_rad=0.0,  # facing +x in gz -> heading 90 deg
        ned=(-2.0, 10.0, -3.0),
        heading_deg=90.0,
    )
    enriched = tc.compute(raw_truth)
    assert enriched is not None
    assert enriched["course"]["fwd"] == 10.0
    assert enriched["course"]["right"] == 2.0
    assert enriched["corridor"] is not None
    # Entrance is at fwd=8, right=0; drone at fwd=10, right=2 -> along_axis = 2.0, lateral = 2.0
    assert enriched["corridor"]["along_axis_m"] == 2.0
    assert enriched["corridor"]["lateral_m"] == 2.0


# --- the generated world must be the legacy world --------------------------------------------------------------

import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parent.parent


def _models(sdf_path):
    """{name: (static, pose, size, ambient, diffuse, has_collision, albedo)} for every box model."""
    out = {}
    for m in ET.parse(sdf_path).getroot().iter("model"):
        if m.get("name", "").startswith("banner_"):  # rulebook foam boards, added on top of the legacy world
            continue
        vis = m.find("link/visual")
        if vis is None:
            continue
        size = vis.find("geometry/box/size")
        if size is None:  # ground plane: compared separately
            continue
        mat = vis.find("material")
        albedo = mat.find("pbr/metal/albedo_map")
        nums = lambda e: tuple(round(float(v), 4) for v in e.text.split())
        out[m.get("name")] = (
            m.findtext("static"),
            nums(m.find("pose")),
            nums(size),
            nums(mat.find("ambient")),
            nums(mat.find("diffuse")),
            m.find("link/collision") is not None,
            Path(albedo.text).name if albedo is not None else None,
        )
    return out


def test_generated_world_is_the_legacy_world(tmp_path):
    from sim.build_world import build_world

    new = build_world(out_file=tmp_path / "w.sdf")
    legacy = REPO / "legacy" / "aerothon_mission.sdf"
    got, want = _models(new), _models(legacy)
    # rulebook change: the exit (former orange) corridor floor is blue #0000FF; everything else is the legacy world
    st, pose, size, _, _, coll, alb = want["orange_floor"]
    want["orange_floor"] = (st, pose, size, (0.0, 0.0, 1.0, 1.0), (0.0, 0.0, 1.0, 1.0), coll, alb)
    assert set(got) == set(want), f"model sets differ: only new {set(got) - set(want)}, only legacy {set(want) - set(got)}"
    for name in want:
        assert got[name] == want[name], f"{name}: {got[name]} != legacy {want[name]}"

    # drone spawn, ground and world name are the legacy ones too
    gr, wr = ET.parse(new).getroot(), ET.parse(legacy).getroot()
    assert gr.find("world").get("name") == wr.find("world").get("name") == "aerothon_mission"
    gi, wi = gr.find("world/include"), wr.find("world/include")
    assert gi.findtext("uri") == wi.findtext("uri") == "model://iris_with_gimbal"
    assert gi.findtext("pose").split() == wi.findtext("pose").split()
    gp = gr.find("world/model[@name='ground']/link/visual/geometry/plane/size").text
    assert gp == wr.find("world/model[@name='ground']/link/visual/geometry/plane/size").text


def test_committed_world_is_up_to_date(tmp_path):
    from sim.build_world import build_world

    fresh = build_world(out_file=tmp_path / "w.sdf").read_text()
    assert (REPO / "sim" / "worlds" / "aerothon_mission.sdf").read_text() == fresh, \
        "sim/worlds/aerothon_mission.sdf is stale: run `python sim/build_world.py`"


def test_course_yaml_matches_legacy_geometry():
    c = Course.from_yaml(REPO / "sim" / "course.yaml")
    assert c.origin_gz == (-3.0, 3.0, 0.0) and c.origin_heading_deg == 90.0
    qr = c.get_object("start_qr")
    # legacy: drone (-3,3), start QR (0,3) -> 3 m straight ahead
    assert c.course_to_gz(qr.fwd, qr.right, 0.0)[:2] == (0.0, 3.0)
    # forward corridor entrance (x=6, y=3) is 9 m ahead, centred on the drone's line
    ent = c.corridors["forward"]["entrance"]
    assert c.course_to_gz(ent[0], ent[1], 0.0)[:2] == (6.0, 3.0)
    assert c.corridors["forward"]["width_m"] == 3.5 and c.corridors["forward"]["length_m"] == 10.0


def test_banners_are_in_the_world(tmp_path):
    from sim.build_world import build_world

    root = ET.parse(build_world(out_file=tmp_path / "w.sdf")).getroot()
    c = Course.from_yaml(REPO / "sim" / "course.yaml")
    ban = {o.id: o for o in c.objects if o.type == "banner"}
    assert set(ban) == {"banner_entry_arch", "banner_entry_ground", "banner_exit_arch", "banner_exit_ground"}
    for name, o in ban.items():
        m = root.find(f"world/model[@name=\x27{name}\x27]")
        assert m is not None and m.find("link/collision") is None
        board, face = (v.find("geometry/box/size").text.split() for v in m.findall("link/visual"))
        assert [round(float(v), 4) for v in board] == [round(v, 4) for v in o.size]   # 11.5 ft x 1.5 ft / 1 ft
        assert round(float(face[1]), 4) == round(o.size[1] - 2 * 0.0254, 4)           # 1 in white border all round
    assert ban["banner_entry_arch"].size[1:] == [3.5052, 0.4572] and ban["banner_exit_ground"].size[:2] == [0.3048, 3.5052]
    # arches sit on the wall tops (5 m): green across the green corridor start, blue across the exit corridor entrance
    for name, fwd, right in (("banner_entry_arch", 9.0, 0.0), ("banner_exit_arch", 19.0, 6.0)):
        assert abs(ban[name].fwd - fwd) < 0.02 and ban[name].right == right and abs(ban[name].up + ban[name].size[2] / 2 - 5.0) < 1e-3
    assert ban["banner_entry_ground"].right == 0.0 and ban["banner_exit_ground"].right == 6.0
