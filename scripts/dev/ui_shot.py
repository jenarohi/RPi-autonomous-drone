#!/usr/bin/env python3
"""Screenshot the mission-control UI with headless Chrome (Playwright) and report console errors.

    python scripts/dev/ui_shot.py --url http://barathros.local:8080 --out /tmp/shots [--tab gz] [--wait 20]

Needs `pip install playwright` and a local Google Chrome (channel="chrome", so WebGL works headless).
Writes <out>/main.png plus one PNG per tab visited; exits non-zero when the page logged errors.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

TABS = {"map": "tab-map", "cams": "tab-cams", "gz": "tab-gzweb"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--out", default="/tmp/skyscan_shots")
    ap.add_argument("--tab", action="append", default=[], help="map | cams | gz (repeatable); default: all")
    ap.add_argument("--wait", type=float, default=6.0, help="seconds to let each tab render")
    ap.add_argument("--theme", default=None, help="light | pure-white | dark")
    ap.add_argument("--size", default="1600x900")
    ap.add_argument("--click", action="append", default=[], help="CSS selector to click before the screenshots (repeatable)")
    ap.add_argument("--pause", type=float, default=0.0, help="seconds to wait after the clicks")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = (int(v) for v in args.size.split("x"))
    tabs = args.tab or list(TABS)
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True,
                                     args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": w, "height": h})
        page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
        page.on("response", lambda r: errors.append(f"[http {r.status}] {r.url}") if r.status >= 400 else None)
        page.goto(args.url, wait_until="domcontentloaded")
        if args.theme:
            page.evaluate("t => localStorage.setItem('axiom_theme', t)", args.theme)
            page.reload(wait_until="domcontentloaded")
        time.sleep(2.0)
        for sel in args.click:
            page.click(sel)
            time.sleep(0.5)
        if args.pause:
            time.sleep(args.pause)
        page.screenshot(path=str(out / "main.png"))
        for t in tabs:
            page.click(f"button.tab-btn[data-tab='{TABS[t]}']")
            time.sleep(args.wait)
            page.screenshot(path=str(out / f"tab_{t}.png"))
        browser.close()
    for e in errors:
        print(e)
    print(f"{len(errors)} console message(s); screenshots in {out}")
    return 1 if any(e.startswith(("[pageerror]", "[http 5")) for e in errors) else 0


if __name__ == "__main__":
    sys.exit(main())
