import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class SquareDriver(Node):
    def __init__(self):
        super().__init__('square_driver')

        self.pub = self.create_publisher(
            Twist, '/model/vehicle_blue/cmd_vel', 10)

        self.sub = self.create_subscription(
            Odometry, '/model/vehicle_blue/odometry',
            self.odom_callback, 10)

        self.x = None
        self.y = None
        self.yaw = None
        self.phase = 0
        self.count = 0
        self.start_x = None
        self.start_y = None
        self.start_yaw = None

        self.timer = self.create_timer(0.1, self.control)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        self.yaw = math.atan2(
            2 * (q.w * q.z + q.x * q.y),
            1 - 2 * (q.y * q.y + q.z * q.z))

    def control(self):
        if self.yaw is None or self.phase == 2:
            return

        if self.start_x is None:
            self.start_x = self.x
            self.start_y = self.y
            self.start_yaw = self.yaw
            self.get_logger().info('Starting square movement')

        cmd = Twist()

        if self.phase == 0:
            distance = math.hypot(
                self.x - self.start_x,
                self.y - self.start_y)

            if distance < 0.5:
                cmd.linear.x = 0.15
            else:
                self.phase = 1
                self.start_yaw = self.yaw

        elif self.phase == 1:
            target = self.start_yaw + math.pi / 2
            error = math.atan2(
                math.sin(target - self.yaw),
                math.cos(target - self.yaw))

            if abs(error) > 0.05:
                cmd.angular.z = 0.3 if error > 0 else -0.3
            else:
                self.count += 1
                self.get_logger().info(
                    f'Turn {self.count}/4 completed')

                if self.count >= 4:
                    self.phase = 2
                    self.get_logger().info('Square movement completed')
                else:
                    self.start_x = self.x
                    self.start_y = self.y
                    self.phase = 0

        self.pub.publish(cmd)

    def destroy_node(self):
        self.pub.publish(Twist())
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
