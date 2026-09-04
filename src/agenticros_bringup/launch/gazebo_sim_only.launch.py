#!/usr/bin/env python3
"""
Gazebo Simulation Only - No real hardware.
Use for testing navigation, SLAM, and control algorithms.
Power: Wall power for Orin only. No Pi, no Picar hat, no motors.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
import os

def generate_launch_description():

    # --- ROS 2 Domain Configuration ---
    ros_domain_id = LaunchConfiguration('ros_domain_id')
    
    SetEnvironmentVariable(
        name='ROS_DOMAIN_ID',
        value=ros_domain_id
    ),
    
    DeclareLaunchArgument(
        'ros_domain_id',
        default_value='0',
        description='ROS 2 Domain ID for simulation'
    ),
    
    # --- Gazebo Simulation Setup ---
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('agenticros_bringup'),
                'launch',
                'gazebo_turtlebot3.launch.py'
            ])
        ),
        launch_arguments={
            'ros_domain_id': ros_domain_id,
            'turtlebot3_model': 'burger'  # smaller model for faster simulation
        }.items()
    ),
    
    # --- Robot State Publisher (URDF in simulation) ---
    # Use the same URDF but with use_sim_time=true
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', PathJoinSubstitution([
                FindPackageShare('picar_description'),
                'urdf', 'picar_robot.urdf.xacro'
            ])]),
            'use_sim_time': True,
        }],
    ),
    
    # --- Joint State Publisher ---
    # For the continuous wheel joints in your URDF
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        output='screen',
    ),
    
    # --- RPLidar in Simulation ---
    # Option: Use real RPLidar A1 if connected, or Gazebo simulation
    # Here we'll try to use the rplidar_ros package
    # If LiDAR not connected, Gazebo will use its own plugins
    rplidar_node = Node(
        package='rplidar_ros',
        executable='rplidar_composition',
        name='rplidar_node',
        output='screen',
        parameters=[{
            'serial_port': '/dev/rplidar',
            'frame_id': 'laser_link',
            'angle_compensate': True,
        }],
        # This will fail gracefully if no LiDAR hardware connected
        # In that case, Gazebo's built-in plugins will provide simulated scans
    ),
    
    # --- RViz2 for Visualization ---
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
    ),
    
    # --- Optional: Navigation Stack (Nav2) for simulation testing ---
    # Uncomment to test path planning in simulation
    # nav2 = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(
    #         PathJoinSubstitution([
    #             FindPackageShare('nav2_bringup'),
    #             'launch',
    #             'navigation_launch.py'
    #         ])
    #     ),
    #     launch_arguments={
    #         'use_sim_time': 'true',
    #         'autostart': 'true',
    #     }.items()
    # ),
    
    return LaunchDescription([
        # Set up Gazebo rendering and physics
        SetEnvironmentVariable(
            name='GZ_SIM_RENDERER',
            value='ogre'
        ),
        SetEnvironmentVariable(
            name='GZ_SIM_PHYSICS_ENGINE',
            value='dart'
        ),
        
        # Launch arguments
        ros_domain_id,
        gazebo,
        robot_state_publisher,
        joint_state_publisher,
        # rplidar_node,  # Comment out if no real LiDAR hardware
        rviz,
        # Uncomment below to enable Nav2 in simulation:
        # nav2,
    ])