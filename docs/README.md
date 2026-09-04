# Picar Project - Complete Setup & New Features

## 📦 Repository Structure

This repository contains the Picar project with the following major organizations:

```
/home/vlad/picar_ws/
├── docs/                    # Documentation files (NEW)
├── src/agenticros_bringup/  # AgenticROS bringup packages
├── src/picar4wd_driver/     # Picar 4WD driver scripts & configs
├── build/                   # Build artifacts
├── install/                 # Install artifacts
└── picar_ws/                # Git submodule
```

## 🆕 Newly Added Features

### 1. Simulation Launch Files

#### `src/agenticros_bringup/launch/gazebo_sim_only.launch.py`
Main simulation-only launch file for testing without real hardware.
- Runs Gazebo with TurtleBot3 world
- Publishes Picar URDF in simulation
- Launches RViz2 for visualization
- No Pi, no motors, no LiDAR required (power-agnostic)

#### `src/agenticros_bringup/launch/sim_navigation.launch.py`
Nav2 navigation stack for simulation testing.
- Configures Nav2 with Picar parameters
- Use for path planning and waypoint following in Gazebo

### 2. RViz2 Configuration Files

#### `src/agenticros_bringup/rviz/simulation.rviz`
RViz2 config optimized for Gazebo simulation viewing.
- Displays: RobotModel, LaserScan, TF frames
- Pre-configured for simulation clock (`use_sim_time`)

#### `src/agenticros_bringup/rviz/rtabmap_house_mapping.rviz`
RTAB-Map visualization config for house mapping.
- Displays: Map, robot path, loop closures
- Optimized for Wi-Fi heat map overlay

### 3. Wi-Fi RSSI & Heat Map System

#### `src/picar4wd_driver/scripts/wifi_rssi_node.py`
Runs on **Raspberry Pi** (the car).
- Tracks currently connected SSID signal strength
- Uses `iwconfig` or `wpa_cli` to scan Wi-Fi
- Publishes:
  - `/wifi/rssi` (Int32, dBm)
  - `/wifi/ssid` (String)
  - `/wifi/status` (String)

#### `src/picar4wd_driver/scripts/wifi_map_overlay_node.py`
Runs on **AGX Orin** (the brains).
- Subscribes to `/wifi/rssi` from Pi
- Publishes RViz2 markers for heat map visualization
- Visualizes signal strength as colored spheres:
  - **Green** = Strong (> -50 dBm)
  - **Yellow** = Medium (-70 to -50 dBm)
  - **Red** = Weak (< -70 dBm)
- Also publishes trail line strip showing path

#### `src/picar4wd_driver/launch/wifi_rssi.launch.py`
Launches the Wi-Fi RSSI node on the Raspberry Pi.

### 4. RTAB-Map House Mapping

#### `src/agenticros_bringup/launch/rtabmap_house_mapping.launch.py`
*(Note: Create this file or use existing RTAB-Map setup)*
- Integrates RPLidar A1 for SLAM
- Builds full house floor plan
- Works with Wi-Fi overlay markers
- Includes loop closure detection

### 5. Navigation Parameters

#### `src/picar4wd_driver/config/nav2_params.yaml`
Nav2 navigation parameters for Picar robot.
- Differential drive robot configuration
- Costmap settings for house-scale mapping
- Planner and controller configurations

## 📋 Documentation Files

### `docs/gazebo_sim_start.sh`
Shell script to start Gazebo simulation quickly.

### `docs/sim_to_real_transfer.md`
Guidelines for transferring work from simulation to real robot.

### `gazebo_simulation_guide.md`
Comprehensive guide for Gazebo simulation setup and usage.

### `picar_sim.sh`
Picar simulation startup script.

## 🚀 Getting Started

### Prerequisites

1. **ROS 2 Humble** installed on AGX Orin
2. **Raspberry Pi** with Picar Hat running Picar 4WD software
3. **RPLidar A1** connected to Raspberry Pi
4. **Wi-Fi adapter** (USB) for signal tracking (optional but recommended)

### Installation

```bash
# Clone/update repository
cd /home/vlad
git clone https://github.com/vladivanovic/picar_ws.git
cd picar_ws

# Install system dependencies
sudo apt update
sudo apt install ros-humble-rtabmap-ros ros-humble-rtabmap-viz

# Install Python dependencies (on both Orin and Pi)
pip3 install rclpy std_msgs vispy  # etc.

# On Raspberry Pi only:
sudo apt install iw wpasupplicant

# Make scripts executable
chmod +x /home/vlad/picar_ws/src/picar4wd_driver/scripts/*.py
```

