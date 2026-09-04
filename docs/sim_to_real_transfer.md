# Picar Gazebo → Real Simulation-to-Real Transfer

## Overview
Picar simulation uses identical topic names as the real hardware bridge, allowing direct transfer of policies without code changes.

## Topic Mapping (Sim ↔ Real)

| Topic | Type | Direction | Sim Source | Real Source |
|-------|------|-----------|------------|-------------|
| `/cmd_vel` | `geometry_msgs/Twist` | ROS → GZ | gz-diff-drive plugin | RealSense drivers |
| `/odom` | `nav_msgs/Odometry` | GZ → ROS | gz-odometry plugin | EKF fusion |
| `/scan` | `sensor_msgs/LaserScan` | GZ → ROS | laser sensor | RealSense D435 lidar |
| `/camera/camera/color/image_raw` | `sensor_msgs/Image` | GZ → ROS | rgbd_camera | RealSense D435 RGB |
| `/camera/camera/depth/image_rect_raw` | `sensor_msgs/Image` | GZ → ROS | rgbd_camera | RealSense D435 depth (16UC1/mm) |
| `/camera/camera/depth/points` | `sensor_msgs/PointCloud2` | GZ → ROS | rgbd_camera | PCL conversion |
| `/imu/data` | `sensor_msgs/Imu` | GZ → ROS | IMU plugin | RealSense IMU |
| `/tf` | `tf2_msgs/TFMessage` | GZ → ROS | transform bridge | Robot state publisher |
| `/tf_static` | `tf2_msgs/TFMessage` | GZ → ROS | static TF bridge | /base_link → /camera transforms |
| `/clock` | `rosgraph_msgs/Clock` | GZ → ROS | simulation clock | Hardware clock |

## Simulation-Ready Topics for Testing

- **Odometry estimation**: `/odom` matches real EKF output
- **SLAM navigation**: Test gmapping/RTAB-Map on simulated LiDAR
- **Object detection**: Simulated depth camera identical to real D435
- **Collision avoidance**: Test Obstacle avoidance algorithm on obstacles in indoor world

## Transfer Procedure

### 1. Simulate with Real-World Data
```bash
# Run in Gazebo, record episodes
ros2 bag record -a -o bag/episode_$(date +%Y%m%d_%H%M%S)

# Convert to LeRobot format (if applicable)
ros2 bag to_lerobot bag/episode_*.bag --config lerobot_config.json
```

### 2. Fine-Tune with Real Hardware
```bash
# On real robot, teleop to ground-truth environment
ros2 launch picar4wd_driver picar_bringup.launch.py

# Record real episodes for domain randomization
export SO101_RERUN_ENV_DIR=~/ros2_ws/src/agenticros_sim
ros2 bag record -a -o bag/real_$(date +%Y%m%d_%H%M%S)
```

### 3. Validate Similarity
- **LiDAR pointcloud overlap**: 95%+ overlap expected
- **Depth range**: Sim = 0.1–12m, Real = 0.1–10m (same sensor model)
- **IMU noise**: Add Gaussian noise to real hardware to match simulation

## Power Breakout Warning (LiDAR)
The LiDAR power breakout must be completed before real hardware testing. Ensure:
- 5V@5A power supply for RealSense
- Serial port `/dev/ttyUSB0` configured
- Proper ground connection to avoid voltage drops

## ROS2 Workspace Required
```bash
cd $WS_ROOT
colcon build --symlink-install
source install/setup.bash
```

## Quick Start
```bash
# Sim mode
bash docs/gazebo_sim_start.sh

# Real mode
bash start_picar_jetson.sh

# Teleop both sim and real (requires two instances)
ros2 launch agenticros_sim sim_amr.launch.py ...
# Terminal 2: teleop simulation
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.5}, angular: {z: 0.0}}'
```
