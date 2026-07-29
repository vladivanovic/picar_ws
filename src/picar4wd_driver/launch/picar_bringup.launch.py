from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from launch.actions.group import GroupAction
from launch.actions.namespace import Namespace

def generate_launch_description():
    return LaunchDescription([
        # RPLiDAR A1 — start FIRST, let it stabilize
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='screen',
            parameters=[{
                'serial_port': '/dev/rplidar',
                'frame_id': 'lidar_link',
                'angle_compensate': True,
            }],
        ),

        # Static TF: base_link -> lidar_link
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_tf',
            arguments=['-0.05', '0', '0.10', '0', '0', '0', 'base_link', 'lidar_link'],
        ),

        # Hardware drivers wrapped in picar_pi namespace
        Namespace(
            namespace='picar_pi',
            actions=[
                # Motor driver — delayed to avoid current spike conflict
                TimerAction(
                    period=10.0,
                    actions=[
                        Node(
                            package='picar4wd_driver',
                            executable='motor_driver_node',
                            name='motor_driver_node',
                            output='screen',
                            parameters=[{'max_speed': 50}],
                        ),
                    ],
                ),
            ]
        ),
    ])