#!/bin/bash
# AGX Orin (control unit) startup.
# Usage: ./start_picar_jetson.sh [real|sim]
#
#   real - SLAM Toolbox + cmd_vel relay + Wi-Fi heat-map overlay + RViz
#          against the real car. Odometry runs ON THE PI (the odometry
#          node moved there -- it integrates the command stream the
#          motors actually receive, and publishes odom -> base_link).
#   sim  - PiCar in Gazebo + SLAM Toolbox (sim time) + overlay + RViz.
#
# Workspace path is derived from this script's location -- an earlier
# version hardcoded an ~/.openclaw/workspace path that only existed on
# one machine.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
MODE="${1:-real}"

source /opt/ros/jazzy/setup.bash
if [ ! -f "$SCRIPT_DIR/install/setup.bash" ]; then
    echo "Workspace not built. Run: colcon build --symlink-install" >&2
    exit 1
fi
source "$SCRIPT_DIR/install/setup.bash"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

SLAM_PARAMS="$(ros2 pkg prefix picar4wd_driver)/share/picar4wd_driver/config/slam_toolbox.yaml"

PIDS=()
cleanup() {
    echo "Stopping..."
    for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
}
trap cleanup INT TERM EXIT

if [ "$MODE" = "real" ]; then
    echo "=== PiCar Orin startup: REAL (domain $ROS_DOMAIN_ID) ==="

    # No cmd_vel relay in the standard setup: teleop/Nav2 publish
    # /cmd_vel here, the Pi's motor driver subscribes /cmd_vel, and DDS
    # connects them directly on the shared domain. The relay
    # (agenticros_bringup cmd_vel_bridge.launch.py) only matters when a
    # namespaced source -- e.g. AgenticROS publishing /<ns>/cmd_vel --
    # needs forwarding to /cmd_vel; launch it separately in that case.
    echo "[1/4] (no cmd_vel relay needed -- DDS connects /cmd_vel directly)"

    echo "[2/4] SLAM Toolbox (params: $SLAM_PARAMS)"
    ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
        --params-file "$SLAM_PARAMS" -p use_sim_time:=false &
    PIDS+=($!)
    sleep 3
    ros2 lifecycle set /slam_toolbox configure || true
    ros2 lifecycle set /slam_toolbox activate || true

    echo "[3/4] Wi-Fi heat-map overlay (positions from /odom)"
    ros2 run picar4wd_driver wifi_map_overlay_node &
    PIDS+=($!)

    echo "[4/4] RViz (foreground; close it or Ctrl+C to stop everything)"
    RVIZ_CFG="$SCRIPT_DIR/src/agenticros_sim/config/picar_view.rviz"
    if [ -f "$RVIZ_CFG" ]; then
        ros2 run rviz2 rviz2 -d "$RVIZ_CFG"
    else
        ros2 run rviz2 rviz2
    fi

elif [ "$MODE" = "sim" ]; then
    echo "=== PiCar Orin startup: SIMULATION (domain $ROS_DOMAIN_ID) ==="

    echo "[1/3] PiCar in Gazebo (with its RViz)"
    ros2 launch agenticros_sim sim_picar.launch.py use_rviz:=true &
    PIDS+=($!)
    sleep 8

    echo "[2/3] SLAM Toolbox (sim time)"
    ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
        --params-file "$SLAM_PARAMS" -p use_sim_time:=true &
    PIDS+=($!)
    sleep 3
    ros2 lifecycle set /slam_toolbox configure || true
    ros2 lifecycle set /slam_toolbox activate || true

    echo "[3/3] Wi-Fi heat-map overlay"
    ros2 run picar4wd_driver wifi_map_overlay_node --ros-args -p use_sim_time:=true &
    PIDS+=($!)

    echo "Running. Drive with teleop or /cmd_vel publishes. Ctrl+C stops all."
    wait
else
    echo "ERROR: Unknown mode '$MODE'. Use 'real' or 'sim'." >&2
    exit 1
fi
