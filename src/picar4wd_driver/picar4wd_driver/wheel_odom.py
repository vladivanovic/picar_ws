"""Wheel-speed odometry maths for the PiCar-4WD. Pure Python, no ROS,
so it can be unit-tested anywhere.

Hardware facts (SunFounder picar-4wd library, verified against its
source): the car has TWO speed sensors, on the REAR wheels
(``fc.left_rear_speed`` on GPIO 25, ``fc.right_rear_speed`` on GPIO 4).
Each counts slots on a 20-slot disc and reports an UNSIGNED speed in
cm/s (the library hardcodes a 3.3 cm wheel radius). Direction is not
measured -- it has to come from the sign of the power currently applied
to that side, which is why measured odometry lives in the motor driver
node: it's the one process that knows both.

Skid steering: this car turns like a tank -- all four wheels are driven
and the turn is produced by a speed difference between the sides, with
the tyres scrubbing sideways. Differential-drive kinematics still
apply, but with an EFFECTIVE track width that is larger than the
geometric 0.14 m, because scrub eats some of the rotation. Using the
geometric width makes odometry systematically over-report yaw in
turns -- which is what used to throw the SLAM map off. Calibrate
``effective_track_width`` (procedure in the README) instead of trusting
either number.
"""

from __future__ import annotations

import math


def signed_speed(magnitude_mps: float, direction: float) -> float:
    """Apply a direction (+1 / -1 / 0, from applied motor power) to an
    unsigned wheel speed. Direction 0 (no power, no known heading)
    yields 0: better to under-report coasting than to guess a sign."""
    if direction > 0:
        return abs(magnitude_mps)
    if direction < 0:
        return -abs(magnitude_mps)
    return 0.0


def twist_from_wheels(left_mps: float, right_mps: float,
                      effective_track_width: float) -> tuple[float, float]:
    """(linear m/s, angular rad/s) from signed left/right wheel speeds."""
    v = (left_mps + right_mps) / 2.0
    omega = (right_mps - left_mps) / effective_track_width
    return v, omega


def update_pose(x: float, y: float, theta: float,
                v: float, omega: float, dt: float) -> tuple[float, float, float]:
    """Integrate a constant (v, omega) step with exact arc geometry."""
    if dt <= 0.0:
        return x, y, theta
    if abs(omega) < 1e-6:
        return (x + v * math.cos(theta) * dt,
                y + v * math.sin(theta) * dt,
                theta)
    radius = v / omega
    new_theta = theta + omega * dt
    return (x + radius * (math.sin(new_theta) - math.sin(theta)),
            y + radius * (-math.cos(new_theta) + math.cos(theta)),
            new_theta)
