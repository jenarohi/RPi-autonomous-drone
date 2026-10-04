# SkyScan Mission Control

Team **Axiom Dynamics** · AeroTHON 2026 · Track 1 · Mission 2 ("SkyScan: Autonomous Rapid Delivery").

This branch (`stage-a-mission-control`) rebuilds the autonomous-drone software around one mission-control web UI
and implements **Stage A (pre-corridor operations)**:

| | |
|---|---|
| A1 | autonomous takeoff |
| A2 | climb to 5 m and move forward about 1 m |
| A3 | detect and decode the start QR code (flat on the ground, scanned from 5 m) |
| A4 | detect the green corridor and align with its entrance |

The simulated course is the original SkyScan world (`legacy/aerothon_mission.sdf`). The old 12-state prototype is
kept untouched in `legacy/`.

## Run it

On the robotics box, double-click **SkyScan Mission Control** on the desktop, or:

```bash
scripts/skyscan.sh            # Gazebo (headless) + ArduPilot SITL + server + one full-screen Firefox window
scripts/skyscan.sh --no-sim   # server only
scripts/skyscan.sh --window   # normal window instead of kiosk
```

Close the Firefox window to stop everything. The cockpit is also at `http://barathros.local:8080` from any
computer on the network. Server log: `~/.local/state/skyscan/server.log`.

In the UI: tick stages and press **RUN SELECTED**, or press the **RUN** button on a stage card. Every stage shows a
live **GO / NO-GO** and a **DETAILS** drawer (preconditions, success criteria with measured values, measurements,
products, stage log, snapshots). Nothing runs unless you press a button. The **GAZEBO 3D** tab is Gazebo itself,
embedded in the page.

## Docs

* `docs/STAGE_A.md`: the course, and each stage's preconditions, procedure, success criteria and failure modes
* `docs/ARCHITECTURE.md`: modules, frames, data contract, WebSocket protocol, box facts
* `legacy/README.md`: the old prototype

## Develop

```bash
python -m pytest tests -q --ignore=tests/test_sitl_stage_a.py     # unit tests, run anywhere
scripts/dev/box.sh test --sim -- python -m pytest -s tests/test_sitl_stage_a.py -m sitl   # SITL end-to-end A1-A4 (needs the box)
python scripts/dev/ui_shot.py --url http://barathros.local:8080   # screenshots of the UI tabs
python scripts/dev/ui_run_stages.py --url http://barathros.local:8080 --mode selected   # operate the UI
```

Everything tunable is in `config/skyscan.yaml`.
