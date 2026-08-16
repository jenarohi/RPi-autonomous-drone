# ============================================================
# pid.py — Full PID controller with integral + anti-windup
# Replaces the old PD-only controller. Used everywhere.
# ============================================================
from config import PID_DEADBAND


class PID:
    """
    Full PID controller with:
    - Deadband (ignores tiny errors → prevents jitter)
    - Integral with anti-windup clamping
    - Derivative on error (not measurement) for simplicity
    - Output clamping

    Usage:
        pid = PID(kp=0.4, ki=0.03, kd=0.15, clamp=0.6)
        while running:
            output = pid.compute(error, dt)
            # apply output as velocity command
    """

    def __init__(self, kp=0.3, ki=0.0, kd=0.1,
                 deadband=PID_DEADBAND, clamp=0.5,
                 integral_limit=0.3):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.deadband      = deadband
        self.clamp         = clamp
        self.integral_limit = integral_limit  # anti-windup cap on integral

        self._integral  = 0.0
        self._last_err  = 0.0

    def compute(self, error, dt=0.1):
        """
        Compute PID output.

        Args:
            error: current error (positive/negative)
            dt:    time since last call (seconds)

        Returns:
            control output, clamped to [-clamp, +clamp]
        """
        if abs(error) < self.deadband:
            # In deadband: decay integral, zero derivative
            self._integral *= 0.9
            self._last_err  = 0.0
            return 0.0

        # Proportional
        p_out = self.kp * error

        # Integral with anti-windup
        self._integral += error * dt
        self._integral  = max(-self.integral_limit,
                               min(self.integral_limit, self._integral))
        i_out = self.ki * self._integral

        # Derivative
        if dt > 0:
            d_out = self.kd * (error - self._last_err) / dt
        else:
            d_out = 0.0
        self._last_err = error

        out = p_out + i_out + d_out
        return max(-self.clamp, min(self.clamp, out))

    def reset(self):
        """Reset state — call when switching targets or states."""
        self._integral = 0.0
        self._last_err = 0.0
