#!/usr/bin/env python3
"""Pre-generate the cockpit's voice callouts as mp3 clips.

    FINEVOICE_API_KEY=... python scripts/dev/gen_voice.py            # pilot voice + radio effect (default)
    DEEPGRAM_API_KEY=...  python scripts/dev/gen_voice.py --engine deepgram
    python scripts/dev/gen_voice.py --check                          # list callouts in app.js that have no clip

Writes skyscan/server/static/voice/<hash>.mp3 and manifest.json ({text: url}). The UI plays a clip when the text is
in the manifest and falls back to the browser's speech synthesis for anything else (custom messages). API keys are
only needed here, never at runtime, and are never stored in the repo.

The default engine is FineVoice "Captain Andrew Walker" (a calm aviation voice). Clips are post-processed with
ffmpeg into a cockpit-radio sound: narrow band-pass, compression, light clipping, a faint hiss bed and a squelch
burst before and after every transmission. Use --no-fx for the clean voice.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "skyscan" / "server" / "static"
OUT = STATIC / "voice"
DEEPGRAM_URL = "https://api.deepgram.com/v2/speak?model=flux-hannah-en&speed=1&expressivity=0"
FINEVOICE_API = "https://apis.finevoice.ai"
FINEVOICE_VOICE = "1f977122-8f88-4ec0-8f17-ab1542e6b77e"  # Captain Andrew Walker

# Cockpit radio: voice band-pass + compression + soft clip + hiss bed, wrapped in two squelch bursts.
RADIO_FILTER = (
    "[0:a]aformat=sample_rates=22050:channel_layouts=mono,highpass=f=380,lowpass=f=3200,"
    "acompressor=threshold=0.05:ratio=6:attack=5:release=80:makeup=4,"
    "asoftclip=type=tanh:threshold=0.6,volume=0.9[v];"
    "anoisesrc=d=60:c=pink:a=0.012:r=22050,highpass=f=500,lowpass=f=3500[hiss];"
    "[v][hiss]amix=inputs=2:duration=first:normalize=0[body];"
    "anoisesrc=d=0.09:c=white:a=0.25:r=22050,bandpass=f=1800:w=2200,afade=t=out:st=0.04:d=0.05[sq1];"
    "anoisesrc=d=0.14:c=white:a=0.22:r=22050,bandpass=f=1800:w=2200,afade=t=out:st=0.05:d=0.09[sq2];"
    "[sq1][body][sq2]concat=n=3:v=0:a=1,loudnorm=I=-16:TP=-1.5:LRA=7[o]"
)

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
    # Stage B: green corridor navigation
    "Descending to corridor altitude.",
    "Corridor altitude established.",
    "Entering the corridor.",
    "Inside the corridor.",
    "Navigating the corridor. Avoiding obstacles.",
    "Corridor traversal complete.",
    "Detecting the corridor exit.",
    "Corridor exit detected. Delivery zone ahead.",
    "Stage B corridor navigation completed successfully.",
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


def _read(req: urllib.request.Request, timeout: int = 60) -> bytes:
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw


def synth_deepgram(text: str, key: str) -> bytes:
    req = urllib.request.Request(DEEPGRAM_URL, data=json.dumps({"text": text}).encode(), method="POST",
                                 headers={"Authorization": f"Token {key}", "Content-Type": "application/json"})
    return _read(req)


def synth_finevoice(text: str, key: str) -> bytes:
    """Submit a speech-synthesis task and download the mp3 (polls the task if the result is not immediate)."""
    head = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = json.dumps({"voice": FINEVOICE_VOICE, "text": text}).encode()
    job = json.loads(_read(urllib.request.Request(f"{FINEVOICE_API}/v1/audio/speech-synthesis", data=body,
                                                  method="POST", headers=head)))
    deadline = time.time() + 90
    while not job.get("urls"):
        if job.get("status") in ("failed", "error") or time.time() > deadline or not job.get("taskId"):
            raise RuntimeError(f"finevoice task did not produce audio: {str(job)[:200]}")
        time.sleep(2)
        job = json.loads(_read(urllib.request.Request(f"{FINEVOICE_API}/v1/task/{job['taskId']}", headers=head)))
    return _read(urllib.request.Request(job["urls"][0]))


def radio_fx(mp3: bytes) -> bytes:
    """Run a clip through the cockpit-radio filter chain."""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp, "in.mp3"), Path(tmp, "out.mp3")
        src.write_bytes(mp3)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", RADIO_FILTER,
                        "-map", "[o]", "-ar", "22050", "-ac", "1", "-b:a", "48k", str(dst)], check=True)
        return dst.read_bytes()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate clips that already exist")
    ap.add_argument("--engine", choices=["finevoice", "deepgram"], default="finevoice")
    ap.add_argument("--no-fx", action="store_true", help="skip the cockpit-radio effect")
    args = ap.parse_args()
    if args.check:
        return check()
    key_var = "FINEVOICE_API_KEY" if args.engine == "finevoice" else "DEEPGRAM_API_KEY"
    key = os.environ.get(key_var)
    if not key:
        print(f"set {key_var} in the environment", file=sys.stderr)
        return 2
    use_fx = not args.no_fx
    if use_fx and not shutil.which("ffmpeg"):
        print("ffmpeg not found; install it or pass --no-fx", file=sys.stderr)
        return 2
    synth = synth_finevoice if args.engine == "finevoice" else synth_deepgram
    OUT.mkdir(parents=True, exist_ok=True)
    # engines.json remembers which engine made each clip, so a rerun only fills in clips from other/missing engines
    # (clips without a record count as deepgram, the original engine).
    engines_file = OUT / "engines.json"
    engines: dict[str, str] = json.loads(engines_file.read_text()) if engines_file.exists() else {}
    manifest: dict[str, str] = {}
    failed = 0
    for text in phrases():
        name = clip_name(text)
        path = OUT / name
        if args.force or not path.exists() or engines.get(name, "deepgram") != args.engine:
            try:
                audio = synth(text, key)
                path.write_bytes(radio_fx(audio) if use_fx else audio)
                engines[name] = args.engine
                engines_file.write_text(json.dumps(engines, indent=1, sort_keys=True))
                print("generated", name, "-", text)
            except (urllib.error.URLError, TimeoutError, RuntimeError, subprocess.CalledProcessError) as exc:
                print("FAILED", text, "-", exc, file=sys.stderr)
                failed += 1
                continue
        manifest[text] = f"/static/voice/{name}"
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True))
    print(f"{len(manifest)} clips in manifest, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
