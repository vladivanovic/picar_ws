#!/usr/bin/env python3
"""Command-based odometry for the PiCar-4WD.

There are no wheel encoders on this car, so this node dead-reckons the
pose by integrating the ``cmd_vel`` stream. That is *commanded* motion,
not measured motion: wheel slip, a stalled motor, or picking the car up
all produce confident-looking movement. Treat the output as an aid for
SLAM scan matching, never as ground truth.

It publishes:
  * ``odom`` (nav_msgs/Odometry) with deliberately honest (large)
    covariances, and
  * the ``odom -> base_link`` TF, which slam_toolbox/Nav2 require.
    (slam_toolbox provides ``map -> odom``; it does not provide this one.
    An earlier version of this node had the TF broadcast commented out
    on that mistaken assumption, which broke the TF tree.)

Run this node on the Pi, next to the motor driver, so it integrates the
same command stream the motors actually receive -- not a copy relayed
back across Wi-Fi from the control unit.
"""

import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped
from tf2_ros import TransformBroadcaster


class OdometryNode(Node):
    def __init__(self):
        super().__init__('odometry_node')

        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_vel_callback, 10)

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.linear_vel = 0.0
        self.angular_vel = 0.0
        self.last_time = self.get_clock().now()

        self.timer = self.create_timer(0.05, self.publish_odom)
        self.get_logger().info(
            'Odometry node started (command dead-reckoning; TF %s -> %s)'
            % (self.odom_frame, self.base_frame))

    def cmd_vel_callback(self, msg):
        self.linear_vel = msg.linear.x
        self.angular_vel = msg.angular.z

    def publish_odom(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        if dt <= 0.0 or dt > 1.0:
            dt = 0.0  # clock jump / first tick: don't integrate a huge step

        # Exact arc integration (better than Euler for turning in place).
        if abs(self.angular_vel) < 1e-6:
            self.x += self.linear_vel * math.cos(self.theta) * dt
            self.y += self.linear_vel * math.sin(self.theta) * dt
        else:
            radius = self.linear_vel / self.angular_vel
            self.x += radius * (math.sin(self.theta + self.angular_vel * dt)
                                - math.sin(self.theta))
            self.y += radius * (-math.cos(self.theta + self.angular_vel * dt)
                                + math.cos(self.theta))
        self.theta += self.angular_vel * dt

        qz = math.sin(self.theta / 2.0)
        qw = math.cos(self.theta / 2.0)

        # TF: odom -> base_link (required by slam_toolbox and Nav2).
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.linear_vel
        odom.twist.twist.angular.z = self.angular_vel

        # Honest covariances for unmeasured, integrated commands:
        # x/y/yaw are guesses that drift, so they get large variances
        # instead of the all-zero "this pose is exact" default.
        pose_cov = [0.0] * 36
        pose_cov[0] = 0.25    # x variance (m^2)
        pose_cov[7] = 0.25    # y
        pose_cov[14] = 1e6    # z unused on a ground robot
        pose_cov[21] = 1e6    # roll unused
        pose_cov[28] = 1e6    # pitch unused
        pose_cov[35] = 0.5    # yaw variance (rad^2)
        odom.pose.covariance = pose_cov
        twist_cov = [0.0] * 36
        twist_cov[0] = 0.1
        twist_cov[35] = 0.2
        odom.twist.covariance = twist_cov

        self.odom_publisher.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
