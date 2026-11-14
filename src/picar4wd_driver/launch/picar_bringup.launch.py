"""Real-robot bringup for the Raspberry Pi.

Starts, all at once and with no artificial delays:
  * robot_state_publisher (URDF from picar_description)
  * RPLidar A1 (rplidar_ros) on /scan, frame lidar_link
  * motor_driver_node (subscribes cmd_vel -> /cmd_vel) with watchdog,
    publishing measured wheel-speed odometry + odom -> base_link TF
    (the speed sensors live in the same library/GPIO as the motors,
    and their unsigned readings need this node's power signs)
  * wifi_rssi_node (optional, include_wifi:=true by default)

Topic scheme: NO namespace. The motor driver listens on /cmd_vel, the
lidar publishes /scan, odometry is /odom. (An earlier design used a
picar_pi namespace; it was removed from this file in Aug 2026 while the
Orin-side bridge kept targeting /picar_pi/cmd_vel, which silently broke
the command chain. One scheme, everywhere, is the fix.)

There is deliberately no startup delay between lidar and motors: the
delays and respawn settings that used to be here were workarounds for
the lidar browning out on shared power. With the lidar on its own 5 V
supply (see README) they are unnecessary, and the motor watchdog makes
an early cmd_vel safe anyway. respawn stays available as a launch
argument for bench debugging, default off so lidar failures are loud.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    picar_description_pkg = FindPackageShare('picar_description')
    urdf_path = PathJoinSubstitution(
        [picar_description_pkg, 'urdf', 'picar_robot.urdf.xacro'])

    return LaunchDescription([
        DeclareLaunchArgument(
            'serial_port', default_value='/dev/rplidar',
            description='Lidar serial device (udev symlink; see udev/99-rplidar.rules)'),
        DeclareLaunchArgument(
            'lidar_respawn', default_value='false',
            description='Respawn the lidar node if it exits (bench debugging only)'),
        DeclareLaunchArgument(
            'include_wifi', default_value='true',
            description='Also run the Wi-Fi RSSI node'),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': Command(['xacro ', urdf_path]),
                'use_sim_time': False,
            }],
        ),

        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='screen',
            respawn=LaunchConfiguration('lidar_respawn'),
            respawn_delay=2.0,
            parameters=[{
                'channel_type': 'serial',
                'serial_port': LaunchConfiguration('serial_port'),
                'serial_baudrate': 115200,  # RPLidar A1
                'frame_id': 'lidar_link',
                'inverted': False,
                'angle_compensate': True,
            }],
        ),

        Node(
            package='picar4wd_driver',
            executable='motor_driver_node',
            name='motor_driver_node',
            output='screen',
            parameters=[{
                'max_speed': 50,
                'cmd_timeout': 0.5,
                'track_width': 0.14,
                # Measured odometry from the rear wheel speed sensors.
                # effective_track_width is the SKID-STEER value, larger
                # than the geometric 0.14 m -- calibrate it (README:
                # "Skid steering and odometry") and put the result here.
                'publish_odom': True,
                'effective_track_width': 0.14,
            }],
        ),

        Node(
            package='picar4wd_driver',
            executable='wifi_rssi_node',
            name='wifi_rssi_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('include_wifi')),
        ),
    ])
