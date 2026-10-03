# ============================================================
# config.py — AeroTHON 2026 Mission Configuration
# ============================================================

# ── SITL CONNECTION ──────────────────────────────────────────
SITL_CONNECTION = "tcp:127.0.0.1:5762"

# ── MISSION ALTITUDES (metres AGL) ──────────────────────────
ALT_TAKEOFF  = 5.0    # takeoff + QR scan altitude
ALT_CORRIDOR = 3.0    # corridor fly-through altitude (~10ft)
ALT_SEARCH   = 10.0   # delivery zone search altitude
ALT_DELIVERY = 5.0    # payload drop altitude (hover height above ground)

# ── WORLD GEOMETRY (metres offset from drone home) ──────────
# Drone spawns at SDF (x=-3, y=3) → home = (x=-3, y=3)
# All offsets below: east = +X, north = +Y relative to home
HOME_TO_QR_EAST          = 3.0    # start QR at SDF x=0 → 3m east of home
HOME_TO_CORRIDOR_EAST    = 9.0    # green corridor entrance at SDF x=6 → 9m east
CORRIDOR_EXIT_EAST       = 19.0   # corridor exit at SDF x=16 → 19m east
CORRIDOR_LENGTH          = 10.0   # both corridors are 10m long (SDF x=6..16)

# Green corridor centre (drone home y=3, corridor centre at SDF y=3 → offset 0)
GREEN_CENTRE_NORTH   =  0.0    # green corridor = same y as home
GREEN_HALF_WIDTH     =  1.75   # 3.5m wide total

# Orange corridor centre is at SDF y=-3, home is at SDF y=3 → -6m south
ORANGE_CENTRE_NORTH  = -6.0    # orange corridor is 6m south of home
ORANGE_HALF_WIDTH    =  1.75

# Delivery zone (SDF x=19..59, y=-15..15, 40m×30m)
# In home-relative coords (home at SDF x=-3):
DELIVERY_ZONE_E_MIN  =  22.0   # SDF x=19 → 19-(-3)=22m east of home
DELIVERY_ZONE_E_MAX  =  62.0   # SDF x=59 → 59-(-3)=62m east of home
DELIVERY_ZONE_N_MIN  = -18.0   # SDF y=-15 → -15-3=-18m north of home
DELIVERY_ZONE_N_MAX  =  12.0   # SDF y=15  → 15-3=12m north of home

# ── GAZEBO CAMERA TOPICS ────────────────────────────────────
# Down camera: added to iris_with_standoffs/base_link by add_down_camera.py
DOWN_CAM_TOPIC = (
    "/world/aerothon_mission/model/iris/model/iris_with_standoffs"
    "/link/base_link/sensor/down_camera/image"
)
DOWN_CAM_PROC_W = 640
DOWN_CAM_PROC_H = 480

# Front camera: the ardupilot_gazebo iris_with_gimbal gimbal camera.
# The topic path for the gimbal camera in ardupilot_gazebo is:
#   /world/<world>/model/iris/model/gimbal/link/pitch_link/sensor/camera/image
# NOTE: If this topic does not appear, run:
#   gz topic -l | grep iris
# to find the exact topic and update FRONT_CAM_TOPIC accordingly.
FRONT_CAM_TOPIC = (
    "/world/aerothon_mission/model/iris/model/gimbal"
    "/link/pitch_link/sensor/camera/image"
)
FRONT_CAM_W = 320
FRONT_CAM_H = 240

# Down camera field-of-view (degrees horizontal) — from add_down_camera.py: 60°
CAMERA_FOV_DEG = 60.0

# ── HSV COLOUR RANGES ───────────────────────────────────────
# GREEN corridor / banner (SDF RGB 0.1, 0.8, 0.1)
GREEN_LOWER  = ( 38,  80,  80)
GREEN_UPPER  = ( 82, 255, 255)

# ORANGE corridor / banner (SDF RGB 0.95, 0.55, 0.05)
ORANGE_LOWER = ( 10, 120, 120)
ORANGE_UPPER = ( 25, 255, 255)

# RED no-land zones (SDF RGB 0.9, 0.1, 0.1)
RED_LOWER1   = (  0, 100, 100)
RED_UPPER1   = (  8, 255, 255)
RED_LOWER2   = (172, 100, 100)
RED_UPPER2   = (180, 255, 255)

# ── QR DETECTION ────────────────────────────────────────────
QR_CONFIRM_FRAMES   = 4    # consecutive consistent reads = confirmed
QR_SCAN_EVERY_N     = 2    # process QR every N frames (reduces CPU)

# ── BANNER DETECTION ────────────────────────────────────────
BANNER_MIN_AREA_DOWN  = 500    # min px area in DOWN camera for green
BANNER_MIN_AREA_FRONT = 300    # min px area in FRONT camera for banner
BANNER_ALIGN_THRESH   = 0.10   # ±10% from centre = aligned
BANNER_CONFIRM_FRAMES = 5      # consecutive frames with banner

# ── PID GAINS ───────────────────────────────────────────────
# Corridor lateral PID (green floor Y-offset → NED north velocity)
CORR_KP    = 0.50
CORR_KI    = 0.02
CORR_KD    = 0.18
CORR_CLAMP = 0.7

# QR/target centering (down camera QR offset → NED velocity)
QR_KP    = 0.35
QR_KI    = 0.02
QR_KD    = 0.12
QR_CLAMP = 0.4

# Banner alignment (front camera X-offset → NED lateral velocity)
BNR_KP    = 0.30
BNR_KI    = 0.01
BNR_KD    = 0.10
BNR_CLAMP = 0.4

# Generic deadband (errors below this ignored)
PID_DEADBAND = 0.03

# ── CORRIDOR NAVIGATION ─────────────────────────────────────
CORR_FORWARD_SPEED      = 0.9    # nominal forward speed m/s
CORR_FORWARD_SLOW       = 0.35   # slowed speed near obstacle
CORR_LIDAR_SLOW_M       = 2.5    # slow down if obstacle closer than this
CORR_LIDAR_STOP_M       = 0.9    # emergency stop threshold
CORR_SIDE_SAFE_M        = 0.55   # min side clearance before hard steer
CORR_LATERAL_LIDAR_GAIN = 0.45   # wall error → lateral velocity gain
CORR_LOST_FRAMES        = 20     # frames without green → re-center
CORR_TIMEOUT            = 90     # max seconds per corridor traverse

# ── SEARCH PATTERN ──────────────────────────────────────────
SEARCH_OVERLAP   = 0.25   # 25% strip overlap
SEARCH_SPEED_MPS = 3.0    # WPNAV_SPEED during lawnmower
SEARCH_WP_RADIUS = 2.0    # waypoint acceptance radius (m)

# ── PAYLOAD DELIVERY ────────────────────────────────────────
DELIVERY_CENTER_THRESH = 0.08   # QR offset < 8% = "centered"
DELIVERY_CENTER_FRAMES = 20     # consecutive centered frames before drop
ROPE_LENGTH_M          = 5.0    # winch rope length

# ── TIMEOUTS (seconds) ──────────────────────────────────────
TIMEOUT_QR_SCAN   = 30
TIMEOUT_BANNER    = 25
TIMEOUT_CORRIDOR  = 90
TIMEOUT_SEARCH    = 200
TIMEOUT_CENTERING = 15
TIMEOUT_DELIVERY  = 40
TIMEOUT_RETURN    = 120
