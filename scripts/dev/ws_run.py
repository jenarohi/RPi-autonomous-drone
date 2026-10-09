#!/usr/bin/env python3
"""Run mission stages through the server's WebSocket and print the result of each (no browser, no UI).

    python scripts/dev/ws_run.py A1 A2 A3 A4          # run these stages in order, wait for the run to end
    python scripts/dev/ws_run.py B1 B2 B3 B4 --json out.json
    python scripts/dev/ws_run.py --status             # GO / NO-GO per stage right now, then exit

Talks to http://127.0.0.1:8080 (--url to change). Exit code 0 only if every requested stage succeeded.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time

import aiohttp

TERMINAL = {"success", "failed", "nogo", "aborted", "skipped"}


def show(rep: dict) -> None:
    print(f"\n=== {rep['stage_id']} {rep['title']}: {rep['state'].upper()}  {rep.get('message') or ''}")
    for c in rep.get("checks") or []:
        print(f"  pre  [{'ok' if c['ok'] else ('--' if c.get('blocking') is False else 'NO')}] {c['name']}  {c.get('detail') or ''}")
    for c in rep.get("criteria") or []:
        extra = ""
        if c.get("value") is not None or c.get("limit") is not None:
            extra = f"  ({c.get('value')} / {c.get('limit')})"
        print(f"  crit [{'ok' if c['ok'] else ('--' if c.get('blocking') is False else 'NO')}] {c['name']}{extra}  {c.get('detail') or ''}")
    for k, v in (rep.get("metrics") or {}).items():
        print(f"  metric {k} = {v}")
    if rep.get("error"):
        print("  error:", str(rep["error"]).strip().splitlines()[-1])


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stages", nargs="*")
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--json")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--timeout", type=float, default=600.0)
    args = ap.parse_args()
    reports: dict[str, dict] = {}
    pre: dict[str, dict] = {}
    n_lidar = n_nav = 0
    last_nav: dict = {}
    async with aiohttp.ClientSession() as sess:
        async with sess.ws_connect(args.url.rstrip("/") + "/ws", max_msg_size=0) as ws:
            sent = False
            t_end = time.time() + args.timeout
            t_status = time.time() + 4.0
            while time.time() < t_end:
                try:
                    msg = await ws.receive(timeout=1.0)
                except asyncio.TimeoutError:
                    msg = None
                if args.status and time.time() > t_status:
                    for sid, p in sorted(pre.items()):
                        print(f"{sid}: {'GO' if p['go'] else 'NO-GO'}  " + "; ".join(f"{c['name']}" for c in p['checks'] if not c['ok'] and c.get('blocking') is not False))
                    return 0
                if msg is None:
                    continue
                if msg.type != aiohttp.WSMsgType.TEXT:
                    break
                m = json.loads(msg.data)
                t = m.get("t")
                if t == "hello":
                    for p in (m.get("snapshot") or {}).get("latest", []):
                        if p.get("t") == "precond":
                            pre[p["key"]] = p
                    if args.stages and not sent:
                        await ws.send_str(json.dumps({"cmd": "run", "id": "ws_run", "stages": args.stages}))
                        sent = True
                elif t == "precond":
                    pre[m["key"]] = m
                elif t == "ack" and not m.get("ok"):
                    print("command rejected:", m.get("msg"))
                    return 2
                elif t == "stage":
                    rep = m["report"]
                    reports[m["key"]] = rep
                    if rep["state"] in TERMINAL and rep["stage_id"] in args.stages:
                        show(rep)
                elif t == "lidar" and m.get("r"):
                    n_lidar += 1
                elif t == "nav":
                    n_nav += 1
                    last_nav = m
                elif t == "event" and m.get("src") in ("MISSION",):
                    print(f"  [{m.get('sev')}] {m.get('msg')}")
                elif t == "run" and sent and m.get("state") in ("done", "failed", "nogo", "aborted", "success"):
                    print(f"\nrun finished: {m['state']} - {m.get('message')}")
                    break
    print(f"(lidar messages seen: {n_lidar}, nav messages: {n_nav}, last nav: {last_nav})")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(reports, f, indent=1)
    return 0 if all(reports.get(s, {}).get("state") == "success" for s in args.stages) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
