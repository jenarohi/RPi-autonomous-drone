"""Payload winch: lower the payload on a rope to the ground, release it there, wind the rope back in.

Rulebook (Mission 2, p.35-37): the payload is *lowered with a controlled pulley mechanism from 5 m and released only
after reaching the ground at the target QR code*. The winch is driven through a servo / AUX output of the flight
controller (``MAV_CMD_DO_SET_SERVO``; SITL already reserves channel 12 for it, sim/params/skyscan_sitl.parm). There is
no rope-length sensor, so the rope paid out is the winch speed times the time it ran: set ``winch.lower_mps`` /
``raise_mps`` to what the real drum does at ``pwm_lower`` / ``pwm_raise`` (the legacy mock used 0.5 m/s).

The winch never blocks: the stage keeps flying and calls ``tick()`` every control cycle.

States:  stowed -> lowering -> down -> (releasing) -> released -> raising -> stowed        any -> fault on a servo error
"""
from __future__ import annotations

import time
from typing import Any, Callable

from skyscan.utils.logger import get_logger

log = get_logger("PAYLOAD/WINCH")


class Winch:
    def __init__(self, cfg: Any, link: Any = None, clock: Callable[[], float] = time.time) -> None:
        g = lambda k, d: getattr(cfg, k, d)           # noqa: E731 - config lookup with default
        self.backend = str(g("backend", "servo"))      # servo = MAV_CMD_DO_SET_SERVO | mock = no hardware, timing only
        self.channel = int(g("servo_channel", 12))
        self.pwm_stop = int(g("pwm_stop", 1500))
        self.pwm_lower = int(g("pwm_lower", 1100))
        self.pwm_raise = int(g("pwm_raise", 1900))
        self.rope_length_m = float(g("rope_length_m", 5.0))
        self.lower_mps = float(g("lower_mps", 0.5))
        self.raise_mps = float(g("raise_mps", 0.5))
        self.slack_m = float(g("slack_m", 0.2))                       # rope paid out beyond the hover height so it lies slack
        self.settle_s = float(g("ground_settle_s", 1.0))              # wait on the ground before releasing
        self.release_channel = int(g("release_channel", 0))           # 0: a spring hook lets go on ground contact (legacy)
        self.release_pwm = int(g("release_pwm", 1900))
        self.release_idle_pwm = int(g("release_idle_pwm", 1100))
        self.release_hold_s = float(g("release_hold_s", 1.5))
        self.link, self.clock = link, clock
        self.phase = "stowed"
        self.rope_out_m = 0.0
        self.acks_failed = 0
        self.commands: list[tuple[float, int, int, bool]] = []        # (t, channel, pwm, acked): the audit trail
        self.error: str | None = None
        self._t0 = 0.0
        self._target_m = 0.0
        self._from_m = 0.0
        self._t_down = 0.0
        self._t_release = 0.0

    # --- hardware ------------------------------------------------------------------------------------------

    @property
    def simulated(self) -> bool:
        return self.backend != "servo" or self.link is None

    def _drive(self, channel: int, pwm: int) -> bool:
        ok = True
        if not self.simulated:
            try:
                ok = bool(self.link.set_servo(channel, pwm))
            except Exception as exc:  # noqa: BLE001
                log.error(f"servo command failed: {exc}")
                ok = False
        self.commands.append((self.clock(), channel, pwm, ok))
        if not ok:
            self.acks_failed += 1
            self.error = f"flight controller did not accept servo {channel} = {pwm}"
            log.error(self.error)
        return ok

    # --- operation -----------------------------------------------------------------------------------------

    def start_lower(self, depth_m: float) -> bool:
        """Start paying rope out until the payload is ``depth_m`` (+ slack) below the winch. False if the rope is too short."""
        want = float(depth_m) + self.slack_m
        if want > self.rope_length_m + 1e-6:
            self.error = f"rope too short: need {want:.2f} m, have {self.rope_length_m:.2f} m"
            self.phase = "fault"
            return False
        self._target_m, self._from_m, self._t0 = want, self.rope_out_m, self.clock()
        if not self._drive(self.channel, self.pwm_lower):
            self.phase = "fault"
            return False
        self.phase = "lowering"
        log.info(f"lowering the payload: {want:.2f} m of rope at {self.lower_mps} m/s")
        return True

    def start_raise(self) -> bool:
        if self.phase not in ("released", "down", "stowed") or self.rope_out_m <= 0.0:
            return self.phase == "stowed"
        self._from_m, self._t0 = self.rope_out_m, self.clock()
        if not self._drive(self.channel, self.pwm_raise):
            self.phase = "fault"
            return False
        self.phase = "raising"
        return True

    def release(self) -> bool:
        """Let the payload go. Only valid once it is on the ground (``down`` and settled)."""
        if self.phase != "down" or self.clock() - self._t_down < self.settle_s:
            return False
        if self.release_channel:
            if not self._drive(self.release_channel, self.release_pwm):
                self.phase = "fault"
                return False
            self._t_release = self.clock()
            self.phase = "releasing"
        else:
            self.phase = "released"                                     # spring hook: it let go on ground contact
        return True

    def stop(self) -> None:
        """Halt the drum (and park the release servo)."""
        self._drive(self.channel, self.pwm_stop)
        if self.release_channel and self.phase == "releasing":
            self._drive(self.release_channel, self.release_idle_pwm)

    def tick(self) -> str:
        """Advance the state machine; call every control cycle."""
        now = self.clock()
        if self.phase == "lowering":
            self.rope_out_m = min(self._target_m, self._from_m + (now - self._t0) * self.lower_mps)
            if self.rope_out_m >= self._target_m - 1e-9:
                self._drive(self.channel, self.pwm_stop)
                self.phase, self._t_down = "down", now
        elif self.phase == "raising":
            self.rope_out_m = max(0.0, self._from_m - (now - self._t0) * self.raise_mps)
            if self.rope_out_m <= 1e-9:
                self._drive(self.channel, self.pwm_stop)
                self.phase = "stowed"
        elif self.phase == "releasing" and now - self._t_release >= self.release_hold_s:
            self._drive(self.release_channel, self.release_idle_pwm)
            self.phase = "released"
        return self.phase

    @property
    def on_ground(self) -> bool:
        return self.phase in ("down", "releasing", "released")

    def status(self) -> dict[str, Any]:
        return {"phase": self.phase, "rope_out_m": round(self.rope_out_m, 2), "backend": self.backend,
                "acks_failed": self.acks_failed, "error": self.error}
