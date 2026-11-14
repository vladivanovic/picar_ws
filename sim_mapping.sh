#!/bin/bash
# Simulation mapping: PiCar in Gazebo + SLAM Toolbox + Wi-Fi overlay + RViz.
#
# This is a convenience wrapper around start_picar_jetson.sh sim.
# (It previously launched an RTAB-Map launch file and RViz config that
# were never in the repo, hid the failures behind /dev/null, and
# reported success anyway. The project uses SLAM Toolbox: it is the
# right tool for a 2D-lidar-only robot, and it is what real mode runs.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/start_picar_jetson.sh" sim
