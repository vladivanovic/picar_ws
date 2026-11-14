#!/bin/bash
# PiCar Gazebo simulation only (no SLAM) -- AGX Orin or any desktop.
# Workspace path is derived from this script's location (an earlier
# version hardcoded an ~/.openclaw path that existed on one machine).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source /opt/ros/jazzy/setup.bash
if [ -f "$SCRIPT_DIR/install/setup.bash" ]; then
    source "$SCRIPT_DIR/install/setup.bash"
fi
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

echo "==== PiCar Gazebo simulation (domain $ROS_DOMAIN_ID) ===="
echo "Drive: ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.0}}' -r 10"
echo "Scan:  ros2 topic echo /scan"
echo ""

ros2 launch agenticros_sim sim_picar.launch.py use_rviz:=true gui:=true
