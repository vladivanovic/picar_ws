#!/bin/bash
# Jetson Orin Nano startup script (Control Unit)
# - Sources ROS 2 environment
# - Sources the picar workspace
# - Sets ROS domain ID
# - Adjusts tty permissions (if LiDAR is directly connected)
# - Launches AgenticROS discovery, Odometry, SLAM, and the cmd_vel bridge.
# - Starts RViz2 for remote visualization and control

# Determine the correct ROS 2 distribution (Jazzy for consistency with Pi)
# If this Jetson setup is specifically tied to Humble, this line will need to be adjusted.
source /opt/ros/jazzy/setup.bash

# Picar workspace (installed on Jetson)
source ~/picar_ws/install/setup.bash

# Use the same DDS domain ID that the Pi uses
export ROS_DOMAIN_ID=42

# Permissions needed for USB serial on the Jetson (e.g., for LiDAR connection)
# GPIO and /dev/mem permissions are not needed on the Control Unit.
sudo chmod 666 /dev/ttyUSB0

# ----------------------------------------------------------------
# Launch Control Unit components as per README.md and project requirements
# ----------------------------------------------------------------

# 1. Start Discovery Agent
ros2 run agenticros_discovery discovery_node --ros-args -p robot_namespace:=control_unit -p robot_id:=orin_master -p has_lidar:=true &

# 2. Start Odometry (dead reckoning based on cmd_vel)
# This odometry is basic; for more accurate SLAM, an encoder-based odometry would be preferred.
ros2 run picar4wd_driver odom_node &

# 3. Start SLAM Toolbox for mapping
# Using async_slam_toolbox_node for real-time mapping.
# Parameters can be tuned in a separate config file if needed.
ros2 run slam_toolbox async_slam_toolbox_node --ros-args -p use_sim_time:=false -p slam_params_file:=$(ros2 pkg prefix agenticros_sim)/share/agenticros_sim/config/mapper_params_online_async.yaml &

# 4. Start Bridge & High-level Logic
ros2 launch agenticros_bringup cmd_vel_bridge.launch.py &

# Wait briefly for nodes to start before launching RViz
sleep 5

# ----------------------------------------------------------------
# Start RViz2 for remote monitoring / driving
# ----------------------------------------------------------------
# Get the RViz config path from the agenticros_bringup package
RVIZ_CFG_PKG_PATH=$(ros2 pkg prefix agenticros_bringup)/share/agenticros_bringup/rviz/turtlebot3_agenticros.rviz

# If the config file does not exist yet, you can create a minimal one.
if [ -f "$RVIZ_CFG_PKG_PATH" ]; then
    ros2 run rviz2 rviz2 -d "$RVIZ_CFG_PKG_PATH"
else
    echo "RViz config not found at $RVIZ_CFG_PKG_PATH – starting RViz without a config."
    ros2 run rviz2 rviz2
fi

# Bring all backgrounded ROS 2 processes to the foreground (optional, but useful for observing output)
# fg %1
# fg %2
# fg %3
# fg %4
