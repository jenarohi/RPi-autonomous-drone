"""Mission runner coordinating stage execution, safety monitoring, and run lifecycle."""
from __future__ import annotations

import math
import threading
import time
import traceback
from typing import Any, Callable

from skyscan.bus import EventBus
from skyscan.mission.context import Aborted, MissionContext
from skyscan.mission.stage import Stage
from skyscan.mission.stage_a import StageA1, StageA2, StageA3, StageA4
from skyscan.mission.stage_b import StageB1, StageB2, StageB3, StageB4
from skyscan.mission.stage_c import StageC1, StageC2, StageC3, StageC4
from skyscan.mission.stage_d import StageD1, StageD2, StageD3
from skyscan.mission.stage_e import StageE1, StageE2, StageE3, StageE4, StageE5, StageE6
from skyscan.types import Check, Sev, StageReport, StageState
from skyscan.utils.logger import get_logger

log = get_logger("MISSION/RUNNER")


class MissionRunner:
    """Executes mission stages in canonical order with safety supervision."""

    def __init__(
        self,
        cfg: Any,
        bus: EventBus,
        link: Any,
        vision: Any,
        recorder: Any = None,
        truth_fn: Callable[[], dict[str, Any] | None] | None = None,
        lidar: Any = None,
    ) -> None:
        self.cfg = cfg
        self.bus = bus
        self.link = link
        self.vision = vision
        self.recorder = recorder
        self.truth_fn = truth_fn
        self.lidar = lidar

        self.stages: list[Stage] = [StageA1(), StageA2(), StageA3(), StageA4(),
                                    StageB1(), StageB2(), StageB3(), StageB4(),
                                    StageC1(), StageC2(), StageC3(), StageC4(),
                                    StageD1(), StageD2(), StageD3(),
                                    StageE1(), StageE2(), StageE3(), StageE4(), StageE5(), StageE6()]
        self._stage_map: dict[str, Stage] = {s.id: s for s in self.stages}

        self._mission_state: dict[str, Any] = {}
        self._reports: dict[str, StageReport] = {
            s.id: StageReport(stage_id=s.id, title=s.title, state=StageState.IDLE)
            for s in self.stages
        }

        self._abort_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._active_run_id: str | None = None
        self._active_stages: list[str] = []
        self._current_stage: str | None = None

    @property
    def busy(self) -> bool:
        """True if a mission thread is actively running."""
        return bool(self._thread and self._thread.is_alive())

    def reset(self) -> None:
        """Reset mission shared state and stage reports."""
        with self._lock:
            if self.busy:
                raise RuntimeError("Cannot reset while mission runner is busy")
            log.info("Resetting mission runner state")
            self._mission_state.clear()
            if hasattr(self.vision, "set_corridor_colour"):
                self.vision.set_corridor_colour("green")
            self._reports = {
                s.id: StageReport(stage_id=s.id, title=s.title, state=StageState.IDLE)
                for s in self.stages
            }
            self.bus.publish("mission", {"origin": None, "outputs": {}})
            for sid, rep in self._reports.items():
                self.bus.publish("stage", {"key": sid, "report": rep.to_dict()})
            self.bus.publish("run", {
                "state": "idle",
                "run_id": None,
                "stages": [],
                "current": None,
                "started_at": None,
                "ended_at": None,
                "message": "Reset to idle",
            })

    def describe(self) -> list[dict[str, Any]]:
        """Return stage descriptions for UI consumption."""
        desc = []
        for s in self.stages:
            desc.append(s.describe(self._stage_cfg(s)))
        return desc

    def _stage_cfg(self, stage: Stage) -> Any:
        """``mission.stage_<letter>.<id>`` (stage_a for A1..A4, stage_b for B1..B4, ..., stage_e for E1..E6)."""
        mcfg = getattr(self.cfg, "mission", self.cfg)
        group = getattr(mcfg, f"stage_{stage.id[:1].lower()}", mcfg)
        return getattr(group, stage.id.lower(), {})

    def _make_ctx(self, stage: Stage) -> MissionContext:
        return MissionContext(
            stage_id=stage.id,
            title=stage.title,
            cfg=self._stage_cfg(stage),
            full_cfg=self.cfg,
            bus=self.bus,
            link=self.link,
            vision=self.vision,
            mission_state=self._mission_state,
            abort_event=self._abort_event,
            recorder=self.recorder,
            truth_fn=self.truth_fn,
            lidar=self.lidar,
        )

    def preview(self) -> dict[str, list[Check]]:
        """Instant GO / NO-GO of every stage against the current vehicle state. Evaluates only, commands nothing."""
        out: dict[str, list[Check]] = {}
        for stage in self.stages:
            try:
                out[stage.id] = stage.preview(self._make_ctx(stage))
            except Exception as exc:  # noqa: BLE001 - a broken check must show up as NO-GO, not kill the publisher
                out[stage.id] = [Check(name="Precondition check", ok=False, detail=f"{type(exc).__name__}: {exc}")]
        return out

    def run(self, stage_ids: list[str]) -> tuple[bool, str]:
        """Start execution of selected stages in canonical order."""
        with self._lock:
            if self.busy:
                log.warn("Run rejected: mission runner is already busy")
                return False, "Mission runner is already busy"

            # Validate requested stages
            canonical = [s.id for s in self.stages if s.id in stage_ids]
            if not canonical:
                return False, f"None of requested stages {stage_ids} are valid"

            run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}"
            self._active_run_id = run_id
            self._active_stages = canonical
            self._abort_event.clear()

            # Selected stages become QUEUED; the others keep their last report (so running A3 alone does not
            # wipe what A1 and A2 produced).
            for s in self.stages:
                if s.id in canonical:
                    self._reports[s.id] = StageReport(
                        stage_id=s.id,
                        title=s.title,
                        state=StageState.QUEUED,
                        run_id=run_id,
                    )
                    self.bus.publish("stage", {"key": s.id, "report": self._reports[s.id].to_dict()})

            self.bus.publish("run", {
                "state": "running",
                "run_id": run_id,
                "stages": canonical,
                "current": None,
                "started_at": time.time(),
                "ended_at": None,
                "message": f"Starting stages {', '.join(canonical)}",
            })

            log.info(f"Starting run {run_id} with stages: {canonical}")
            self._thread = threading.Thread(target=self._run_loop, name="mission", daemon=True)
            self._thread.start()
            return True, f"Started run {run_id}"

    def abort(self, reason: str = "operator", hold: bool = True, wait_s: float = 2.0) -> bool:
        """Abort current mission run and optionally command vehicle to hold."""
        log.warn(f"Abort requested: reason='{reason}', hold={hold}")
        self._abort_event.set()

        t_end = time.time() + wait_s
        while time.time() < t_end:
            if not self.busy:
                break
            time.sleep(0.05)

        stopped = not self.busy

        if hold and self.link is not None:
            st = self.link.state()
            if st.armed:
                log.info("Enforcing HOLD after abort")
                self.link.hold(force_guided=True)

        return stopped

    # ───────────────────────────── Mission worker ─────────────────────────────

    def _run_loop(self) -> None:
        """Mission execution worker thread."""
        run_id = self._active_run_id
        stages = list(self._active_stages)
        run_started_at = time.time()
        final_state = "done"
        final_msg = "All stages completed successfully"

        safety_cfg = getattr(self.cfg, "safety", None)
        max_alt = float(getattr(safety_cfg, "max_alt_m", 12.0))
        geofence_r = float(getattr(safety_cfg, "geofence_radius_m", 60.0))

        try:
            for idx, sid in enumerate(stages):
                stage = self._stage_map[sid]
                self._current_stage = sid

                ctx = self._make_ctx(stage)

                self.bus.publish("run", {
                    "state": "running",
                    "run_id": run_id,
                    "stages": stages,
                    "current": sid,
                    "started_at": run_started_at,
                    "ended_at": None,
                    "message": f"Running stage {sid}: {stage.title}",
                })

                # 1. Preconditions check
                ctx.report.state = StageState.CHECKING
                self.bus.publish("stage", {"key": sid, "report": ctx.report.to_dict()})

                checks = stage.preconditions(ctx)
                ctx.report.checks = checks

                blocking_failed = [c for c in checks if (not c.ok) and c.blocking]
                if blocking_failed:
                    ctx.report.state = StageState.NOGO
                    ctx.report.ended_at = time.time()
                    ctx.report.error = f"Blocking precondition failed: {blocking_failed[0].name} ({blocking_failed[0].detail})"
                    ctx.report.message = f"NO-GO: {blocking_failed[0].name}"
                    self._reports[sid] = ctx.report
                    self.bus.publish("stage", {"key": sid, "report": ctx.report.to_dict()})

                    self._skip_remaining(stages[idx + 1:], run_id)
                    final_state = "nogo"
                    final_msg = f"Stage {sid} NO-GO: {blocking_failed[0].name}"
                    log.warn(final_msg)
                    return

                # 2. Run stage
                ctx.report.state = StageState.RUNNING
                self.bus.publish("stage", {"key": sid, "report": ctx.report.to_dict()})

                # Start safety monitor helper thread for this stage
                stop_safety = threading.Event()
                safety_thread = threading.Thread(
                    target=self._safety_monitor,
                    args=(stop_safety, max_alt, geofence_r),
                    name=f"safety-{sid}",
                    daemon=True
                )
                safety_thread.start()

                try:
                    success = stage.run(ctx)
                finally:
                    stop_safety.set()
                    safety_thread.join(timeout=1.0)

                ctx.report.ended_at = time.time()
                if success:
                    ctx.report.state = StageState.SUCCESS
                    ctx.report.message = ctx.report.message or f"Stage {sid} completed successfully"
                    self._reports[sid] = ctx.report
                    self.bus.publish("stage", {"key": sid, "report": ctx.report.to_dict()})
                else:
                    ctx.report.state = StageState.FAILED
                    ctx.report.message = ctx.report.message or f"Stage {sid} failed"
                    self._reports[sid] = ctx.report
                    self.bus.publish("stage", {"key": sid, "report": ctx.report.to_dict()})

                    self._skip_remaining(stages[idx + 1:], run_id)
                    final_state = "failed"
                    final_msg = f"Stage {sid} failed"
                    if self.link:
                        self.link.hold(force_guided=True)
                    return

        except Aborted as exc:
            log.warn(f"Run aborted: {exc}")
            sid = self._current_stage or "unknown"
            if sid in self._reports:
                rep = self._reports[sid]
                rep.state = StageState.ABORTED
                rep.ended_at = time.time()
                rep.error = str(exc)
                rep.message = "Aborted by operator or safety trigger"
                self.bus.publish("stage", {"key": sid, "report": rep.to_dict()})
            idx = stages.index(sid) if sid in stages else -1
            if idx >= 0:
                self._skip_remaining(stages[idx + 1:], run_id)
            final_state = "aborted"
            final_msg = f"Aborted: {exc}"

        except Exception as exc:
            log.error(f"Unexpected exception during stage execution: {exc}")
            sid = self._current_stage or "unknown"
            if sid in self._reports:
                rep = self._reports[sid]
                rep.state = StageState.FAILED
                rep.ended_at = time.time()
                rep.error = traceback.format_exc()
                rep.message = f"Unhandled error: {exc}"
                self.bus.publish("stage", {"key": sid, "report": rep.to_dict()})
            idx = stages.index(sid) if sid in stages else -1
            if idx >= 0:
                self._skip_remaining(stages[idx + 1:], run_id)
            final_state = "failed"
            final_msg = f"Error in {sid}: {exc}"
            if self.link:
                self.link.hold(force_guided=True)

        finally:
            self._current_stage = None
            self.bus.publish("run", {
                "state": final_state,
                "run_id": run_id,
                "stages": stages,
                "current": None,
                "started_at": run_started_at,
                "ended_at": time.time(),
                "message": final_msg,
            })
            log.info(f"Run {run_id} finished: {final_state.upper()} ({final_msg})")

    def _skip_remaining(self, remaining_stages: list[str], run_id: str) -> None:
        """Mark remaining stages as SKIPPED."""
        for sid in remaining_stages:
            rep = StageReport(
                stage_id=sid,
                title=self._stage_map[sid].title,
                state=StageState.SKIPPED,
                run_id=run_id,
                message="Skipped due to earlier stage result",
            )
            self._reports[sid] = rep
            self.bus.publish("stage", {"key": sid, "report": rep.to_dict()})

    def _safety_monitor(self, stop_event: threading.Event, max_alt: float, geofence_r: float) -> None:
        """Background safety supervisor while a stage runs."""
        while not stop_event.is_set() and not self._abort_event.is_set():
            if self.link is None:
                break
            st = self.link.state()

            # 1. Heartbeat link loss
            if not st.link:
                log.error("Safety violation: vehicle telemetry link lost!")
                self.bus.event("MISSION", "Safety violation: MAVLink link lost", Sev.CRITICAL)
                self._abort_event.set()
                break

            # 2. Mode changed away from GUIDED (manual takeover / RC switch). A stage that hands over to the flight
            #    controller itself (E6: LAND for the touchdown) lists that mode in ``_allowed_modes`` while it does.
            allowed = ("GUIDED", "AUTO", "UNKNOWN", *self._mission_state.get("_allowed_modes", ()))
            if st.armed and st.mode not in allowed:
                log.warn(f"Operator takeover detected! Mode changed to {st.mode}. Halting autonomous mission.")
                self.bus.event("MISSION", f"Operator takeover: mode changed to {st.mode}", Sev.WARN)
                # Abort without sending hold command (let the human fly!)
                self._abort_event.set()
                break

            # 3. Altitude limit check
            if st.rel_alt_m is not None and st.rel_alt_m > max_alt:
                log.error(f"Safety violation: maximum altitude exceeded! ({st.rel_alt_m:.1f}m > {max_alt}m)")
                self.bus.event("MISSION", f"Altitude ceiling breached: {st.rel_alt_m:.1f}m > {max_alt}m", Sev.CRITICAL)
                self._abort_event.set()
                break

            # 4. Geofence radius check from course origin
            origin = self._mission_state.get("_course_frame") or self._mission_state.get("origin")
            origin_ned = None
            if hasattr(origin, "origin_ned"):
                origin_ned = origin.origin_ned
            elif isinstance(origin, dict) and "ned" in origin:
                origin_ned = origin["ned"]

            if origin_ned and st.ned is not None:
                dx = st.ned[0] - origin_ned[0]
                dy = st.ned[1] - origin_ned[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > geofence_r:
                    log.error(f"Safety violation: geofence breached! ({dist:.1f}m > {geofence_r}m)")
                    self.bus.event("MISSION", f"Geofence breached: {dist:.1f}m > {geofence_r}m", Sev.CRITICAL)
                    self._abort_event.set()
                    break

            time.sleep(0.2)
