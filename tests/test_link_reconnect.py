"""MavLink must reconnect when the peer goes silent (pymavlink does not raise when SITL restarts)."""
import time
from types import SimpleNamespace

from skyscan.bus import EventBus
from skyscan.fc import link as link_mod


class SilentMaster:
    """Behaves like a pymavlink TCP connection whose peer died: recv_match returns nothing, close works."""

    created: list = []

    def __init__(self, *a, **kw):
        self.closed = False
        SilentMaster.created.append(self)

    def recv_match(self, blocking=True, timeout=0.1):
        time.sleep(0.02)
        return None

    def close(self):
        self.closed = True

    def mode_mapping(self):
        return {}


def test_silent_connection_is_closed_and_reopened(monkeypatch):
    SilentMaster.created.clear()
    monkeypatch.setattr(link_mod.mavutil, "mavlink_connection", SilentMaster)
    cfg = SimpleNamespace(url="tcp:127.0.0.1:5760", link_timeout_s=0.2, reconnect_s=0.05, stale_reconnect_s=0.3,
                          heartbeat_hz=0.0, stream_rates_hz={})
    link = link_mod.MavLink(cfg, EventBus())
    link.start()
    try:
        t0 = time.time()
        while len(SilentMaster.created) < 3 and time.time() - t0 < 5.0:
            time.sleep(0.05)
    finally:
        link.stop()
    assert len(SilentMaster.created) >= 3, "the silent connection was never replaced"
    assert all(m.closed for m in SilentMaster.created[:-1]), "old connections must be closed"
