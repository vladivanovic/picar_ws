#!/usr/bin/env python3
"""Wi-Fi signal heat-map overlay (runs on the control unit / Orin).

Subscribes to:
  /wifi/rssi  (std_msgs/Int32)   -- from the Pi's wifi_rssi_node
  /odom       (nav_msgs/Odometry) -- robot pose, used to place markers

Publishes:
  /wifi/heatmap_markers (visualization_msgs/MarkerArray)

A sample is only recorded when the robot has moved at least
``min_distance`` metres since the last one, so parked time doesn't stack
hundreds of markers on one spot. Markers are green (>-50 dBm), yellow
(>-70 dBm) or red (weaker), plus a line-strip trail.

This replaces the previous version, which never learned the robot's
position at all -- its set_robot_position() was never called by anything
and it had no odom/TF subscription, so every marker was published at the
map origin. It also published individual Markers with an ID counter
shared between spheres and the trail, so they overwrote each other;
MarkerArray with stable IDs fixes that.
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA

TRAIL_ID = 999999


def rssi_color(rssi: int) -> ColorRGBA:
    if rssi > -50:
        return ColorRGBA(r=0.0, g=1.0, b=0.0, a=0.9)
    if rssi > -70:
        return ColorRGBA(r=1.0, g=1.0, b=0.0, a=0.9)
    return ColorRGBA(r=1.0, g=0.0, b=0.0, a=0.9)


class WiFiMapOverlayNode(Node):
    def __init__(self):
        super().__init__('wifi_map_overlay_node')

        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('min_distance', 0.25)   # m between samples
        self.declare_parameter('max_samples', 2000)
        odom_topic = self.get_parameter('odom_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.min_distance = float(self.get_parameter('min_distance').value)
        self.max_samples = int(self.get_parameter('max_samples').value)

        self.create_subscription(Int32, '/wifi/rssi', self.rssi_callback, 10)
        self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        self.marker_pub = self.create_publisher(
            MarkerArray, '/wifi/heatmap_markers', 10)

        self._pose = None          # (x, y) from odom, None until known
        self._samples = []         # list of (x, y, rssi)
        self._last_sample_xy = None

        self.get_logger().info(
            'Wi-Fi heat map overlay started (pose from %s)' % odom_topic)

    def odom_callback(self, msg):
        p = msg.pose.pose.position
        self._pose = (p.x, p.y)

    def rssi_callback(self, msg):
        if self._pose is None:
            return  # No pose yet: a marker at (0,0) would be a lie.
        x, y = self._pose
        if self._last_sample_xy is not None:
            dx = x - self._last_sample_xy[0]
            dy = y - self._last_sample_xy[1]
            if math.hypot(dx, dy) < self.min_distance:
                return
        self._samples.append((x, y, msg.data))
        if len(self._samples) > self.max_samples:
            self._samples = self._samples[-self.max_samples:]
        self._last_sample_xy = (x, y)
        self._publish_markers()

    def _publish_markers(self):
        now = self.get_clock().now().to_msg()
        array = MarkerArray()

        for i, (x, y, rssi) in enumerate(self._samples):
            marker = Marker()
            marker.header.frame_id = self.frame_id
            marker.header.stamp = now
            marker.ns = 'wifi_heatmap'
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = 0.1
            marker.pose.orientation.w = 1.0
            size = 0.12 + abs(rssi) / 100.0 * 0.05
            marker.scale.x = size
            marker.scale.y = size
            marker.scale.z = size
            marker.color = rssi_color(rssi)
            array.markers.append(marker)

        if len(self._samples) >= 2:
            trail = Marker()
            trail.header.frame_id = self.frame_id
            trail.header.stamp = now
            trail.ns = 'wifi_heatmap_trail'
            trail.id = TRAIL_ID
            trail.type = Marker.LINE_STRIP
            trail.action = Marker.ADD
            trail.scale.x = 0.03
            trail.color = ColorRGBA(r=0.2, g=0.6, b=1.0, a=0.6)
            trail.pose.orientation.w = 1.0
            for (x, y, _rssi) in self._samples:
                p = Point()
                p.x = x
                p.y = y
                p.z = 0.05
                trail.points.append(p)
            array.markers.append(trail)

        self.marker_pub.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = WiFiMapOverlayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
