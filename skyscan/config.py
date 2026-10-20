"""
SkyScan (AeroTHON 2026, Mission 2) - every number the mission uses lives here.

Coordinate convention used everywhere in this code base
-------------------------------------------------------
WORLD frame = the Gazebo/SDF frame of aerothon_mission.sdf
    x = east, y = north (metres)
    alt = metres above the take-off ground
    heading = ENU angle in radians: 0 = east (+x), +pi/2 = north (+y), CCW positive

For the real field, survey the course in the same kind of frame (any origin,
x east / y north) and only this file has to change.
"""
import math

# ── Link ───────────────────────────────────────────────────────────────────
MAVLINK_URL = "tcp:127.0.0.1:5762"     # SITL SERIAL1; MAVProxy keeps 5760
MAVLINK_SOURCE_SYSTEM = 250
WORLD_NAME = "aerothon_mission"

# ── Course layout (from create_world.py) ───────────────────────────────────
HOME_XY = (-3.0, 3.0)                  # take-off point: only labels the world frame in logs

# Start QR search, relative to the take-off spot and heading (no QR coordinates):
START_QR_FORWARD_STEP = 1.0            # rulebook: "move forward approximately 1 m"
START_QR_MAX_FORWARD = 5.0             # keep creeping forward up to this far
START_QR_RING_CENTRE = 3.0             # then search a ring this far ahead ...
START_QR_RING = 2.5                    # ... with this radius
START_QR_SPIRAL = (4.0, 7.0)           # still nothing: wider rings of these radii (same 5 m)

CORRIDOR_WIDTH = 3.5
FORWARD_CORRIDOR_NAME = "green"        # found by the front camera, no coordinates
# Return lap (phase 2, --full) still uses a surveyed axis:
# entry = centre of the opening we fly INTO, exit = centre of the far opening
RETURN_CORRIDOR = dict(name="orange", entry=(16.0, -3.0), exit=(6.0, -3.0), colour="orange")

# The delivery zone is NOT given to the code: the drone finds the QR field itself
# (searchmap.py). Red zones known in advance as (xmin, xmax, ymin, ymax); empty = camera only.
KNOWN_RED_ZONES = []
# Soft geofence (safety only, never used to plan the search): the mission refuses to
# command a point outside this box. Must contain the whole course.
GEOFENCE = (-40.0, 90.0, -45.0, 45.0)

# ── Altitudes (m) - rulebook section 4.2.4 ─────────────────────────────────
ALT_QR = 5.0            # take off + scan start QR
ALT_ALIGN = 5.0         # corridor search, approach + entrance alignment: hold 5 m until aligned
ALT_CORRIDOR = 3.0      # 10 ft corridor altitude
ALT_SEARCH = 10.0       # delivery-zone search / return transit
ALT_DELIVERY = 5.0      # payload lowering altitude
ALT_HOME = 5.0          # transit from corridor exit to the take-off point

# ── Speeds (m/s) ───────────────────────────────────────────────────────────
SPEED_TRANSIT = 4.0
SPEED_SCAN = 1.0        # start-QR scan and alignment moves
SPEED_SEARCH = 3.0      # lawnmower over the delivery zone

# ── Down camera (iris_with_standoffs/base_link/down_camera) ────────────────
CAM_SENSOR = "down_camera"
CAM_HFOV = 1.7802       # rad (102 deg) - Raspberry Pi Camera Module 3 Wide (102 x 67 deg)
DOWN_WORK_WIDTH = 640   # colour work (floor, entrance edge, red zones) on a copy this wide;
                        # QR codes are read on the full frame
CAM_HEIGHT_OFFSET = 0.145   # camera height above ground when alt == 0 (0.195 - 0.05)

# ── Front camera (iris_with_standoffs/base_link/front_camera) ─────────────
# Fixed, 45 deg down: finds the green banner / corridor and its direction.
FRONT_CAM_SENSOR = "front_camera"
FRONT_CAM_HFOV = 1.3963     # rad (80 deg), 640x480
FRONT_CAM_TILT = math.radians(45.0)
FRONT_CAM_HEIGHT_OFFSET = 0.195

# HSV ranges (OpenCV: H 0..180). Gazebo colours: green (0.1,0.8,0.1),
# orange (0.95,0.55,0.05), red (0.9,0.1,0.1).
HSV = {
    "green": [((35, 80, 50), (85, 255, 255))],
    "orange": [((8, 120, 90), (24, 255, 255))],
    "red": [((0, 130, 70), (6, 255, 255)), ((172, 130, 70), (180, 255, 255))],
}

# ── LiDAR (iris_with_standoffs/base_link/lidar_360) ────────────────────────
LIDAR_SENSOR = "lidar_360"
LIDAR_MIN_RANGE = 0.45      # drop self-hits on props/legs
LIDAR_MAX_RANGE = 11.9
LIDAR_STALE_S = 0.5

