# ============================================================
# main_mission.py — AeroTHON 2026 Full Autonomous Mission
#
# Mission 2: SkyScan — Autonomous Rapid Delivery
# Rulebook requirements:
#   ✓ Autonomous takeoff
#   ✓ Scan start QR code → identify delivery target
#   ✓ Navigate forward through green corridor (avoiding obstacles)
#   ✓ Lawnmower search of delivery zone
#   ✓ Identify correct target QR, avoid red zones
#   ✓ Precision centering over target
#   ✓ Descend to delivery altitude, lower payload via winch
#   ✓ Ascend, fly to orange corridor entrance
#   ✓ Navigate return through orange corridor (with obstacles)
#   ✓ Autonomous return to takeoff point + land
#
# 12-state machine:
#   INIT → TAKEOFF → QR_SCAN → BANNER_FWD → CORRIDOR_FWD
#   → ASCEND_SEARCH → SEARCH → CENTER → DELIVERY
#   → ASCEND_RET → BANNER_RET → CORRIDOR_RET → RTL
# ============================================================
import time
import sys
import cv2

from flight_controller import FlightController
from down_camera       import DownCamera
from front_camera      import FrontCamera
from lidar_bridge      import LidarBridge
from corridor_nav      import navigate_corridor
from search_pattern    import (generate_search_waypoints,
                               apply_search_speed, restore_normal_speed)
from winch             import Winch
from pid               import PID
from config import (
    ALT_TAKEOFF, ALT_CORRIDOR, ALT_SEARCH, ALT_DELIVERY,
    HOME_TO_QR_EAST, HOME_TO_CORRIDOR_EAST, CORRIDOR_EXIT_EAST,
    CORRIDOR_LENGTH,
    GREEN_CENTRE_NORTH, ORANGE_CENTRE_NORTH,
    TIMEOUT_QR_SCAN, TIMEOUT_BANNER, TIMEOUT_SEARCH,
    TIMEOUT_CENTERING, TIMEOUT_DELIVERY,
    DELIVERY_CENTER_THRESH, DELIVERY_CENTER_FRAMES,
    QR_KP, QR_KI, QR_KD, QR_CLAMP,
    BNR_KP, BNR_KI, BNR_KD, BNR_CLAMP,
    SEARCH_WP_RADIUS,
)


# ── Display ───────────────────────────────────────────────────────────────────

def tick(dc: DownCamera, fc_cam: FrontCamera):
    """Update both camera windows. Call from main thread each loop."""
    d = dc.update()
    f = fc_cam.update()
    if d is not None:
        cv2.imshow("Down Camera",  d)
    if f is not None:
        cv2.imshow("Front Camera", f)
    cv2.waitKey(1)


def wait(sec: float, dc: DownCamera, fc_cam: FrontCamera):
    """Hold position for `sec` seconds while keeping camera windows live."""
    end = time.time() + sec
    while time.time() < end:
        tick(dc, fc_cam)
        time.sleep(0.03)


def log(state: str, msg: str):
    print(f"[{state:14s}] {msg}")


# ── State 1: TAKEOFF ─────────────────────────────────────────────────────────

def phase_takeoff(fc: FlightController,
                  dc: DownCamera,
                  fc_cam: FrontCamera):
    log("TAKEOFF", f"Arming and taking off to {ALT_TAKEOFF}m ...")
    ok = fc.arm_and_takeoff(ALT_TAKEOFF)
    if not ok:
        log("TAKEOFF", "⚠ Altitude not confirmed — continuing anyway")
    wait(1, dc, fc_cam)
    log("TAKEOFF", "✓ Airborne")


# ── State 2: QR SCAN ─────────────────────────────────────────────────────────

