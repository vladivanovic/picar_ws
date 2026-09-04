#!/bin/bash
# ==============================================================================
# Picar Simulation Mapping Script
# Runs Gazebo simulation with RTAB-Map SLAM and Wi-Fi heat map overlay
# Usage: ./sim_mapping.sh
#
# This script starts ALL needed processes for house floor mapping:
#   1. Gazebo simulation (empty world or TurtleBot3)
#   2. RTAB-Map SLAM node (building the map)
#   3. Wi-Fi RSSI heat map overlay (synthetic signal strengths)
#   4. RViz2 visualization (map + heat map + robot path)
# ==============================================================================

set -e  # Exit on any error

echo ""
echo "================================================================================"
echo "Picar Simulation Mapping - House Floor Plan with Wi-Fi Heat Map"
echo "================================================================================"
echo ""

# ==============================================================================
# STEP 1: Verify Environment
# ==============================================================================
echo "[1/6] Verifying ROS 2 environment..."

if [ -z "$ROS_DOMAIN_ID" ]; then
    echo "   Setting ROS_DOMAIN_ID=42 (default for Picar)"
    export ROS_DOMAIN_ID=42
fi

# Source ROS 2
source /opt/ros/jazzy/setup.bash 2>/dev/null || \
source /opt/ros/humble/setup.bash 2>/dev/null || \
echo "   WARNING: Could not auto-detect ROS 2 installation"

# Source Picar workspace
source /home/vlad/picar_ws/install/setup.bash 2>/dev/null || \
source /home/vlad/picar_ws/install/local_setup.bash 2>/dev/null || \
echo "   WARNING: Could not source Picar workspace"

echo "   ROS 2 Domain: $ROS_DOMAIN_ID"
echo "   ✅ Environment ready"
echo ""

# ==============================================================================
# STEP 2: Launch Gazebo Simulation
# ==============================================================================
echo "[2/6] Launching Gazebo simulation..."

# Launch the simulation-only launch file
ros2 launch agenticros_bringup gazebo_sim_only.launch.py > /dev/null 2>&1 &

GAZEO_PID=$!
echo "   Gazebo started (PID: $GAZEO_PID)"
echo "   Waiting 8 seconds for Gazebo to initialize..."
sleep 8

# Verify Gazebo is running
if kill -0 $GAZEO_PID 2>/dev/null; then
    echo "   ✅ Gazebo simulation running"
else
    echo "   ❌ Gazebo failed to start - checking..."
    wait $GAZEO_PID 2>/dev/null
    echo "   Moving on anyway..."
fi
echo ""

# ==============================================================================
# STEP 3: Launch RTAB-Map SLAM
# ==============================================================================
echo "[3/6] Starting RTAB-Map SLAM for mapping..."

ros2 launch agenticros_bringup rtabmap_house_mapping.launch.py use_sim_time:=true > /dev/null 2>&1 &

RTABMAP_PID=$!
echo "   RTAB-Map started (PID: $RTABMAP_PID)"
echo "   Waiting 5 seconds for SLAM initialization..."
sleep 5

echo "   RTAB-Map is now building the map as you move the robot"
echo "   Use RViz2 to monitor progress"
echo ""

# ==============================================================================
# STEP 4: Launch Wi-Fi Heat Map Overlay
# ==============================================================================
echo "[4/6] Starting Wi-Fi heat map overlay node..."

ros2 run picar4wd_driver wifi_map_overlay_node.py > /dev/null 2>&1 &

WIFI_PID=$!
echo "   Wi-Fi overlay node started (PID: $WIFI_PID)"
echo "   This node generates synthetic RSSI values based on robot position"
echo "   Creates heat map markers in RViz2:"
echo "      • Green = Strong signal"
echo "      • Yellow = Medium signal"
echo "      • Red = Weak signal"
echo ""

# ==============================================================================
# STEP 5: Launch RViz2
# ==============================================================================
echo "[5/6] Starting RViz2 visualization..."

# Use the RTAB-Map RViz config if it exists, otherwise simulation.rviz
RVIZ_CFG="/home/vlad/picar_ws/src/agenticros_bringup/rviz/rtabmap_house_mapping.rviz"
if [ -f "$RVIZ_CFG" ]; then
    ros2 run rviz2 rviz2 -d "$RVIZ_CFG" > /dev/null 2>&1 &
    RVIZ_PID=$!
    echo "   Using RTAB-Map RViz config: $RVIZ_CFG"
