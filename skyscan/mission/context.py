"""Mission context passed to stages during execution."""
from __future__ import annotations

import math
import threading
import time
from typing import Any, Callable

from skyscan.bus import EventBus
from skyscan.geo import CourseFrame
from skyscan.types import Check, Sev, StageReport, VehicleState
from skyscan.utils.logger import get_logger

log = get_logger("MISSION/CTX")


def height_above_ground(st: VehicleState, full_cfg: Any, now: float | None = None) -> tuple[float | None, str]:
    """``MissionContext.height()`` for any vehicle state, e.g. the one saved with a camera frame (pass that frame's time
    as ``now`` so a rangefinder reading is judged against the moment of the frame, not against the present)."""
    hcfg = getattr(full_cfg, "height", None)
    source = str(getattr(hcfg, "source", "auto")).lower()
    max_age = float(getattr(hcfg, "rangefinder_max_age_s", 0.5))
    ref = time.time() if now is None else now
    rng = st.range_m
    fresh = rng is not None and st.range_t is not None and (ref - st.range_t) <= max_age
    if fresh and st.range_min_m is not None and rng < st.range_min_m:
        fresh = False
    if fresh and st.range_max_m is not None and st.range_max_m > 0 and rng > st.range_max_m:
        fresh = False
    if source in ("auto", "rangefinder") and fresh:
        tilt = math.cos(math.radians(st.roll_deg or 0.0)) * math.cos(math.radians(st.pitch_deg or 0.0))
        return float(rng) * max(0.2, tilt), "lidar"
    if source == "rangefinder":
        return None, "none"
    return st.rel_alt_m, ("ekf" if st.rel_alt_m is not None else "none")


class Aborted(Exception):
    """Raised when an operation is cancelled via abort event."""


