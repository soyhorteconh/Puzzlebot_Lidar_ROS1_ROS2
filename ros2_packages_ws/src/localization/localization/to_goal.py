#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import numpy as np
import copy
from geometry_msgs.msg import Pose
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from sensor_msgs.msg import LaserScan

import math
import time
import sys
sys.path.append('/home/puzzlebot/ros2_packages_ws/src/localization/localization/')
from class_controller import Controller
from class_bug0 import Bug0


def euler_from_quaternion(x, y, z, w):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        # t0 = +2.0 * (w * x + y * z)
        # t1 = +1.0 - 2.0 * (x * x + y * y)
        # roll_x = math.atan2(t0, t1)
     
        # t2 = +2.0 * (w * y - z * x)
        # t2 = +1.0 if t2 > +1.0 else t2
        # t2 = -1.0 if t2 < -1.0 else t2
        # pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
     
        return yaw_z # in radians

class ToGoalNode(Node):
    def __init__(self):
        super().__init__("toGoalNode")

        self.x_d = 0
        self.y_d = 0
        self.theta_d = 0
        self.x_pose = 0
        self.y_pose = 0
        self.theta_pose = 0
        self.x_pose_prev = 0
        self.y_pose_prev = 0
        self.theta_pose_prev = 0
        self.wl = 0.0
        self.wr = 0.0
        self.prev_distance = 10000
        self.ranges = []
        self.flag_set_point = False
        self.cmd_vel_msg = Twist()
        self.controller = Controller()
        self.bug0 = Bug0()
        self.controller_flag = True
        self.state = 'controller'
        self.lidar_flag = False

        print("Running To Goal Node")

        self.sub_odom = self.create_subscription(Odometry, "/odom", self.odom_cb ,10)   
        self.sub_scan = self.create_subscription(LaserScan, "/scan", self.scan_cb, 10) 
        self.sub_set_point = self.create_subscription(Pose, "/set_point", self.setPoint_cb, 10)   

        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel",1)

        self.start_time = self.get_clock().now()
        timer_period = 1/10  # seconds
        self.timer = self.create_timer(timer_period, self.run)


    def odom_cb(self, msg):

        self.x_pose_prev = self.x_pose
        self.y_pose_prev = self.y_pose
        self.theta_pose_prev = self.theta_pose

        self.x_pose = msg.pose.pose.position.x
        self.y_pose = msg.pose.pose.position.y
        self.theta_pose = euler_from_quaternion(msg.pose.pose.orientation.x,msg.pose.pose.orientation.y,
                                                msg.pose.pose.orientation.z,msg.pose.pose.orientation.w)

        self.bug0.pos_x = self.x_pose
        self.bug0.pos_y = self.y_pose
        self.bug0.pos_theta = self.theta_pose
        
        self.controller.x_pose = self.x_pose
        self.controller.y_pose = self.y_pose
        self.controller.theta_pose = self.theta_pose

    def calculate_dt(self):
        self.current_time = self.start_time
        self.duration = self.get_clock().now() - self.start_time
        self.dt = self.duration.nanoseconds * 1e-9

    def scan_cb(self, msg):
        self.ranges = msg.ranges
        self.lidar_flag = True

    def setPoint_cb(self, msg):
        self.x_d = msg.position.x
        self.y_d = msg.position.y

        self.bug0.goal_x = self.x_d
        self.bug0.goal_y = self.y_d
        
        self.controller.x_d = self.x_d
        self.controller.y_d = self.y_d

        self.flag_set_point = True

    def stop(self):
        # while ((abs(self.x_pose - self.x_pose_prev) > 0.064) or (abs(self.y_pose - self.y_pose_prev) > 0.064)
        #         or (abs(self.theta_pose - self.theta_pose_prev) > 0.064)):
        self.cmd_vel_msg.linear.x = 0.0
        self.cmd_vel_msg.angular.z = 0.0
        self.cmd_vel_pub.publish(self.cmd_vel_msg)
        print("stoping")

    def update_velocities_bug0(self):
        self.cmd_vel_msg.linear.x = self.bug0.linear_v
        self.cmd_vel_msg.angular.z = self.bug0.angular_v

        self.cmd_vel_pub.publish(self.cmd_vel_msg)

    def check_wall(self):
        for i in range(0,2):
            if (self.ranges[i] <= 0.45):
                self.stop()
                time.sleep(1)
                return True
        for i in range(1078,1080):
            if (self.ranges[i] <= 0.45):
                self.stop()
                time.sleep(1)
                return True
        return False
    
    def turn(self):
        self.cmd_vel_msg.linear.x = 0.0
        self.cmd_vel_msg.angular.z = 0.5
        self.cmd_vel_pub.publish(self.cmd_vel_msg)
        self.state = 'follow_wall'

    def follow_wall(self):
        self.bug0.calculate_angular_e()
        print(self.bug0.theta_e)
        self.bug0.real_dist = self.ranges[810]
        # print("Enfrente en wall", self.ranges[0])
        # print("A lado en wall", self.ranges[810])
        if (abs(self.bug0.theta_e) < 0.25):
            self.state = 'controller'
        else:
            self.bug0.distance_controller(self.dt)
            self.update_velocities_bug0()

    def controller_alg(self):
        self.controller.update_vel(self.dt)
        self.cmd_vel_msg = self.controller.cmd_vel_msg
        self.cmd_vel_pub.publish(self.cmd_vel_msg)

    def run(self):
        if self.lidar_flag:
            # print("Enfrente en run ", self.ranges[0])
            # print("A lado en run ", self.ranges[810])
            self.calculate_dt()
            if self.check_wall():
                self.state = 'turn'
            print(self.state)

            if (self.state == 'turn'):
                self.turn()
                time.sleep(0.5)
                self.stop()
                time.sleep(1)
            elif(self.state == 'follow_wall'):
                self.follow_wall()
            elif(self.state == 'controller'):
                self.controller_alg()

            self.start_time = self.get_clock().now()
            self.lidar_flag = False
        

    
def main():
    rclpy.init()
    to_goal_node = ToGoalNode()
    rclpy.spin(to_goal_node)
    to_goal_node.destroy_node()
    rclpy.shutdown()
