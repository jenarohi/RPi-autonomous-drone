# ============================================================
# corridor_nav.py — Velocity-based corridor navigation
#
# Design:
#   Three simultaneous control layers at 10 Hz:
#   1. FORWARD: constant east/west velocity along corridor axis
#   2. LATERAL CAMERA: PID on green_offset_Y (north-south in image)
#      green_offset_y: +ve = floor centroid is NORTH of drone
#                    → correct by pushing south (NED north negative)
#   3. LATERAL LIDAR: reactive layer, steer away from walls
#      Takes priority (hard override) when dangerously close to wall
#
#   Exit detection: green floor gone for 8+ frames OR distance limit reached.
#
# Direction:
#   "forward" → heading east (positive NED east velocity)
#   "return"  → heading west (negative NED east velocity)
#               front LiDAR becomes rear; use 180° arc for obstacle avoidance
# ============================================================
import time
from pid import PID
from config import (
    ALT_CORRIDOR,
    CORR_FORWARD_SPEED, CORR_FORWARD_SLOW,
    CORR_LIDAR_SLOW_M, CORR_LIDAR_STOP_M,
    CORR_SIDE_SAFE_M, CORR_LATERAL_LIDAR_GAIN,
    CORR_TIMEOUT, CORR_CLAMP,
    CORR_KP, CORR_KI, CORR_KD,
)

DIRECTION_FWD = +1   # east
DIRECTION_RET = -1   # west


