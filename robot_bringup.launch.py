"""
Robot Hardware Bringup Launch File
Target: Real Picar Hardware Node

DEPRECATED: This launch file appears to be a placeholder or an outdated
bringup configuration. The active and correct bringup for the Raspberry Pi
is located at `picar_ws/src/picar4wd_driver/launch/picar_bringup.launch.py`.

This script launches the essential drivers and state publishers for the robot.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Use FindPackageShare for portability to find the URDF path
    picar_description_pkg = FindPackageShare('picar_description')
    urdf_path = PathJoinSubstitution([picar_description_pkg, 'urdf', 'picar_robot.urdf.xacro'])

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Set to true for simulation, false for real hardware",
        ),

        # 1. Robot State Publisher: Publishes the TF tree based on the URDF
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{
                "robot_description": Command(["xacro ", urdf_path]),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }],
        ),

        # 2. Hardware Bridge / Driver (PLACEHOLDER)
        # Replace 'agenticros_bringup' and 'cmd_vel_bridge' with your actual driver package/executable
        # NOTE: The actual motor driver is in picar_ws/src/picar4wd_driver/picar4wd_driver/motor_driver_node.py
        # and launched via picar_ws/src/picar4wd_driver/launch/picar_bringup.launch.py
        Node(
            package="agenticros_bringup", 
            executable="cmd_vel_bridge", # Example: the node that converts /cmd_vel to PWM
            name="picar_hardware_bridge",
            output="screen",
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),

        # 3. LiDAR Driver (PLACEHOLDER)
        # Example for RPLiDAR; adjust package/executable to your specific sensor
        # NOTE: The actual LiDAR driver is launched via picar_ws/src/picar4wd_driver/launch/picar_bringup.launch.py
        Node(
            package="rplidar_ros", 
            executable="rplidar_composition",
            name="lidar_node",
            output="screen",
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),
    ])
