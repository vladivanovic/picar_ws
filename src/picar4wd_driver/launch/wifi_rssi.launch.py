#!/usr/bin/env python3
"""
Launch file for Wi-Fi RSSI node on Raspberry Pi.
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():

    # Start the Wi-Fi RSSI node on the Pi
    wifi_node = ExecuteProcess(
        cmd=['python3', '/home/vlad/picar_ws/src/picar4wd_driver/scripts/wifi_rssi_node.py'],
        output='screen',
        name='wifi_rssi_node'
    )
    
    return LaunchDescription([wifi_node])