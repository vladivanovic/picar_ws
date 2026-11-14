#!/bin/bash
# PiCar teleop helper: keyboard driving on /cmd_vel.
# The Pi bringup uses NO namespace, so teleop publishes straight to
# /cmd_vel -- the same topic the motor driver subscribes to.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source /opt/ros/jazzy/setup.bash
if [ -f "$WS_ROOT/install/setup.bash" ]; then
    source "$WS_ROOT/install/setup.bash"
fi
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

echo "Starting PiCar teleop on /cmd_vel (domain $ROS_DOMAIN_ID)"
echo "Keys: i/j/k/l/u/o/m/,/. to move, k to stop."
echo "Note: the motor driver stops the car 0.5s after the last command,"
echo "so closing this terminal is also a stop."

ros2 run teleop_twist_keyboard teleop_twist_keyboard
