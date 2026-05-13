#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/picar_ws/install/setup.bash
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd
export ROS_DOMAIN_ID=42

tmux new-session -d -s picar
tmux send-keys -t picar "ros2 run picar4wd_driver motor_driver_node" Enter
tmux split-window -h -t picar
tmux send-keys -t picar "ros2 run picar4wd_driver sonar_node" Enter
tmux split-window -v -t picar
tmux send-keys -t picar "ros2 run picar4wd_driver odom_node" Enter
tmux attach -t picar