# ── Green corridor search (front camera -> ground map) ────────────────────
BANNER_COLOUR = "green"
BANNER_YAW_STEP = math.radians(45.0)   # look-around step
BANNER_LOOK_FRAMES = 3                 # front frames voted into the map per look
BANNER_MAP_VOTES = 2                   # a map cell counts as green after this many frames
BANNER_MIN_LENGTH = 4.5                # a candidate strip must be at least this long (m)
BANNER_MAX_RANGE = 30.0                # ignore ground further than this (m) ...
BANNER_RANGE_PER_M = 4.0               # ... or than this many times the camera height
BANNER_SEARCH_RINGS = (10.0, 20.0)     # 360 spin found nothing: move out on rings of these radii ...
BANNER_SEARCH_BEARINGS = 8             # ... at this many bearings, spinning 360 deg at each
BANNER_INVESTIGATE_DIST = 7.0          # partly seen green blob: get this close and look
BANNER_SEARCH_TIMEOUT = 150.0          # whole FIND_BANNER stage (s)
BANNER_BLOCKED_DIST = 1.5              # LiDAR return this close ahead while searching -> stop the leg
BANNER_APPROACH_STEP = 4.0             # re-look every this many metres on the way in
BANNER_APPROACH_SPEED = 2.5
HANDOVER_DIST = 5.0                    # down camera may take over this close to the entrance
HANDOVER_FRAMES = 3                    # consecutive down frames showing the corridor floor

# ── Corridor navigation ────────────────────────────────────────────────────
APPROACH_DIST = 1.2         # hover this far before the entrance to align
EXIT_MARGIN = 1.2           # corridor finished this far past the exit
DRONE_RADIUS = 0.40         # prop-tip radius of the airframe
SAFETY_MARGIN = 0.20        # extra clearance kept from walls / obstacles
CORRIDOR_SPAN = 3.0         # lateral search range (m) either side of the drone
CORRIDOR_WINDOWS = ((-0.6, 0.6), (0.6, 1.6), (1.6, 3.2))   # look-ahead bands (m)
CORRIDOR_SPEED = 1.0        # max forward speed
CORRIDOR_STOP_DIST = 0.9    # stop when an obstacle is this close in our path
CORRIDOR_K_FWD = 0.7
CORRIDOR_K_LAT = 1.2
CORRIDOR_MAX_LAT = 0.6
CORRIDOR_TIMEOUT = 90.0
WALL_DIST = 2.6             # a return beside us closer than this counts as a wall
WALL_CONFIRM_SCANS = 5      # consecutive scans with walls on both sides = inside
EXIT_CONFIRM_SCANS = 10     # consecutive scans without walls (after inside) = exited
CORRIDOR_MAX_LENGTH = 40.0  # safety: stop if we travel this far without an exit
HEADING_FROM_WALLS_GAIN = 0.2   # per scan, low-pass of the LiDAR wall-angle correction
CORRIDOR_STUCK_S = 15.0     # no progress for this long = FAILED

# Alignment acceptance
ALIGN_LAT_TOL = 0.15        # m
ALIGN_YAW_TOL = math.radians(3.0)
ALIGN_MAX_CORRECTION = 2.0  # reject a measurement that moves the axis more than this
ALIGN_MAX_YAW_CORRECTION = math.radians(20.0)
ALIGN_ATTEMPTS = 6
ALIGN_EDGE_AHEAD = 0.7      # align hovering OUTSIDE, with the entrance edge this far ahead (m)
ALIGN_CREEP_STEP = 0.8      # floor not in the down camera yet: creep forward this much ...
ALIGN_CREEP_MAX = 4.0       # ... up to this far in total
ALIGN_MIN_FLOOR_ROWS = 0.2  # floor must span this fraction of the image height to measure
ALIGN_FALLBACK_TO_PRIOR = False  # True: enter on the estimate anyway (warn); False: retry / search again

