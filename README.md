# PiCar-4WD ROS2 Project

A distributed ROS2 robotics project using a Sunfounder PiCar-4WD (Raspberry Pi 3B) and an Nvidia Jetson Orin Nano for autonomous navigation and mapping.

## Architecture


┌─────────────────────────┐ WiFi (ROS2 DDS) ┌─────────────────────────┐
│ Jetson Orin Nano │◄────────────────────────────►│ Raspberry Pi 3B │
│ (Ubuntu 22.04) │ │ (Ubuntu 24.04) │
│ ROS2 Humble │ │ ROS2 Jazzy │
│ │ │ │
│ - Nav2 (path planning) │ /cmd_vel ────────────────► │ - Motor driver node │
│ - SLAM Toolbox │ ◄──────────── /scan │ - Sonar scanner node │
│ - RViz2 (visualization)│ ◄──────────── /odom │ - Odometry node │
│ - Teleop / Autonomy │ ◄──────────── /tf │ - Static TF publisher │
└─────────────────────────┘ └─────────────────────────┘

## Hardware

- **Raspberry Pi 3B** with Sunfounder PiCar-4WD hat
- **Nvidia Jetson Orin Nano Super** (8GB)
- **Sensors**: Ultrasonic sonar (servo-mounted, sweeping), RPLiDAR A1-M8 (pending)
- **Power**: 2x TR18650 3.7V 3000mAh batteries (hat/motors), USB 5V/2.5A+ (Pi)

## Prerequisites

### Raspberry Pi 3B

- Ubuntu Server 24.04 LTS (64-bit, arm64)
- ROS2 Jazzy (ros-base)
- Sunfounder picar-4wd Python library
- I2C enabled

### Jetson Orin Nano

- JetPack 6.x (Ubuntu 22.04)
- ROS2 Humble (desktop)
- Nav2, SLAM Toolbox

## Installation

### Raspberry Pi Setup

#### 1. Install ROS2 Jazzy

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-jazzy-ros-base ros-dev-tools

# add to bashrc

echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "source ~/picar_ws/install/setup.bash" >> ~/.bashrc
echo "export PYTHONPATH=\$PYTHONPATH:/home/ubuntu/picar-4wd" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source ~/.bashrc

# install sunfounder library

cd ~
git clone https://github.com/sunfounder/picar-4wd.git
cd picar-4wd

# remove root check and pip library installation then run manually

pip install gpiozero smbus2 websockets
sudo apt install python3-smbus

# verify python path

python3 -c "import picar_4wd as fc; print('Library loaded OK')"

# ensure i2c is enabled

sudo nano /boot/firmware/config.txt
# Add: dtparam=i2c_arm=on

sudo modprobe i2c-dev
echo "i2c-dev" | sudo tee /etc/modules-load.d/i2c.conf
sudo apt install -y i2c-tools
sudo reboot

# then verify

sudo i2cdetect -y 1

# setup GPIO permissions

sudo groupadd gpio
sudo groupadd spi
sudo usermod -aG gpio,i2c,spi ubuntu
sudo chmod 666 /dev/mem
sudo chmod 666 /dev/gpiomem

cat << 'UDEV' | sudo tee /etc/udev/rules.d/99-gpio.rules
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0666"
SUBSYSTEM=="mem", KERNEL=="mem", GROUP="gpio", MODE="0666"
SUBSYSTEM=="mem", KERNEL=="gpiomem", GROUP="gpio", MODE="0666"
UDEV

sudo udevadm control --reload-rules
sudo udevadm trigger

# log out and back in, create a swap file if needed

sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# build ros2 package

cd ~/picar_ws
colcon build
source install/setup.bash

# jetson nano setup

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox ros-humble-teleop-twist-keyboard

# add to bash

echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source ~/.bashrc

# now quick start the picar

~/start_picar.sh

# start teleop on jetson

~/start_picar.sh

# then drive

u    i    o        i = forward
j    k    l        , = backward
m    ,    .        j = turn left
                   l = turn right
                   k = stop
                   z/x = decrease/increase speed

# Terminal 1: Start SLAM
ros2 launch slam_toolbox online_async_launch.py

# Terminal 2: Visualize
rviz2

# Terminal 3: Drive with teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Launch Nav2 with saved map
ros2 launch nav2_bringup navigation_launch.py map:=./my_map.yaml



ROS2 Topics

Topic	Type	Source	Description
/cmd_vel	geometry_msgs/Twist	Jetson	Velocity commands
/scan	sensor_msgs/LaserScan	Pi	Sonar sweep data
/odom	nav_msgs/Odometry	Pi	Dead-reckoning odometry
/tf	tf2_msgs/TFMessage	Pi	Transform tree

Network Configuration

Both machines must be on the same WiFi network with matching ROS_DOMAIN_ID.


If multicast issues occur, use Cyclone DDS:
sudo apt install ros-<distro>-rmw-cyclonedds-cpp
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

Known Limitations

Sonar: 1Hz scan rate, 120° FOV, sparse data. SLAM works but produces low-resolution maps.
Odometry: Dead-reckoning only (no wheel encoders). Drifts over time. SLAM scan-matching partially compensates.
Power: Pi 3B requires dedicated 5V/2.5A+ supply. USB ports from laptops are insufficient.

Roadmap

Motor control via ROS2
Sonar scanning via ROS2
Odometry estimation
Cross-machine communication (Jazzy ↔ Humble)
SLAM mapping with sonar
RPLiDAR A1-M8 integration
Nav2 autonomous navigation
Camera integration (visual odometry)
Autonomous exploration

Troubleshooting

Problem	Solution
ros2: command not found	Source ROS2: source /opt/ros/<distro>/setup.bash
GPIO permission denied	Check udev rules and group membership, logout/login
I2C IOError	Ensure PiCar hat battery switch is ON
SSH key mismatch after reflash	ssh-keygen -R <ip_address>
Undervoltage warnings	Use dedicated 5V/2.5A+ wall adapter, short thick cable
Cross-machine topics not visible	Check ROS_DOMAIN_ID matches on both machines
