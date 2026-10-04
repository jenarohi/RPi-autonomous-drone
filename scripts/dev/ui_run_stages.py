#!/usr/bin/env python3
"""Drive the mission-control UI like an operator and report what each stage card shows.

    python scripts/dev/ui_run_stages.py --url http://barathros.local:8080 --mode stage    --stages A1,A2,A3,A4 --out /tmp/run
    python scripts/dev/ui_run_stages.py --url http://barathros.local:8080 --mode selected --stages A1,A2 --out /tmp/run

  --mode stage     press each stage's own RUN button, one after the other, waiting for it to finish
  --mode selected  tick only --stages, then press RUN SELECTED once

Needs `pip install playwright` and Google Chrome. Writes <out>/*.png and prints the final text of every card's
detail drawer. Exit code 0 only when every stage that was run ended SUCCESS.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

TERMINAL = {"SUCCESS", "FAILED", "NO-GO", "ABORTED", "SKIPPED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--out", default="/tmp/skyscan_run")
    ap.add_argument("--mode", choices=("stage", "selected"), default="stage")
    ap.add_argument("--stages", default="A1,A2,A3,A4")
    ap.add_argument("--timeout", type=float, default=240.0, help="seconds allowed per stage")
    ap.add_argument("--ready-timeout", type=float, default=240.0, help="seconds to wait for the vehicle to be GO")
    ap.add_argument("--size", default="1600x1000")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = (int(v) for v in args.size.split("x"))
    stages = [s for s in args.stages.split(",") if s]
    results: dict[str, str] = {}

    def text(page, sel):
        return page.inner_text(sel).strip()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True,
                                     args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": w, "height": h})
        seen: list[str] = []
        page.on("console", lambda m: seen.append(f"[{m.type}] {m.text[:200]}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: seen.append(f"[pageerror] {e}"))
        page.on("dialog", lambda d: (seen.append(f"[dialog] {d.message}"), d.dismiss()))
        page.on("websocket", lambda ws: ws.on("framesent", lambda f: seen.append(f"[sent] {str(f)[:160]}")))
        page.goto(args.url, wait_until="domcontentloaded")
        page.wait_for_selector("#stage-card-A1", timeout=30000)

        first = stages[0]
        print(f"waiting for {first} to be GO ...", flush=True)
        t0 = time.time()
        while text(page, f"#go-{first}") != "GO":
            if time.time() - t0 > args.ready_timeout:
                page.screenshot(path=str(out / "not_ready.png"))
                print(f"{first} never became GO: {text(page, f'#hint-{first}')}")
                return 2
            time.sleep(1.0)
        page.screenshot(path=str(out / "00_ready.png"))
        print(f"ready after {time.time() - t0:.0f}s; pills:",
              {s: text(page, f"#go-{s}") for s in ("A1", "A2", "A3", "A4")}, flush=True)

        def wait_done(sid: str) -> str:
            t1 = time.time()
            last = ""
            while time.time() - t1 < args.timeout:
                tag = text(page, f"#tag-{sid}")
                ph = text(page, f"#phase-{sid}")
                if ph != last:
                    print(f"  {sid} [{tag}] {ph}", flush=True)
                    last = ph
                if tag in TERMINAL:
                    return tag
                time.sleep(1.0)
            return "TIMEOUT"

        def press(sel: str, sid: str) -> None:
            """Click and make sure the command really started the stage (retry once, show why if not)."""
            for attempt in (1, 2):
                before = len(seen)
                page.click(sel)
                t2 = time.time()
                while time.time() - t2 < 10.0:
                    if text(page, f"#tag-{sid}") not in ("IDLE", "SKIPPED"):
                        return
                    time.sleep(0.5)
                print(f"  !! {sid} did not start after click #{attempt}; page said: {seen[before:]}", flush=True)

        if args.mode == "stage":
            for i, sid in enumerate(stages, 1):
                print(f"-> RUN {sid}", flush=True)
                press(f".stage-run[data-stage='{sid}']", sid)
                results[sid] = wait_done(sid)
                page.screenshot(path=str(out / f"{i:02d}_{sid}_{results[sid].lower()}.png"))
                if results[sid] != "SUCCESS":
                    break
        else:
            for sid in ("A1", "A2", "A3", "A4"):
                box = page.locator(f"#stage-card-{sid} input[type=checkbox]")
                if box.is_checked() != (sid in stages):
                    box.click()
            print("-> RUN SELECTED", flush=True)
            press("#btn-run-stages", stages[0])
            for sid in stages:
                results[sid] = wait_done(sid)
                if results[sid] != "SUCCESS":
                    break
            page.screenshot(path=str(out / "01_selected_done.png"))

        for sid in ("A1", "A2", "A3", "A4"):
            page.click(f".stage-more[data-stage='{sid}']")
        time.sleep(1.0)
        page.screenshot(path=str(out / "99_details.png"), full_page=True)
        for sid in ("A1", "A2", "A3", "A4"):
            print(f"\n===== {sid} detail =====")
            print(text(page, f"#detail-{sid}"))
        print("\nproducts:", text(page, ".mission-outputs"))
        browser.close()

    print("\nresults:", results)
    return 0 if results and all(v == "SUCCESS" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