def phase_qr_scan(fc: FlightController,
                  dc: DownCamera,
                  fc_cam: FrontCamera) -> str:
    """
    Fly east to hover over start QR, decode it.
    QR at SDF x=0, y=3 = 3m east of home at corridor height ALT_TAKEOFF.
    Returns the delivery target string (e.g. "DELIVERY-C").
    """
    log("QR_SCAN", f"Flying {HOME_TO_QR_EAST}m east to start QR ...")
    fc.goto_offset_wait(GREEN_CENTRE_NORTH, HOME_TO_QR_EAST,
                        ALT_TAKEOFF, radius=1.0, timeout=20)
    wait(1, dc, fc_cam)

    log("QR_SCAN", f"Scanning for QR (max {TIMEOUT_QR_SCAN}s) ...")
    t0 = time.time()
    target = ""

    while time.time() - t0 < TIMEOUT_QR_SCAN:
        tick(dc, fc_cam)
        r = dc.get_result()
        if r["confirmed_qr"]:
            target = r["confirmed_qr"]
            log("QR_SCAN", f"✓ Decoded: '{target}' ({time.time()-t0:.1f}s)")
            break
        time.sleep(0.04)
    else:
        target = "DELIVERY-C"   # default fallback
        log("QR_SCAN", f"Timeout — using default target: '{target}'")

    dc.set_target(target)
    wait(0.5, dc, fc_cam)
    return target


# ── State 3: BANNER ALIGN (approach corridor entrance) ───────────────────────

def phase_banner_align(fc: FlightController,
                       dc: DownCamera,
                       fc_cam: FrontCamera,
                       corridor_north_m: float,
                       direction: str = "forward"):
    """
    Fly to corridor entrance, yaw to face it, detect & align with banner.

    direction="forward" → approaching GREEN corridor from west (yaw 90°)
    direction="return"  → approaching ORANGE corridor from east (yaw 270°)
    """
    label      = "FWD" if direction == "forward" else "RET"
    yaw_deg    = 90 if direction == "forward" else 270

    # Fly to 3m west of corridor entrance (safe approach)
    if direction == "forward":
        approach_east = HOME_TO_CORRIDOR_EAST - 3.0
    else:
        approach_east = CORRIDOR_EXIT_EAST + 3.0

    log(f"BANNER_{label}", f"Flying to approach: N={corridor_north_m:.1f}m "
                           f"E={approach_east:.1f}m ...")
    fc.goto_offset_wait(corridor_north_m, approach_east,
                        ALT_TAKEOFF, radius=2.0, timeout=40)

    # Yaw to face the corridor entrance
    fc.set_yaw(yaw_deg)
    wait(2, dc, fc_cam)

    log(f"BANNER_{label}", f"Looking for banner (max {TIMEOUT_BANNER}s) ...")
    pid_align = PID(kp=BNR_KP, ki=BNR_KI, kd=BNR_KD, clamp=BNR_CLAMP)
    t0        = time.time()
    confirmed = False

    while time.time() - t0 < TIMEOUT_BANNER:
        tick(dc, fc_cam)
        fr = fc_cam.get_result()

        if not fr["detected"]:
            # Creep forward slowly to find banner
            fc.set_velocity_body(0.3, 0, 0)
            time.sleep(0.1)
            continue

        if fr["confirmed"]:
            confirmed = True
            if fr["aligned"]:
                fc.stop()
                log(f"BANNER_{label}",
                    f"✓ Aligned ({fr['colour']} offset={fr['offset_x']:+.3f})")
                break

        # Lateral correction: banner right → slide right (body-frame vy+)
        lat_cmd = pid_align.compute(fr["offset_x"])
        fc.set_velocity_body(0.2, lat_cmd, 0)
        time.sleep(0.1)

    fc.stop()
    if not confirmed:
        log(f"BANNER_{label}",
            "⚠ Banner not confirmed — proceeding anyway")
    wait(0.5, dc, fc_cam)


# ── State 4: CORRIDOR FORWARD ─────────────────────────────────────────────────

def phase_corridor_forward(fc: FlightController,
                           dc: DownCamera,
                           fc_cam: FrontCamera,
                           lidar: LidarBridge):
    """Navigate eastward through GREEN corridor."""
    log("CORR_FWD", f"Descending to {ALT_CORRIDOR}m ...")
    pos = fc.get_position()
    if pos:
        fc.goto_wait(pos['lat'], pos['lon'],
                     ALT_CORRIDOR, radius=0.4, timeout=15)
    wait(1, dc, fc_cam)
    dc._lost_green = 0   # reset exit detector

    log("CORR_FWD", "Entering GREEN corridor ...")
    ok = navigate_corridor(
        fc, dc, fc_cam, lidar,
        tick_fn=lambda: tick(dc, fc_cam),
        direction="forward",
        total_dist_m=CORRIDOR_LENGTH + 3.0,   # +3m safety margin
    )
    fc.stop()
    log("CORR_FWD", f"Green corridor {'✓ done' if ok else '⚠ timeout'}")


