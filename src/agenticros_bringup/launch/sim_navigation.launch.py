#!/usr/bin/env python3
"""
Simulation Navigation Stack (Nav2) - Test path planning in Gazebo
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('nav2_bringup'),
                    'launch',
                    'navigation_launch.py'
                ])
            ),
            launch_arguments={
                'use_sim_time': 'true',
                'autostart': 'true',
                'params_file': PathJoinSubstitution([
                    FindPackageShare('picar4wd_driver'),
                    'config',
                    'nav2_params.yaml'
                ]),
            }.items()
        )
    ])