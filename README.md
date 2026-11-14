# PiCar Robot Car

A distributed ROS 2 robot: a **Raspberry Pi** on the car runs the hardware
(motors, RPLidar), and an **NVIDIA AGX Orin** runs SLAM, monitoring and
higher-level logic. Both machines talk over Wi-Fi on a shared ROS domain.

> **Status note:** updated 2026-11-14 with the unbreak-real-robot fixes:
> single /cmd_vel scheme, motor watchdog, odometry TF, installed Wi-Fi
> nodes. Wi-Fi heat-mapping is functional but experimental; Nav2 params
> are provided but Nav2 is not launched by the standard scripts yet.

## Hardware

| Part | Notes |
|---|---|
| SunFounder PiCar-4WD | Raspberry Pi + PiCar-4WD HAT |
| RPLidar A1 | Connected to the Pi by USB (serial). **Powered from its own 5 V supply**, separate from the Pi rail — see "LiDAR power" below |
| NVIDIA AGX Orin | Control unit, on the same LAN/subnet as the Pi |
| Network | Both machines on the same Wi-Fi network and subnet |

## Software prerequisites

Both machines:

- Ubuntu 24.04 with **ROS 2 Jazzy**
- This workspace built with colcon (below)

Raspberry Pi only:

- SunFounder's `picar-4wd` Python library installed
  (https://github.com/sunfounder-robotics/picar-4wd)
- `rplidar_ros` (e.g. `ros-jazzy-rplidar-ros`)
- Your user in the `dialout` and `gpio` groups (one-time setup, below)

AGX Orin only:

- `slam_toolbox` (`ros-jazzy-slam-toolbox`)
- `rviz2`

## One-time setup

### Both machines

```bash
cd ~
git clone git@github.com:vladivanovic/Picar_ws.git picar_ws
cd picar_ws
rosdep install --from-paths src --ignore-src -r -y   # installs declared ROS deps
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=42        # must match on both machines; add to ~/.bashrc
```

### Raspberry Pi — serial device and permissions

The lidar is expected at `/dev/rplidar`. Create that stable name once with a
udev rule (this also survives USB port changes and `ttyUSB` numbering swaps):

```bash
# /etc/udev/rules.d/99-rplidar.rules
# SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar", MODE="0660", GROUP="dialout"
sudo cp udev/99-rplidar.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout,gpio $USER   # then log out/in
```

(Verify the vendor/product IDs with `lsusb` — 10c4:ea60 is the CP210x bridge
on the A1's adapter board.) No `chmod` on `/dev/mem` or the serial port is
needed or wanted at runtime.

## LiDAR power — read this before debugging "lidar issues"

The RPLidar is powered from a **separate 5 V supply** (e.g. the second port of
the power bank; Pi on port 1, LiDAR on port 2), *not* from the Pi's USB/5 V
rail. On shared power, motor-start current dips reset the lidar's USB bridge
and the scan drops out — this presented for a long time as a software problem.

Split-cable rules:

- Data (D+/D−) and **ground** go to the Pi. Ground must be common.
- 5 V comes **only** from the separate supply. Do **not** connect the Pi-side
  USB 5 V (VBUS) wire — two 5 V sources must never be tied together, and the
  Pi's port must not back-power the lidar.

## Running the real robot

### 1. On the Raspberry Pi

```bash
cd ~/picar_ws && source install/setup.bash
./start_picar_pi.sh real
# equivalent to: ros2 launch picar4wd_driver picar_bringup.launch.py
```

### 2. On the AGX Orin

```bash
cd ~/picar_ws && source install/setup.bash
./start_picar_jetson.sh real
```

This starts SLAM Toolbox, the Wi-Fi heat-map overlay and RViz. Odometry runs on the Pi (in its bringup). No cmd_vel relay is needed: /cmd_vel is the same topic on both machines and DDS connects them directly. The relay in agenticros_bringup is only for namespaced sources such as AgenticROS.

### 3. Verify, in this order (first run, and after any change)

Don't skip the ladder — each step proves the next one can work:

```bash
ros2 topic hz /scan                 # steady rate, no dropouts when motors start
ros2 run tf2_tools view_frames      # map → odom → base_link → lidar_link, one tree
ros2 topic echo /odom               # values respond to cmd_vel (dead-reckoned, see note)
ros2 run teleop_twist_keyboard teleop_twist_keyboard   # drive slowly, low speed first
```

> Odometry is currently dead-reckoned from commanded velocity, not measured
> from the wheels — treat it as an aid to SLAM scan-matching, not truth.

**Safety:** the motor driver stops the car if no `cmd_vel` arrives for
0.5 s (watchdog). Even so: test on blocks / wheels up first, keep speeds low
for first runs, and keep a hand on the power switch.

### 4. Drive it

Teleop publishes `/cmd_vel`; the Orin relay forwards it to the car.
Alternatively, one-shot commands from any sourced terminal:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}, angular: {z: 0.0}}' -r 10
```

Stop by ending the publisher — the watchdog stops the car within 0.5 s.

### 5. Save a map (SLAM Toolbox)

```bash
mkdir -p ~/picar_ws/maps
ros2 run nav2_map_server map_saver_cli -f ~/picar_ws/maps/my_house
```

## Simulation

Gazebo simulation of the PiCar (no hardware needed), from the workspace root:

```bash
ros2 launch agenticros_sim sim_picar.launch.py use_rviz:=true
```

Drive it with the same `/cmd_vel` commands as above. Simulation uses its own
clock (`use_sim_time`); don't mix sim and real nodes on the same ROS domain at
the same time.

## Running the Pi on a Raspberry Pi 3B

The Pi in this project is a 3B (1 GB RAM). That is enough for the motor
driver + lidar + odometry + RSSI nodes, as long as nothing heavier runs
there (SLAM, Nav2, RViz and recording all belong on the Orin). The things
that actually make it reliable:

- **Power:** a real 5.1 V / 2.5 A supply on a short, thick micro-USB cable
  (voltage drop in thin cables is the 3B's #1 fault), lidar on its own
  rail as above. Check with `vcgencmd get_throttled` — it must read
  `0x0` after a hard run; anything else means under-voltage/throttling
  has happened since boot.
- **Headless and thin:** server/lite OS, no desktop, `gpu_mem=16`,
  disable snapd/bluetooth/avahi if unused.
- **zram swap** (≈512 MB, lz4) instead of swap on the microSD card.
- **Wi-Fi power-save OFF, permanently** (NetworkManager
  `wifi.powersave=2`) — power-save causes 100–900 ms latency spikes that
  look exactly like DDS dropouts. The 3B is 2.4 GHz-only, so keep the
  antenna unobstructed and RSSI better than about −70 dBm.
- **Supervise it:** one systemd unit for the bringup
  (`Restart=on-failure`, started after `network-online.target`, with
  `ROS_DOMAIN_ID=42` in the unit's environment), the BCM hardware
  watchdog enabled, journald capped, and a cloned spare microSD card.
  Use a high-endurance card — SD wear and power-pull corruption are the
  other two classic Pi-on-a-robot deaths.
- Check time sync (chrony) before bringup: TF/SLAM across two machines
  hates a Pi clock that is still unsynced.

## Repository layout

| Path | What |
|---|---|
| `src/picar4wd_driver/` | Real-hardware drivers: motor driver, odometry, sonar, Wi-Fi RSSI nodes + real-robot bringup |
| `src/picar_description/` | The PiCar URDF (single source of truth, used by real bringup and sim) |
| `src/agenticros_sim/` | Gazebo worlds, models and sim launch for the PiCar (plus unrelated AMR/arm experiments) |
| `src/agenticros_bringup/` | `cmd_vel` relay and assorted sim/RViz launch files |
| `src/agenticros_*` | AgenticROS framework packages (discovery, agent bridge, follow-me) — not required for basic driving/SLAM |
| `start_picar_pi.sh` / `start_picar_jetson.sh` | Per-machine startup for real-robot mode |
| `udev/` | Device rules (lidar serial symlink) |

## Troubleshooting

| Symptom | Check |
|---|---|
| Motors don't respond | `ros2 topic list \| grep cmd_vel` on the Pi — the motor driver, the relay output and teleop must all be the **same** topic (`/cmd_vel`). Then `ros2 topic echo` it while driving. |
| `/scan` missing or intermittent | Power first: is the lidar on its own supply? Then `ls -l /dev/rplidar`, `lsusb`, and `ros2 topic hz /scan` while starting the motors — dropouts under motor load = power, not software. |
| SLAM not building / TF errors | `view_frames` — if `odom → base_link` is missing, SLAM has no pose; check the odometry node is running on the Pi. |
| Nodes can't see each other | Same `ROS_DOMAIN_ID` (42) exported on **both** machines, same subnet, `ping` each way. |
| No Wi-Fi markers in RViz | Wi-Fi heat mapping is WIP — see the review notes; it is not part of standard bringup. |

## Work in progress

- Wi-Fi RSSI heat-map overlay (nodes exist in `picar4wd_driver`; position
  stamping and RViz marker handling are being reworked)
- Nav2 autonomous navigation (parameter file is a placeholder; teleop +
  SLAM mapping work today)