else
    RVIZ_CFG="/home/vlad/picar_ws/src/agenticros_bringup/rviz/simulation.rviz"
    if [ -f "$RVIZ_CFG" ]; then
        ros2 run rviz2 rviz2 -d "$RVIZ_CFG" > /dev/null 2>&1 &
        RVIZ_PID=$!
        echo "   Using simulation RViz config: $RVIZ_CFG"
    else
        ros2 run rviz2 rviz2 > /dev/null 2>&1 &
        RVIZ_PID=$!
        echo "   Starting bare RViz2 (no pre-configured layout)"
    fi
fi

echo "   RViz2 started (PID: $RVIZ_PID)"
echo "   The following displays should appear:"
echo "      • /map - RTAB-Map occupancy grid"
echo "      • /robot_model - Your Picar robot"
echo "      • /wifi/heatmap_markers - Wi-Fi signal spheres"
echo "      • /wifi_heatmap_trail - Path with signal trend"
echo "      • /scan - LiDAR data"
echo "      • /rtabmap/path - Robot trajectory"
echo ""

# ==============================================================================
# STEP 6: Summary & Instructions
# ==============================================================================
echo "[6/6] Setup complete! All processes running."
echo ""
echo "================================================================================"
echo "SIMULATION MAPPING ACTIVE"
echo "================================================================================"
echo ""
echo "   Running processes:"
echo "      • Gazebo simulation    (PID: $GAZEO_PID)"
echo "      • RTAB-Map SLAM        (PID: $RTABMAP_PID)"
echo "      • Wi-Fi overlay        (PID: $WIFI_PID)"
echo "      • RViz2 visualization  (PID: $RVIZ_PID)"
echo ""
echo "================================================================================"
echo "MAPPING INSTRUCTIONS:"
echo "================================================================================"
echo ""
echo "   1. Robot control (in NEW terminal):"
echo "      ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5, y: 0.0}, angular: {z: 0.0}}' -r 10"
echo ""
echo "   2. Move robot to map the house:"
echo "      • Start at the entrance/hallway"
echo "      • Move into each room, covering all areas"
echo "      • Go down hallways and connect rooms"
echo "      • Make multiple passes for better coverage"
echo "      • Tip: Move slowly for better SLAM accuracy"
echo ""
echo "   3. Monitor progress in RViz2:"
echo "      • Watch the /map occupancy grid build in real-time"
echo "      • See Wi-Fi heat map spheres appear:"
echo "          - Green as you get near 'router' positions"
echo "          - Yellow in mid-house rooms"
echo "          - Red in far rooms/corners (dead zones)"
echo "      • Follow the trail line showing your path"
echo ""
echo "   4. Loop closure help:"
echo "      • RTAB-Map automatically detects when you revisit areas"
echo "      • Try to pass through the same hallways/doors again"
echo "      • This helps correct the map accuracy"
echo ""
echo "   5. Save the map when finished:"
echo "      • In RViz2, open rtabmap_viz (bottom panel or Tools menu)"
echo "      • Go to File → Save Map"
echo "      • Name it: my_house_floor_plan"
echo "      • Choose location: /home/vlad/picar_ws/maps/"
echo ""
echo "   6. When done, stop all processes:"
echo "      kill $GAZEO_PID $RTABMAP_PID $WIFI_PID $RVIZ_PID"
echo ""
echo "================================================================================"
echo "QUICK TROUBLESHOOTING:"
echo "================================================================================"
echo ""
echo "   • If /scan not appearing: Ensure Gazebo LiDAR is publishing"
echo "   • If no Wi-Fi markers: Check wifi_map_overlay_node is running"
echo "   • If RViz2 empty: Verify rviz config file exists"
echo "   • If mapping stalls: Move robot more, ensure coverage of all rooms"
echo "   • If map has gaps: Ensure you visit all areas including corners"
echo ""
echo "================================================================================"
echo "PRESS CTRL+C TO STOP ALL PROCESSES AND EXIT"
echo "================================================================================"

# Wait for user to press Ctrl+C
echo ""
echo "Waiting... (Press Ctrl+C to stop all processes and exit)"

# Set up trap to kill all child processes on exit
trap 'echo ""; echo "Stopping all processes..."; kill $GAZEO_PID $RTABMAP_PID $WIFI_PID $RVIZ_PID 2>/dev/null; echo "All processes stopped."; exit 0' INT TERM

# Keep script running until Ctrl+C
while true; do
    sleep 1
    # Check if any major process died
    if ! kill -0 $GAZEO_PID 2>/dev/null; then
        echo ""
        echo "⚠️  Gazebo simulation ended unexpectedly"
        break
    fi
done