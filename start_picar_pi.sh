#!/bin/bash
# Raspberry Pi (Jazzy) startup script
# - Sources ROS 2 Jazzy
# - Sources the picar workspace
# - Sets ROS domain ID
# - Adjusts GPIO / tty permissions
# - Launches the full bringup (lidar, odometry, motor driver, etc.)

# ROS 2 Jazzy environment
source /opt/ros/jazzy/setup.bash

# Picar workspace
source ~/picar_ws/install/setup.bash

# Make sure the Python path includes the Sunfounder library
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd

# Use domain ID 42 for DDS discovery
export ROS_DOMAIN_ID=42

# GPIO and serial port permissions (required on the Pi)
sudo chmod 666 /dev/mem
sudo chmod 666 /dev/gpiomem
sudo chmod 666 /dev/ttyUSB0

# Launch the complete bringup that starts:
#   • RPLiDAR composition node
#   • static TF between base_link and lidar_link
#   • odometry (dead‑reckoning) node
#   • motor driver node (triggered after a short delay)
ros2 launch picar4wd_driver picar_bringup.launch.py