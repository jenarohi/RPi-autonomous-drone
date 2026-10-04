"""Run recorder: files appear per run with telemetry, events, reports."""
import csv
import json
import time

from skyscan.bus import EventBus
from skyscan.config import load_config
from skyscan.recorder import TELEM_COLUMNS, Recorder
from skyscan.types import Check, StageReport, StageState, VehicleState


def _wait_for(path, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


def test_recorder_writes_run_files(tmp_path):
    cfg = load_config(overrides=[f"server.runs_dir={tmp_path}"])
    bus = EventBus()
    rec = Recorder(cfg, bus)
    rec.start()
    try:
        bus.event("SYS", "before run")                       # session only
        bus.publish("telem", {"v": VehicleState(armed=False)})   # no run yet → not in a run csv
        bus.publish("run", {"state": "running", "run_id": "R1", "stages": ["A1"], "current": "A1",
                            "started_at": time.time(), "ended_at": None, "message": ""})
        for i in range(5):
            bus.publish("telem", {"v": VehicleState(armed=True, mode="GUIDED", ned=(0.0, 0.0, -i * 0.5),
                                                    rel_alt_m=i * 0.5)})
            bus.publish("vision", {"key": "down", "cam": "down", "seq": i})
        rep = StageReport("A1", "Autonomous Takeoff", state=StageState.SUCCESS, run_id="R1",
                          started_at=time.time() - 9, ended_at=time.time(), message="hover at 2.5 m",
                          checks=[Check("link", True, "heartbeat 0.2 s")],
                          criteria=[Check("altitude", True, "2.48 m", value=2.48, limit=0.3)],
                          metrics={"time_to_alt_s": 7.2}, snapshots=["/runs/R1/a1_end.jpg"],
                          log=[{"ts": time.time(), "sev": "info", "msg": "armed"}])
        bus.publish("stage", {"key": "A1", "report": rep})
        bus.publish("mission", {"origin": {"ned": [0, 0, 0], "heading_deg": 90.0}, "outputs": {}})
        bus.event("MISSION", "A1 success", "good")
        bus.publish("run", {"state": "done", "run_id": "R1", "stages": ["A1"], "current": None,
                            "started_at": time.time() - 10, "ended_at": time.time(), "message": "1/1 stages"})
        assert _wait_for(tmp_path / "R1" / "report.html")
    finally:
        rec.stop()
    run = tmp_path / "R1"
    rows = list(csv.reader(open(run / "telemetry.csv")))
    assert rows[0] == TELEM_COLUMNS and len(rows) == 6
    assert rows[-1][TELEM_COLUMNS.index("ned_d")] == "-2.0"
    events = [json.loads(line) for line in open(run / "events.jsonl")]
    kinds = [e["t"] for e in events]
    assert "stage" in kinds and "mission" in kinds and "telem" not in kinds
    assert not any(e.get("msg") == "before run" for e in events)
    assert len(open(run / "vision.jsonl").readlines()) == 1        # downsampled
    summary = json.load(open(run / "run.json"))
    assert summary["stages"]["A1"]["state"] == "success"
    md = (run / "REPORT.md").read_text()
    assert "A1 — Autonomous Takeoff — SUCCESS" in md and "time_to_alt_s" in md and "![](a1_end.jpg)" in md
    assert "<img src='a1_end.jpg'>" in (run / "report.html").read_text()
    sessions = list((tmp_path / "sessions").glob("*.jsonl"))
    assert sessions and "before run" in sessions[0].read_text()
