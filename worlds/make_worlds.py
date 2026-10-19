#!/usr/bin/env python3
"""
Challenge worlds for the perception-driven phase 1 (start QR -> find green corridor).
Same course as create_world.py (orange corridor, delivery zone, QR A-E, red zones),
but the drone + start QR are moved away from the green corridor so the drone has to
search for it, and green decoys are added. The original aerothon_mission.sdf is not
touched.

    python3 worlds/make_worlds.py          # writes worlds/<name>.sdf

  offset : drone well left of + behind the corridor, corridor rotated 12 deg,
           entrance ~20 m away (beyond the low look range -> must climb);
           green tarp + grass patch as decoys
  behind : drone faces AWAY from the corridor (must turn round to find it)
  far    : corridor ~33 m away, out of view even from 12 m -> search points on rings
  All worlds: 7 QR codes (A-G, target C) and 3 red zones in the delivery zone.
  fake   : a wall-less green strip of corridor size lies nearer than the real
           corridor: the drone should try it, LiDAR finds no walls, reject, search again
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")          # copies of the course QRs + F, G

GREEN = (0.1, 0.8, 0.1)
GREY = (0.65, 0.65, 0.65)


def box(name, x, y, z, sx, sy, sz, rgb, yaw=0.0, solid=True):
    r, g, b = rgb
    c = (f'<collision name="c"><geometry><box><size>{sx} {sy} {sz}</size>'
         f'</box></geometry></collision>') if solid else ""
    return (f'<model name="{name}"><static>true</static>'
            f'<pose>{x:.3f} {y:.3f} {z} 0 0 {yaw:.5f}</pose>'
            f'<link name="l"><visual name="v"><geometry>'
            f'<box><size>{sx} {sy} {sz}</size></box></geometry>'
            f'<material><ambient>{r} {g} {b} 1</ambient>'
            f'<diffuse>{r} {g} {b} 1</diffuse></material>'
            f'</visual>{c}</link></model>')


def qr(name, x, y, png, size=1.0):
    return (f'<model name="{name}"><static>true</static>'
            f'<pose>{x} {y} 0.011 0 0 0</pose>'
            f'<link name="l"><visual name="v"><geometry>'
            f'<box><size>{size} {size} 0.001</size></box></geometry>'
            f'<material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse>'
            f'<pbr><metal><albedo_map>{TEX}/{png}</albedo_map></metal></pbr>'
            f'</material></visual></link></model>')


def corridor(prefix, entry, yaw_deg, rgb, length=10.0, width=3.5, walls=True):
    """Floor + 5 m walls, entrance centre at `entry`, running along yaw_deg."""
    a = math.radians(yaw_deg)
    t, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    cx, cy = entry[0] + t[0] * length / 2, entry[1] + t[1] * length / 2
    out = [box(f"{prefix}_floor", cx, cy, 0.005, length, width, 0.01, rgb, a)]
    if walls:
        for side, k in (("wL", 1), ("wR", -1)):
            out.append(box(f"{prefix}_{side}", cx + k * n[0] * width / 2, cy + k * n[1] * width / 2, 2.5,
                           length, 0.2, 5.0, GREY, a))
    return out


# Delivery field in its own frame (centre 0,0, x along the 40 m side): 7 QR codes
# (rulebook: 6-7) and 3 red zones. NOT marked on the ground - like the real event,
# where the zone exists only as organiser coordinates.
FIELD_QRS = {"a": (-17, 10), "b": (-9, -8), "c": (-1, 5), "d": (7, -12), "e": (15, 9),
             "f": (-18.5, -13.5), "g": (18.5, -1)}
FIELD_REDS = [(-13, 6), (5, -5), (11, 4)]


def field(centre=(39.0, 0.0), yaw_deg=0.0):
    """QR codes + red zones of the delivery field, placed at `centre`, rotated yaw_deg."""
    a = math.radians(yaw_deg)

    def at(p):
        return (centre[0] + p[0] * math.cos(a) - p[1] * math.sin(a),
                centre[1] + p[0] * math.sin(a) + p[1] * math.cos(a))

    p = [qr(f"qr_{k}", *at(xy), f"qr_{k}.png") for k, xy in FIELD_QRS.items()]
    p += [box(f"red{i + 1}", *at(xy), 0.008, 3, 3, 0.005, (0.9, 0.1, 0.1), yaw=a, solid=False)
          for i, xy in enumerate(FIELD_REDS)]
    return p


def course(green_entry=(6.0, 3.0), green_yaw=0.0, dz=((39.0, 0.0), 0.0), orange=((16.0, -3.0), 180.0)):
    p = corridor("green", green_entry, green_yaw, GREEN)
    (ex, ey), oyaw = orange
    p += corridor("orange", (ex, ey), oyaw, (0.95, 0.55, 0.05))
    th = math.radians(oyaw)
    t, n = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    # obstacles inside the orange corridor: (distance from the entrance, lateral offset to the left, size y)
    for i, (sd, lat, sy) in enumerate(((3.0, -1.0, 1.0), (5.0, 1.0, 1.0), (7.0, -0.5, 1.2)), 1):
        p.append(box(f"obs{i}", ex + sd * t[0] + lat * n[0], ey + sd * t[1] + lat * n[1], 2.5,
                     0.4, sy, 5.0, (0.4, 0.4, 0.4), th))
    return p + field(*dz)


def paper(name, x, y):
    """Blank white 1 m sheet: looks like a QR from far away (scout decoy)."""
    return box(name, x, y, 0.006, 1.0, 1.0, 0.002, (1.0, 1.0, 1.0), solid=False)


def world(drone, drone_yaw_deg, qr_xy, parts, start_png="qr_start.png"):
    yaw = math.radians(drone_yaw_deg)
    return f'''<?xml version="1.0" ?>
<sdf version="1.9">
<world name="aerothon_mission">
<physics name="1ms" type="ignore"><max_step_size>0.001</max_step_size><real_time_factor>1.0</real_time_factor></physics>
<plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
<light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 10 0 0 0</pose>
<diffuse>0.8 0.8 0.8 1</diffuse><specular>0.2 0.2 0.2 1</specular><direction>-0.5 0.1 -0.9</direction></light>
<model name="ground"><static>true</static><link name="l">
<collision name="c"><geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry></collision>
<visual name="v"><geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
<material><ambient>0.5 0.5 0.5 1</ambient><diffuse>0.5 0.5 0.5 1</diffuse></material></visual></link></model>
<include><uri>model://iris_with_gimbal</uri><name>iris</name><pose>{drone[0]} {drone[1]} 0.195 0 0 {yaw:.5f}</pose></include>
{qr("start_qr", qr_xy[0], qr_xy[1], start_png)}
{chr(10).join(parts)}
</world>
</sdf>'''


SCENARIOS = {
    # name: (drone xy, drone yaw deg, start QR xy, green yaw deg, extra parts)
    "offset": ((-14.0, -6.0), 0.0, (-11.5, -6.0), 12.0,
               [box("decoy_tarp", -3.0, -1.0, 0.006, 5.0, 1.5, 0.01, GREEN, math.radians(30), False),
                box("decoy_grass", -6.0, 11.0, 0.004, 10.0, 7.0, 0.008, GREEN, 0.0, False)]),
    "behind": ((-6.0, 3.0), 180.0, (-8.5, 3.0), 0.0, []),
    "far": ((-24.0, -12.0), 90.0, (-24.0, -9.5), 0.0,
            [box("decoy_grass", -16.0, 2.0, 0.004, 9.0, 9.0, 0.008, GREEN, 0.0, False)]),
    "fake": ((-14.0, 3.0), 0.0, (-11.5, 3.0), 0.0,
             corridor("fake", (-5.0, -9.0), 20.0, GREEN, walls=False)),
}


# Delivery-search worlds: easy phase 1 (drone at -3,3 facing the corridor), the QR
# field put somewhere different each time and NOT marked. The drone gets no zone
# coordinates - it has to find the field.
#   name: (field centre, field yaw deg, target letter, extra parts)
DELIVERY = {
    "dz_ahead": ((39.0, 0.0), 0.0, "c", []),
    "dz_side": ((36.0, 24.0), 0.0, "g", [paper("paper1", 24.0, 7.0), paper("paper2", 31.0, -6.0)]),
    "dz_rot": ((45.0, -4.0), 30.0, "f", []),
    "dz_far": ((58.0, 8.0), -15.0, "e", [paper("paper1", 27.0, 2.0)]),
}

# Return-corridor worlds: the orange corridor is NOT where the old code assumed
# (16, -3): the drone has to find it. name: (field centre, field yaw, target, orange (entry, yaw))
RETURN = {
    "ret_south": (((39.0, 0.0), 0.0), "c", ((24.0, -14.0), 185.0)),
    "ret_north": (((45.0, -4.0), 30.0), "f", ((12.0, 15.0), 190.0)),
    "ret_near": (((39.0, 0.0), 0.0), "c", ((30.0, -2.0), 175.0)),
}


if __name__ == "__main__":
    for name, (drone, dyaw, qxy, gyaw, extra) in SCENARIOS.items():
        path = os.path.join(HERE, f"{name}.sdf")
        with open(path, "w") as f:
            f.write(world(drone, dyaw, qxy, course(green_yaw=gyaw) + extra))
        print(f"{path}: drone {drone} facing {dyaw:.0f} deg, start QR {qxy}, green corridor yaw {gyaw:.0f} deg"
              f"  ->  run_mission.py --home {drone[0]} {drone[1]}")
    for name, (centre, yaw, target, extra) in DELIVERY.items():
        path = os.path.join(HERE, f"{name}.sdf")
        with open(path, "w") as f:
            f.write(world((-3.0, 3.0), 0.0, (0.0, 3.0), course(dz=(centre, yaw)) + extra,
                          start_png=f"qr_start_{target}.png"))
        print(f"{path}: QR field centre {centre}, yaw {yaw:.0f} deg, target {target.upper()}"
              f"  ->  run_mission.py --full --home -3 3")
    for name, (dz, target, orange) in RETURN.items():
        path = os.path.join(HERE, f"{name}.sdf")
        with open(path, "w") as f:
            f.write(world((-3.0, 3.0), 0.0, (0.0, 3.0), course(dz=dz, orange=orange),
                          start_png=f"qr_start_{target}.png"))
        print(f"{path}: orange entrance {orange[0]}, yaw {orange[1]:.0f} deg, target {target.upper()}"
              f"  ->  run_mission.py --full --home -3 3")
