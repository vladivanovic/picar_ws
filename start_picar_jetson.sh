#!/bin/bash
# Jetson Orin Nano startup script
# Optimized for both real robot AND simulation modes
# Usage: ./start_picar_jetson.sh [real|sim]
#
# Modes:
#   real  - Full robot with SLAM, navigation, real hardware
#   sim   - Gazebo simulation with SLAM, Wi-Fi heat map overlay

source /opt/ros/jazzy/setup.bash
source ~/.openclaw/workspace/picar_ws/install/setup.bash
export ROS_DOMAIN_ID=42

# ============================================
# PARSE ARGUMENTS
# ============================================
MODE="${1:-real}"  # Default to real mode

echo "============================================"
echo "Picar Jetson Startup - Mode: $MODE"
echo "============================================"

# ============================================
# REAL MODE: Full robot with hardware
# ============================================
if [ "$MODE" = "real" ]; then
    echo ""
    echo "[REAL MODE] Starting full robot stack..."
    
    # 1. Start Discovery Agent
    echo "[1/5] Starting Discovery Agent..."
    ros2 run agenticros_discovery discovery_node --ros-args -p robot_namespace:=control_unit -p robot_id:=orin_master -p has_lidar:=true &
    
    # 2. Start Odometry
    echo "[2/5] Starting Odometry..."
    ros2 run picar4wd_driver odom_node --ros-args -p use_sim_time:=false &
    
    # 3. Start SLAM Toolbox
    echo "[3/5] Starting SLAM Toolbox..."
    ros2 run slam_toolbox async_slam_toolbox_node --ros-args -p use_sim_time:=false -p slam_params_file:=$(ros2 pkg prefix slam_toolbox)/share/slam_toolbox/config/mapper_params_online_async.yaml &
    sleep 5
    ros2 lifecycle set /slam_toolbox configure
    ros2 lifecycle set /slam_toolbox activate
    
    # 4. Start Bridge (Added required src_cmd_vel argument)
    echo "[4/5] Starting CMD Vel Bridge..."
    ros2 launch agenticros_bringup cmd_vel_bridge.launch.py src_cmd_vel:=/cmd_vel &
    
    # 5. Start RViz
    echo "[5/5] Starting RViz..."
    RVIZ_CFG="$HOME/.openclaw/workspace/picar_ws/src/agenticros_bringup/rviz/turtlebot3_agenticros.rviz"
    if [ -f "$RVIZ_CFG" ]; then
        ros2 run rviz2 rviz2 -d "$RVIZ_CFG"
    else
        ros2 run rviz2 rviz2
    fi
    
    echo ""
    echo "✅ Real mode startup complete!"
    echo "   Robot: Enabled (motors, LiDAR, hardware)"
    echo "   SLAM: Active (slam_toolbox)"
    echo "   Navigation: Ready ( Nav2 via cmd_vel_bridge)"
    echo ""

# ============================================
# SIMULATION MODE: Gazebo + SLAM + Wi-Fi Heat Map
# ============================================
elif [ "$MODE" = "sim" ]; then
    echo ""
    echo "[SIMULATION MODE] Starting Gazebo simulation with SLAM and Wi-Fi heat map..."
    
    # 1. Start Gazebo Simulation (separate terminal-friendly)
    echo "[1/5] Starting Gazebo simulation only..."
    ros2 launch agenticros_bringup gazebo_sim_only.launch.py &
    GAZEO_PID=$!
    
    # Wait for Gazebo to initialize
    sleep 8
    
    # 2. Start RTAB-Map for SLAM/Mapping
    echo "[2/5] Starting RTAB-Map SLAM for mapping..."
    ros2 launch agenticros_bringup rtabmap_house_mapping.launch.py use_sim_time:=true &
    RTABMAP_PID=$!
    sleep 5
    
    # 3. Start Wi-Fi RSSI node on Pi (simulated data)
    echo "[3/5] Starting Wi-Fi RSSI overlay node..."
    ros2 run picar4wd_driver wifi_map_overlay_node.py &
    WIFI_PID=$!
    sleep 3
    
    # 4. Start RViz2 with mapping config
    echo "[4/5] Starting RViz2 with mapping configuration..."
    RVIZ_CFG="$HOME/picar_ws/src/agenticros_bringup/rviz/rtabmap_house_mapping.rviz"
    if [ -f "$RVIZ_CFG" ]; then
        ros2 run rviz2 rviz2 -d "$RVIZ_CFG" &
    else
        ros2 run rviz2 rviz2 &
    fi
    RVIZ_PID=$!
    sleep 3
    
    # 5. Summary
    echo "[5/5] Setup complete! All nodes running."
    echo ""
    echo "============================================"
    echo "SIMULATION MODE ACTIVE"
    echo "============================================"
    echo "   Gazebo:     Running (PID: $GAZEO_PID)"
    echo "   RTAB-Map:   Mapping active (PID: $RTABMAP_PID)"
    echo "   Wi-Fi:      Heat map overlay (PID: $WIFI_PID)"
    echo "   RViz2:      Visualization active (PID: $RVIZ_PID)"
    echo ""
    echo "   To stop all processes, run: kill $GAZEO_PID $RTABMAP_PID $WIFI_PID $RVIZ_PID"
    echo ""
    echo "   Robot control (in separate terminal):"
    echo "     ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5, y: 0.0}, angular: {z: 0.0}}' -r 10"
    echo ""
    echo "   Mapping the house:"
    echo "     1. Move robot around all rooms and hallways"
    echo "     2. Watch green/yellow/red spheres appear in RViz2 (Wi-Fi signal)"
    echo "     3. Return to start area for loop closure"
    echo "     4. Save map in rtabmap_viz: File → Save Map"
    echo ""

else
    echo "ERROR: Unknown mode '$MODE'. Use 'real' or 'sim'."
    exit 1
fi