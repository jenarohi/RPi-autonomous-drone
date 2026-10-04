"""Run recorder — everything a run produced, for post-flight review.

    runs/<run_id>/
      events.jsonl    every bus message during the run except high-rate state (+ a short tail)
      telemetry.csv   VehicleState rows at the telem rate
      vision.jsonl    vision messages, downsampled to ≤ 2 Hz per camera
      run.json        final run message, stage reports, mission state
      REPORT.md / report.html   human-readable summary (snapshots inline in the HTML)
      *.jpg           stage snapshots (written by the mission runner)
    runs/sessions/<start>.jsonl   all non-high-rate messages of this server session

The bus listener only enqueues; one writer thread does all file I/O.
"""
from __future__ import annotations

import csv
import html
import json
import logging
import queue
import threading
import time
from dataclasses import fields
from pathlib import Path
from typing import Any, TextIO

from skyscan.bus import EventBus
from skyscan.config import Cfg, repo_path
from skyscan.types import VehicleState

log = logging.getLogger(__name__)

HIGH_RATE = {"telem", "vision", "proc", "truth"}
TERMINAL_RUN_STATES = {"done", "failed", "aborted", "nogo"}
TAIL_S = 3.0
VISION_MIN_DT = 0.5


def _telem_columns() -> list[str]:
    cols = ["ts"]
    for f in fields(VehicleState):
        if f.name in ("ned", "vel_ned", "home_ned"):
            cols += [f"{f.name}_{a}" for a in ("n", "e", "d")]
        elif f.name == "home":
            cols += ["home_lat", "home_lon", "home_alt"]
        else:
            cols.append(f.name)
    return cols


TELEM_COLUMNS = _telem_columns()


def _telem_row(msg: dict) -> list[Any]:
    v = msg.get("v") or {}
    row: list[Any] = [msg.get("ts")]
    for f in fields(VehicleState):
        val = v.get(f.name)
        if f.name in ("ned", "vel_ned", "home_ned", "home"):
            row += list(val) if isinstance(val, (list, tuple)) and len(val) == 3 else [None, None, None]
        else:
            row.append(val)
    return row


class _RunFiles:
    def __init__(self, run_dir: Path, run_id: str) -> None:
        self.run_id = run_id
        self.dir = run_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events: TextIO = open(self.dir / "events.jsonl", "a", encoding="utf-8")
        self.vision: TextIO = open(self.dir / "vision.jsonl", "a", encoding="utf-8")
        tel_path = self.dir / "telemetry.csv"
        new = not tel_path.exists()
        self._tel_fh: TextIO = open(tel_path, "a", newline="", encoding="utf-8")
        self.telem = csv.writer(self._tel_fh)
        if new:
            self.telem.writerow(TELEM_COLUMNS)
        self.last_vision: dict[str, float] = {}
        self.stages: dict[str, dict] = {}
        self.run_msg: dict | None = None
        self.mission: dict | None = None
        self.closing_at: float | None = None

    def close(self) -> None:
        for fh in (self.events, self.vision, self._tel_fh):
            try:
                fh.close()
            except OSError:
                pass


