"""
Robot Hardware Bringup Launch File
Target: Real Picar Hardware Node
This script launches the essential drivers and state publishers for the robot.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # Path to the URDF we just fixed in the workspace
    urdf_path = "/home/vlad/.openclaw/workspace/ros2_ws/src/agenticros_sim/urdf/picar_robot.urdf.xacro"

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
        # Replace 'agenticros_bringup' and 'picar_hardware_bridge' with your actual driver package/executable
        Node(
            package="agenticros_bringup", 
            executable="cmd_vel_bridge", # Example: the node that converts /cmd_vel to PWM
            name="picar_hardware_bridge",
            output="screen",
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),

        # 3. LiDAR Driver (PLACEHOLDER)
        # Example for RPLiDAR; adjust package/executable to your specific sensor
        Node(
            package="rplidar_ros", 
            executable="rplidar_composition",
            name="lidar_node",
            output="screen",
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),
    ])
