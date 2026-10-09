"""Mission-control web server (aiohttp): the UI, the ``/ws`` hub, MJPEG camera streams, run files.

Components are injected through :class:`Services`, so the same server runs against the real system
(``python -m skyscan``) and against the UI mock (``python -m skyscan.server.mock``).
Protocol: docs/ARCHITECTURE.md §9.
"""
from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
import socket
import time
import weakref
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiohttp import WSMsgType, web

from skyscan import __version__
from skyscan.bus import EventBus, Subscription, jsonable
from skyscan.config import Cfg, repo_path
from skyscan.gz.frames import FrameHub
from skyscan.server import scenario_api
from skyscan.types import Sev

log = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"
# File types the embedded Gazebo viewer (gzweb) may fetch from the sim's model/texture folders.
SIM_ASSET_EXT = {".dae", ".stl", ".obj", ".mtl", ".glb", ".gltf", ".png", ".jpg", ".jpeg"}
_BOUNDARY = "skyscanframe"


@dataclass
class Services:
    """Everything the server talks to. Only ``cfg``, ``bus`` and ``hub`` are mandatory."""
    cfg: Cfg
    bus: EventBus
    hub: FrameHub
    link: Any = None        # skyscan.fc.link.MavLink (or compatible)
    runner: Any = None      # skyscan.mission.runner.MissionRunner
    vision: Any = None      # skyscan.vision.pipeline.VisionPipeline
    procman: Any = None     # skyscan.sim.procman.ProcessManager (sim profile only)
    gz: Any = None          # skyscan.gz.bridge.GzBridge (sim profile only)
    lidar: Any = None       # skyscan.lidar.LidarHub (2D scan) → "lidar" messages
    recorder: Any = None
    course: dict | None = None                          # skyscan.sim.course.Course.to_dict()
    truth_fn: Callable[[], dict | None] | None = None   # sim ground-truth metrics → "truth" messages
    truth_comp: Any = None                              # skyscan.sim.truth.TruthComputer: its course is swapped by a scenario
    scenario: dict | None = None                        # the random scenario loaded now (skyscan/server/scenario_api.py)
    scenario_base: Any = None                           # (canonical world file, canonical course file), set on first apply
    profile: str = "sim"
    started_at: float = field(default_factory=time.time)


@dataclass
class _State:
    svc: Services
    jpeg: "JpegCache"
    closing: bool = False
    websockets: "weakref.WeakSet[web.WebSocketResponse]" = field(default_factory=weakref.WeakSet)
    tasks: list[asyncio.Task] = field(default_factory=list)


STATE = web.AppKey("skyscan_state", _State)
SIM_ROOTS = web.AppKey("sim_asset_roots", list)


def dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), allow_nan=False)


class CommandError(Exception):
    """Operator command rejected; the message goes back in the ack."""


