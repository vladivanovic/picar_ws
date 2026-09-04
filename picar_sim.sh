#!/bin/bash
# Picar Gazebo Simulation Startup
# NVIDIA AGX Orin (Control Unit)
# Launches Gazebo Harmonic with diff-drive AMR

set -e

WS_ROOT=/home/vlad/.openclaw/workspace/picar_ws
ROS_DISTRO=jazzy

# Source ROS2
source /opt/ros/$ROS_DISTRO/setup.bash

# Source workspace
if [ -d "$WS_ROOT/install" ]; then
    source "$WS_ROOT/install/setup.bash"
fi

echo "==== Picar Gazebo Simulation Starting ===="
echo "URDF: agenticros_sim/urdf/agenticros_amr.urdf.xacro (2-wheeled diff-drive)"
echo "Sensors: RGBD camera, LiDAR (360 samples), IMU"
echo "World: agenticros_indoor.sdf (12x12m indoor with obstacles)"
echo ""

# Launch simulator with RViz
ros2 launch agenticros_sim sim_amr.launch.py \
    use_rviz:=true \
    gui:=true \
    world:=worlds/agenticros_indoor.sdf

echo ""
echo "Press Ctrl+C to stop simulation"
echo ""
echo "Quick commands:"
echo "  Drive: ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.0}}' --rate 10"
echo "  LiDAR: ros2 topic echo /scan"
echo "  Depth: ros2 topic echo /camera/camera/depth/points"
