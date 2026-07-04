#!/bin/bash
# Jetson Orin Nano (Humble) startup script
# - Sources ROS 2 Humble
# - Sources the picar workspace
# - Sets ROS domain ID
# - Adjusts permissions
# - Launches the motor driver / bringup (if not already running on the Pi)
# - Starts RViz2 for remote visualization and control

# ROS 2 Humble environment
source /opt/ros/humble/setup.bash

# Picar workspace (installed on Jetson)
source ~/picar_ws/install/setup.bash

# Extend Python path to include the Sunfounder driver library
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd

# Use the same DDS domain ID that the Pi uses
export ROS_DOMAIN_ID=42

# Permissions needed for GPIO and USB serial on the Jetson
sudo chmod 666 /dev/mem
sudo chmod 666 /dev/gpiomem
sudo chmod 666 /dev/ttyUSB0

# ----------------------------------------------------------------
# Bring up the robot driver (same launch file used on the Pi)
# ----------------------------------------------------------------
# This will start the RPLiDAR node, odometry, and (via Timer) the
# motor driver.  The launch file is platform‑agnostic; it just
# configures the nodes it needs.
ros2 launch picar4wd_driver picar_bringup.launch.py

# ----------------------------------------------------------------
# Start RViz2 for remote monitoring / driving
# ----------------------------------------------------------------
# Adjust the path to your RViz config if you store it elsewhere.
RVIZ_CFG="$HOME/picar_ws/src/agenticros_bringup/rviz/jetson_agenticros.rviz"

# If the config file does not exist yet, you can create a minimal one.
# For now we assume it already exists.
if [ -f "$RVIZ_CFG" ]; then
    ros2 run rviz2 rviz2 -d "$RVIZ_CFG"
else
    echo "RViz config not found at $RVIZ_CFG – starting RViz without a config."
    ros2 run rviz2 rviz2
fi