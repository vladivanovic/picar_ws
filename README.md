# Picar Robot Car Project

## Overview
A distributed robotics system where the **NVIDIA AGX Orin** acts as the primary Control Unit and the **Raspberry Pi** handles the hardware drivers (Motors, LiDAR).

## Architecture
- **Control Unit (AGX Orin):** Runs high-level logic, RViz2 monitoring, SLAM/Odometry, and now Wi-Fi heat map mapping
- **Hardware Unit (Raspberry Pi):** Runs motor drivers, LiDAR, and now Wi-Fi RSSI signal tracking

## 🆕 New: Simulation & Wi-Fi Mapping Modes

The project now supports two primary modes:

### **Mode: `sim` (Simulation with Gazebo + SLAM + Wi-Fi Heat Map)**
Use this for house floor plan mapping WITHOUT real hardware.
- Launches Gazebo simulation
- Builds map with RTAB-Map SLAM
- Generates Wi-Fi heat map overlay (synthetic signal strengths)
- Visualizes in RViz2 with colored spheres (Green=Strong, Yellow=Medium, Red=Weak)

**Usage:**
```bash
# From picar_ws root
./sim_mapping.sh
# Then control robot:
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5, y: 0.0}, angular: {z: 0.0}}' -r 10
```

### **Mode: `real` (Full Robot with Hardware)**
Use this for actual robot operation with real Wi-Fi tracking.

**On Raspberry Pi:**
```bash
./start_picar_pi.sh real
```

**On AGX Orin:**
```bash
./start_picar_jetson.sh real
```

### **Mode: `real sim` (Combined)**
You can also run real robot and simulation in parallel, or switch between them using the shell scripts.

## 📦 Shell Scripts

| Script | Purpose |
|--------|---------|
| `start_picar_jetson.sh` | AGX Orin startup with `real` or `sim` modes |
| `start_picar_pi.sh` | Raspberry Pi startup with `real` or `sim` modes |
| `sim_mapping.sh` | Complete simulation mapping pipeline (Gazebo + RTAB-Map + Wi-Fi heat map) |

## 📦 Deployment Instructions

### Robot Car (Raspberry Pi)
```bash
cd /home/vlad/picar_ws
git pull origin main
colcon build --symlink-install
source install/setup.bash

# Real mode: Launch hardware drivers
ros2 launch picar4wd_driver picar_bringup.launch.py

# Simulation mode: Use ./start_picar_pi.sh sim
# OR: ./sim_mapping.sh for full mapping pipeline
```

### Control Unit (AGX Orin)
```bash
cd /home/vlad/picar_ws
git pull origin main
colcon build --symlink-install
source install/setup.bash

# Real mode: Start full robot stack
./start_picar_jetson.sh real

# Simulation mode: Use ./start_picar_jetson.sh sim
# OR: Use ./sim_mapping.sh for mapping pipeline
```

## 🗺️ House Mapping with Wi-Fi Heat Map

When using `./sim_mapping.sh` or the simulation modes:

1. **Start the mapping pipeline** - launches Gazebo, RTAB-Map, Wi-Fi overlay, RViz2
2. **Control the robot** in a NEW terminal:
   ```bash
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5, y: 0.0}, angular: {z: 0.0}}' -r 10
   ```
3. **Move robot around the house**:
   - Start at entrance/hallway
   - Move into each room, covering all areas
   - Go down hallways and connect rooms
   - Make multiple passes for better coverage
   - Move slowly for better SLAM accuracy
4. **Monitor progress in RViz2**:
   - Watch the `/map` occupancy grid build in real-time
   - See Wi-Fi heat map spheres appear:
     - **Green** = Strong signal (near "router" positions)
     - **Yellow** = Medium signal (mid-house rooms)
     - **Red** = Weak signal (far rooms/corners = dead zones)
   - Follow the trail line showing your path
5. **Help loop closure** by passing through same hallways/doors again
6. **Save the map** when finished:
   - In RViz2, open rtabmap_viz
   - File → Save Map
   - Name: `my_house_floor_plan`
   - Location: `/home/vlad/picar_ws/maps/`

## 🛠️ Troubleshooting

- **Network:** Ensure both units are on the same subnet and can ping each other
- **Namespace:** If commands aren't reaching the motors, verify the bridge is relaying to `/picar_pi/cmd_vel`
- **Gazebo not starting:** Check `./sim_mapping.sh` output for errors
- **No Wi-Fi markers in RViz2:** Verify `wifi_map_overlay_node` is running
- **Map has gaps:** Ensure you visit all areas including corners and hallways
- **RTAB-Map not building:** Move robot more, ensure coverage of all rooms

## 📁 Key Files Created

| File | Purpose |
|------|---------|
| `sim_mapping.sh` | Complete simulation mapping pipeline |
| `start_picar_jetson.sh` | AGX Orin startup (real/sim modes) |
| `start_picar_pi.sh` | Raspberry Pi startup (real/sim modes) |
| `wifi_rssi_node.py` | Pi: Tracks connected SSID RSSI |
| `wifi_map_overlay_node.py` | Orin: Publishes Wi-Fi heat map markers |
| `nav2_params.yaml` | Nav2 navigation parameters |
| `rtabmap_house_mapping.launch.py` | RTAB-Map SLAM launch |
| `simulation.rviz` | RViz2 config for simulation |
| `rtabmap_house_mapping.rviz` | RViz2 config for RTAB-Map |

## 📬 Need Help?

Check the `docs/` directory for detailed guides, or refer to the specific script's help:
```bash
# Example: ./sim_mapping.sh will show usage if needed
# Or check individual files for configuration details
```

---
*Last updated: 2026-09-04*
*Model: nvidia/nemotron-3.5-lightning-30b-a3b*
*Platform: discord*