#!/usr/bin/env python3
"""
Wi-Fi Signal Heat Map Overlay for RTAB-Map.
Subscribes to /wifi/rssi and publishes RViz2 markers for heat map visualization.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA, Header
import numpy as np


class WiFiMapOverlayNode(Node):
    def __init__(self):
        super().__init__('wifi_map_overlay_node')
        
        # Subscriber: Wi-Fi RSSI from Pi
        self.rssi_sub = self.create_subscription(
            Int32, '/wifi/rssi', self.rssi_callback, 10
        )
        
        # Subscriber: SSID name
        self.ssid_sub = self.create_subscription(
            String, '/wifi/ssid', self.ssid_callback, 10
        )
        
        # Publisher: RViz2 markers for heat map
        self.marker_pub = self.create_publisher(
            Marker, '/wifi/heatmap_markers', 10
        )
        
        # Data storage: list of (position, rssi, timestamp)
        self.rssi_history = []
        self.max_history = 100
        
        # Current SSID
        self.current_ssid = "Unknown"
        
        # Robot position (set via set_robot_position or from TF)
        self.last_position_x = 0.0
        self.last_position_y = 0.0
        
        # Marker ID counter
        self.marker_id_counter = 0
        
        self.get_logger().info('Wi-Fi Heat Map Overlay Node started')
    
    def ssid_callback(self, msg):
        """Update current SSID."""
        self.current_ssid = msg.data
        self.get_logger().info(f'Now tracking: {self.current_ssid}')
    
    def rssi_callback(self, msg):
        """Handle RSSI updates and publish heat map markers."""
        rssi = msg.data
        
        # Store in history with current position
        self.rssi_history.append({
            'x': self.last_position_x,
            'y': self.last_position_y,
            'rssi': rssi,
            'timestamp': self.get_clock().now().nanoseconds / 1e9
        })
        
        # Keep only recent history
        if len(self.rssi_history) > self.max_history:
            self.rssi_history = self.rssi_history[-self.max_history:]
        
        # Publish marker
        self.publish_wifi_marker(rssi)
    
    def set_robot_position(self, x, y):
        """Set robot's current position."""
        self.last_position_x = x
        self.last_position_y = y
    
    def publish_wifi_marker(self, rssi):
        """Publish RViz2 marker for Wi-Fi signal strength."""
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'wifi_heatmap'
        marker.id = self.marker_id_counter
        self.marker_id_counter = (self.marker_id_counter + 1) % 10000
        
        # Type: SPHERE for individual points
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        
        # Position at current robot location
        marker.pose.position.x = self.last_position_x
        marker.pose.position.y = self.last_position_y
        marker.pose.position.z = 0.1
        
        # Identity quaternion
        marker.pose.orientation.x = 0.0
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = 1.0
        
        # Scale based on signal strength
        size_base = 0.1
        size_variation = abs(rssi) / 100.0 * 0.05
        marker.scale.x = size_base + size_variation
        marker.scale.y = size_base + size_variation
        marker.scale.z = size_base + size_variation
        
        # Color based on RSSI (dBm): Green=strong, Yellow=medium, Red=weak
        if rssi > -50:
            marker.color = ColorRGBA(r=0.0, g=1.0, b=0.0, a=0.9)
        elif rssi > -70:
            marker.color = ColorRGBA(r=1.0, g=1.0, b=0.0, a=0.9)
        else:
            marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=0.9)
        
        self.marker_pub.publish(marker)
        
        # Also publish trail marker
        self.publish_trail_marker()
    
    def publish_trail_marker(self):
        """Publish a line strip showing the robot's path."""
        trail_marker = Marker()
        trail_marker.header.frame_id = 'map'
        trail_marker.header.stamp = self.get_clock().now().to_msg()
        trail_marker.ns = 'wifi_heatmap_trail'
        trail_marker.id = self.marker_id_counter
        self.marker_id_counter = (self.marker_id_counter + 1) % 10000
        
        trail_marker.type = Marker.LINE_STRIP
        trail_marker.action = Marker.ADD
        trail_marker.scale.x = 0.05
        
        # Build trail from recent history
        recent = self.rssi_history[-20:] if len(self.rssi_history) > 20 else self.rssi_history
        
        for point_data in recent:
            p = Point()
            p.x = point_data['x']
            p.y = point_data['y']
            p.z = 0.05
            trail_marker.points.append(p)
        
        # Set color based on latest RSSI
        if self.rssi_history:
            latest_rssi = self.rssi_history[-1]['rssi']
            if latest_rssi > -50:
                trail_marker.color = ColorRGBA(r=0.0, g=1.0, b=0.0, a=0.5)
            elif latest_rssi > -70:
                trail_marker.color = ColorRGBA(r=1.0, g=1.0, b=0.0, a=0.5)
            else:
                trail_marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=0.5)
        else:
            trail_marker.color = ColorRGBA(r=0.0, g=0.0, b=1.0, a=0.5)
        
        self.marker_pub.publish(trail_marker)
    
    def main(self):
        """Keep node running."""
        try:
            rclpy.spin(self)
        except KeyboardInterrupt:
            pass
        finally:
            self.destroy_node()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = WiFiMapOverlayNode()
    node.main()


if __name__ == '__main__':
    main()