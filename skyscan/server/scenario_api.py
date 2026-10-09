"""HTTP endpoints behind the dashboard's RANDOM pop-up (see skyscan/sim/scenario.py).

    GET  /api/scenario            what is loaded now (canonical course or a scenario) and the zone it is drawn in
    POST /api/scenario/preview    {params} -> the layout those parameters give; nothing changes
    POST /api/scenario/apply      {params} -> write the world, swap truth + UI course, restart Gazebo + SITL
    POST /api/scenario/reset      back to the canonical course (sim/course.yaml), restart Gazebo + SITL

Applying restarts the simulator, so it is refused while a mission run is in progress, and on a real vehicle. A scenario
lasts until the next reset or until the server restarts (a restarted server starts on the canonical course again).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiohttp import web

from skyscan.bus import jsonable
from skyscan.config import repo_path
from skyscan.sim import scenario as sc
from skyscan.sim.course import Course
from skyscan.types import Sev
from skyscan.utils.logger import get_logger

log = get_logger("SERVER/SCENARIO")


def _zone(svc: Any) -> sc.Zone:
    z = svc.cfg.get_path("mission.stage_c.zone")
    if not z:
        raise web.HTTPServiceUnavailable(text="no delivery zone in the config (mission.stage_c.zone)")
    return sc.Zone.from_cfg(z)


def info(svc: Any) -> dict[str, Any]:
    cur = svc.scenario
    return {
        "available": bool(svc.profile == "sim" and svc.procman is not None),
        "busy": bool(svc.runner is not None and getattr(svc.runner, "busy", False)),
        "active": bool(cur),
        "scenario": cur.get("layout") if cur else None,
        "params": cur.get("params") if cur else None,
        "zone": _zone(svc).to_dict(),
        "letters": list(sc.LETTERS),
    }


def _fail(status: int, text: str) -> web.Response:
    return web.json_response({"ok": False, "error": text}, status=status)


async def _body(request: web.Request) -> dict[str, Any]:
    if not request.content_type.startswith("application/json"):
        raise web.HTTPUnsupportedMediaType(text="send application/json")
    try:
        d = await request.json()
    except Exception:  # noqa: BLE001
        raise web.HTTPBadRequest(text="invalid JSON") from None
    return d if isinstance(d, dict) else {}


def register(app: web.Application, get_svc: Callable[[web.Request], Any], spawn: Callable[[Any, Awaitable[Any], str], None]) -> None:
    def svc_of(request: web.Request) -> Any:
        return get_svc(request)

    async def get_info(request: web.Request) -> web.Response:
        return web.json_response(jsonable(info(svc_of(request))))

    async def preview(request: web.Request) -> web.Response:
        svc = svc_of(request)
        try:
            params = sc.Params.from_dict((await _body(request)).get("params"))
            layout = sc.generate(params, _zone(svc))
        except sc.ScenarioError as exc:
            return _fail(400, str(exc))
        return web.json_response(jsonable({"ok": True, "layout": sc.describe(layout, params)}))

    def guard(svc: Any) -> web.Response | None:
        if svc.profile != "sim" or svc.procman is None:
            return _fail(409, "scenarios need the simulator (sim profile)")
        if svc.runner is not None and getattr(svc.runner, "busy", False):
            return _fail(409, "a run is in progress: abort it first (applying restarts the simulator)")
        return None

    def baseline(svc: Any) -> tuple[Path, Path]:
        """(canonical world file, canonical course file); remembered the first time a scenario is applied."""
        st = svc.scenario_base
        if st is None:
            st = (Path(svc.procman.world_file), repo_path(svc.cfg.get_path("sim.course_file", "sim/course.yaml")))
            svc.scenario_base = st
        return st

    def swap_course(svc: Any, course: Course | None, extra: dict[str, Any]) -> None:
        if svc.truth_comp is not None:
            svc.truth_comp.course = course
        svc.course = course.to_dict() if course else None
        svc.bus.publish("course", {"course": svc.course, **extra})

    async def apply(request: web.Request) -> web.Response:
        svc = svc_of(request)
        bad = guard(svc)
        if bad:
            return bad
        try:
            params = sc.Params.from_dict((await _body(request)).get("params"))
            layout = sc.generate(params, _zone(svc))
        except sc.ScenarioError as exc:
            return _fail(400, str(exc))
        world_file, course_file = baseline(svc)
        out_dir = world_file.parent / "scenario"
        try:
            files = await asyncio.get_running_loop().run_in_executor(None, sc.write, layout, course_file, out_dir)
            course = Course.from_yaml(files["course"])
        except Exception as exc:  # noqa: BLE001
            log.exception("scenario write failed")
            return _fail(500, f"could not build the world: {exc}")
        svc.procman.world_file = files["world"]
        desc = sc.describe(layout, params)
        svc.scenario = {"layout": desc, "params": params.to_dict()}
        swap_course(svc, course, {"scenario": desc})
        if svc.runner is not None:
            try:
                await asyncio.get_running_loop().run_in_executor(None, svc.runner.reset)
            except RuntimeError:
                pass
        svc.bus.event("SIM", f"Random scenario applied: seed {layout.seed}, {len(layout.reds)} red zone(s), "
                             f"{len(layout.qrs)} QR codes, delivery target {layout.target}. Restarting the simulator.", Sev.INFO)
        spawn(svc, svc.procman.restart_sim(), "sim restart (scenario)")
        return web.json_response(jsonable({"ok": True, "message": "Scenario written. The simulator is restarting.", "layout": desc}))

    async def reset(request: web.Request) -> web.Response:
        svc = svc_of(request)
        bad = guard(svc)
        if bad:
            return bad
        world_file, course_file = baseline(svc)
        svc.procman.world_file = world_file
        svc.scenario = None
        swap_course(svc, Course.from_yaml(course_file) if course_file.exists() else None, {"scenario": None})
        if svc.runner is not None:
            try:
                await asyncio.get_running_loop().run_in_executor(None, svc.runner.reset)
            except RuntimeError:
                pass
        svc.bus.event("SIM", "Canonical course restored. Restarting the simulator.", Sev.INFO)
        spawn(svc, svc.procman.restart_sim(), "sim restart (canonical course)")
        return web.json_response({"ok": True, "message": "Canonical course restored. The simulator is restarting."})

    app.router.add_get("/api/scenario", get_info)
    app.router.add_post("/api/scenario/preview", preview)
    app.router.add_post("/api/scenario/apply", apply)
    app.router.add_post("/api/scenario/reset", reset)
