"""Server protocol tests with fake components (no MAVLink, no Gazebo)."""
import asyncio
import time

import numpy as np
from aiohttp.test_utils import TestClient, TestServer

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.gz.frames import FrameHub
from skyscan.server.app import Services, create_app
from skyscan.types import Frame, VehicleState


class FakeLink:
    def __init__(self):
        self.calls = []

    def state(self):
        return VehicleState(t=time.time(), link=True, mode="GUIDED", rel_alt_m=float("nan"))

    def hold(self, force_guided=False):
        self.calls.append(("hold", force_guided))
        return True

    def land(self):
        self.calls.append(("land",))
        return True

    def rtl(self):
        self.calls.append(("rtl",))
        return False

    def disarm(self, force=False):
        self.calls.append(("disarm", force))
        return True

    def set_gimbal(self, pitch, yaw=0.0):
        self.calls.append(("gimbal", pitch, yaw))
        return True


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.busy = False

    def run(self, stages):
        self.calls.append(("run", stages))
        self.busy = True
        return True, "run started"

    def abort(self, reason="operator", hold=True, wait_s=2.0):
        self.calls.append(("abort", reason, hold))
        self.busy = False
        return True

    def reset(self):
        self.calls.append(("reset",))

    def describe(self):
        return [{"id": "A1", "title": "Autonomous Takeoff"}]


SEEN = []


