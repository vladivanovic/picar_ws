"""
Control Node Bringup Launch File
Target: PC / Control Station
This script launches RViz2 and SLAM for mapping.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Attempt to find the pre-existing RViz config from the bringup package
    try:
        pkg = FindPackageShare("agenticros_bringup")
        default_rviz_cfg = PathJoinSubstitution([pkg, "rviz", "turtlebot3_agenticros.rviz"])
    except:
        default_rviz_cfg = "/home/vlad/.openclaw/workspace/ros2_ws/src/agenticros_bringup/rviz/turtlebot3_agenticros.rviz"

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Set to true for simulation, false for real hardware",
        ),

        # 1. RViz2: Visualization of Map, TF, and LaserScan
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", default_rviz_cfg],
            parameters=[
                {"use_sim_time": ParameterValue(LaunchConfiguration("use_sim_time"), value_type=bool)}
            ],
            output="screen",
        ),

        # 2. SLAM Toolbox: The mapping brain
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[{
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                # You can add specific SLAM parameters here (e.g. map resolution)
            }],
        ),
    ])
