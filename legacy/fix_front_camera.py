#!/usr/bin/env python3
"""
fix_front_camera.py — Diagnose and fix the front camera not showing up.

Run this WHILE Gazebo is running (after loading aerothon_mission.sdf).

Steps:
  1. Lists all Gazebo image topics
  2. Finds the front/gimbal camera topic
  3. Prints the correct FRONT_CAM_TOPIC to put in config.py
  4. Optionally shows a live preview window

Usage:
  python3 ~/aerothon_sim/fix_front_camera.py
"""
import sys
import time
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("WARNING: opencv not installed — no preview window")

try:
    from gz.transport13 import Node
    from gz.msgs10 import image_pb2, stringmsg_pb2
    HAS_GZ = True
    print("gz.transport13 loaded ✓")
except ImportError:
    try:
        from gz.transport12 import Node
        from gz.msgs9 import image_pb2
        HAS_GZ = True
        print("gz.transport12 loaded ✓")
    except ImportError:
        HAS_GZ = False
        print("ERROR: gz.transport not available")
        sys.exit(1)

print()
print("=" * 60)
print("  AeroTHON 2026 Front Camera Diagnostic")
print("=" * 60)
print()

# ── Step 1: List all Gazebo topics ────────────────────────────────────────────
node = Node()

print("Fetching topic list from Gazebo ...")
print("(Make sure Gazebo is running with aerothon_mission.sdf loaded)")
print()
time.sleep(1)

topics = node.topic_list()
image_topics = [t for t in topics if "image" in t.lower()]

print(f"Found {len(image_topics)} image topic(s):")
for i, t in enumerate(image_topics):
    print(f"  [{i+1}] {t}")

print()

# ── Step 2: Find gimbal / pitch_link topic ────────────────────────────────────
gimbal_topics = [t for t in image_topics
                 if any(kw in t for kw in
                        ['gimbal', 'pitch', 'front', 'camera'])]

down_topics   = [t for t in image_topics
                 if 'down' in t or 'base_link' in t]

print(f"Likely FRONT camera topics ({len(gimbal_topics)}):")
for t in gimbal_topics:
    print(f"  ✓ {t}")

print()
print(f"Likely DOWN camera topics ({len(down_topics)}):")
for t in down_topics:
    print(f"  ✓ {t}")

print()

# ── Step 3: Recommend config update ──────────────────────────────────────────
if gimbal_topics:
    best = gimbal_topics[0]
    print("=" * 60)
    print("ACTION REQUIRED — Update config.py:")
    print()
    print(f"  FRONT_CAM_TOPIC = \"{best}\"")
    print()
    print("Copy the line above into ~/aerothon_sim/config.py")
    print("=" * 60)
    print()

    # ── Step 4: Live preview ──────────────────────────────────────────────────
    if HAS_CV2:
        latest_frame = [None]

        def cb(msg):
            try:
                img = np.frombuffer(msg.data, dtype=np.uint8)
                if msg.pixel_format_type == 4:
                    img = img.reshape(msg.height, msg.width, 4)[:, :, :3]
                else:
                    img = img.reshape(msg.height, msg.width, 3)
                latest_frame[0] = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Frame error: {e}")

        print(f"Subscribing to: {best}")
        node.subscribe(image_pb2.Image, best, cb)
        print("Waiting for frames ... (press Q to quit)")
        time.sleep(1)

        while True:
            if latest_frame[0] is not None:
                cv2.imshow("Front Camera Preview", latest_frame[0])
            key = cv2.waitKey(30)
            if key == ord('q'):
                break

        cv2.destroyAllWindows()
else:
    print("=" * 60)
    print("NO FRONT CAMERA TOPIC FOUND!")
    print()
    print("Possible causes:")
    print("  1. iris_with_gimbal model not loaded in SDF")
    print("     → Check: <include><uri>model://iris_with_gimbal</uri>...")
    print("     → in ~/gz_ws/src/aerothon_world/worlds/aerothon_mission.sdf")
    print()
    print("  2. ardupilot_gazebo not in GZ_SIM_RESOURCE_PATH")
    print("     → The iris_with_gimbal model must be found by Gazebo")
    print()
    print("  3. Camera sensor missing from iris_with_gimbal model")
    print("     → Run: add_down_camera.py (also check gimbal camera exists)")
    print()
    print("All image topics found:")
    for t in image_topics:
        print(f"  {t}")
    print("=" * 60)