class Recorder:
    def __init__(self, cfg: Cfg, bus: EventBus) -> None:
        self.cfg = cfg
        self.bus = bus
        self.runs_dir = repo_path(cfg.get_path("server.runs_dir", "runs"))
        self._q: queue.Queue[dict | None] = queue.Queue(maxsize=20000)
        self._thread: threading.Thread | None = None
        self._run: _RunFiles | None = None
        self._session: TextIO | None = None
        self.dropped = 0

    # ── lifecycle ──────────────────────────────────────────────────────
    def start(self) -> None:
        if self._thread is not None:
            return
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        sess_dir = self.runs_dir / "sessions"
        sess_dir.mkdir(parents=True, exist_ok=True)
        self._session = open(sess_dir / f"{time.strftime('%Y%m%d-%H%M%S')}.jsonl", "a", encoding="utf-8")
        self._thread = threading.Thread(target=self._writer, name="recorder", daemon=True)
        self._thread.start()
        self.bus.add_listener(self._on_msg)

    def stop(self, timeout: float = 3.0) -> None:
        self.bus.remove_listener(self._on_msg)
        if self._thread is None:
            return
        self._q.put(None)
        self._thread.join(timeout)
        self._thread = None

    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def save_snapshot(self, stage_id: str, name: str, img: Any) -> str | None:
        if self._run is None:
            return None
        import cv2
        fname = f"{stage_id}_{name}_{int(time.time())}.jpg"
        p = self._run.dir / fname
        try:
            cv2.imwrite(str(p), img)
            return f"/runs/{self._run.run_id}/{fname}"
        except Exception:
            return None

    # ── bus side (publishing thread: enqueue only) ─────────────────────
    def _on_msg(self, msg: dict) -> None:
        try:
            self._q.put_nowait(msg)
        except queue.Full:
            self.dropped += 1

    # ── writer thread ──────────────────────────────────────────────────
    def _writer(self) -> None:
        while True:
            try:
                msg = self._q.get(timeout=0.5)
            except queue.Empty:
                msg = ...  # type: ignore[assignment]
            if msg is None:
                break
            try:
                if msg is not ...:
                    self._handle(msg)
                self._maybe_finish()
            except Exception:  # noqa: BLE001 - recording must never take the server down
                log.exception("recorder failed on %s", msg if msg is ... else msg.get("t"))
        if self._run is not None:
            self._finish()
        if self._session is not None:
            self._session.close()

    def _handle(self, msg: dict) -> None:
        kind = msg.get("t")
        if kind not in HIGH_RATE and self._session is not None:
            self._session.write(json.dumps(msg, separators=(",", ":")) + "\n")
            self._session.flush()
        if kind == "run":
            self._on_run(msg)
        run = self._run
        if run is None:
            return
        if kind == "telem":
            run.telem.writerow(_telem_row(msg))
        elif kind == "vision":
            cam = str(msg.get("key"))
            ts = float(msg.get("ts") or 0)
            if ts - run.last_vision.get(cam, 0.0) >= VISION_MIN_DT:
                run.last_vision[cam] = ts
                run.vision.write(json.dumps(msg, separators=(",", ":")) + "\n")
        elif kind not in HIGH_RATE:
            run.events.write(json.dumps(msg, separators=(",", ":")) + "\n")
            run.events.flush()
            if kind == "stage" and msg.get("key"):
                run.stages[str(msg["key"])] = msg.get("report") or {}
            elif kind == "mission":
                run.mission = msg

    def _on_run(self, msg: dict) -> None:
        run_id = msg.get("run_id")
        state = msg.get("state")
        if not run_id:
            return
        if self._run is not None and self._run.run_id != run_id:
            self._finish()
        if self._run is None and state not in TERMINAL_RUN_STATES | {"idle"}:
            self._run = _RunFiles(self.run_dir(str(run_id)), str(run_id))
        if self._run is not None:
            self._run.run_msg = msg
            if state in TERMINAL_RUN_STATES and self._run.closing_at is None:
                self._run.closing_at = time.time() + TAIL_S

    def _maybe_finish(self) -> None:
        if self._run is not None and self._run.closing_at is not None and time.time() >= self._run.closing_at:
            self._finish()

    def _finish(self) -> None:
        run = self._run
        self._run = None
        if run is None:
            return
        try:
            summary = {"run": run.run_msg, "stages": run.stages, "mission": run.mission}
            (run.dir / "run.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            (run.dir / "REPORT.md").write_text(render_markdown(summary), encoding="utf-8")
            (run.dir / "report.html").write_text(render_html(summary), encoding="utf-8")
        finally:
            run.close()


# ───────────────────────────── report rendering ─────────────────────────────

def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:.4g}"
    if isinstance(v, (dict, list)):
        return json.dumps(v, separators=(", ", ": "))
    return str(v)


def _clock(ts: float | None) -> str:
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "—"


def _dur(rep: dict) -> str:
    a, b = rep.get("started_at"), rep.get("ended_at")
    return f"{b - a:.1f} s" if a and b else "—"


def _ordered_stages(summary: dict) -> list[tuple[str, dict]]:
    run = summary.get("run") or {}
    order = list(run.get("stages") or [])
    stages = summary.get("stages") or {}
    keys = [k for k in order if k in stages] + sorted(k for k in stages if k not in order)
    return [(k, stages[k]) for k in keys]


