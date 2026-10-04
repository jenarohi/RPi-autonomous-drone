#!/usr/bin/env python3
"""Pre-generate the cockpit's voice callouts with Deepgram text-to-speech.

    DEEPGRAM_API_KEY=... python scripts/dev/gen_voice.py            # generate missing clips
    python scripts/dev/gen_voice.py --check                          # list callouts in app.js that have no clip

Writes skyscan/server/static/voice/<hash>.mp3 and manifest.json ({text: url}). The UI plays a clip when the text is
in the manifest and falls back to the browser's speech synthesis for anything else (custom messages). The API key is
only needed here, never at runtime, and is never stored in the repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "skyscan" / "server" / "static"
OUT = STATIC / "voice"
URL = "https://api.deepgram.com/v2/speak?model=flux-hannah-en&speed=1&expressivity=0"

FIXED = [
    "Voice callouts enabled.",
    "Aborting the mission run. Holding position.",
    "Starting mission sequence.",
    "Mission state reset.",
    "Holding position. Loiter mode engaged.",
    "Preparing for landing. Initiating vertical descent.",
    "Return to launch engaged. Returning to base.",
    "Emergency disarm. Motors stopped.",
    "Stopping simulation stack.",
    "Starting simulation stack.",
    "Restarting simulation stack.",
    "Preparing for landing. Vertical descent initiated.",
    "Return to launch active. Returning to base.",
    "Loiter mode engaged. Drone holding position.",
    "Drone is taking off. Climbing to 2.5 meters.",
    "Climbing to 5 meters altitude and positioning forward.",
    "Scanning the start QR code.",
    "Looking for the green corridor. Aligning with its axis.",
    "Takeoff complete. Hover stabilized at 2.5 meters.",
    "Climb and positioning complete. 5 meters altitude established.",
    "Start QR code decoded successfully.",
    "Green corridor aligned. Axis locked.",
    "Stage A pre-corridor operations completed successfully.",
    "Mission run aborted.",
    "Simulation stack online and ready.",
]
STAGES = ["A1", "A2", "A3", "A4"]
TARGETS = ["A", "B", "C", "D", "E"]


def phrases() -> list[str]:
    out = list(FIXED)
    out += [f"Running stage {s}." for s in STAGES]
    out += [f"Stage {s} failed." for s in STAGES]
    out += [f"Delivery target confirmed: Target {t}." for t in TARGETS]
    return out


def clip_name(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12] + ".mp3"


def check() -> int:
    known = set(phrases())
    src = (STATIC / "app.js").read_text()
    literals = set(re.findall(r"speak\('([^'$]+)'", src))
    missing = sorted(literals - known)
    for m in missing:
        print("no clip planned for:", m)
    print(f"{len(literals)} literal callouts in app.js, {len(missing)} without a clip")
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate clips that already exist")
    args = ap.parse_args()
    if args.check:
        return check()
    key = os.environ.get("DEEPGRAM_API_KEY")
    if not key:
        print("set DEEPGRAM_API_KEY in the environment", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    failed = 0
    for text in phrases():
        name = clip_name(text)
        path = OUT / name
        if args.force or not path.exists():
            req = urllib.request.Request(URL, data=json.dumps({"text": text}).encode(), method="POST",
                                         headers={"Authorization": f"Token {key}", "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    path.write_bytes(r.read())
                print("generated", name, "-", text)
            except (urllib.error.URLError, TimeoutError) as exc:
                print("FAILED", text, "-", exc, file=sys.stderr)
                failed += 1
                continue
        manifest[text] = f"/static/voice/{name}"
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    print(f"{len(manifest)} clips in manifest, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
