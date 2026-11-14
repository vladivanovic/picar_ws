"""Unit tests for wheel-speed odometry maths (pure Python, no ROS).

Run locally without a ROS install:
    cd src/picar4wd_driver && python3 -m pytest test/test_wheel_odom.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from picar4wd_driver.wheel_odom import signed_speed, twist_from_wheels, update_pose  # noqa: E402


def test_signed_speed():
    assert signed_speed(0.4, 1.0) == 0.4
    assert signed_speed(0.4, -1.0) == -0.4
    assert signed_speed(0.4, 0.0) == 0.0   # unknown direction: report nothing
    assert signed_speed(-0.4, 1.0) == 0.4  # magnitude is unsigned by definition


def test_straight_line():
    v, omega = twist_from_wheels(0.5, 0.5, 0.14)
    assert v == 0.5 and omega == 0.0
    x, y, theta = update_pose(0.0, 0.0, 0.0, v, omega, 2.0)
    assert abs(x - 1.0) < 1e-9 and y == 0.0 and theta == 0.0


def test_turn_in_place():
    # Skid steer: sides counter-rotate.
    v, omega = twist_from_wheels(-0.2, 0.2, 0.14)
    assert v == 0.0
    assert omega > 0
    x, y, theta = update_pose(0.0, 0.0, 0.0, v, omega, 1.0)
    assert abs(x) < 1e-9 and abs(y) < 1e-9
    assert abs(theta - omega) < 1e-9


def test_effective_track_width_reduces_reported_yaw():
    # The skid-steer point: a wider effective track reports less yaw for
    # the same wheel speeds, compensating for scrub.
    _, omega_geom = twist_from_wheels(-0.2, 0.2, 0.14)
    _, omega_eff = twist_from_wheels(-0.2, 0.2, 0.28)
    assert omega_eff < omega_geom
    assert abs(omega_eff - omega_geom / 2.0) < 1e-9


def test_arc_conserves_radius():
    v, omega = 0.4, 0.5
    x, y, theta = update_pose(0.0, 0.0, 0.0, v, omega, 1.0)
    # After 1 s on an arc of radius v/omega, heading is omega and the
    # position lies on the circle.
    assert abs(theta - 0.5) < 1e-9
    radius = v / omega
    assert abs(math.hypot(x, y - radius) - radius) < 1e-6


def test_zero_dt_no_motion():
    assert update_pose(1.0, 2.0, 0.3, 1.0, 1.0, 0.0) == (1.0, 2.0, 0.3)