async def _blocking(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run a blocking component call (MAVLink round-trips, runner waits) off the event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


def _need(component: Any, what: str) -> Any:
    if component is None:
        raise CommandError(f"{what} is not available in this profile")
    return component


# ───────────────────────────── JPEG cache ─────────────────────────────

class JpegCache:
    """Encodes each camera frame to JPEG at most once, however many viewers there are."""

    def __init__(self, hub: FrameHub, quality: int = 70) -> None:
        self.hub = hub
        self.quality = int(quality)
        self._cache: dict[str, tuple[tuple[int, float], bytes]] = {}
        self._locks: dict[str, asyncio.Lock] = collections.defaultdict(asyncio.Lock)

    async def get(self, cam: str) -> tuple[tuple[int, float], bytes] | None:
        frame = self.hub.latest(cam)
        if frame is None:
            return None
        ident = (frame.seq, frame.t)
        hit = self._cache.get(cam)
        if hit and hit[0] == ident:
            return hit
        async with self._locks[cam]:
            hit = self._cache.get(cam)
            if hit and hit[0] == ident:
                return hit
            import cv2  # lazy: keeps importing the server cheap
            ok, buf = await _blocking(cv2.imencode, ".jpg", frame.img, [int(cv2.IMWRITE_JPEG_QUALITY), self.quality])
            if not ok:
                return None
            hit = (ident, buf.tobytes())
            self._cache[cam] = hit
            return hit


# ───────────────────────────── operator commands ─────────────────────────────

async def _cmd_run(svc: Services, msg: dict) -> tuple[bool, str]:
    stages = msg.get("stages")
    if not isinstance(stages, list) or not stages or not all(isinstance(s, str) for s in stages):
        raise CommandError("'stages' must be a non-empty list of stage ids")
    runner = _need(svc.runner, "mission runner")
    return await _blocking(runner.run, stages)


async def _cmd_abort(svc: Services, msg: dict) -> tuple[bool, str]:
    runner = _need(svc.runner, "mission runner")
    stopped = await _blocking(runner.abort, "operator abort", True)
    return True, "run aborted" if stopped else "abort requested"


async def _safety_action(svc: Services, action: str) -> tuple[bool, str]:
    """HOLD / LAND / RTL: stop any run first (without its own hold for LAND/RTL), then command."""
    link = _need(svc.link, "MAVLink")
    if svc.runner is not None and getattr(svc.runner, "busy", False):
        await _blocking(svc.runner.abort, f"operator {action.upper()}", action == "hold")
    if action == "hold":
        ok = await _blocking(link.hold, True)
    elif action == "land":
        ok = await _blocking(link.land)
    else:
        ok = await _blocking(link.rtl)
    return bool(ok), f"{action.upper()} {'accepted' if ok else 'FAILED'}"


async def _cmd_disarm(svc: Services, msg: dict) -> tuple[bool, str]:
    link = _need(svc.link, "MAVLink")
    force = bool(msg.get("force"))
    if force and msg.get("confirm") != "FORCE":
        raise CommandError("force disarm needs confirm='FORCE' (the vehicle will fall if airborne)")
    ok = await _blocking(link.disarm, force)
    return bool(ok), ("FORCE " if force else "") + ("disarmed" if ok else "disarm rejected")


async def _cmd_gimbal(svc: Services, msg: dict) -> tuple[bool, str]:
    link = _need(svc.link, "MAVLink")
    try:
        pitch = float(msg.get("pitch"))
        yaw = float(msg.get("yaw", 0.0))
    except (TypeError, ValueError):
        raise CommandError("'pitch' (and optional 'yaw') must be numbers") from None
    pitch = max(-90.0, min(30.0, pitch))
    ok = await _blocking(link.set_gimbal, pitch, yaw)
    return bool(ok), f"gimbal pitch {pitch:.0f}°" + ("" if ok else " not acknowledged")


async def _cmd_reset(svc: Services, msg: dict) -> tuple[bool, str]:
    runner = _need(svc.runner, "mission runner")
    if getattr(runner, "busy", False):
        raise CommandError("a run is in progress — abort it first")
    await _blocking(runner.reset)
    return True, "mission state cleared"


async def _cmd_sim(svc: Services, msg: dict) -> tuple[bool, str]:
    pm = _need(svc.procman, "simulator control")
    action = msg.get("action")
    fn: Callable[[], Awaitable[Any]] | None = {
        "start": pm.start_sim, "stop": pm.stop_sim, "restart": pm.restart_sim,
    }.get(action)
    if fn is None:
        raise CommandError("sim action must be start | stop | restart")
    if action in ("stop", "restart") and svc.runner is not None and getattr(svc.runner, "busy", False):
        raise CommandError("a run is in progress — abort it first")
    _spawn(svc, fn(), f"sim {action}")
    return True, f"sim {action} started — watch the process panel"


async def _cmd_gz_gui(svc: Services, msg: dict) -> tuple[bool, str]:
    pm = _need(svc.procman, "simulator control")
    action = msg.get("action")
    if action not in ("open", "close"):
        raise CommandError("gz_gui action must be open | close")
    _spawn(svc, pm.open_gz_gui() if action == "open" else pm.close_gz_gui(), f"gz gui {action}")
    return True, f"Gazebo GUI {action} requested"


async def _cmd_ping(svc: Services, msg: dict) -> tuple[bool, str]:
    return True, "pong"


COMMANDS: dict[str, Callable[[Services, dict], Awaitable[tuple[bool, str]]]] = {
    "run": _cmd_run,
    "abort": _cmd_abort,
    "hold": lambda s, m: _safety_action(s, "hold"),
    "land": lambda s, m: _safety_action(s, "land"),
    "rtl": lambda s, m: _safety_action(s, "rtl"),
    "disarm": _cmd_disarm,
    "gimbal": _cmd_gimbal,
    "reset_mission": _cmd_reset,
    "sim": _cmd_sim,
    "gz_gui": _cmd_gz_gui,
    "ping": _cmd_ping,
}
QUIET_COMMANDS = {"ping"}


def _spawn(svc: Services, coro: Awaitable[Any], what: str) -> None:
    async def runner() -> None:
        try:
            await coro
        except Exception as exc:  # noqa: BLE001
            log.exception("%s failed", what)
            svc.bus.event("SYS", f"{what} failed: {exc}", Sev.ERROR)
    asyncio.get_running_loop().create_task(runner())


async def _handle_command(svc: Services, ws: web.WebSocketResponse, raw: str, peer: str | None) -> None:
    cid = None
    name = "?"
    try:
        msg = json.loads(raw)
        if not isinstance(msg, dict):
            raise CommandError("command must be a JSON object")
        cid = msg.get("id")
        name = str(msg.get("cmd"))
        handler = COMMANDS.get(name)
        if handler is None:
            raise CommandError(f"unknown command {name!r}")
        if name not in QUIET_COMMANDS:
            detail = {k: v for k, v in msg.items() if k not in ("cmd", "id")}
            svc.bus.event("UI", f"Operator command: {name.upper()}" + (f" {detail}" if detail else ""),
                          Sev.INFO, peer=peer, cmd=name)
        ok, text = await handler(svc, msg)
    except CommandError as exc:
        ok, text = False, str(exc)
    except json.JSONDecodeError:
        ok, text = False, "invalid JSON"
    except Exception as exc:  # noqa: BLE001 - report, never kill the socket
        log.exception("command %s failed", name)
        ok, text = False, f"{type(exc).__name__}: {exc}"
    if not ok and name not in QUIET_COMMANDS:
        svc.bus.event("UI", f"{name.upper()} rejected: {text}", Sev.WARN, peer=peer, cmd=name)
    if not ws.closed:
        await ws.send_str(dumps({"t": "ack", "ts": time.time(), "id": cid, "cmd": name, "ok": bool(ok), "msg": text}))


# ───────────────────────────── handlers ─────────────────────────────

def build_hello(svc: Services) -> dict:
    """First message on every WebSocket. Take it *after* subscribing (snapshot/seq rule)."""
    cfg = svc.cfg
    cams = {}
    for name, c in (cfg.get("cameras") or {}).items():
        st = svc.hub.stats(name)
        cams[name] = {"hfov_deg": c.get("hfov_deg"), "mount": c.get("mount"), "w": st["w"], "h": st["h"]}
    sim_ws = cfg.get_path("sim.websocket") or {}
    return jsonable({
        "t": "hello",
        "ts": time.time(),
        "server": {"version": __version__, "profile": svc.profile, "host": socket.gethostname(),
                   "pid": os.getpid(), "started_at": svc.started_at},
        "config": {
            "ui": cfg.get("ui") or {},
            "cameras": cams,
            "gzweb": {"enabled": svc.profile == "sim" and bool(sim_ws.get("enabled")), "port": sim_ws.get("port")},
            "mission": cfg.get("mission") or {},
            "safety": cfg.get("safety") or {},
            "telem_hz": cfg.get_path("server.telem_hz", 10),
        },
        "course": svc.course,
        "scenario": (svc.scenario or {}).get("layout"),
        "stages": svc.runner.describe() if svc.runner is not None else [],
        "snapshot": svc.bus.snapshot(),
    })


async def _ws_sender(ws: web.WebSocketResponse, sub: Subscription, snap_seq: int, svc: Services) -> None:
    dropped = 0
    try:
        while not ws.closed and not sub.closed:
            batch = await sub.next_batch(timeout=5.0)
            if sub.dropped != dropped:          # client fell behind: resend a full snapshot
                dropped = sub.dropped
                snap = svc.bus.snapshot()
                snap_seq = snap["seq"]
                await ws.send_str(dumps({"t": "resync", "ts": time.time(), "snapshot": snap}))
            for m in batch:
                if m.get("seq", 0) > snap_seq:
                    await ws.send_str(dumps(m))
    except (ConnectionError, RuntimeError):
        pass


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    svc = request.app[STATE].svc
    token = svc.cfg.get_path("server.auth_token") or ""
    if token and request.query.get("token") != token:
        raise web.HTTPForbidden(text="bad or missing token")
    ws = web.WebSocketResponse(heartbeat=15.0, max_msg_size=1 << 20)
    await ws.prepare(request)
    request.app[STATE].websockets.add(ws)
    sub = svc.bus.subscribe()
    sender: asyncio.Task | None = None
    try:
        hello = build_hello(svc)
        await ws.send_str(dumps(hello))
        sender = asyncio.create_task(_ws_sender(ws, sub, hello["snapshot"]["seq"], svc))
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await _handle_command(svc, ws, msg.data, request.remote)
            elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                break
    except (ConnectionError, RuntimeError):
        pass
    finally:
        svc.bus.unsubscribe(sub)
        if sender is not None:
            sender.cancel()
        request.app[STATE].websockets.discard(ws)
    return ws


async def mjpeg_handler(request: web.Request) -> web.StreamResponse:
    """``/video/<cam>.mjpg[?fps=N]`` — raw frames; overlays are drawn client-side from ``vision``."""
    svc = request.app[STATE].svc
    cam = request.match_info["cam"]
    if cam not in (svc.cfg.get("cameras") or {}) and svc.hub.latest(cam) is None:
        raise web.HTTPNotFound(text=f"unknown camera {cam!r}")
    max_fps = float(svc.cfg.get_path("server.mjpeg_max_fps", 12))
    try:
        fps = min(max_fps, max(0.5, float(request.query.get("fps", max_fps))))
    except ValueError:
        fps = max_fps
    resp = web.StreamResponse(headers={
        "Content-Type": f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
        "Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache",
    })
    await resp.prepare(request)
    state = request.app[STATE]
    cache = state.jpeg
    last = None
    min_dt = 1.0 / fps
    try:
        while not state.closing:
            t0 = time.monotonic()
            item = await cache.get(cam)
            if item is None or item[0] == last:
                await asyncio.sleep(0.03)
                continue
            last, jpg = item
            await resp.write(b"--" + _BOUNDARY.encode() + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                             + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
            await asyncio.sleep(max(0.0, min_dt - (time.monotonic() - t0)))
    except ConnectionError:
        pass
    return resp


async def snapshot_handler(request: web.Request) -> web.Response:
    cam = request.match_info["cam"]
    item = await request.app[STATE].jpeg.get(cam)
    if item is None:
        raise web.HTTPNotFound(text=f"no frame from {cam!r}")
    return web.Response(body=item[1], content_type="image/jpeg", headers={"Cache-Control": "no-store"})


async def state_handler(request: web.Request) -> web.Response:
    svc = request.app[STATE].svc
    body = {"server": {"version": __version__, "profile": svc.profile},
            "stages": svc.runner.describe() if svc.runner is not None else [],
            "snapshot": svc.bus.snapshot()}
    return web.Response(text=dumps(jsonable(body)), content_type="application/json")


async def health_handler(request: web.Request) -> web.Response:
    svc = request.app[STATE].svc
    link = svc.link.state().link if svc.link is not None else None
    return web.json_response({"ok": True, "version": __version__, "profile": svc.profile, "link": link,
                              "cams": {c: svc.hub.stats(c) for c in svc.hub.cams()}})


async def index_handler(request: web.Request) -> web.StreamResponse:
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return web.Response(text="SkyScan server is running, but the UI is not built yet "
                                 "(skyscan/server/static/index.html missing).", content_type="text/plain")
    return web.FileResponse(index)


def _make_remote_auth(credentials: str) -> Callable:
    """HTTP Basic auth for requests that arrive through a Cloudflare tunnel (they carry Cf-* headers).

    Direct LAN requests are left alone. Fails closed: with no credentials configured, tunnelled requests get 403,
    so exposing the port through a tunnel by accident never exposes the cockpit.
    """
    import base64
    import hmac
    expected = "Basic " + base64.b64encode(credentials.encode()).decode() if credentials else ""

    @web.middleware
    async def remote_auth(request: web.Request, handler: Callable) -> web.StreamResponse:
        if "Cf-Connecting-Ip" in request.headers or "Cf-Ray" in request.headers:
            if not expected:
                raise web.HTTPForbidden(text="remote access is not configured")
            if not hmac.compare_digest(request.headers.get("Authorization", ""), expected):
                raise web.HTTPUnauthorized(headers={"WWW-Authenticate": 'Basic realm="SkyScan Mission Control"'})
        return await handler(request)
    return remote_auth


@web.middleware
async def no_cache_middleware(request: web.Request, handler: Callable) -> web.StreamResponse:
    resp = await handler(request)
    if request.path == "/" or request.path.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


def _sim_asset_roots(svc: Services) -> list[Path]:
    """Folders gzweb may read meshes/textures from: the vendored models + world, and Gazebo's own resource path."""
    pm = svc.procman
    if pm is None:
        return []
    cands: list[Any] = [getattr(pm, "models_dir", None), getattr(getattr(pm, "world_file", None), "parent", None)]
    cands += [p for p in os.environ.get("GZ_SIM_RESOURCE_PATH", "").split(":") if p]
    roots: list[Path] = []
    for c in cands:
        try:
            r = Path(c).resolve()
        except (TypeError, OSError, RuntimeError):
            continue
        if r.is_dir() and r not in roots:
            roots.append(r)
    return roots


async def gzws_proxy_handler(request: web.Request) -> web.StreamResponse:
    """Same-origin relay to the Gazebo websocket server (gz launch, default port 9090).

    The browser then needs only this one port: it works through a tunnel / reverse proxy, over https (wss) and
    behind the password gate, which a direct ws://host:9090 connection from the page does not.
    """
    import aiohttp
    svc: Services = request.app[STATE].svc
    port = int(svc.cfg.get_path("sim.websocket.port", 9090))
    client = web.WebSocketResponse(max_msg_size=0, heartbeat=20)
    await client.prepare(request)
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.ws_connect(f"http://127.0.0.1:{port}", max_msg_size=0, heartbeat=20) as upstream:
                async def up() -> None:
                    async for m in client:
                        if m.type == WSMsgType.TEXT:
                            await upstream.send_str(m.data)
                        elif m.type == WSMsgType.BINARY:
                            await upstream.send_bytes(m.data)
                        else:
                            break

                async def down() -> None:
                    async for m in upstream:
                        if m.type == WSMsgType.TEXT:
                            await client.send_str(m.data)
                        elif m.type == WSMsgType.BINARY:
                            await client.send_bytes(m.data)
                        else:
                            break

                tasks = [asyncio.ensure_future(up()), asyncio.ensure_future(down())]
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for t in tasks:
                    t.cancel()
    except Exception as exc:  # noqa: BLE001 - gz websocket not up yet: close so the page can retry / fall back
        log.info("gz websocket relay ended: %s", exc)
    finally:
        await client.close()
    return client


async def sim_asset_handler(request: web.Request) -> web.StreamResponse:
    """Serve a model mesh / texture by the absolute path Gazebo reports for it.

    gzweb first asks the page's own origin for each resource (the path Gazebo resolved ``model://...`` to) and only then
    falls back to pulling it through the websocket, which is slower and noisy. Read-only, image/mesh types only, and
    only inside the sim resource folders.
    """
    try:
        real = Path("/" + request.match_info["tail"]).resolve(strict=True)
    except (OSError, RuntimeError):
        raise web.HTTPNotFound()
    if real.suffix.lower() not in SIM_ASSET_EXT or not real.is_file() or \
            not any(real.is_relative_to(r) for r in request.app[SIM_ROOTS]):
        raise web.HTTPNotFound()
    return web.FileResponse(real, headers={"Cache-Control": "public, max-age=3600"})


# ───────────────────────────── periodic publishers ─────────────────────────────

async def _every(hz: float, fn: Callable[[], None], what: str, state: _State) -> None:
    period = 1.0 / max(0.1, float(hz))
    while not state.closing:
        t0 = time.monotonic()
        try:
            fn()
        except Exception:  # noqa: BLE001
            log.exception("%s publisher failed", what)
        await asyncio.sleep(max(0.01, period - (time.monotonic() - t0)))


def _publish_telem(svc: Services) -> None:
    if svc.link is not None:
        svc.bus.publish("telem", {"v": svc.link.state()})


def _publish_truth(svc: Services) -> None:
    if svc.truth_fn is not None:
        t = svc.truth_fn()
        if t is not None:
            svc.bus.publish("truth", t)


def _publish_lidar(svc: Services) -> None:
    """Latest 2D scan + wall geometry for the cockpit's lidar panel. Always publishes (``r`` is None when no data), so a
    stalled sensor shows as NO DATA instead of a frozen picture."""
    if svc.lidar is None:
        return
    from skyscan.lidar import nearest, wall_info
    stats = svc.lidar.stats()
    scan = svc.lidar.latest()
    if scan is None or stats["age_s"] is None or stats["age_s"] > 2.0:
        svc.bus.publish("lidar", {"r": None, "hz": 0.0, "age_s": stats["age_s"], "walls": None, "nearest_m": None})
        return
    walls = wall_info(scan)
    near = nearest(scan)
    svc.bus.publish("lidar", {**scan.to_wire(), "hz": stats["hz"], "age_s": stats["age_s"], "walls": walls.to_dict(),
                              "nearest_m": round(near, 2) if near != float("inf") else None})


def _make_precond_publisher(svc: Services) -> Callable[[], None]:
    """GO / NO-GO of each stage, published when it changes (and every few seconds so a new client is never stale).
    Evaluation only: nothing is ever started from here."""
    last: dict[str, tuple[str, float]] = {}

    def publish() -> None:
        runner = svc.runner
        if runner is None or getattr(runner, "busy", False) or not hasattr(runner, "preview"):
            return                                   # while a run is active the stage reports carry their own checks
        now = time.monotonic()
        for sid, checks in runner.preview().items():
            body = [c.to_dict() for c in checks]
            sig = json.dumps(body, sort_keys=True, default=str)
            prev = last.get(sid)
            if prev is not None and prev[0] == sig and now - prev[1] < 5.0:
                continue
            last[sid] = (sig, now)
            go = all(c.ok for c in checks if c.blocking)
            svc.bus.publish("precond", {"key": sid, "go": go, "checks": body})
    return publish


def _make_proc_publisher(svc: Services) -> Callable[[], None]:
    try:
        import psutil
        psutil.cpu_percent(None)
    except Exception:  # noqa: BLE001
        psutil = None  # type: ignore[assignment]

    def publish() -> None:
        cams = sorted(set(svc.cfg.get("cameras") or {}) | set(svc.hub.cams()))
        payload: dict[str, Any] = {"sim": "n/a", "detail": "", "rtf": None, "sim_time": None, "paused": None,
                                   "procs": [], "cams": {c: svc.hub.stats(c) for c in cams}}
        if svc.procman is not None:
            st = svc.procman.status()
            payload.update(sim=st.get("sim", "?"), detail=st.get("detail", ""), procs=st.get("procs", []))
        if svc.gz is not None:
            ws = svc.gz.world_stats() or {}
            payload.update(rtf=ws.get("rtf"), sim_time=ws.get("sim_time"), paused=ws.get("paused"))
        if psutil is not None:
            vm = psutil.virtual_memory()
            payload["host"] = {"cpu_pct": psutil.cpu_percent(None), "mem_pct": vm.percent,
                               "load": list(os.getloadavg())}
        svc.bus.publish("proc", payload)
    return publish


# ───────────────────────────── app ─────────────────────────────

def create_app(svc: Services) -> web.Application:
    app = web.Application(middlewares=[_make_remote_auth(os.environ.get("SKYSCAN_REMOTE_AUTH", "")), no_cache_middleware])
    state = _State(svc=svc, jpeg=JpegCache(svc.hub, svc.cfg.get_path("server.mjpeg_quality", 70)))
    app[STATE] = state

    runs_dir = repo_path(svc.cfg.get_path("server.runs_dir", "runs"))
    runs_dir.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    app.router.add_get("/", index_handler)
    app.router.add_get("/ws", ws_handler)
    app.router.add_get("/video/{cam}.mjpg", mjpeg_handler)
    app.router.add_get("/snapshot/{cam}.jpg", snapshot_handler)
    app.router.add_get("/api/state", state_handler)
    app.router.add_get("/api/health", health_handler)
    scenario_api.register(app, lambda request: request.app[STATE].svc, _spawn)
    app.router.add_static("/static/", STATIC_DIR, follow_symlinks=False)
    app.router.add_static("/runs/", runs_dir, show_index=True)
    if svc.procman is not None:
        app.router.add_get("/gzws", gzws_proxy_handler)
    roots = _sim_asset_roots(svc)
    if roots:
        app[SIM_ROOTS] = roots
        app.router.add_get("/{tail:.+}", sim_asset_handler)    # last: only paths nothing else claimed

    async def on_startup(app: web.Application) -> None:
        svc.bus.attach_loop(asyncio.get_running_loop())
        cfg = svc.cfg
        state.tasks[:] = [
            asyncio.create_task(_every(cfg.get_path("server.telem_hz", 10), lambda: _publish_telem(svc), "telem", state)),
            asyncio.create_task(_every(cfg.get_path("server.proc_hz", 1), _make_proc_publisher(svc), "proc", state)),
            asyncio.create_task(_every(cfg.get_path("server.truth_hz", 5), lambda: _publish_truth(svc), "truth", state)),
            asyncio.create_task(_every(1.0, _make_precond_publisher(svc), "precond", state)),
            asyncio.create_task(_every(cfg.get_path("server.lidar_hz", 5), lambda: _publish_lidar(svc), "lidar", state)),
        ]

    async def on_shutdown(app: web.Application) -> None:
        state.closing = True
        for ws in list(state.websockets):
            await ws.close(code=1001, message=b"server shutdown")

    async def on_cleanup(app: web.Application) -> None:
        for t in state.tasks:
            t.cancel()
        await asyncio.gather(*state.tasks, return_exceptions=True)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_cleanup.append(on_cleanup)
    return app


async def serve(svc: Services, host: str | None = None, port: int | None = None) -> web.AppRunner:
    """Start the server on the running loop; returns the AppRunner (``await runner.cleanup()`` to stop)."""
    app = create_app(svc)
    runner = web.AppRunner(app, access_log=None, handle_signals=False, shutdown_timeout=2.0)
    await runner.setup()
    site = web.TCPSite(runner, host or svc.cfg.get_path("server.host", "0.0.0.0"),
                       int(port or svc.cfg.get_path("server.port", 8080)))
    await site.start()
    return runner
