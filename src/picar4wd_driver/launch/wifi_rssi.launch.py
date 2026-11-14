"""Launch just the Wi-Fi RSSI node (Pi), e.g. for bench testing."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'interface', default_value='wlan0',
            description='Wi-Fi interface to report on'),
        Node(
            package='picar4wd_driver',
            executable='wifi_rssi_node',
            name='wifi_rssi_node',
            output='screen',
            parameters=[{'interface': LaunchConfiguration('interface')}],
        ),
    ])
