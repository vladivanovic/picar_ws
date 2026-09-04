#!/usr/bin/env python3
"""
Wi-Fi RSSI Signal Tracking Node for Raspberry Pi.
Tracks the currently connected SSID's signal strength and publishes it via ROS2.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
import subprocess
import re

class WiFiRSSINode(Node):
    def __init__(self):
        super().__init__('wifi_rssi_node')
        
        # Publisher: Wi-Fi signal strength (dBm)
        self.rssi_pub = self.create_publisher(Int32, '/wifi/rssi', 10)
        
        # Publisher: SSID name
        self.ssid_pub = self.create_publisher(String, '/wifi/ssid', 10)
        
        # Publisher: connection status
        self.status_pub = self.create_publisher(String, '/wifi/status', 10)
        
        # Timer: scan every 2 seconds
        self.timer = self.create_timer(2.0, self.scan_wifi)
        
        # State tracking
        self.current_ssid = "Unknown"
        self.current_rssi = 0
        self.connected = False
        
        self.get_logger().info('Wi-Fi RSSI Node started - tracking connected SSID')
    
    def scan_wifi(self):
        """Scan Wi-Fi and find the currently connected SSID's signal strength."""
        try:
            # Method 1: Use iwconfig (most compatible)
            result = subprocess.run(
                ['iwconfig', '2>/dev/null'], 
                capture_output=True, text=True, timeout=5
            )
            
            # Check if wlan0 exists and is connected
            if 'wlan0' in result.stdout or 'wlan1' in result.stdout:
                self._parse_iwconfig(result.stdout)
            else:
                # Try alternative: wpa_cli
                self._parse_wpa_cli()
                
        except Exception as e:
            self.get_logger().warn(f'Wi-Fi scan error: {e}')
        
        # Always publish current state
        self._publish_state()
    
    def _parse_iwconfig(self, output):
        """Parse iwconfig output for connected SSID and signal."""
        lines = output.split('\n')
        
        for line in lines:
            # Look for ESSID (connected network)
            if 'ESSID:' in line:
                match = re.search(r'ESSID:"([^"]*)"', line)
                if match:
                    self.current_ssid = match.group(1)
                    self.get_logger().info(f'Connected to: {self.current_ssid}')
            
            # Look for Signal level
            if 'Signal level' in line or 'Signal=' in line:
                # Parse signal strength (typically in dBm)
                # Pattern: "Signal level=-50/70" or similar
                match = re.search(r'Signal\s*level\s*=\s*(-?\d+)/', line)
                if match:
                    self.current_rssi = int(match.group(1))
                else:
                    # Alternative: "Signal=-50"
                    match = re.search(r'Signal=(-?\d+)', line)
                    if match:
                        self.current_rssi = int(match.group(1))
            
            # Look for link quality
            if 'Link Quality' in line:
                match = re.search(r'Link Quality:(\d+)/(\d+)', line)
                if match:
                    quality = int(match.group(1))
                    max_quality = int(match.group(2))
                    # Approximate conversion to dBm
                    self.current_rssi = int(quality * 100 / max_quality) - 100
        
        # If we couldn't parse signal, try wpa_cli
        if self.current_rssi == 0 and self.current_ssid != "Unknown":
            self._try_wpa_cli_signal()
    
    def _try_wpa_cli_signal(self):
        """Try wpa_cli for signal strength."""
        try:
            result = subprocess.run(
                ['wpa_cli', 'status', '2>/dev/null'],
                capture_output=True, text=True, timeout=5
            )
            if 'ssid' in result.stdout:
                # Parse signal
                for line in result.stdout.split('\n'):
                    if 'signal' in line.lower():
                        match = re.search(r'signal=(-?\d+)', line)
                        if match:
                            self.current_rssi = int(match.group(1))
        except Exception:
            pass
    
    def _parse_wpa_cli(self):
        """Parse wpa_cli output when iwconfig not available."""
        try:
            result = subprocess.run(
                ['wpa_cli', 'status', '2>/dev/null'],
                capture_output=True, text=True, timeout=5
            )
            
            if 'ssid=' in result.stdout:
                # Extract SSID
                for line in result.stdout.split('\n'):
                    if line.startswith('ssid:'):
                        self.current_ssid = line.split(':', 1)[1].strip()
                
                # Extract signal
                for line in result.stdout.split('\n'):
                    if 'signal=' in line.lower():
                        match = re.search(r'signal=(-?\d+)', line)
                        if match:
                            self.current_rssi = int(match.group(1))
        except Exception:
            pass
    
    def _publish_state(self):
        """Publish current Wi-Fi state as ROS2 messages."""
        # Publish SSID
        ssid_msg = String()
        ssid_msg.data = self.current_ssid
        self.ssid_pub.publish(ssid_msg)
        
        # Publish RSSI (signal strength in dBm)
        rssi_msg = Int32()
        rssi_msg.data = self.current_rssi
        self.rssi_pub.publish(rssi_msg)
        
        # Publish status
        status_msg = String()
        if self.connected and self.current_ssid != "Unknown":
            status_msg.data = f"Connected to {self.current_ssid} (RSSI: {self.current_rssi} dBm)"
        else:
            status_msg.data = "Scanning for Wi-Fi..."
        self.status_pub.publish(status_msg)
    
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
    node = WiFiRSSINode()
    node.main()


if __name__ == '__main__':
    main()