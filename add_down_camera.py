#!/usr/bin/env python3
"""Adds a fixed downward-facing camera sensor to the iris drone model."""
import os

model_path = os.path.expanduser(
    "~/gz_ws/src/ardupilot_gazebo/models/iris_with_standoffs/model.sdf"
)

# Read the model file
with open(model_path, "r") as f:
    content = f.read()

# Check if already added
if "down_camera" in content:
    print("Downward camera already exists in model. Skipping.")
    exit(0)

# The camera sensor XML to add inside base_link
down_cam_xml = """
      <!-- DOWNWARD FIXED CAMERA (added for AeroTHON) -->
      <sensor name="down_camera" type="camera">
        <pose>0 0 -0.05 0 1.5708 0</pose>
        <always_on>1</always_on>
        <update_rate>15</update_rate>
        <camera>
          <horizontal_fov>1.0472</horizontal_fov>
          <image>
            <width>640</width>
            <height>480</height>
            <format>RGB_INT8</format>
          </image>
          <clip>
            <near>0.1</near>
            <far>100</far>
          </clip>
        </camera>
      </sensor>
"""

# Insert before the closing </link> of base_link
# Find the first </link> which belongs to base_link
insert_marker = '</link>'
idx = content.find(insert_marker)
if idx == -1:
    print("ERROR: Could not find </link> in model.sdf")
    exit(1)

new_content = content[:idx] + down_cam_xml + "    " + content[idx:]

# Backup original
backup = model_path + ".bak"
if not os.path.exists(backup):
    with open(backup, "w") as f:
        f.write(content)
    print(f"Backup: {backup}")

with open(model_path, "w") as f:
    f.write(new_content)

print(f"✅ Added downward camera to {model_path}")
print("Topic will be: .../iris_with_standoffs/link/base_link/sensor/down_camera/image")
