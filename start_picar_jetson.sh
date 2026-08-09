#!/bin/bash
# Jetson Orin Nano startup script
# Optimized for remote control (no local hardware/serial dependencies)

source /opt/ros/jazzy/setup.bash
source ~/.openclaw/workspace/picar_ws/install/setup.bash

export ROS_DOMAIN_ID=42

# 1. Start Discovery Agent
ros2 run agenticros_discovery discovery_node --ros-args -p robot_namespace:=control_unit -p robot_id:=orin_master -p has_lidar:=true &

# 2. Start Odometry
ros2 run picar4wd_driver odom_node --ros-args -p use_sim_time:=false &

# 3. Start SLAM Toolbox
# Using absolute install path for the config to ensure it's found
ros2 run slam_toolbox async_slam_toolbox_node --ros-args -p use_sim_time:=false -p slam_params_file:=$(ros2 pkg prefix slam_toolbox)/share/slam_toolbox/config/mapper_params_online_async.yaml &
sleep 5
ros2 lifecycle set /slam_toolbox configure
ros2 lifecycle set /slam_toolbox activate

# 4. Start Bridge (Added required src_cmd_vel argument)
ros2 launch agenticros_bringup cmd_vel_bridge.launch.py src_cmd_vel:=/cmd_vel &

sleep 5

# Start RViz
RVIZ_CFG="$HOME/.openclaw/workspace/picar_ws/src/agenticros_bringup/rviz/turtlebot3_agenticros.rviz"
if [ -f "$RVIZ_CFG" ]; then
    ros2 run rviz2 rviz2 -d "$RVIZ_CFG"
else
    ros2 run rviz2 rviz2
fi
