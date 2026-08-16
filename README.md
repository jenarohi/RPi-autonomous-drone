# RPi Autonomous Drone - AeroTHON 2026

Autonomous drone simulation and mission control for **SAEINDIA AeroTHON 2026 - Track 1: Rotorcraft Systems Challenge (UAS)**.

**Theme:** Aerial Surveillance and Rapid Delivery

---

## Mission 2: SkyScan - Autonomous Rapid Delivery

A fully autonomous 12-state mission:

| State | Phase |
|-------|-------|
| 1 | Takeoff |
| 2 | Scan start QR code - identify delivery target |
| 3 | Align to green corridor banner |
| 4 | Navigate forward through green corridor |
| 5 | Ascend to search altitude |
| 6 | Lawnmower search of 40x30m delivery zone |
| 7 | Precision centering over target QR |
| 8 | Descend + winch payload delivery |
| 9 | Ascend for return |
| 10 | Align to orange corridor banner |
| 11 | Navigate return through orange corridor (with obstacles) |
| 12 | RTL + autonomous landing |

---

## Stack

- **Simulator:** Gazebo Harmonic (gz-sim)
- **Autopilot:** ArduPilot SITL (ArduCopter)
- **Communication:** MAVLink via pymavlink
- **Vision:** OpenCV + pyzbar (QR decoding)
- **Transport:** gz.transport13 / gz.msgs10
- **Platform:** WSL2 Ubuntu 22.04

---

## World Layout

- Drone spawns at x=-3, y=3
- Start QR at x=0
- Green corridor: x=6..16, y=1.25..4.75
- Orange corridor: x=6..16, y=-1.25..-4.75 (with obstacles)
- Delivery zone: x=19..59, y=-15..15 (40m x 30m)

---

## File Structure

| File | Purpose |
|------|---------|
| main_mission.py | 12-state mission orchestrator |
| flight_controller.py | MAVLink/ArduPilot interface |
| corridor_nav.py | PID + LiDAR corridor navigation |
| down_camera.py | Nadir camera - QR, green/red detection |
| front_camera.py | Forward gimbal camera - banner detection |
| lidar_bridge.py | Gazebo LiDAR to MAVLink OBSTACLE_DISTANCE |
| search_pattern.py | Lawnmower waypoint generator |
| pid.py | Full PID controller with anti-windup |
| winch.py | Payload winch (simulation mock) |
| mission_plan.py | GPS anchor calculator |
| config.py | All tunable parameters |
| create_world.py | Gazebo SDF world generator |

---

## How to Run (WSL2 Ubuntu 22.04)

**Terminal 1 - Gazebo:**
`bash
GZ_SIM_RESOURCE_PATH=$HOME/gz_ws/src/ardupilot_gazebo/models:$HOME/gz_ws/src/aerothon_world/worlds:$GZ_SIM_RESOURCE_PATH gz sim -v4 -r aerothon_mission.sdf
`

**Terminal 2 - ArduPilot SITL:**
`bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map
`

**Terminal 3 - Mission:**
`bash
cd ~/aerothon_sim
source ~/drone_env/bin/activate
python3 main_mission.py
`

Select option **6** for full autonomous mission.