def navigate_corridor(fc, dc, fc_cam, lidar, tick_fn,
                      direction="forward",
                      total_dist_m=None):
    """
    Navigate through the corridor using velocity control.

    Args:
        fc          : FlightController
        dc          : DownCamera
        fc_cam      : FrontCamera (passed for display refresh only)
        lidar       : LidarBridge
        tick_fn     : callable — call each loop to update cv2 windows
        direction   : "forward" (east) or "return" (west)
        total_dist_m: hard distance limit in metres (failsafe)

    Returns:
        True  — clean exit (green floor lost at end of tunnel)
        False — timeout or other failure
    """
    sign      = DIRECTION_FWD if direction == "forward" else DIRECTION_RET
    dir_label = "FWD→" if direction == "forward" else "←RET"

    print(f"[CORR {dir_label}] Start. Alt={ALT_CORRIDOR}m, "
          f"timeout={CORR_TIMEOUT}s")

    # PID: green_offset_y → NED north velocity
    # green_offset_y +ve  = floor centroid is NORTH of drone
    #                      → drone drifted south
    #                      → need POSITIVE north velocity (move north)
    # So: error = green_offset_y, output = north velocity  (same sign)
    pid_lat = PID(kp=CORR_KP, ki=CORR_KI, kd=CORR_KD, clamp=CORR_CLAMP)

    t_start       = time.time()
    dist_travelled = 0.0
    prev_time      = time.time()

    # Ensure we're at corridor altitude before entering
    _hold_alt(fc, tick_fn)

    while True:
        loop_start = time.time()
        tick_fn()

        elapsed = time.time() - t_start

        # ── Timeout ─────────────────────────────────────────────────────────
        if elapsed > CORR_TIMEOUT:
            print(f"[CORR {dir_label}] TIMEOUT {elapsed:.0f}s — stopping")
            fc.stop()
            return False

        # ── Distance limit (failsafe) ────────────────────────────────────────
        if total_dist_m is not None and dist_travelled >= total_dist_m:
            print(f"[CORR {dir_label}] Distance limit {dist_travelled:.1f}m — done")
            fc.stop()
            return True

        # ── Corridor exit (down camera) ──────────────────────────────────────
        r = dc.get_result()
        if r["corridor_exit"]:
            print(f"[CORR {dir_label}] Green floor lost — corridor exit ✓")
            fc.stop()
            return True

        # ── LiDAR readings ───────────────────────────────────────────────────
        # For forward: front=0°, left=270° (north wall), right=90° (south wall)
        # For return:  front=180°, walls are same (corridor walls don't change)
        if direction == "forward":
            front_d = lidar.get_front_distance()
        else:
            front_d = lidar.get_min_distance_in_arc(180, 30)

        left_d  = lidar.get_left_distance()    # north wall distance
        right_d = lidar.get_right_distance()   # south wall distance

        # ── Forward velocity ─────────────────────────────────────────────────
        if front_d < CORR_LIDAR_STOP_M:
            vFwd = 0.0
            print(f"[CORR {dir_label}] ⚠ FRONT {front_d:.2f}m — STOP")
        elif front_d < CORR_LIDAR_SLOW_M:
            factor = ((front_d - CORR_LIDAR_STOP_M)
                      / (CORR_LIDAR_SLOW_M - CORR_LIDAR_STOP_M))
            vFwd = CORR_FORWARD_SLOW + factor * (CORR_FORWARD_SPEED - CORR_FORWARD_SLOW)
        else:
            vFwd = CORR_FORWARD_SPEED

        vE = sign * vFwd   # NED east (positive = east = forward in green corridor)

        # ── Lateral: camera-based PID ────────────────────────────────────────
        now  = time.time()
        dt   = max(0.01, now - prev_time)
        prev_time = now

        cam_lat = 0.0
        if r["green_detect"]:
            # green_offset_y: +ve = floor is NORTH of drone → push north (+vN)
            cam_lat = pid_lat.compute(r["green_offset_y"], dt)
        else:
            pid_lat.reset()

        # ── Lateral: LiDAR wall following ───────────────────────────────────
        # Corridor is along east-west, walls are on north (left) and south (right).
        # left_d  = north wall distance
        # right_d = south wall distance
        # wall_err positive  → north wall is CLOSER → drone drifted north
        #                    → push south (negative vN)
        lidar_lat = 0.0
        if left_d < float('inf') and right_d < float('inf'):
            wall_err = right_d - left_d  # +ve = south wall closer = drone drifted south
            lidar_lat = CORR_LATERAL_LIDAR_GAIN * wall_err
        # Hard override: dangerously close to one wall
        if left_d  < CORR_SIDE_SAFE_M:
            lidar_lat = -CORR_CLAMP        # push south HARD (away from north wall)
        if right_d < CORR_SIDE_SAFE_M:
            lidar_lat =  CORR_CLAMP        # push north HARD (away from south wall)

        # Combine and clamp
        vN = max(-CORR_CLAMP, min(CORR_CLAMP, cam_lat + lidar_lat))

        # ── Send velocity ────────────────────────────────────────────────────
        fc.set_velocity_ned(vN, vE, 0.0)

        # ── Distance tracking ────────────────────────────────────────────────
        dist_travelled += vFwd * dt

        # ── Log every 2s ────────────────────────────────────────────────────
        if int(elapsed * 5) % 10 == 0:
            print(f"  [{dir_label}] t={elapsed:.1f}s dist={dist_travelled:.1f}m "
                  f"F={front_d:.1f} L={left_d:.1f} R={right_d:.1f} "
                  f"vN={vN:+.2f} vE={vE:+.2f} "
                  f"grn={'Y' if r['green_detect'] else 'N'} "
                  f"off_y={r['green_offset_y']:+.2f}")

        # ── Maintain ~10 Hz ──────────────────────────────────────────────────
        loop_elapsed = time.time() - loop_start
        sleep_t = 0.1 - loop_elapsed
        if sleep_t > 0:
            time.sleep(sleep_t)

    return True


def _hold_alt(fc, tick_fn,
              target_alt=ALT_CORRIDOR, tol=0.35, timeout=15):
    """
    Gently bring drone to corridor altitude before entering.
    Only moves if more than tol away.
    """
    pos = fc.get_position()
    if not pos:
        return
    if abs(pos['alt'] - target_alt) < tol:
        return
    print(f"[CORR] Adjusting altitude {pos['alt']:.1f}m → {target_alt}m")
    fc.goto_wait(pos['lat'], pos['lon'], target_alt,
                 radius=0.35, timeout=timeout)
    tick_fn()
