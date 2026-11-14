import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'picar4wd_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vlad Ivanovic',
    maintainer_email='vladivanovic@gmail.com',
    description='ROS 2 drivers for the SunFounder PiCar-4WD: motor driver '
                'with cmd_vel watchdog, command odometry, sonar, and '
                'Wi-Fi RSSI / heat-map nodes.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_driver_node = picar4wd_driver.motor_driver_node:main',
            'sonar_node = picar4wd_driver.sonar_node:main',
            'odom_node = picar4wd_driver.odom_node:main',
            'wifi_rssi_node = picar4wd_driver.wifi_rssi_node:main',
            'wifi_map_overlay_node = picar4wd_driver.wifi_map_overlay_node:main',
        ],
    },
)
