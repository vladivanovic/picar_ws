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
* **Mixing:** skid-steer (differential) mixing with the track width
  (see mixing.py) instead of adding m/s and rad/s together. This car
  turns like a tank: all four wheels are driven and a turn is a speed
  difference between the sides.
* **Measured odometry (optional, on by default in bringup):** the
  SunFounder library exposes speed sensors on both REAR wheels
  (20-slot discs). They report unsigned cm/s, so the direction has to
  come from the power this node is applying -- which is why odometry
  is published from here rather than a separate process (it also
  avoids two processes fighting over GPIO). Set publish_odom:=false
  to fall back to the command-based odom_node.
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

from picar4wd_driver.mixing import mix, ramp_towards
from picar4wd_driver.wheel_odom import signed_speed, twist_from_wheels, update_pose

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
        # Measured (wheel-speed) odometry
        self.declare_parameter('publish_odom', False)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('effective_track_width', 0.14)  # m, calibrate!
        self.declare_parameter('speed_scale', 1.0)       # measured-speed correction

        self.max_speed = float(self.get_parameter('max_speed').value)
        self.ref_speed = float(self.get_parameter('ref_speed').value)
        self.track_width = float(self.get_parameter('track_width').value)
        self.min_power = float(self.get_parameter('min_power').value)
        self.cmd_timeout = float(self.get_parameter('cmd_timeout').value)
        self.ramp_rate = float(self.get_parameter('ramp_rate').value)
        self.publish_odom = bool(self.get_parameter('publish_odom').value)
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.effective_track_width = float(
            self.get_parameter('effective_track_width').value)
        self.speed_scale = float(self.get_parameter('speed_scale').value)

        self._target_left = 0.0
        self._target_right = 0.0
        self._current_left = 0.0
        self._current_right = 0.0
        self._last_cmd_time = None  # None = no command received yet
        self._stopped = True

        # Odometry state (wheel-speed based)
        self._x = 0.0
        self._y = 0.0
        self._theta = 0.0
        self._last_dir_left = 0.0    # last non-zero power sign, per side
        self._last_dir_right = 0.0
        self._odom_pub = None
        self._tf_broadcaster = None
        if self.publish_odom:
            try:
                fc.start_speed_thread()
                self._odom_pub = self.create_publisher(Odometry, 'odom', 10)
                self._tf_broadcaster = TransformBroadcaster(self)
                self.get_logger().info(
                    'Wheel-speed odometry on (effective track width %.2fm)'
                    % self.effective_track_width)
            except Exception as e:  # sensor/GPIO problem: drive anyway
                self.publish_odom = False
                self.get_logger().error(
                    'Could not start speed sensors (%s); odometry disabled' % e)

        self.subscription = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self._control_period = 0.05  # 20 Hz
        self._last_tick = self.get_clock().now()
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
        now = self.get_clock().now()
        dt = (now - self._last_tick).nanoseconds / 1e9
        self._last_tick = now
        if dt <= 0.0 or dt > 1.0:
            dt = self._control_period

        # Watchdog: no fresh command -> target zero and hard-stop once.
        watchdog_stop = False
        if self._last_cmd_time is not None:
            age = (now - self._last_cmd_time).nanoseconds / 1e9
            if age > self.cmd_timeout:
                self._target_left = 0.0
                self._target_right = 0.0
                watchdog_stop = True
                if not self._stopped:
                    fc.stop()
                    self._current_left = 0.0
                    self._current_right = 0.0
                    self._stopped = True
                    self.get_logger().warn(
                        'cmd_vel timeout (%.2fs) -- motors stopped' % age)

        if not watchdog_stop:
            max_step = self.ramp_rate * self._control_period
            self._current_left = ramp_towards(
                self._current_left, self._target_left, max_step)
            self._current_right = ramp_towards(
                self._current_right, self._target_right, max_step)

            left = int(round(self._current_left))
            right = int(round(self._current_right))
            if left == 0 and right == 0:
                if not self._stopped:
                    fc.stop()
                    self._stopped = True
            else:
                self._stopped = False
                fc.left_front.set_power(left)
                fc.left_rear.set_power(left)
                fc.right_front.set_power(right)
                fc.right_rear.set_power(right)

        # Remember travel direction per side for signing the (unsigned)
        # wheel-speed readings; keep the last non-zero sign so a car
        # coasting to a stop still reports the right direction.
        if self._current_left > 0.5:
            self._last_dir_left = 1.0
        elif self._current_left < -0.5:
            self._last_dir_left = -1.0
        if self._current_right > 0.5:
            self._last_dir_right = 1.0
        elif self._current_right < -0.5:
            self._last_dir_right = -1.0

        if self.publish_odom:
            self._update_odom(now, dt)

    def _update_odom(self, now, dt):
        # Library reports unsigned cm/s per rear wheel.
        left_mag = fc.left_rear_speed() / 100.0 * self.speed_scale
        right_mag = fc.right_rear_speed() / 100.0 * self.speed_scale
        left = signed_speed(left_mag, self._last_dir_left)
        right = signed_speed(right_mag, self._last_dir_right)
        v, omega = twist_from_wheels(left, right, self.effective_track_width)
        self._x, self._y, self._theta = update_pose(
            self._x, self._y, self._theta, v, omega, dt)

        qz = math.sin(self._theta / 2.0)
        qw = math.cos(self._theta / 2.0)

        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self._x
        t.transform.translation.y = self._y
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self._tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = omega
        # Measured forward speed is decent; yaw from skid-steer wheel
        # speeds is not (scrub), so yaw keeps a large variance and SLAM
        # scan matching should be trusted over it in turns.
        pose_cov = [0.0] * 36
        pose_cov[0] = 0.05
        pose_cov[7] = 0.05
        pose_cov[14] = 1e6
        pose_cov[21] = 1e6
        pose_cov[28] = 1e6
        pose_cov[35] = 0.5
        odom.pose.covariance = pose_cov
        twist_cov = [0.0] * 36
        twist_cov[0] = 0.02
        twist_cov[35] = 0.2
        odom.twist.covariance = twist_cov
        self._odom_pub.publish(odom)

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
