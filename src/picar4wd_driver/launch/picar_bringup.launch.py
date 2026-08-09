from launch import LaunchDescription
from launch.actions import TimerAction, GroupAction
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import Command, PathJoinSubstitution
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

        # Hardware drivers wrapped in picar_pi namespace
        GroupAction([
            PushRosNamespace('picar_pi'),
            # 1. Start LiDAR FIRST
            Node(
                package='rplidar_ros',
                executable='rplidar_composition',
                name='rplidar_node',
                output='screen',
                respawn=True,
                respawn_delay=2.0,
                parameters=[{
                    'serial_port': '/dev/rplidar',
                    'frame_id': 'lidar_link',
                    'angle_compensate': True,
                }],
            ),
            # 2. Wait 10 seconds for LiDAR to lock and stabilize
            TimerAction(
                period=10.0,
                actions=[
                    # 3. Start motors AFTER LiDAR is already running
                    Node(
                        package='picar4wd_driver',
                        executable='motor_driver_node',
                        name='motor_driver_node',
                        output='screen',
                        parameters=[{'max_speed': 50}],
                    ),
                ],
            ),
        ]),
    ])