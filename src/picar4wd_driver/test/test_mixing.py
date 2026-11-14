"""Unit tests for the differential-drive mixing (pure Python, no ROS).

Run locally without a ROS install:
    cd src/picar4wd_driver && python3 -m pytest test/test_mixing.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from picar4wd_driver.mixing import mix, ramp_towards, wheel_speeds  # noqa: E402


def test_straight():
    assert mix(0.5, 0.0) == (25, 25)
    assert mix(1.0, 0.0) == (50, 50)
    assert mix(0.0, 0.0) == (0, 0)
    assert mix(-0.5, 0.0) == (-25, -25)


def test_turn_in_place_is_symmetric():
    left, right = mix(0.0, 1.0, track_width=0.14)
    assert left == -right
    assert left < 0 < right


def test_turn_uses_track_width_not_raw_addition():
    # Old (buggy) code: left=(v-w)*50, right=(v+w)*50 -> (0, 50) here.
    # With a 0.14 m track, a gentle arc should keep both wheels moving.
    left, right = mix(0.5, 0.5, track_width=0.14)
    assert left > 0
    assert right > left


def test_clamping():
    left, right = mix(10.0, 0.0)
    assert (left, right) == (100, 100)
    left, right = mix(-10.0, 0.0)
    assert (left, right) == (-100, -100)


def test_min_power_deadband():
    assert mix(0.02, 0.0, min_power=0.0) == (1, 1)
    assert mix(0.02, 0.0, min_power=20.0) == (20, 20)
    assert mix(-0.02, 0.0, min_power=20.0) == (-20, -20)
    # Zero stays zero even with a deadband.
    assert mix(0.0, 0.0, min_power=20.0) == (0, 0)


def test_wheel_speeds():
    left, right = wheel_speeds(1.0, 2.0, 0.14)
    assert abs(left - 0.86) < 1e-9
    assert abs(right - 1.14) < 1e-9


def test_ramp():
    assert ramp_towards(0.0, 100.0, 12.5) == 12.5
    assert ramp_towards(90.0, 100.0, 12.5) == 100.0
    assert ramp_towards(50.0, 0.0, 12.5) == 37.5
    assert ramp_towards(0.0, 100.0, 0.0) == 100.0
