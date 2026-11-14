#!/bin/bash
# Raspberry Pi startup -- real robot hardware.
# Usage: ./start_picar_pi.sh [--no-wifi]
#
# Runs picar_bringup in the FOREGROUND (lidar, motors, odometry,
# robot_state_publisher, Wi-Fi RSSI). Run it under systemd or tmux for
# unattended use; Ctrl+C stops everything cleanly.
#
# One-time setup lives in the README (udev rule for /dev/rplidar, user in
# dialout/gpio groups). This script deliberately does NOT sudo-chmod
# /dev/mem, /dev/gpiomem or the serial port on every run -- an earlier
# version did, and world-writable /dev/mem is a serious security hole
# that also has to be redone after every reboot.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

source /opt/ros/jazzy/setup.bash
if [ ! -f "$SCRIPT_DIR/install/setup.bash" ]; then
    echo "Workspace not built. Run: colcon build --symlink-install" >&2
    exit 1
fi
source "$SCRIPT_DIR/install/setup.bash"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

# SunFounder picar-4wd library: prefer an installed copy; fall back to a
# checkout next to the workspace or in the home directory. Override by
# exporting PICAR_4WD_PATH before running this script.
if ! python3 -c "import picar_4wd" 2>/dev/null; then
    for cand in "${PICAR_4WD_PATH:-}" "$HOME/picar-4wd" "$SCRIPT_DIR/../picar-4wd"; do
        if [ -n "$cand" ] && [ -d "$cand" ]; then
            export PYTHONPATH="$cand:${PYTHONPATH:-}"
            break
        fi
    done
fi
if ! python3 -c "import picar_4wd" 2>/dev/null; then
    echo "WARNING: picar_4wd library not importable; motor/sonar nodes will fail." >&2
    echo "Install SunFounder picar-4wd or set PICAR_4WD_PATH to its location." >&2
fi

# Loud, early checks instead of mysterious node crashes later.
if [ ! -e /dev/rplidar ]; then
    echo "WARNING: /dev/rplidar does not exist." >&2
    echo "Is the lidar plugged in, and is udev/99-rplidar.rules installed?" >&2
fi
if ! id -nG "$USER" | grep -qw dialout; then
    echo "WARNING: $USER is not in the dialout group (serial access may fail)." >&2
fi
# Pi health: under-voltage / throttling history (0x0 is clean). This is
# the check that would have caught the lidar power problem immediately.
if command -v vcgencmd >/dev/null 2>&1; then
    echo "Pi throttle status: $(vcgencmd get_throttled)  (throttled=0x0 is clean)"
fi

INCLUDE_WIFI=true
if [ "${1:-}" = "--no-wifi" ]; then
    INCLUDE_WIFI=false
fi

echo "Starting PiCar bringup (domain $ROS_DOMAIN_ID, wifi=$INCLUDE_WIFI)..."
exec ros2 launch picar4wd_driver picar_bringup.launch.py include_wifi:=$INCLUDE_WIFI
