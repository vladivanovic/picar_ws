#!/usr/bin/env python3
"""Gazebo simulation only (TurtleBot3 world) -- no real hardware.

This file previously crashed immediately: it used
IncludeLaunchDescription, PythonLaunchDescriptionSource and Command
without importing them, built SetEnvironmentVariable actions as
throwaway tuples that were never launched (so the ROS domain was never
set, and defaulted to 0 while the rest of the project uses 42), and
contained a real RPLidar node in a file promising "no real hardware".

For simulating the PiCar itself, prefer:
    ros2 launch agenticros_sim sim_picar.launch.py
This launch remains for the TurtleBot3/AgenticROS experiments.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def generate_launch_description():
    ros_domain_id = LaunchConfiguration('ros_domain_id')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('agenticros_bringup'),
                'launch',
                'gazebo_turtlebot3.launch.py'
            ])
        ),
        launch_arguments={
            'turtlebot3_model': 'burger',
        }.items()
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('agenticros_bringup'),
            'rviz',
            'simulation.rviz'
        ])],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'ros_domain_id', default_value='42',
            description='ROS 2 domain (matches the rest of the PiCar project)'),
        SetEnvironmentVariable(name='ROS_DOMAIN_ID', value=ros_domain_id),
        SetEnvironmentVariable(name='GZ_SIM_RENDERER', value='ogre'),
        gazebo,
        rviz,
    ])
