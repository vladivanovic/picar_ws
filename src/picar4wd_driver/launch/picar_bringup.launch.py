from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Motor driver node
        Node(
            package='picar4wd_driver',
            executable='motor_driver_node',
            name='motor_driver_node',
            output='screen',
            parameters=[{'max_speed': 50}],
        ),

        # Sonar scanner node
        Node(
            package='picar4wd_driver',
            executable='sonar_node',
            name='sonar_scanner_node',
            output='screen',
            parameters=[{
                'angle_min': -60.0,
                'angle_max': 60.0,
                'angle_step': 10.0,
                'max_range': 3.0,
                'scan_rate': 1.0,
            }],
        ),

        # Odometry node
        Node(
            package='picar4wd_driver',
            executable='odom_node',
            name='odometry_node',
            output='screen',
        ),

        # Static TF: base_link -> sonar_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_sonar_tf',
            arguments=['0.08', '0', '0.05', '0', '0', '0', 'base_link', 'sonar_link'],
        ),
    ])
