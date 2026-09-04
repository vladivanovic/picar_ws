#!/bin/bash
# Raspberry Pi (Jazzy) startup script
# Updated: Now includes Wi-Fi RSSI tracking alongside robot bringup
# Usage: ./start_picar_pi.sh [real|sim]
#
# Modes:
#   real  - Full robot with LiDAR, motors, Wi-Fi RSSI tracking
#   sim   - Wi-Fi signal simulation for Gazebo mapping

source /opt/ros/jazzy/setup.bash
source ~/picar_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd

# ============================================
# PARSE ARGUMENTS
# ============================================
MODE="${1:-real}"  # Default to real mode

echo "============================================"
echo "Picar Pi Startup - Mode: $MODE"
echo "============================================"

# GPIO and serial port permissions (required on the Pi)
echo "[1/5] Setting GPIO/serial permissions..."
sudo chmod 666 /dev/mem
sudo chmod 666 /dev/gpiomem
sudo chmod 666 /dev/ttyUSB0

# ============================================
# REAL MODE: Full robot with Wi-Fi tracking
# ============================================
if [ "$MODE" = "real" ]; then
    echo ""
    echo "[REAL MODE] Starting robot bringup with Wi-Fi RSSI tracking..."
    
    # 1. Launch complete bringup (LiDAR, odometry, motor driver)
    echo "[2/5] Starting Picar bringup (LiDAR, odometry, motors)..."
    ros2 launch picar4wd_driver picar_bringup.launch.py &
    
    # 2. Start Wi-Fi RSSI node
    echo "[3/5] Starting Wi-Fi RSSI node..."
    ros2 run picar4wd_driver wifi_rssi_node.py &
    
    # Verify Wi-Fi node is publishing
    sleep 3
    echo "[4/5] Verifying Wi-Fi topics..."
    ros2 topic list | grep -E "/wifi/"
    
    # 5. Completion
    echo "[5/5] Real mode setup complete!"
    echo ""
    echo "✅ Robot: Enabled (motors, LiDAR, hardware)"
    echo "   Wi-Fi:   Tracking connected SSID RSSI"
    echo "   Topics:  /wifi/rssi, /wifi/ssid, /wifi/status"
    echo "   Control: Use /cmd_vel for motor control"
    echo ""

# ============================================
# SIMULATION MODE: Wi-Fi signal simulation for Gazebo
# ============================================
elif [ "$MODE" = "sim" ]; then
    echo ""
    echo "[SIMULATION MODE] Starting Wi-Fi signal simulation for Gazebo mapping..."
    
    echo "[1/3] Starting Wi-Fi map overlay node (simulated RSSI)..."
    ros2 run picar4wd_driver wifi_map_overlay_node.py &
    WIFI_PID=$!
    sleep 3
    
    echo "[2/3] Wi-Fi overlay ready - generating synthetic signal strengths..."
    echo "   - Will create heat map markers in RViz2"
    echo "   - Green=strong, Yellow=medium, Red=weak signal"
    echo "   - Markers follow robot path in Gazebo simulation"
    
    echo "[3/3] Simulation mode Wi-Fi ready!"
    echo ""
    echo "   To use with Gazebo simulation:"
    echo "     ros2 launch agenticros_bringup gazebo_sim_only.launch.py"
    echo "     # Then in separate terminal:"
    echo "     ros2 run picar4wd_driver wifi_map_overlay_node.py"
    echo "     ros2 run rviz2 rviz2 -d $HOME/picar_ws/src/agenticros_bringup/rviz/simulation.rviz"
    echo ""
    echo "   The Wi-Fi node will generate synthetic RSSI values based on"
    echo "   robot position, creating a heat map as you move the robot."
    echo ""

else
    echo "ERROR: Unknown mode '$MODE'. Use 'real' or 'sim'."
    exit 1
fi