def render_markdown(summary: dict) -> str:
    run = summary.get("run") or {}
    out = [f"# SkyScan run {run.get('run_id', '?')}", "",
           f"- **Result:** {str(run.get('state', '?')).upper()} — {run.get('message') or ''}",
           f"- **Stages selected:** {', '.join(run.get('stages') or [])}",
           f"- **Started:** {_clock(run.get('started_at'))} · **Ended:** {_clock(run.get('ended_at'))}", ""]
    for sid, rep in _ordered_stages(summary):
        out += [f"## {sid} — {rep.get('title', '')} — {str(rep.get('state', '?')).upper()} ({_dur(rep)})", ""]
        if rep.get("message"):
            out += [rep["message"], ""]
        if rep.get("error"):
            out += [f"**Error:** {rep['error']}", ""]
        for title, key in (("Preconditions", "checks"), ("Success criteria", "criteria")):
            items = rep.get(key) or []
            if items:
                out += [f"### {title}", "", "| | check | value | limit | detail |", "|---|---|---|---|---|"]
                for c in items:
                    mark = "GO" if c.get("ok") else ("NO-GO" if c.get("blocking", True) else "WARN")
                    out.append(f"| {mark} | {c.get('name')} | {_fmt(c.get('value'))} | {_fmt(c.get('limit'))} "
                               f"| {c.get('detail', '')} |")
                out.append("")
        for title, key in (("Metrics", "metrics"), ("Outputs", "outputs")):
            items = rep.get(key) or {}
            if items:
                out += [f"### {title}", ""] + [f"- **{k}:** {_fmt(v)}" for k, v in items.items()] + [""]
        if rep.get("snapshots"):
            out += ["### Snapshots", ""] + [f"![]({Path(s).name})" for s in rep["snapshots"]] + [""]
        if rep.get("log"):
            out += ["### Stage log", ""] + [f"- {_clock(e.get('ts'))} [{e.get('sev', 'info')}] {e.get('msg', '')}"
                                            for e in rep["log"]] + [""]
    mission = (summary.get("mission") or {})
    if mission:
        out += ["## Mission state", "", "```json", json.dumps({k: mission.get(k) for k in ("origin", "outputs")},
                                                              indent=2), "```", ""]
    return "\n".join(out)


def render_html(summary: dict) -> str:
    run = summary.get("run") or {}
    e = html.escape
    parts = [f"<!doctype html><meta charset=utf-8><title>SkyScan run {e(str(run.get('run_id', '')))}</title>",
             "<style>body{font:14px/1.45 system-ui,sans-serif;margin:24px auto;max-width:1100px;background:#0b1018;"
             "color:#d6e2f0}h1,h2,h3{font-weight:600}h2{border-top:1px solid #243246;padding-top:14px}"
             "table{border-collapse:collapse;margin:6px 0 12px}td,th{border:1px solid #243246;padding:3px 8px;"
             "text-align:left}.ok{color:#4cd07d}.bad{color:#ff5d5d}.warn{color:#ffb84d}img{max-width:48%;"
             "margin:4px;border:1px solid #243246}code{color:#9fd3ff}</style>",
             f"<h1>SkyScan run {e(str(run.get('run_id', '?')))}</h1>",
             f"<p><b>Result:</b> {e(str(run.get('state', '?')).upper())} — {e(str(run.get('message') or ''))}<br>"
             f"<b>Stages:</b> {e(', '.join(run.get('stages') or []))} · <b>Started</b> {_clock(run.get('started_at'))}"
             f" · <b>Ended</b> {_clock(run.get('ended_at'))}</p>"]
    for sid, rep in _ordered_stages(summary):
        state = str(rep.get("state", "?"))
        cls = "ok" if state == "success" else ("bad" if state in ("failed", "nogo", "aborted") else "warn")
        parts.append(f"<h2>{e(sid)} — {e(str(rep.get('title', '')))} — <span class={cls}>{e(state.upper())}</span>"
                     f" <small>({_dur(rep)})</small></h2>")
        if rep.get("message"):
            parts.append(f"<p>{e(rep['message'])}</p>")
        if rep.get("error"):
            parts.append(f"<p class=bad><b>Error:</b> {e(rep['error'])}</p>")
        for title, key in (("Preconditions", "checks"), ("Success criteria", "criteria")):
            items = rep.get(key) or []
            if items:
                rows = "".join(
                    f"<tr><td class={'ok' if c.get('ok') else ('bad' if c.get('blocking', True) else 'warn')}>"
                    f"{'GO' if c.get('ok') else ('NO-GO' if c.get('blocking', True) else 'WARN')}</td>"
                    f"<td>{e(str(c.get('name')))}</td><td>{e(_fmt(c.get('value')))}</td>"
                    f"<td>{e(_fmt(c.get('limit')))}</td><td>{e(str(c.get('detail', '')))}</td></tr>" for c in items)
                parts.append(f"<h3>{title}</h3><table><tr><th></th><th>check</th><th>value</th><th>limit</th>"
                             f"<th>detail</th></tr>{rows}</table>")
        for title, key in (("Metrics", "metrics"), ("Outputs", "outputs")):
            items = rep.get(key) or {}
            if items:
                rows = "".join(f"<tr><td>{e(str(k))}</td><td><code>{e(_fmt(v))}</code></td></tr>"
                               for k, v in items.items())
                parts.append(f"<h3>{title}</h3><table>{rows}</table>")
        if rep.get("snapshots"):
            parts.append("<h3>Snapshots</h3>" + "".join(f"<img src='{e(Path(s).name)}'>" for s in rep["snapshots"]))
        if rep.get("log"):
            parts.append("<h3>Stage log</h3><pre>" + e("\n".join(
                f"{_clock(x.get('ts'))} [{x.get('sev', 'info')}] {x.get('msg', '')}" for x in rep["log"])) + "</pre>")
    return "\n".join(parts)
