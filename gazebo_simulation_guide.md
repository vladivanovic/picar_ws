# Picar Gazebo Simulation - Quick Start Guide

## Pre-Flight Checklist
- [ ] `agenticros_sim` package installed in `picar_ws`
- [ ] ROS2 Jazzy sourced
- [ ] Gazebo Harmonic compatible with ROS2 Jazzy
- [ ] AgenticROS driver nodes ready for testing

## Step 1: Source Workspace
```bash
cd /home/vlad/.openclaw/workspace/picar_ws
colcon build --symlink-install
source install/setup.bash
```

## Step 2: Start Simulation
```bash
# Headless (no GUI)
ros2 launch agenticros_sim sim_amr.launch.py use_rviz:=false gui:=false

# With RViz visualization
ros2 launch agenticros_sim sim_amr.launch.py use_rviz:=true
```

## Step 3: Control the Robot
```bash
# Subscribe to ROS2 topics
ros2 topic list

# Drive the AMR (diff-drive)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.3}, angular: {z: 0.1}}' --rate 10

# Monitor LiDAR scan
ros2 topic echo /scan

# Monitor depth camera
ros2 topic echo /camera/camera/depth/points
```

## Step 4: Connect to Real Hardware
The simulation topics match the real hardware exactly. When you have the power breakout for LiDAR ready:

```bash
# Real hardware launch
ros2 launch agenticros_bringup cmd_vel_bridge.launch.py

# Simulation still runs with same topics
# Just switch the driver node
```

## Simulation → Real Transfer
See `docs/sim_to_real_transfer.md` for topic mappings and transfer procedures.

## Isaac Sim Cleanup (SO101)
**Not applicable to Picar** - Isaac Sim cleanup was requested for LeRobot/SO101 workspace only.

## Hardware Power Breakout Reminder
Before testing real LiDAR:
1. Identify power requirements (5V@5A for RealSense)
2. Ensure proper voltage regulation
3. Verify ground continuity
4. Test with resistive load before connecting

## Key Topics to Monitor
- `/scan` - LiDAR data (matches real driver)
- `/cmd_vel` - Motion command ( publishes to both sim and real)
- `/odom` - Odometry output (EKF fusion)

## Quick Commands
```bash
# Teleop simulation with keyboard
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}' --rate 20

# Monitor TF tree
ros2 run tf2_tools view_frames.py > ~/tf_frames.dot
cat ~/tf_frames.dot

# Export TF visualization
python3 -c "import rospy; import tf; ..." # custom script
```

## Notes
- Gazebo Harmonic is compatible with ROS2 Jazzy
- Depth camera uses 16UC1 encoding (millimeters) by default
- Add `--ros-args -r /odometry:=/odom` if topic mapping differs
- Real hardware uses same namespace: `/picar_pi`