async def _until(ws, pred, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        msg = await ws.receive_json(timeout=max(0.05, end - time.monotonic()))
        SEEN.append(msg)
        if pred(msg):
            return msg
    raise AssertionError("timed out waiting for message")


def test_server_end_to_end(tmp_path):
    async def main():
        cfg = load_config(overrides=[f"server.runs_dir={tmp_path / 'runs'}", "server.telem_hz=20"])
        bus, hub = EventBus(), FrameHub()
        hub.put(Frame("down", 1, time.time(), np.full((48, 64, 3), 90, np.uint8)))
        link, runner = FakeLink(), FakeRunner()
        svc = Services(cfg, bus, hub, link=link, runner=runner, course={"objects": []},
                       truth_fn=lambda: {"ned": [0, 0, 0]})
        async with TestClient(TestServer(create_app(svc))) as client:
            r = await client.get("/api/health")
            assert r.status == 200 and (await r.json())["link"] is True

            ws = await client.ws_connect("/ws")
            hello = await ws.receive_json(timeout=3)
            assert hello["t"] == "hello" and hello["stages"][0]["id"] == "A1"
            assert hello["config"]["cameras"]["down"]["hfov_deg"] == 60.0
            assert hello["course"] == {"objects": []} and "seq" in hello["snapshot"]

            telem = await _until(ws, lambda m: m["t"] == "telem")
            assert telem["v"]["mode"] == "GUIDED" and telem["v"]["rel_alt_m"] is None   # NaN sanitised
            await _until(ws, lambda m: m["t"] == "truth")
            proc = await _until(ws, lambda m: m["t"] == "proc", timeout=4)
            assert proc["cams"]["down"]["seq"] == 1

            await ws.send_json({"cmd": "ping", "id": "p"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "p")
            assert ack["ok"] and ack["msg"] == "pong"

            await ws.send_json({"cmd": "run", "id": "r", "stages": ["A1", "A2"]})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "r")
            assert ack["ok"] and runner.calls[0] == ("run", ["A1", "A2"])

            await ws.send_json({"cmd": "land", "id": "l"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "l")
            assert ack["ok"] and ("abort", "operator LAND", False) in runner.calls and ("land",) in link.calls

            await ws.send_json({"cmd": "rtl", "id": "t"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "t")
            assert not ack["ok"] and "FAILED" in ack["msg"]

            await ws.send_json({"cmd": "hold", "id": "h"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "h")
            assert ack["ok"] and ("hold", True) in link.calls

            await ws.send_json({"cmd": "disarm", "id": "d", "force": True})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "d")
            assert not ack["ok"] and ("disarm", True) not in link.calls
            await ws.send_json({"cmd": "disarm", "id": "d2", "force": True, "confirm": "FORCE"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "d2")
            assert ack["ok"] and ("disarm", True) in link.calls

            await ws.send_json({"cmd": "gimbal", "id": "g", "pitch": -200})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "g")
            assert ack["ok"] and ("gimbal", -90.0, 0.0) in link.calls

            await ws.send_json({"cmd": "sim", "id": "s", "action": "start"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "s")
            assert not ack["ok"] and "not available" in ack["msg"]

            await ws.send_json({"cmd": "bogus", "id": "b"})
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] == "b")
            assert not ack["ok"]
            await ws.send_str("{not json")
            ack = await _until(ws, lambda m: m["t"] == "ack" and m["id"] is None)
            assert not ack["ok"]

            ui = [m["msg"] for m in SEEN if m["t"] == "event" and m["src"] == "UI"]
            assert "Operator command: RUN {'stages': ['A1', 'A2']}" in ui
            assert any(u.startswith("RTL rejected") for u in ui) and "PING" not in " ".join(ui)

            r = await client.get("/snapshot/down.jpg")
            body = await r.read()
            assert r.status == 200 and body[:2] == b"\xff\xd8"
            assert (await client.get("/snapshot/front.jpg")).status == 404
            assert (await client.get("/video/nope.mjpg")).status == 404

            r = await client.get("/video/down.mjpg")
            assert r.headers["Content-Type"].startswith("multipart/x-mixed-replace")
            chunk = await asyncio.wait_for(r.content.read(4096), 3)
            assert b"--skyscanframe" in chunk and b"\xff\xd8" in chunk
            r.close()

            r = await client.get("/")
            assert r.status == 200
            r = await client.get("/api/state")
            assert r.status == 200 and "snapshot" in await r.json()
            await ws.close()

    asyncio.run(main())


def test_sim_asset_route_is_confined_to_sim_folders(tmp_path):
    from types import SimpleNamespace

    models = tmp_path / "models"
    (models / "drone" / "meshes").mkdir(parents=True)
    (models / "drone" / "meshes" / "body.dae").write_text("<COLLADA/>")
    (models / "drone" / "notes.txt").write_text("not a mesh")
    secret = tmp_path / "secret.png"
    secret.write_bytes(b"png")

    async def main():
        cfg = load_config(overrides=[f"server.runs_dir={tmp_path / 'runs'}"])
        procman = SimpleNamespace(models_dir=models, world_file=tmp_path / "worlds" / "w.sdf")
        svc = Services(cfg=cfg, bus=EventBus(), hub=FrameHub(), procman=procman)
        async with TestClient(TestServer(create_app(svc))) as client:
            ok = await client.get(f"{models}/drone/meshes/body.dae")
            assert ok.status == 200 and await ok.text() == "<COLLADA/>"
            assert (await client.get(f"{models}/drone/notes.txt")).status == 404          # not a mesh/texture type
            assert (await client.get(str(secret))).status == 404                          # outside the sim folders
            assert (await client.get(f"{models}/../secret.png")).status == 404            # traversal
            assert (await client.get(f"{models}/drone/meshes/missing.dae")).status == 404

    asyncio.run(main())


def test_sim_asset_route_absent_without_a_simulator(tmp_path):
    async def main():
        cfg = load_config(overrides=[f"server.runs_dir={tmp_path / 'runs'}"])
        svc = Services(cfg=cfg, bus=EventBus(), hub=FrameHub())
        async with TestClient(TestServer(create_app(svc))) as client:
            assert (await client.get("/usr/share/anything.png")).status == 404

    asyncio.run(main())


def test_tunnelled_requests_need_the_password_but_lan_does_not(tmp_path, monkeypatch):
    import base64

    async def main(creds, expect_ok_with):
        monkeypatch.setenv("SKYSCAN_REMOTE_AUTH", creds)
        cfg = load_config(overrides=[f"server.runs_dir={tmp_path / 'runs'}"])
        svc = Services(cfg=cfg, bus=EventBus(), hub=FrameHub())
        async with TestClient(TestServer(create_app(svc))) as client:
            assert (await client.get("/api/health")).status == 200                      # LAN: open
            tun = {"Cf-Connecting-Ip": "1.2.3.4"}
            r = await client.get("/api/health", headers=tun)
            assert r.status == (401 if creds else 403)
            if creds:
                bad = {**tun, "Authorization": "Basic " + base64.b64encode(b"x:y").decode()}
                assert (await client.get("/api/health", headers=bad)).status == 401
                good = {**tun, "Authorization": "Basic " + base64.b64encode(creds.encode()).decode()}
                assert (await client.get("/api/health", headers=good)).status == 200

    asyncio.run(main("pilot:s3cret", True))
    asyncio.run(main("", False))