# ── State 5: ASCEND TO SEARCH ALTITUDE ───────────────────────────────────────

def phase_ascend_search(fc: FlightController,
                        dc: DownCamera,
                        fc_cam: FrontCamera):
    log("ASCEND", f"Ascending to {ALT_SEARCH}m ...")
    pos = fc.get_position()
    if pos:
        fc.goto_wait(pos['lat'], pos['lon'],
                     ALT_SEARCH, radius=0.5, timeout=25)
    wait(1, dc, fc_cam)
    log("ASCEND", "✓ At search altitude")


# ── State 6: SEARCH DELIVERY ZONE ────────────────────────────────────────────

def phase_search(fc: FlightController,
                 dc: DownCamera,
                 fc_cam: FrontCamera,
                 target: str):
    """
    Lawnmower search of delivery zone looking for target QR.
    Red zone avoidance: if large red area detected below, nudge north.
    Returns (found_lat, found_lon) or (None, None) if not found.
    """
    log("SEARCH", f"Starting search for target='{target}'")
    apply_search_speed(fc)
    wps = generate_search_waypoints(fc.home_lat, fc.home_lon, ALT_SEARCH)
    log("SEARCH", f"{len(wps)} waypoints to cover")

    t_start   = time.time()
    found_lat = None
    found_lon = None

    for i, (wlat, wlon) in enumerate(wps):
        if time.time() - t_start > TIMEOUT_SEARCH:
            log("SEARCH", "⚠ Search TIMEOUT")
            break

        fc.goto(wlat, wlon, ALT_SEARCH)
        wp_t = time.time()

        while time.time() - wp_t < 15:
            tick(dc, fc_cam)
            r   = dc.get_result()
            pos = fc.get_position()

            # ── Target found ─────────────────────────────────────────────
            if r["target_found"]:
                if r["qr_near_red"]:
                    log("SEARCH", f"⚠ Target near RED ZONE at WP{i+1} — skipping")
                    # Don't break: competition QR should not be in red zone,
                    # but keep scanning in case of SDF placement error
                else:
                    fc.stop()
                    log("SEARCH", f"✓ TARGET '{target}' found at WP{i+1}!")
                    found_lat = pos['lat'] if pos else wlat
                    found_lon = pos['lon'] if pos else wlon
                    break

            # ── Red zone under drone: nudge north to avoid ───────────────
            if r["red_zone"] and r["red_area_px"] > 8000:
                fc.set_velocity_ned(0.5, 0, 0)   # brief north push
                time.sleep(0.4)

            # ── Waypoint arrival check ───────────────────────────────────
            if pos:
                d = fc._gps_dist(pos['lat'], pos['lon'], wlat, wlon)
                if d < SEARCH_WP_RADIUS:
                    break

            time.sleep(0.08)

        if found_lat is not None:
            break

        # Progress log every 5 WPs
        if i % 5 == 0:
            r       = dc.get_result()
            elapsed = time.time() - t_start
            log("SEARCH", f"WP{i+1}/{len(wps)} t={elapsed:.0f}s "
                           f"qr='{r['confirmed_qr'] or '-'}' "
                           f"target={'✓' if r['target_found'] else '-'}")

    restore_normal_speed(fc)

    if found_lat is None:
        log("SEARCH", "⚠ Target NOT found — delivery at last QR position")
    return found_lat, found_lon


# ── State 7: CENTER OVER TARGET QR ───────────────────────────────────────────

