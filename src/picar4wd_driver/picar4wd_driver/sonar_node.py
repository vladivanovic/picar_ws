#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import picar_4wd as fc
import math
import time

class SonarScannerNode(Node):
    def __init__(self):
        super().__init__('sonar_scanner_node')
        self.scan_publisher = self.create_publisher(LaserScan, 'scan', 10)

        self.declare_parameter('angle_min', -60.0)
        self.declare_parameter('angle_max', 60.0)
        self.declare_parameter('angle_step', 10.0)
        self.declare_parameter('max_range', 3.0)
        self.declare_parameter('scan_rate', 1.0)

        self.angle_min = self.get_parameter('angle_min').value
        self.angle_max = self.get_parameter('angle_max').value
        self.angle_step = self.get_parameter('angle_step').value
        self.max_range = self.get_parameter('max_range').value
        scan_rate = self.get_parameter('scan_rate').value

        self.timer = self.create_timer(1.0 / scan_rate, self.scan_callback)
        self.get_logger().info('Sonar scanner node started')

    def scan_callback(self):
        scan_msg = LaserScan()
        scan_msg.header.stamp = self.get_clock().now().to_msg()
        scan_msg.header.frame_id = 'sonar_link'

        scan_msg.angle_min = math.radians(self.angle_min)
        scan_msg.angle_max = math.radians(self.angle_max)
        scan_msg.angle_increment = math.radians(self.angle_step)
        scan_msg.range_min = 0.02
        scan_msg.range_max = self.max_range

        ranges = []

        current_angle = self.angle_min
        while current_angle <= self.angle_max:
            fc.servo.set_angle(int(current_angle))
            time.sleep(0.05)

            distance_cm = fc.us.get_distance()
            distance_m = distance_cm / 100.0 if distance_cm > 0 else self.max_range

            if distance_m < scan_msg.range_min:
                distance_m = scan_msg.range_min
            elif distance_m > scan_msg.range_max:
                distance_m = float('inf')

            ranges.append(distance_m)
            current_angle += self.angle_step

        scan_msg.ranges = ranges
        scan_msg.time_increment = 0.05
        scan_msg.scan_time = len(ranges) * 0.05

        self.scan_publisher.publish(scan_msg)
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
