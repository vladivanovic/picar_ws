"""Pure differential-drive mixing for the PiCar-4WD.

No ROS and no hardware imports here, so this module can be unit-tested
anywhere (see test/test_mixing.py).

Model: a Twist gives a body linear velocity ``v`` (m/s) and angular
velocity ``omega`` (rad/s). Each side's wheel-ground speed is

    v_left  = v - omega * track_width / 2
    v_right = v + omega * track_width / 2

Wheel speeds are converted to motor power (-100..100 %) by scaling with
``power_at_ref_speed``: the power that ``ref_speed`` m/s of wheel speed
should produce. With the defaults (50 % at 1.0 m/s) this preserves the
pre-2026-11 tuning where a 1 m/s command meant 50 % power, except that
turning now uses the real track width instead of adding rad/s to m/s.
"""

from __future__ import annotations


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def wheel_speeds(linear_x: float, angular_z: float, track_width: float) -> tuple[float, float]:
    """Return (left, right) wheel-ground speeds in m/s for a Twist."""
    turn = angular_z * track_width / 2.0
    return linear_x - turn, linear_x + turn


def speed_to_power(
    wheel_speed: float,
    power_at_ref_speed: float = 50.0,
    ref_speed: float = 1.0,
    min_power: float = 0.0,
) -> int:
    """Convert a wheel speed in m/s to a motor power in -100..100 %.

    ``min_power`` is an optional deadband: a non-zero command whose power
    would be too small to overcome motor stall is lifted to ``min_power``
    (keeping its sign). Leave it 0.0 until you have measured the car's
    stall threshold on the floor; typical TT motors need ~15-25 %.
    """
    if wheel_speed == 0.0:
        return 0
    power = wheel_speed / ref_speed * power_at_ref_speed
    power = clamp(power, -100.0, 100.0)
    if min_power > 0.0 and abs(power) < min_power:
        power = min_power if power > 0 else -min_power
    return int(round(power))


def mix(
    linear_x: float,
    angular_z: float,
    track_width: float = 0.14,
    power_at_ref_speed: float = 50.0,
    ref_speed: float = 1.0,
    min_power: float = 0.0,
) -> tuple[int, int]:
    """Return (left_power, right_power) in -100..100 % for a Twist."""
    left, right = wheel_speeds(linear_x, angular_z, track_width)
    return (
        speed_to_power(left, power_at_ref_speed, ref_speed, min_power),
        speed_to_power(right, power_at_ref_speed, ref_speed, min_power),
    )


def ramp_towards(current: float, target: float, max_step: float) -> float:
    """Move ``current`` toward ``target`` by at most ``max_step``."""
    if max_step <= 0:
        return float(target)
    return current + clamp(target - current, -max_step, max_step)