class MissionContext:
    """Context and execution helpers provided to each running stage."""

    def __init__(
        self,
        stage_id: str,
        title: str,
        cfg: Any,
        full_cfg: Any,
        bus: EventBus,
        link: Any,
        vision: Any,
        mission_state: dict[str, Any],
        abort_event: threading.Event,
        recorder: Any = None,
        truth_fn: Callable[[], dict[str, Any] | None] | None = None,
        lidar: Any = None,
    ) -> None:
        self.stage_id = stage_id
        self.title = title
        self.cfg = cfg
        self.full_cfg = full_cfg
        self.bus = bus
        self.link = link
        self.vision = vision
        self.mission = mission_state
        self._abort = abort_event
        self.recorder = recorder
        self._truth_fn = truth_fn
        self.lidar = lidar                  # skyscan.lidar.LidarHub (2D scan), or None

        self.report = StageReport(
            stage_id=stage_id,
            title=title,
            run_id=getattr(recorder, "run_id", None) if recorder else None,
            started_at=time.time(),
        )
        self._last_phase_pub = 0.0

    @property
    def course(self) -> CourseFrame | None:
        """Get the CourseFrame if recorded in mission outputs."""
        frame = self.mission.get("_course_frame")
        if isinstance(frame, CourseFrame):
            return frame
        origin = self.mission.get("origin")
        if isinstance(origin, CourseFrame):
            return origin
        if isinstance(origin, dict) and "ned" in origin and "heading_deg" in origin:
            return CourseFrame(origin_ned=tuple(origin["ned"]), heading_deg=float(origin["heading_deg"]))
        return None

    def set_course(self, frame: CourseFrame) -> None:
        """Record the CourseFrame into shared mission state."""
        log.info(f"Setting course frame origin: NED {frame.origin_ned}, heading {frame.heading_deg}°")
        self.mission["_course_frame"] = frame
        self.mission["origin"] = frame
        self.report.outputs["origin"] = {
            "ned": list(frame.origin_ned),
            "heading_deg": frame.heading_deg,
        }
        self._publish_mission()

    def _publish_mission(self) -> None:
        """Push the shared mission products (course origin, QR payload, corridor axis ...) to the UI."""
        frame = self.course
        self.bus.publish("mission", {
            "origin": {"ned": list(frame.origin_ned), "heading_deg": frame.heading_deg} if frame else None,
            "outputs": {k: v for k, v in self.mission.items() if not k.startswith("_")},
        })

    def state(self) -> VehicleState:
        """Get current vehicle state snapshot."""
        if self.link is None:
            return VehicleState()
        return self.link.state()

    def scan(self, max_age_s: float | None = None) -> Any:
        """Latest lidar scan if it is fresh enough, else None."""
        if self.lidar is None:
            return None
        lcfg = getattr(self.full_cfg, "lidar", None)
        age = max_age_s if max_age_s is not None else float(getattr(lcfg, "fresh_s", 1.0))
        return self.lidar.fresh(age)

    def height(self) -> tuple[float | None, str]:
        """Height above the ground and which sensor says so: ``(metres, "lidar" | "ekf" | "none")``.

        The downward lidar / rangefinder (tilt-corrected) wins whenever it is reporting; the EKF's height above home
        is the fallback unless ``height.source`` forces one of them.
        """
        return height_above_ground(self.state(), self.full_cfg)

    def check_abort(self) -> None:
        """Check if abort was requested and raise Aborted."""
        if self._abort.is_set():
            log.warn("Abort detected during execution")
            raise Aborted("Stage aborted by operator or safety monitor")

    def sleep(self, seconds: float) -> None:
        """Sleep in small increments checking for abort."""
        deadline = time.time() + max(0.0, seconds)
        while time.time() < deadline:
            self.check_abort()
            time.sleep(min(0.05, max(0.001, deadline - time.time())))

    def wait(self, pred: Callable[[VehicleState], bool], timeout: float, desc: str = "") -> bool:
        """Wait for condition on vehicle state with abort check."""
        log.debug(f"Waiting for condition: {desc or 'unnamed'} (timeout={timeout}s)")
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.check_abort()
            st = self.state()
            if pred(st):
                return True
            time.sleep(0.05)
        return False

    def emit(self, msg: str, sev: Sev | str = Sev.INFO, **data: Any) -> None:
        """Emit a bus event scoped to the current mission stage."""
        if isinstance(sev, str):
            sev = Sev(sev.lower())
        now = time.time()
        self.report.log.append({"ts": now, "sev": sev.value, "msg": msg})
        self.bus.event("MISSION", msg, sev, stage=self.stage_id, **data)
        if sev in (Sev.ERROR, Sev.CRITICAL):
            log.error(f"[{self.stage_id}] {msg}")
        elif sev == Sev.WARN:
            log.warn(f"[{self.stage_id}] {msg}")
        else:
            log.info(f"[{self.stage_id}] {msg}")

    def phase(self, name: str, progress: float | None = None) -> None:
        """Update stage phase and optionally progress (throttled to 5 Hz)."""
        self.report.phase = name
        if progress is not None:
            self.report.progress = max(0.0, min(1.0, float(progress)))

        now = time.time()
        if now - self._last_phase_pub >= 0.2:
            self._last_phase_pub = now
            self.bus.publish("stage", {"key": self.stage_id, "report": self.report.to_dict()})

    def metric(self, key: str, value: Any) -> None:
        """Record a measured metric into the stage report."""
        self.report.metrics[key] = value

    def output(self, key: str, value: Any) -> None:
        """Record an output product into stage report and shared mission dict."""
        self.report.outputs[key] = value
        self.mission[key] = value
        self._publish_mission()

    def snapshot(self, cam: str, name: str, overlay: Callable[[Any], Any] | None = None) -> str | None:
        """Save an annotated camera snapshot into the run folder."""
        if not self.recorder:
            return None
        frame = self.vision.hub.latest(cam) if (self.vision and hasattr(self.vision, "hub")) else None
        if frame is None or frame.img is None:
            log.warn(f"No frame available for camera '{cam}' snapshot '{name}'")
            return None

        img = frame.img.copy()
        if overlay is not None:
            try:
                img = overlay(img)
            except Exception as exc:
                log.warn(f"Snapshot overlay failed: {exc}")
        elif self.vision and hasattr(self.vision, "annotate"):
            try:
                img = self.vision.annotate(cam, img)
            except Exception as exc:
                log.warn(f"Vision annotate failed: {exc}")

        rel_path = self.recorder.save_snapshot(self.stage_id, name, img)
        if rel_path:
            self.report.snapshots.append(rel_path)
        return rel_path

    def truth(self) -> dict[str, Any] | None:
        """Return simulator ground truth if available."""
        if self._truth_fn is not None:
            try:
                return self._truth_fn()
            except Exception:
                return None
        return None
