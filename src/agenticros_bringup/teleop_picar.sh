#!/bin/bash
# Picar Robot Teleop helper
# This script sources ROS2 Humble and runs the teleop_twist_keyboard node
# remapping /cmd_vel to /picar/cmd_vel

# Source ROS2 Humble
source /opt/ros/humble/setup.bash

# Source the current workspace
# Assuming it's run from the workspace or standard location
if [ -f "$HOME/.openclaw/workspace/ros2_ws/install/setup.bash" ]; then
    source "$HOME/.openclaw/workspace/ros2_ws/install/setup.bash"
fi

echo "Starting Picar Teleop..."
echo "Use WASD to move, Space to stop."
echo "Topic: /picar/cmd_vel"

ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/picar/cmd_vel
