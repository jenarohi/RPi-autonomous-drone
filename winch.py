# ============================================================
# winch.py — Payload winch (simulation mock)
#
# In simulation there is no real hardware. We simulate the
# timing of a servo winch lowering a 5m rope at ~0.5 m/s.
# The spring-hook auto-releases on ground contact.
# ============================================================
import time
from config import ROPE_LENGTH_M


class Winch:
    LOWER_SPEED_MPS = 0.5   # rope lowers at 0.5 m/s

    def __init__(self):
        print("[Winch] SIMULATION MODE")

    def deploy(self):
        """Lower payload to ground and release."""
        lower_time = ROPE_LENGTH_M / self.LOWER_SPEED_MPS
        print(f"[Winch] Lowering {ROPE_LENGTH_M}m rope "
              f"({lower_time:.0f}s @ {self.LOWER_SPEED_MPS}m/s) ...")
        steps = 10
        for i in range(steps):
            rope_out = (i + 1) * ROPE_LENGTH_M / steps
            print(f"  [Winch] rope={rope_out:.1f}m / {ROPE_LENGTH_M}m")
            time.sleep(lower_time / steps)
        print("[Winch] Payload at ground — spring hook releasing ...")
        time.sleep(1.5)
        print("[Winch] ✓ Payload released!")

    def retract(self):
        """Retract rope after delivery."""
        retract_time = ROPE_LENGTH_M / self.LOWER_SPEED_MPS
        print(f"[Winch] Retracting rope ({retract_time:.0f}s) ...")
        time.sleep(retract_time)
        print("[Winch] ✓ Rope fully retracted")

    def cleanup(self):
        pass
