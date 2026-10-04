"""EventBus — the one way data reaches the UI (and the run recorder).

* ``publish()`` / ``event()`` / ``log_lines()`` may be called from **any thread**.
* Fan-out to WebSocket clients happens on the asyncio loop thread (``attach_loop``).
* Every message is ``{"t": kind, "ts": epoch_s, "seq": n, ...payload}``; ``seq`` is global and
  strictly increasing, so a client that received ``snapshot()["seq"] == S`` ignores live messages
  with ``seq <= S`` (they are already reflected in the snapshot).
* Slow clients never block publishers: high-rate state kinds (``COALESCE``) keep only the newest
  message per key per client; everything else is queued (bounded, oldest dropped and counted).
"""
from __future__ import annotations

import asyncio
import collections
import dataclasses
import enum
import itertools
import logging
import math
import threading
import time
from pathlib import Path
from typing import Any, Callable

from skyscan.types import Sev

log = logging.getLogger(__name__)

#: High-rate state kinds: per client only the newest message per (kind, key) is delivered.
COALESCE = frozenset({"telem", "vision", "proc", "truth"})
#: History kinds: not part of the latest-state cache.
HISTORY = frozenset({"event", "log", "ack", "hello"})
_RESERVED = ("t", "ts", "seq")


def jsonable(obj: Any) -> Any:
    """Convert to plain JSON types: dataclasses → dicts, enums → values, tuples → lists,
    numpy → python, NaN/±inf → None. Fields named ``img`` are skipped (image buffers)."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, enum.Enum):
        return jsonable(obj.value)
    if isinstance(obj, (str, int)):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k.value if isinstance(k, enum.Enum) else k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset, collections.deque)):
        return [jsonable(v) for v in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: jsonable(getattr(obj, f.name)) for f in dataclasses.fields(obj) if f.name != "img"}
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return f"<{len(obj)} bytes>"
    if type(obj).__module__ == "numpy":
        if hasattr(obj, "tolist"):          # ndarray and numpy scalars
            return jsonable(obj.tolist())
    if hasattr(obj, "to_dict"):
        return jsonable(obj.to_dict())
    return str(obj)


class Subscription:
    """One consumer (typically a WebSocket client). Use only on the event-loop thread."""

    def __init__(self, fifo_max: int = 5000) -> None:
        self._fifo: collections.deque[dict] = collections.deque()
        self._fifo_max = fifo_max
        self._latest: dict[str, dict] = {}
        self._wake = asyncio.Event()
        self.dropped = 0          # FIFO messages dropped because the client fell behind
        self.closed = False

    def push(self, msg: dict, coalesce_key: str | None = None) -> None:
        if self.closed:
            return
        if coalesce_key is not None:
            self._latest.pop(coalesce_key, None)   # re-insert so batch order follows recency
            self._latest[coalesce_key] = msg
        else:
            if len(self._fifo) >= self._fifo_max:
                self._fifo.popleft()
                self.dropped += 1
            self._fifo.append(msg)
        self._wake.set()

    def pending(self) -> int:
        return len(self._fifo) + len(self._latest)

    async def next_batch(self, timeout: float | None = None) -> list[dict]:
        """Wait until something is queued, then return everything queued (FIFO first, then the
        newest state messages). Returns ``[]`` on timeout or when closed."""
        while not self._fifo and not self._latest:
            if self.closed:
                return []
            self._wake.clear()
            try:
                if timeout is None:
                    await self._wake.wait()
                else:
                    await asyncio.wait_for(self._wake.wait(), timeout)
            except asyncio.TimeoutError:
                return []
        batch = list(self._fifo)
        self._fifo.clear()
        if self._latest:
            batch.extend(self._latest.values())
            self._latest.clear()
        return batch

    def close(self) -> None:
        self.closed = True
        self._wake.set()


class EventBus:
    def __init__(self, history: int = 500, log_history: int = 400) -> None:
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subs: set[Subscription] = set()          # loop thread only
        self._latest: dict[str, dict] = {}
        self._events: collections.deque[dict] = collections.deque(maxlen=history)
        self._logs: dict[str, collections.deque[str]] = {}
        self._log_history = log_history
        self._listeners: list[Callable[[dict], None]] = []
        self._seq = itertools.count(1)
        self._last_seq = 0

    # ── wiring ──────────────────────────────────────────────────────────
    def attach_loop(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_running_loop()

    def add_listener(self, fn: Callable[[dict], None]) -> None:
        """Synchronous callback for every message, run on the publishing thread. Must be fast."""
        with self._lock:
            self._listeners.append(fn)

    def remove_listener(self, fn: Callable[[dict], None]) -> None:
        with self._lock:
            if fn in self._listeners:
                self._listeners.remove(fn)

    def subscribe(self, fifo_max: int = 5000) -> Subscription:
        """Loop thread only. Subscribe *before* taking ``snapshot()`` (see module doc)."""
        sub = Subscription(fifo_max)
        self._subs.add(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        self._subs.discard(sub)
        sub.close()

    # ── publishing (any thread) ─────────────────────────────────────────
    def publish(self, kind: str, payload: dict | None = None) -> dict:
        body = jsonable(payload or {})
        msg: dict[str, Any] = {"t": kind, "ts": round(time.time(), 3)}
        msg.update((k, v) for k, v in body.items() if k not in _RESERVED)
        with self._lock:
            msg["seq"] = next(self._seq)
            self._last_seq = msg["seq"]
            if kind == "event":
                self._events.append(msg)
            elif kind == "log":
                src = str(msg.get("src", "?"))
                dq = self._logs.get(src)
                if dq is None:
                    dq = self._logs[src] = collections.deque(maxlen=self._log_history)
                dq.extend(msg.get("lines") or [])
            elif kind not in HISTORY:
                self._latest[self._key(kind, msg)] = msg
            listeners = tuple(self._listeners)
            loop = self._loop
        for fn in listeners:
            try:
                fn(msg)
            except Exception:  # noqa: BLE001 - a broken listener must not break publishers
                log.exception("bus listener %r failed", fn)
        if loop is not None:
            try:
                loop.call_soon_threadsafe(self._fanout, msg)
            except RuntimeError:  # loop closed during shutdown
                pass
        return msg

    def event(self, src: str, msg: str, sev: Sev | str = Sev.INFO, **data: Any) -> dict:
        sev = sev if isinstance(sev, Sev) else Sev(str(sev))
        log.debug("[%s] %s: %s", src, sev.value, msg)
        return self.publish("event", {"src": src, "sev": sev.value, "msg": msg, "data": data})

    def log_lines(self, src: str, lines: list[str]) -> dict | None:
        if not lines:
            return None
        return self.publish("log", {"src": src, "lines": list(lines)})

    # ── reading ─────────────────────────────────────────────────────────
    def latest(self, kind: str, key: str | None = None) -> dict | None:
        with self._lock:
            return self._latest.get(kind if key is None else f"{kind}:{key}")

    def snapshot(self) -> dict:
        """Everything a fresh client needs: latest state per (kind, key), recent events, recent
        log lines per source, and the ``seq`` the snapshot is consistent with."""
        with self._lock:
            return {
                "seq": self._last_seq,
                "latest": list(self._latest.values()),
                "events": list(self._events),
                "logs": {src: list(lines) for src, lines in self._logs.items()},
            }

    # ── internals ───────────────────────────────────────────────────────
    @staticmethod
    def _key(kind: str, msg: dict) -> str:
        key = msg.get("key")
        return kind if key is None else f"{kind}:{key}"

    def _fanout(self, msg: dict) -> None:
        kind = msg["t"]
        ckey = self._key(kind, msg) if kind in COALESCE else None
        for sub in tuple(self._subs):
            sub.push(msg, ckey)
