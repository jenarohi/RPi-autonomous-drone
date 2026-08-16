# ============================================================
# search_pattern.py — Lawnmower delivery zone search
#
# Generates boustrophedon (zigzag) GPS waypoints over the
# delivery zone. Strip spacing is derived from down camera FOV
# and search altitude so full coverage is guaranteed.
#
# Search starts from CORRIDOR EXIT (east side) and sweeps west-to-east
# row by row, alternating direction. This minimises total flight path.
# ============================================================
import math
from pymavlink import mavutil
from config import (
    CAMERA_FOV_DEG, SEARCH_OVERLAP,
    DELIVERY_ZONE_E_MIN, DELIVERY_ZONE_E_MAX,
    DELIVERY_ZONE_N_MIN, DELIVERY_ZONE_N_MAX,
    ALT_SEARCH, SEARCH_SPEED_MPS,
)


def generate_search_waypoints(home_lat, home_lon,
                               altitude_m=ALT_SEARCH):
    """
    Generate lawnmower GPS waypoints covering the delivery zone.

    Camera footprint width at altitude:
        strip_width = 2 * alt * tan(FOV/2)

    Row spacing with overlap:
        spacing = strip_width * (1 - SEARCH_OVERLAP)

    Rows run NORTH-SOUTH (constant east), sweep east across zone.
    This keeps rows perpendicular to the corridor exit direction.

    Returns: list of (lat, lon) tuples
    """
    fov_half_rad = math.radians(CAMERA_FOV_DEG / 2.0)
    strip_w      = 2.0 * altitude_m * math.tan(fov_half_rad)
    spacing      = strip_w * (1.0 - SEARCH_OVERLAP)
    spacing      = max(spacing, 3.0)   # minimum 3m spacing as sanity check

    cos_lat = math.cos(math.radians(home_lat))
    def to_gps(n_m, e_m):
        lat = home_lat + n_m / 111000.0
        lon = home_lon + e_m / (111000.0 * cos_lat)
        return lat, lon

    e_min = DELIVERY_ZONE_E_MIN
    e_max = DELIVERY_ZONE_E_MAX
    n_min = DELIVERY_ZONE_N_MIN
    n_max = DELIVERY_ZONE_N_MAX

    # Build east-running columns (constant east, sweep north)
    waypoints = []
    col = 0
    e   = e_min

    while e <= e_max + spacing * 0.5:
        # North values for this column
        n_vals = []
        n = n_min
        while n <= n_max + spacing * 0.5:
            n_vals.append(n)
            n += spacing

        # Alternate sweep direction each column
        if col % 2 == 1:
            n_vals = n_vals[::-1]

        for n in n_vals:
            waypoints.append(to_gps(n, e))

        e   += spacing
        col += 1

    print(f"[Search] {len(waypoints)} WPs | "
          f"strip={strip_w:.1f}m spacing={spacing:.1f}m "
          f"alt={altitude_m}m overlap={SEARCH_OVERLAP*100:.0f}%")
    return waypoints


def apply_search_speed(fc):
    """Set WPNAV_SPEED for fast scanning. Call before search loop."""
    speed_cms = int(SEARCH_SPEED_MPS * 100)
    fc.master.mav.param_set_send(
        fc.master.target_system,
        fc.master.target_component,
        b'WPNAV_SPEED',
        float(speed_cms),
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
    )
    print(f"[Search] WPNAV_SPEED → {SEARCH_SPEED_MPS} m/s")


def restore_normal_speed(fc):
    """Restore default nav speed after search."""
    fc.master.mav.param_set_send(
        fc.master.target_system,
        fc.master.target_component,
        b'WPNAV_SPEED',
        500.0,   # 5 m/s
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
    )
    print("[Search] WPNAV_SPEED restored → 5 m/s")
