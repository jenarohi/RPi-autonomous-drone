#!/usr/bin/env python3
# create_world.py — AeroTHON 2026 Gazebo World Generator
# Layout (SDF world x-axis = east):
#   Drone(x=-3) -3m-> QR(x=0) -6m-> Green entrance(x=6..16)
#   Orange corridor: x=6..16, y=-1.25 to -4.75
#   Delivery zone:   x=19..59, y=-15..15  (40m x 30m)

import os

home = os.path.expanduser("~")
path = f"{home}/gz_ws/src/aerothon_world/worlds/aerothon_mission.sdf"
tex  = f"{home}/gz_ws/src/aerothon_world/textures"
os.makedirs(os.path.dirname(path), exist_ok=True)


def box(name, x, y, z, sx, sy, sz, r, g, b, solid=True):
    c = (f'<collision name="c"><geometry><box><size>{sx} {sy} {sz}</size>'
         f'</box></geometry></collision>') if solid else ""
    return (f'<model name="{name}"><static>true</static>'
            f'<pose>{x} {y} {z} 0 0 0</pose>'
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
            f'<pbr><metal><albedo_map>{tex}/{png}</albedo_map></metal></pbr>'
            f'</material></visual></link></model>')


p = []

# ── START QR ────────────────────────────────────────────────────
p.append(qr("start_qr", 0, 3, "qr_start.png", size=1.0))

# ── GREEN CORRIDOR  x=6..16, y=1.25..4.75 ───────────────────────
p.append(box("green_floor", 11,  3.0,  0.005, 10, 3.5, 0.01, 0.1, 0.8, 0.1))
p.append(box("green_wL",    11,  4.75, 2.5,   10, 0.2, 5.0,  0.65, 0.65, 0.65))
p.append(box("green_wR",    11,  1.25, 2.5,   10, 0.2, 5.0,  0.65, 0.65, 0.65))

# ── ORANGE CORRIDOR  x=6..16, y=-1.25..-4.75 ────────────────────
p.append(box("orange_floor", 11, -3.0,  0.005, 10, 3.5, 0.01, 0.95, 0.55, 0.05))
p.append(box("orange_wL",    11, -1.25, 2.5,   10, 0.2, 5.0,  0.65, 0.65, 0.65))
p.append(box("orange_wR",    11, -4.75, 2.5,   10, 0.2, 5.0,  0.65, 0.65, 0.65))

# Obstacles inside orange corridor
p.append(box("obs1",  9,  -2.0, 2.5, 0.4, 1.0, 5.0, 0.4, 0.4, 0.4))
p.append(box("obs2", 11,  -4.0, 2.5, 0.4, 1.0, 5.0, 0.4, 0.4, 0.4))
p.append(box("obs3", 13,  -2.5, 2.5, 0.4, 1.2, 5.0, 0.4, 0.4, 0.4))

# ── DELIVERY ZONE  x=19..59, y=-15..15  (40m x 30m) ────────────
# Centre at x=39, y=0
p.append(box("dz_floor", 39, 0, 0.003, 40, 30, 0.005, 0.78, 0.78, 0.82, False))

# 1m x 1m QR codes spread across 40x30m zone
# Zone world coords: x=19..59, y=-15..15
p.append(qr("qr_a",  22,  10, "qr_a.png", 1.0))
p.append(qr("qr_b",  30,  -8, "qr_b.png", 1.0))
p.append(qr("qr_c",  38,   5, "qr_c.png", 1.0))   # TARGET
p.append(qr("qr_d",  46, -12, "qr_d.png", 1.0))
p.append(qr("qr_e",  54,   9, "qr_e.png", 1.0))

# Red no-land zones
p.append(box("red1", 26,  6, 0.008, 3, 3, 0.005, 0.9, 0.1, 0.1, False))
p.append(box("red2", 44, -5, 0.008, 3, 3, 0.005, 0.9, 0.1, 0.1, False))

sdf = f'''<?xml version="1.0" ?>
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
<include><uri>model://iris_with_gimbal</uri><name>iris</name><pose>-3 3 0.195 0 0 0</pose></include>
{chr(10).join(p)}
</world>
</sdf>'''

with open(path, "w") as f:
    f.write(sdf)
print(f"Created: {path}")
print("World layout:")
print("  Drone    @ x=-3,  y=3")
print("  QR start @ x=0,   y=3")
print("  Green    @ x=6..16,  y=1.25..4.75")
print("  Orange   @ x=6..16,  y=-1.25..-4.75  (with obstacles)")
print("  DelivZone@ x=19..59, y=-15..15  (40mx30m)")
print("  QR-C     @ x=38,  y=5  (target)")
