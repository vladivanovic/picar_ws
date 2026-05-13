#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import picar_4wd as fc

class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver_node')
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.get_logger().info('Motor driver node started')

        self.declare_parameter('max_speed', 50)
        self.max_speed = self.get_parameter('max_speed').value

    def cmd_vel_callback(self, msg):
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        left_speed = int((linear_x + angular_z) * self.max_speed)
        right_speed = int((linear_x - angular_z) * self.max_speed)

        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))

        if linear_x == 0 and angular_z == 0:
            fc.stop()
        else:
            fc.left_front.set_power(left_speed)
            fc.left_rear.set_power(left_speed)
            fc.right_front.set_power(right_speed)
            fc.right_rear.set_power(right_speed)

    def destroy_node(self):
        fc.stop()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
