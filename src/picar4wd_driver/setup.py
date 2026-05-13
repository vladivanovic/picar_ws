import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'picar4wd_driver'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='ROS2 driver for Sunfounder PiCar-4WD',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_driver_node = picar4wd_driver.motor_driver_node:main',
            'sonar_node = picar4wd_driver.sonar_node:main',
            'odom_node = picar4wd_driver.odom_node:main',
        ],
    },
)
