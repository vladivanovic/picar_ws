#!/usr/bin/env python3
"""Wi-Fi RSSI tracking node (runs on the Raspberry Pi).

Publishes, every ``period`` seconds (default 2):
  /wifi/rssi    (std_msgs/Int32)  signal strength in dBm (negative)
  /wifi/ssid    (std_msgs/String) connected SSID, "" when not connected
  /wifi/bssid   (std_msgs/String) AP radio we're associated with -- in a
                                  multi-AP / mesh home the same SSID is
                                  several radios, and a survey needs to
                                  know which one each sample came from
                                  (it also reveals roaming as the car moves)
  /wifi/freq    (std_msgs/Int32)  channel centre frequency, MHz
                                  (e.g. 2437 = 2.4 GHz ch 6, 5180 = 5 GHz)
  /wifi/status  (std_msgs/String) human-readable status

Source of truth is ``iw dev <interface> link`` with a /proc/net/wireless
fallback for RSSI. This replaces the previous version, which passed a
literal '2>/dev/null' string as an argument to iwconfig/wpa_cli, looked
for 'ssid:' lines in output that uses 'ssid=', and never set its
connected flag, so /wifi/status always said "Scanning...".
"""

import subprocess

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String  # noqa: F401

from picar4wd_driver.wifi_parsing import parse_iw_link, parse_proc_wireless


class WiFiRSSINode(Node):
    def __init__(self):
        super().__init__('wifi_rssi_node')

        self.declare_parameter('interface', 'wlan0')
        self.declare_parameter('period', 2.0)
        self.interface = self.get_parameter('interface').value
        period = float(self.get_parameter('period').value)

        self.rssi_pub = self.create_publisher(Int32, '/wifi/rssi', 10)
        self.ssid_pub = self.create_publisher(String, '/wifi/ssid', 10)
        self.bssid_pub = self.create_publisher(String, '/wifi/bssid', 10)
        self.freq_pub = self.create_publisher(Int32, '/wifi/freq', 10)
        self.status_pub = self.create_publisher(String, '/wifi/status', 10)

        self._last_ssid = None
        self.timer = self.create_timer(period, self.scan_wifi)
        self.get_logger().info(
            'Wi-Fi RSSI node started on interface %s' % self.interface)

    def _read_link(self):
        # Primary: iw (arguments as a list -- no shell, so no shell
        # redirection tricks; nothing like '2>/dev/null' belongs here).
        try:
            result = subprocess.run(
                ['iw', 'dev', self.interface, 'link'],
                capture_output=True, text=True, timeout=5)
            link = parse_iw_link(result.stdout)
            if link.connected:
                return link
        except (OSError, subprocess.SubprocessError) as e:
            self.get_logger().warn('iw failed (%s); trying fallback' % e)
        # Fallback: /proc/net/wireless has RSSI but no SSID.
        try:
            with open('/proc/net/wireless') as f:
                link = parse_proc_wireless(f.read(), self.interface)
            link.ssid = self._last_ssid  # keep last known SSID
            return link
        except OSError:
            return parse_iw_link('')

    def scan_wifi(self):
        link = self._read_link()
        if link.ssid:
            self._last_ssid = link.ssid

        ssid_msg = String()
        ssid_msg.data = link.ssid or ''
        self.ssid_pub.publish(ssid_msg)

        bssid_msg = String()
        bssid_msg.data = link.bssid or ''
        self.bssid_pub.publish(bssid_msg)

        if link.freq_mhz is not None:
            freq_msg = Int32()
            freq_msg.data = link.freq_mhz
            self.freq_pub.publish(freq_msg)

        if link.rssi_dbm is not None:
            rssi_msg = Int32()
            rssi_msg.data = link.rssi_dbm
            self.rssi_pub.publish(rssi_msg)

        status_msg = String()
        if link.connected and link.rssi_dbm is not None:
            status_msg.data = 'Connected to %s via %s (RSSI: %d dBm)' % (
                link.ssid, link.bssid or '?', link.rssi_dbm)
        elif link.connected:
            status_msg.data = 'Connected to %s (RSSI unknown)' % link.ssid
        elif link.rssi_dbm is not None:
            status_msg.data = 'Interface up, SSID unknown (RSSI: %d dBm)' % link.rssi_dbm
        else:
            status_msg.data = 'Not connected'
        self.status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = WiFiRSSINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