def phase_center_target(fc: FlightController,
                        dc: DownCamera,
                        fc_cam: FrontCamera) -> bool:
    """
    Hover at ALT_SEARCH and PID-centre over confirmed QR code.
    qr_offset: (ox, oy) normalised -1..1
      ox > 0 → QR is east  of drone → move east  (+vE)
      oy > 0 → QR is south of drone → move south (-vN)

    Returns True if centred within DELIVERY_CENTER_FRAMES.
    """
    log("CENTER", f"Centering over target QR (max {TIMEOUT_CENTERING}s) ...")
    pid_x = PID(kp=QR_KP, ki=QR_KI, kd=QR_KD, clamp=QR_CLAMP)
    pid_y = PID(kp=QR_KP, ki=QR_KI, kd=QR_KD, clamp=QR_CLAMP)
    t0              = time.time()
    centred_frames  = 0
    prev_time       = time.time()

    while time.time() - t0 < TIMEOUT_CENTERING:
        tick(dc, fc_cam)
        r  = dc.get_result()
        now = time.time()
        dt  = max(0.01, now - prev_time)
        prev_time = now

        if not r["target_found"]:
            fc.stop()
            time.sleep(0.08)
            centred_frames = 0
            continue

        ox, oy = r["qr_offset"]  # ox=east, oy=south (image Y = south)

        if (abs(ox) < DELIVERY_CENTER_THRESH
                and abs(oy) < DELIVERY_CENTER_THRESH):
            centred_frames += 1
            fc.stop()
            if centred_frames >= DELIVERY_CENTER_FRAMES:
                log("CENTER", f"✓ Centred (ox={ox:+.3f} oy={oy:+.3f})")
                return True
        else:
            centred_frames = 0
            # ox +ve → QR east of drone → fly east (+vE)
            # oy +ve → QR south of drone → fly south (NED north negative)
            vE = pid_x.compute(ox,  dt)
            vN = -pid_y.compute(oy, dt)   # invert because oy south = neg north
            fc.set_velocity_ned(vN, vE, 0)
        time.sleep(0.08)

    fc.stop()
    log("CENTER", "⚠ Centering timeout — proceeding")
    return False


# ── State 8: PAYLOAD DELIVERY ─────────────────────────────────────────────────

def phase_delivery(fc: FlightController,
                   dc: DownCamera,
                   fc_cam: FrontCamera,
                   winch: Winch):
    """
    Descend to ALT_DELIVERY (5m) then lower payload via winch.
    Rulebook: 'lower payload to target point maintaining mission altitude'
    → ALT_DELIVERY = 5m AGL is the lowering height.
    """
    log("DELIVERY", f"Descending to {ALT_DELIVERY}m ...")
    pos = fc.get_position()
    if pos:
        fc.goto_wait(pos['lat'], pos['lon'],
                     ALT_DELIVERY, radius=0.4, timeout=25)
    wait(1, dc, fc_cam)

    log("DELIVERY", "Deploying payload via winch ...")
    winch.deploy()

    log("DELIVERY", "Holding position during deployment ...")
    wait(2, dc, fc_cam)

    log("DELIVERY", "✓ Payload delivered!")


# ── State 9: ASCEND FOR RETURN ────────────────────────────────────────────────

def phase_ascend_return(fc: FlightController,
                        dc: DownCamera,
                        fc_cam: FrontCamera):
    log("ASCEND_RET", f"Ascending to {ALT_SEARCH}m for return ...")
    pos = fc.get_position()
    if pos:
        fc.goto_wait(pos['lat'], pos['lon'],
                     ALT_SEARCH, radius=0.5, timeout=25)
    wait(1, dc, fc_cam)
    log("ASCEND_RET", "✓ At return altitude")


# ── State 10: FLY TO ORANGE CORRIDOR ENTRANCE ────────────────────────────────

def phase_banner_return(fc: FlightController,
                        dc: DownCamera,
                        fc_cam: FrontCamera):
    """
    Fly from delivery zone to ORANGE corridor east entrance.
    Orange corridor is at SDF y=-3, home-relative N=-6m.
    East entrance is at SDF x=16 → E=19m from home.
    We approach from 3m east of entrance (E=22m).
    """
    approach_east = CORRIDOR_EXIT_EAST + 3.0
    log("BANNER_RET", f"Flying to ORANGE entrance: "
                      f"N={ORANGE_CENTRE_NORTH:.1f}m "
                      f"E={approach_east:.1f}m ...")
    fc.goto_offset_wait(ORANGE_CENTRE_NORTH, approach_east,
                        ALT_SEARCH, radius=3.0, timeout=70)
    wait(1, dc, fc_cam)

    # Yaw west to face corridor return entrance
    fc.set_yaw(270)
    wait(2, dc, fc_cam)
    log("BANNER_RET", "✓ At orange corridor entrance, facing west")


# ── State 11: CORRIDOR RETURN ─────────────────────────────────────────────────

