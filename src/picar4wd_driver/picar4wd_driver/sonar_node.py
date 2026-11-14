#!/usr/bin/env python3
"""Servo-swept ultrasonic sonar, published as a LaserScan.

Publishes on ``sonar_scan`` -- deliberately NOT ``scan``, which belongs
to the RPLidar. An earlier version published on ``scan`` too, so running
both sensors corrupted SLAM's input.

The sweep is a state machine driven by a fast timer (one angle step per
tick) instead of blocking time.sleep() calls inside a slow timer
callback, which used to stall the executor for most of each second.
Failed / out-of-range readings are published as +inf ("no return"),
never as a clamped real distance.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

try:
    import picar_4wd as fc
except ImportError:  # pragma: no cover - only importable on the Pi
    fc = None


class SonarScannerNode(Node):
    def __init__(self):
        super().__init__('sonar_scanner_node')

        if fc is None:
            raise RuntimeError(
                'picar_4wd library not importable. Install SunFounder '
                'picar-4wd on the Pi (see README).')

        self.declare_parameter('angle_min', -60.0)
        self.declare_parameter('angle_max', 60.0)
        self.declare_parameter('angle_step', 10.0)
        self.declare_parameter('max_range', 3.0)
        self.declare_parameter('step_period', 0.06)  # s per angle step

        self.angle_min = float(self.get_parameter('angle_min').value)
        self.angle_max = float(self.get_parameter('angle_max').value)
        self.angle_step = float(self.get_parameter('angle_step').value)
        self.max_range = float(self.get_parameter('max_range').value)
        step_period = float(self.get_parameter('step_period').value)

        self.scan_publisher = self.create_publisher(LaserScan, 'sonar_scan', 10)

        self._angles = []
        a = self.angle_min
        while a <= self.angle_max + 1e-9:
            self._angles.append(a)
            a += self.angle_step
        self._idx = 0
        self._ranges = []
        self._sweep_start = None

        self.timer = self.create_timer(step_period, self.step_callback)
        self.get_logger().info(
            'Sonar scanner started on sonar_scan (%d steps/sweep)'
            % len(self._angles))

    def step_callback(self):
        now = self.get_clock().now()
        if self._idx == 0:
            self._sweep_start = now
            self._ranges = []

        angle = self._angles[self._idx]
        fc.servo.set_angle(int(angle))

        distance_cm = fc.us.get_distance()
        if distance_cm is None or distance_cm <= 0:
            distance = float('inf')   # no echo / sensor error
        else:
            distance = distance_cm / 100.0
            if distance > self.max_range:
                distance = float('inf')
        self._ranges.append(distance)
        self._idx += 1

        if self._idx < len(self._angles):
            return

        # Sweep complete: publish it, then start again.
        scan = LaserScan()
        scan.header.stamp = self._sweep_start.to_msg()
        scan.header.frame_id = 'sonar_link'
        scan.angle_min = math.radians(self.angle_min)
        scan.angle_max = math.radians(self.angle_max)
        scan.angle_increment = math.radians(self.angle_step)
        scan.range_min = 0.02
        scan.range_max = self.max_range
        scan.ranges = self._ranges
        scan.time_increment = 0.06
        scan.scan_time = len(self._ranges) * scan.time_increment
        self.scan_publisher.publish(scan)

        self._idx = 0
        fc.servo.set_angle(0)


def main(args=None):
    rclpy.init(args=args)
    node = SonarScannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