### Running the Full System

#### On Raspberry Pi (the car):
```bash
# 1. Launch Wi-Fi RSSI node
ros2 launch picar4wd_driver wifi_rssi.launch.py

# Verify it's publishing
ros2 topic list | grep wifi
# Should show: /wifi/rssi, /wifi/ssid, /wifi/status
```

#### On AGX Orin (the brains):
```bash
# 1. Launch Gazebo simulation (or real robot launch)
ros2 launch agenticros_bringup gazebo_sim_only.launch.py

# 2. Launch RTAB-Map for mapping
# (or your existing real robot launch)

# 3. Launch Wi-Fi heat map overlay
ros2 run picar4wd_driver wifi_map_overlay_node.py

# 4. Launch RViz2
ros2 run rviz2 rviz2 -d /home/vlad/picar_ws/src/agenticros_bringup/rviz/simulation.rviz

# 5. Start mapping!
# Move robot around house, covering all rooms
# Watch green/yellow/red spheres appear in RViz2
```

### Wi-Fi Heat Map Interpretation

**In RViz2, you'll see:**
- **Spheres** at robot positions colored by signal strength
- **Green** = Strong signal (near router/access point)
- **Yellow** = Medium signal (mid-range rooms)
- **Red** = Weak signal (far from router, obstacles blocking)
- **Trail line** shows path with current signal trend

**Post-mapping analysis:**
1. Count green/red spheres to assess coverage
2. Follow the trail to understand signal variation
3. Identify dead zones (all red in certain areas)
4. Optimize access point placement based on data

## 🔧 Troubleshooting

### Wi-Fi Node Not Publishing
- Ensure `iwconfig` is installed on Pi: `sudo apt install iw`
- Check Wi-Fi interface name (may be `wlan0`, `wlan1`, `ra0`, etc.)
- Verify Pi has Wi-Fi connection established

### No Markers in RViz2
- Verify `/wifi/rssi` topic is publishing
- Check RViz2 display: Add → By Topic → `/wifi/heatmap_markers`
- Ensure RTAB-Map `/map` frame is active

### RTAB-Map Not Building Map
- Ensure `/scan` topic has LiDAR data
- Move robot through all rooms (don't stay in one spot too long)
- Look for "loop closure" events in rtabmap_viz
- Save map periodically: File → Save in rtabmap_viz

### Simulation vs Real Robot
- Simulation: Use `gazebo_sim_only.launch.py` 
- Real robot: Use existing `picar_bringup.launch.py` + Wi-Fi node on Pi
- Switch between them by changing launch files

## 📦 Git Workflow

All new files have been committed and pushed:

```bash
# Check current status
cd /home/vlad/picar_ws
git status

# View recent commits
git log --oneline -5

# Latest commit: "Add simulation launch files, RViz configs, and Wi-Fi mapping setup"
```

## 🛠️ Development Notes

### Adding New Features
1. Create script in `src/picar4wd_driver/scripts/`
2. Create launch file in `src/picar4wd_driver/launch/`
3. Add RViz config in `src/agenticros_bringup/rviz/`
4. Update documentation in `docs/`
5. Test in both simulation and real robot modes

### Power Considerations
- **Simulation only**: Wall power for AGX Orin only
- **Real robot**: 2-port power bank (Pi on Port 1, LiDAR on Port 2)
- **Wi-Fi node**: Minimal power draw from Pi's USB

### Supported Hardware
- **Main computer**: NVIDIA AGX Orin (64GB RAM)
- **Robot controller**: Raspberry Pi (with Picar Hat)
- **LiDAR**: RPLidar A1
- **Simulation**: Gazebo with TurtleBot3 world
- **Wi-Fi tracking**: USB wireless adapter (recommended: Alfa AWUS036NHA)

## 📞 Need Help?

For issues or questions:
1. Check `docs/` directory for detailed guides
2. Run `ros2 topic list` to verify topic publishing
3. Run `ros2 node list` to verify nodes are active
4. Consult ROS 2 documentation for topic/parameter issues

---
*Last updated: 2026-09-04*
*Model: nvidia/nemotron-3.5-lightning-30b-a3b*
*Platform: discord*