def phase_corridor_return(fc: FlightController,
                          dc: DownCamera,
                          fc_cam: FrontCamera,
                          lidar: LidarBridge):
    """Navigate westward through ORANGE corridor (with obstacles)."""
    log("CORR_RET", f"Descending to {ALT_CORRIDOR}m ...")
    pos = fc.get_position()
    if pos:
        fc.goto_wait(pos['lat'], pos['lon'],
                     ALT_CORRIDOR, radius=0.4, timeout=15)
    wait(1, dc, fc_cam)
    dc._lost_green = 0   # reset exit detector

    log("CORR_RET", "Entering ORANGE corridor (with obstacles) ...")
    ok = navigate_corridor(
        fc, dc, fc_cam, lidar,
        tick_fn=lambda: tick(dc, fc_cam),
        direction="return",
        total_dist_m=CORRIDOR_LENGTH + 3.0,
    )
    fc.stop()
    log("CORR_RET", f"Orange corridor {'✓ done' if ok else '⚠ timeout'}")


# ── State 12: RTL + LAND ─────────────────────────────────────────────────────

def phase_rtl(fc: FlightController,
              dc: DownCamera,
              fc_cam: FrontCamera):
    log("RTL", "Ascending and returning to takeoff point ...")

    # Ensure safe altitude for transit
    pos = fc.get_position()
    if pos and pos['alt'] < ALT_TAKEOFF:
        fc.goto_wait(pos['lat'], pos['lon'], ALT_TAKEOFF, timeout=20)

    log("RTL", "Flying to home ...")
    fc.goto_wait(fc.home_lat, fc.home_lon,
                 ALT_TAKEOFF, radius=2.0, timeout=70)
    wait(1, dc, fc_cam)

    log("RTL", "Landing ...")
    fc.land()

    for _ in range(60):
        tick(dc, fc_cam)
        if not fc.is_armed():
            log("RTL", "✓ Landed and disarmed!")
            break
        time.sleep(0.5)


# ── FULL MISSION ──────────────────────────────────────────────────────────────

def run_full_mission(fc: FlightController,
                     dc: DownCamera,
                     fc_cam: FrontCamera,
                     lidar: LidarBridge,
                     winch: Winch):
    t_start = time.time()
    log("MISSION", "══════ AEROTHON 2026 MISSION 2 START ══════")

    try:
        # 1. Takeoff
        phase_takeoff(fc, dc, fc_cam)

        # 2. Scan start QR → get delivery target ID
        target = phase_qr_scan(fc, dc, fc_cam)

        # 3. Approach green corridor banner, align laterally
        phase_banner_align(fc, dc, fc_cam,
                           corridor_north_m=GREEN_CENTRE_NORTH,
                           direction="forward")

        # 4. Navigate forward through green corridor
        phase_corridor_forward(fc, dc, fc_cam, lidar)

        # 5. Ascend to search altitude
        phase_ascend_search(fc, dc, fc_cam)

        # 6. Lawnmower search delivery zone
        found_lat, found_lon = phase_search(fc, dc, fc_cam, target)

        # 7. Precision centering over target QR
        phase_center_target(fc, dc, fc_cam)

        # 8. Descend and deploy payload
        phase_delivery(fc, dc, fc_cam, winch)

        # 9. Ascend for return transit
        phase_ascend_return(fc, dc, fc_cam)

        # 10. Fly to orange corridor entrance
        phase_banner_return(fc, dc, fc_cam)

        # 11. Navigate return through orange corridor
        phase_corridor_return(fc, dc, fc_cam, lidar)

        # 12. Return to launch and land
        phase_rtl(fc, dc, fc_cam)

    except KeyboardInterrupt:
        log("MISSION", "⚠ INTERRUPTED — emergency land")
        fc.set_mode('LAND')
        raise

    elapsed = time.time() - t_start
    log("MISSION", f"══════ COMPLETE in {elapsed:.0f}s ══════")
    if elapsed > 900:
        log("MISSION", "⚠ Exceeded 15-minute competition window!")


# ── INDIVIDUAL TEST MODES ─────────────────────────────────────────────────────

def test_qr(fc, dc, fc_cam):
    fc.arm_and_takeoff(ALT_TAKEOFF)
    target = phase_qr_scan(fc, dc, fc_cam)
    wait(2, dc, fc_cam)
    fc.land()
    print(f"[Test] Target decoded: '{target}'")