# ── Delivery search: no zone coordinates (searchmap.py) ───────────────────
# scout -> heat map -> best next look -> stop-and-snap, repeat until the target reads
SEARCH_HEADING = 0.0        # default only; each stop picks its camera heading
SEARCH_USABLE = 0.85        # fraction of the camera footprint trusted for reading QRs
SEARCH_SNAP_FRAMES = 2      # frames read at every stop (2 = a QR is confirmed in one stop)
SEARCH_FOLLOWUP_ALT = 7.0   # QR-looking spot that did not read from 10 m: look from here
SEARCH_FOLLOWUP_MAX = 8     # at most this many follow-up looks
SEARCH_TIMEOUT = 150.0      # whole SEARCH stage (s) - battery budget
# heat map, in the frame of the corridor exit (u forward, v left), metres
SEARCH_CELL = 1.0
SEARCH_BACK = 10.0          # map starts this far behind the exit (never searched there)
SEARCH_MAX_AHEAD = 70.0     # ... and reaches this far ahead
SEARCH_MAX_SIDE = 50.0      # ... and this far to each side
SEARCH_PRIOR_DIST = 25.0    # QR field centre most likely about this far after the exit ...
SEARCH_PRIOR_SPREAD = 20.0  # ... give or take this much
SEARCH_FIELD_SIZE = (40.0, 30.0)    # the codes lie in one field this big (position/rotation unknown)
SEARCH_FIELD_MARGIN = 4.0   # m added to the field size (organiser tolerance, GPS-free guess)
SEARCH_FIELD_ANGLES = 15    # field rotations tried, every this many degrees
SEARCH_FIELD_CODES = 7      # codes in the field (rulebook: 6-7)
SEARCH_DETECT_P = 0.9       # chance a code under a stop's picture is read
SEARCH_BEHIND_PENALTY = 10.0    # field placements reaching behind the exit line are unlikely
SEARCH_SEEN_FACTOR = 0.05   # what is left "unseen" in the sharp middle of a stop's picture
SEARCH_EDGE_FACTOR = 0.3    # ... and in its outer band
SEARCH_TRANSIT_FACTOR = 0.4 # flying between stops: ground under the camera is partly checked
SEARCH_TRANSIT_STEP = 6.0   # ... marked every this many metres of travel (level flight only)
SEARCH_PIN_WEIGHT = 0.5     # each scout pin inside a field placement: x (1 + this) as likely
SEARCH_CANDIDATE_STEP = 2.0 # candidate stops every this many metres
SEARCH_STOP_TIME = 5.0      # s per stop (brake, settle, read) in the cost
SEARCH_MIN_GAIN = 0.01      # stop when the best look has < 1 % chance of holding the target
SCOUT_LOOKS = (0.0, 45.0, -45.0, 90.0, -90.0)   # front-camera scout headings at the exit (deg)
SCOUT_MAX_RANGE = 30.0      # QR-looking squares further than this are ignored
RED_MARGIN = 1.5            # keep this far (m) from any red zone edge
RED_MAP_VOTES = 3           # a ground cell is red after this many frames saw it red
RED_VIEW_ANGLE = math.radians(45.0)   # only ground within this angle of straight down votes
RED_MAX_TILT = math.radians(5.0)      # ... and only while the drone is this level
RED_MIN_AREA = 0.5          # m^2, smaller red blobs are ignored
QR_CONFIRMATIONS = 2        # decodes of the same payload before we trust it

# ── Delivery ───────────────────────────────────────────────────────────────
CENTRE_K = 0.6
CENTRE_MAX_SPEED = 1.0
CENTRE_TOL_HIGH = 0.4       # m, at search altitude
CENTRE_TOL_LOW = 0.15       # m, at delivery altitude
CENTRE_SETTLE_FRAMES = 8
CENTRE_LOST_S = 8.0
PAYLOAD_LOWER_S = 5.0       # hover centred while the payload is lowered
PAYLOAD_SERVO = None        # e.g. (9, 1900) -> MAV_CMD_DO_SET_SERVO on release

# ── Mission ────────────────────────────────────────────────────────────────
MISSION_TIME_LIMIT = 15 * 60.0
ABORT_AT = 8 * 60.0       # battery ~10-11 min of hover: RTL from here
STAGE_RETRIES = 1           # each failed stage is retried once ...
RECOVER_ALT = 7.0           # ONLY when a corridor attempt fails between the walls: climb clear of them
MAX_FALLBACKS = 3          # ... then up to this many times the mission goes back to an
                            # earlier stage (e.g. corridor failed -> search again), then RTL
TELEMETRY_MAX_AGE = 1.0

# ── Return (orange) corridor search ────────────────────────────────────────
RETURN_SEARCH_TIMEOUT = 150.0     # s for the whole FIND_RETURN stage (battery budget)
RETURN_SEARCH_STEP = 12.0         # search points every this many metres on the way home
RETURN_FALLBACK_TO_SURVEY = False # True: if the camera search fails, fly to RETURN_CORRIDOR coordinates
RETURN_ORBIT_R = 9.0              # m: look at a half-hidden corridor blob from this far, from its other sides
RETURN_RESERVE_S = 120.0          # s kept for corridor + landing after the search
ALIGN_TRUST_AFTER = 2           # the same out-of-range down-camera measurement this many extra times is accepted
RETURN_STAGE_AHEAD = 12.0         # m beyond the forward corridor exit: where we look back at the corridor mouths from
RETURN_STAGE_LATERAL = (0.0, 9.0, -9.0, 17.0, -17.0)   # m to the side of the forward axis (left positive)
LAND_FAST_TO_ALT = 1.2        # m: descend at LAND_FAST_SPEED down to here, then LAND mode
LAND_FAST_SPEED = 1.0         # m/s
