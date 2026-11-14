# Documentation

The main documentation is the [top-level README](../README.md): hardware,
one-time setup (udev rule, groups, SunFounder library), running the real
robot, the verification ladder, simulation, and troubleshooting.

This folder keeps supplementary guides:

- `sim_to_real_transfer.md` -- notes on moving from Gazebo to the real car
- `gazebo_sim_start.sh` -- a small simulation launcher helper

Older material that used to live here (a long generated setup document
describing an RTAB-Map launch file, a scripts/ layout and ROS Humble
installs that never matched the repo) was removed in 2026-11; the repo
uses ROS 2 Jazzy, SLAM Toolbox, and nodes installed from the
`picar4wd_driver` package. Git history has the old text if needed.
