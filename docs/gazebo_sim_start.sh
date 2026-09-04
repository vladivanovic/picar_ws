#!/bin/bash
# Picar Gazebo Simulation Startup
# NVIDIA AGX Orin (Control Unit)
# This script sets up Gazebo Harmonic simulation with the diff-drive AMR
# and bridges all topics to match real-robot driver interfaces

set -e

WS_ROOT=$(cd "$(dirname "$0")/.." && pwd)
export ROS_DISTRO=jazzy
source /opt/ros/$ROS_DISTRO/setup.bash
source $WS_ROOT/install/setup.bash

echo "==== Picar Gazebo Simulation Started ===="
echo "World: agenticros_indoor.sdf (12x12m with obstacles)"
echo "AMR: diff-drive with depth cam, lidar, IMU"
echo ""
echo "Starting Gazebo Harmonic with RViz..."

ros2 launch agenticros_sim sim_amr.launch.py use_rviz:=true gui:=true
