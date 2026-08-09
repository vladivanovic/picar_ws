from launch import LaunchDescription
from launch.actions import TimerAction
from launch.actions.group import GroupAction
from launch.actions.namespace import Namespace
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Path to the URDF file
    picar_description_pkg = FindPackageShare('picar_description')
    urdf_path = PathJoinSubstitution([picar_description_pkg, 'urdf', 'picar_robot.urdf.xacro'])

    return LaunchDescription([
        # Robot State Publisher: Publishes the TF tree based on the URDF
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{
                "robot_description": Command(["xacro ", urdf_path]),
                "use_sim_time": False,
            }],
        ),

        # RPLiDAR A1 — start FIRST, let it stabilize
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='screen',
            parameters=[{
                'serial_port': '/dev/rplidar',  # Consider creating a udev rule (e.g., in /etc/udev/rules.d/99-rplidar.rules) to consistently map the LiDAR to this path and set permissions.
                'frame_id': 'lidar_link',
                'angle_compensate': True,
            }],
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
                # Sonar scanner node (disabled)
                # Node(
                #     package='picar4wd_driver',
                #     executable='sonar_node',
                #     name='sonar_scanner_node',
                #     output='screen',
                #     parameters=[
                #         {'angle_min': -60.0},
                #         {'angle_max': 60.0},
                #         {'angle_step': 10.0},
                #         {'max_range': 3.0},
                #         {'scan_rate': 1.0},
                #     ]
                # ),
            ]
        ),
    ])