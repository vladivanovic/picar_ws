#!/usr/bin/env python3
"""Motor driver for the SunFounder PiCar-4WD.

Subscribes to ``cmd_vel`` (geometry_msgs/Twist, relative to the node's
namespace -- in the standard bringup that is simply ``/cmd_vel``) and
drives the four motors via SunFounder's ``picar_4wd`` library.

Safety behaviour (added 2026-11):

* **Watchdog:** a 20 Hz control timer stops the motors if no cmd_vel has
  arrived within ``cmd_timeout`` seconds (default 0.5 s). Before this,
  the last commanded power stayed on the motors forever if the publisher
  (teleop, Nav2, the Orin over Wi-Fi) went away.
* **Ramping:** motor power slews toward the target at
  ``ramp_rate`` %/s instead of stepping instantly, which is kinder to
  the motors, the battery rail and the lidar sharing the car.
* **Mixing:** proper differential mixing with the real track width
  (see mixing.py) instead of adding m/s and rad/s together.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from picar4wd_driver.mixing import mix, ramp_towards

try:
    import picar_4wd as fc
except ImportError:  # pragma: no cover - only importable on the Pi
    fc = None


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver_node')

        if fc is None:
            raise RuntimeError(
                'picar_4wd library not importable. Install SunFounder '
                'picar-4wd on the Pi and/or set PYTHONPATH to its '
                'location (see README, one-time setup).'
            )

        self.declare_parameter('max_speed', 50)          # % power at ref_speed m/s
        self.declare_parameter('ref_speed', 1.0)         # m/s
        self.declare_parameter('track_width', 0.14)      # m, wheel-to-wheel
        self.declare_parameter('min_power', 0.0)         # stall deadband, % (0 = off)
        self.declare_parameter('cmd_timeout', 0.5)       # s, watchdog
        self.declare_parameter('ramp_rate', 250.0)       # %/s

        self.max_speed = float(self.get_parameter('max_speed').value)
        self.ref_speed = float(self.get_parameter('ref_speed').value)
        self.track_width = float(self.get_parameter('track_width').value)
        self.min_power = float(self.get_parameter('min_power').value)
        self.cmd_timeout = float(self.get_parameter('cmd_timeout').value)
        self.ramp_rate = float(self.get_parameter('ramp_rate').value)

        self._target_left = 0.0
        self._target_right = 0.0
        self._current_left = 0.0
        self._current_right = 0.0
        self._last_cmd_time = None  # None = no command received yet
        self._stopped = True

        self.subscription = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self._control_period = 0.05  # 20 Hz
        self.timer = self.create_timer(self._control_period, self.control_tick)

        self.get_logger().info(
            'Motor driver started (watchdog %.2fs, ramp %.0f%%/s, '
            'track width %.2fm)' % (self.cmd_timeout, self.ramp_rate, self.track_width))

    def cmd_vel_callback(self, msg):
        self._last_cmd_time = self.get_clock().now()
        left, right = mix(
            msg.linear.x, msg.angular.z,
            track_width=self.track_width,
            power_at_ref_speed=self.max_speed,
            ref_speed=self.ref_speed,
            min_power=self.min_power,
        )
        self._target_left = float(left)
        self._target_right = float(right)

    def control_tick(self):
        # Watchdog: no fresh command -> target zero and hard-stop once.
        if self._last_cmd_time is not None:
            age = (self.get_clock().now() - self._last_cmd_time).nanoseconds / 1e9
            if age > self.cmd_timeout:
                self._target_left = 0.0
                self._target_right = 0.0
                if not self._stopped:
                    fc.stop()
                    self._current_left = 0.0
                    self._current_right = 0.0
                    self._stopped = True
                    self.get_logger().warn(
                        'cmd_vel timeout (%.2fs) -- motors stopped' % age)
                return

        max_step = self.ramp_rate * self._control_period
        self._current_left = ramp_towards(self._current_left, self._target_left, max_step)
        self._current_right = ramp_towards(self._current_right, self._target_right, max_step)

        left = int(round(self._current_left))
        right = int(round(self._current_right))
        if left == 0 and right == 0:
            if not self._stopped:
                fc.stop()
                self._stopped = True
            return

        self._stopped = False
        fc.left_front.set_power(left)
        fc.left_rear.set_power(left)
        fc.right_front.set_power(right)
        fc.right_rear.set_power(right)

    def destroy_node(self):
        if fc is not None:
            fc.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
