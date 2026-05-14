#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/picar_ws/install/setup.bash
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd
export ROS_DOMAIN_ID=42

# Ensure GPIO permissions
sudo chmod 666 /dev/mem
sudo chmod 666 /dev/gpiomem
sudo chmod 666 /dev/ttyUSB0

ros2 launch picar4wd_driver picar_bringup.launch.py