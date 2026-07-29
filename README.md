# Picar Robot Car Project

## Overview
A distributed robotics system where the **NVIDIA AGX Orin** acts as the primary Control Unit and the **Raspberry Pi** handles the hardware drivers (Motors, LiDAR).

## Architecture
- **Control Unit (AGX Orin):** Runs high-level logic, RViz2 monitoring, and LiDAR-based SLAM/Odometry.
- **Hardware Unit (Raspberry Pi):** Runs motor drivers and sensors.

## Deployment Instructions

### Robot Car (Raspberry Pi)
```bash
# Update workspace
cd /home/vlad/picar_ws
git pull origin main
colcon build --symlink-install
source install/setup.bash

# Launch hardware drivers (Namespaced to /picar_pi)
ros2 launch picar4wd_driver picar_bringup.launch.py
```

### Control Unit (AGX Orin)
```bash
# Update workspace
cd /home/vlad/picar_ws
git pull origin main
colcon build --symlink-install
source install/setup.bash

# 1. Start Discovery Agent
ros2 run agenticros_discovery discovery_node --ros-args -p robot_namespace:=control_unit -p robot_id:=orin_master

# 2. Start Odometry (SLAM/LiDAR)
ros2 run picar4wd_driver odom_node

# 3. Start Bridge & High-level Logic
ros2 launch agenticros_bringup cmd_vel_bridge.launch.py
```

## Troubleshooting
- **Network:** Ensure both units are on the same subnet and can ping each other.
- **Namespace:** If commands aren't reaching the motors, verify that the bridge is relaying to `/picar_pi/cmd_vel`.