def test_corridor_fwd(fc, dc, fc_cam, lidar):
    fc.arm_and_takeoff(ALT_TAKEOFF)
    phase_banner_align(fc, dc, fc_cam,
                       corridor_north_m=GREEN_CENTRE_NORTH,
                       direction="forward")
    phase_corridor_forward(fc, dc, fc_cam, lidar)
    wait(2, dc, fc_cam)
    fc.goto_wait(fc.home_lat, fc.home_lon, ALT_TAKEOFF, timeout=30)
    fc.land()


def test_search(fc, dc, fc_cam):
    fc.arm_and_takeoff(ALT_SEARCH)
    dc.set_target("DELIVERY-C")
    found_lat, found_lon = phase_search(fc, dc, fc_cam, "DELIVERY-C")
    if found_lat:
        phase_center_target(fc, dc, fc_cam)
    fc.land()


def test_delivery(fc, dc, fc_cam, winch):
    fc.arm_and_takeoff(ALT_SEARCH)
    dc.set_target("DELIVERY-C")
    found_lat, found_lon = phase_search(fc, dc, fc_cam, "DELIVERY-C")
    if found_lat:
        phase_center_target(fc, dc, fc_cam)
        phase_delivery(fc, dc, fc_cam, winch)
    fc.land()


def test_return(fc, dc, fc_cam, lidar):
    fc.arm_and_takeoff(ALT_SEARCH)
    phase_banner_return(fc, dc, fc_cam)
    phase_corridor_return(fc, dc, fc_cam, lidar)
    wait(2, dc, fc_cam)
    fc.land()


def test_cameras(dc, fc_cam):
    """Just show camera feeds without flying. Useful for topic debugging."""
    print("[Test] Camera test mode — press Q to quit")
    while True:
        d = dc.update()
        f = fc_cam.update()
        if d is not None:
            cv2.imshow("Down Camera",  d)
        if f is not None:
            cv2.imshow("Front Camera", f)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 56)
    print("  AeroTHON 2026 — Mission 2 Control")
    print("=" * 56)

    # Init subsystems
    fc    = FlightController()
    dc    = DownCamera()
    fc_cam = FrontCamera()
    lidar = LidarBridge(None)   # master assigned after connect
    winch = Winch()

    # Camera test before flight (optional — does NOT require SITL)
    print("\n[INIT] Starting cameras for diagnostics ...")
    dc.start()
    fc_cam.start()

    print("\nOptions:")
    print("  c — Camera test only (no drone, for topic debugging)")
    print("  any key — Connect to SITL and continue to flight menu")
    ch = input("\n>> ").strip().lower()
    if ch == 'c':
        test_cameras(dc, fc_cam)
        cv2.destroyAllWindows()
        return

    # SITL connection
    fc.connect()
    fc.wait_gps()

    # Assign mavlink master to lidar bridge
    lidar._master = fc.master
    lidar.start()
    print("[INIT] Waiting for LiDAR bridge to receive first scans ...")
    time.sleep(2)
    print(f"[INIT] LiDAR scans: {lidar.scan_count}")

    fc.set_tick(lambda: tick(dc, fc_cam))
    wait(2, dc, fc_cam)

    # Menu
    print()
    print("  1 — QR scan test")
    print("  2 — Corridor forward test")
    print("  3 — Search zone test")
    print("  4 — Delivery test (search + drop)")
    print("  5 — Return corridor test")
    print("  6 — FULL MISSION (end to end)")
    print("  q — Quit")

    while True:
        try:
            ch = input("\n>> ").strip().lower()
            if   ch == '1': test_qr(fc, dc, fc_cam)
            elif ch == '2': test_corridor_fwd(fc, dc, fc_cam, lidar)
            elif ch == '3': test_search(fc, dc, fc_cam)
            elif ch == '4': test_delivery(fc, dc, fc_cam, winch)
            elif ch == '5': test_return(fc, dc, fc_cam, lidar)
            elif ch == '6': run_full_mission(fc, dc, fc_cam, lidar, winch)
            elif ch == 'q': break
            else:           print("Unknown option")
        except KeyboardInterrupt:
            print("\nInterrupted — emergency land")
            try:
                fc.set_mode('LAND')
            except Exception:
                pass

    lidar.stop()
    cv2.destroyAllWindows()
    print("[MAIN] Shutdown complete.")


if __name__ == "__main__":
    main()
