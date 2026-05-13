cat << 'EOF' > ~/start_picar.sh
#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/picar_ws/install/setup.bash
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/picar-4wd
export ROS_DOMAIN_ID=42

ros2 launch picar4wd_driver picar_bringup.launch.py
EOF

chmod +x ~/start_picar.sh