import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_name = 'picar_description'
    model_name = 'picar_robot' # This matches the name in your 'create' node
    
    # 1. Declare Arguments
    declare_headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Whether to run Gazebo in headless mode (no GUI)'
    )
    headless_config = LaunchConfiguration('headless')

    # 2. Robot Description
    xacro_file = os.path.join(get_package_share_directory(pkg_name), 'urdf', 'picar_robot.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    params = {'robot_description': robot_description_config.toxml()}

    # 3. Nodes
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )

    node_joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen'
    )

    # 4. Gazebo Sim (Conditional with robust PythonExpression)
    # Gazebo WITH GUI
    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
        condition=UnlessCondition(PythonExpression(["'", headless_config, "' == 'true'"]))
    )

    # Gazebo HEADLESS
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={'gz_args': '-r -s empty.sdf'}.items(),
        condition=IfCondition(PythonExpression(["'", headless_config, "' == 'true'"]))
    )

    # 5. Spawn Entity
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', model_name, '-allow_renaming', 'true'],
        output='screen'
    )

    # 6. Bridge (Updated with model namespacing)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            f'/model/{model_name}/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            f'/model/{model_name}/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            f'/model/{model_name}/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
            f'/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock'
        ],
        output='screen'
    )

    return LaunchDescription([
        declare_headless_arg,
        node_robot_state_publisher,
        node_joint_state_publisher,
        gazebo_gui,
        gazebo_headless,
        spawn_entity,
        bridge,
    ])
