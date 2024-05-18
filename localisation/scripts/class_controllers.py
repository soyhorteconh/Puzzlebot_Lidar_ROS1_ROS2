#!/usr/bin/env python3
import rospy
import numpy as np
from geometry_msgs.msg import Pose
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import math

class Controller():
    def __init__(self):
        try:
            #rospy.init_node('controller_node')
            self.x_d = 0
            self.y_d = 0
            self.theta_d = 0
            self.x_pose = 0
            self.y_pose = 0
            self.theta_pose = 0

            self.linear_e = 0
            self.prev_linear_e = 0
            self.angular_e = 0
            self.prev_angular_e = 0
            self.integral_e_linear = 0
            self.integral_e_angular = 0
            self.x_e = 0
            self.y_e = 0

            self.kp_l = 0.9
            self.ki_l = 0.0
            self.kd_l = 0.0

            self.kp_w = 1.5
            self.ki_w = 0
            self.kd_w = 0

            self.cmd_vel_msg = Twist()
        
            #print("The control node is Running")
            #self.pub_cmd_vel = rospy.Publisher('/cmd_vel',Twist, queue_size = 10)
            #self.odom_sub = rospy.Subscriber('/odom',Odometry ,self.pose_update)
            #self.set_point_sub = rospy.Subscriber('/set_point', Pose,self.set_point_update)
            #self.start_time = rospy.get_time()
            #timer_period = 1/10  # seconds
            #self.timer = rospy.Timer(rospy.Duration(timer_period), self.update_vel)
        except Exception as e:
            pass
            #rospy.logerr("Error during initialization: %s", e)

    def calculate_lineal_e(self):
        self.prev_linear_e = self.linear_e
        self.y_e = self.y_d - self.y_pose
        self.x_e = self.x_d - self.x_pose
        self.linear_e = np.sqrt(self.x_e**2 + self.y_e**2)
        print(self.linear_e)
        if(abs(self.linear_e) < 0.07):
            self.linear_e = 0.0

    def calculate_angular_e(self):
        self.prev_angular_e = self.angular_e
        self.theta_d = math.atan2(self.y_e,self.x_e)
        self.angular_e = self.theta_d - self.theta_pose
        print(self.angular_e)
        if(abs(self.angular_e) <= 0.07):
            self.angular_e = 0.0
    
    def calculate_errors(self):
        self.calculate_lineal_e()
        self.calculate_angular_e()

    def lineal_controller(self):
        proportional = self.kp_l*self.linear_e 

        # self.integral_e_linear += self.linear_e*self.dt
        # integral = self.ki_l*self.integral_e_linear

        # derivate = ((self.linear_e - self.prev_linear_e)/self.dt)*self.kd_l

        self.cmd_vel_msg.linear.x = proportional
    
    def angular_controler(self):
        proportional = self.kp_w*self.angular_e 

        # self.integral_e_angular += self.angular_e*self.dt
        # integral = self.ki_w*self.integral_e_angular

        # derivate = ((self.angular_e - self.prev_angular_e)/self.dt)*self.kd_w
        
        self.cmd_vel_msg.angular.z = proportional
    
    def controller(self):
        self.calculate_errors()
        # print(self.angular_e)
        # if(abs(self.angular_e) <= 0.01):
        # print(self.linear_e)
        self.lineal_controller()
        # else:
        self.angular_controler()



    def update_vel(self, dt):
        self.dt = dt
        self.controller()

    def pose_update(self, msg):
        self.x_pose = msg.pose.pose.position.x
        self.y_pose = msg.pose.pose.position.y
        self.theta_pose = msg.pose.pose.orientation.w


    def set_point_update(self, msg):
        self.x_d = msg.position.x
        self.y_d = msg.position.y

    
# def main():
#     try:
#         rospy.init_node('controller_node')
#         ControlNode()
#         rospy.spin()

#     except rospy.ROSInterruptException:
#         rospy.loginfo("ros interrupt exception")

#     except Exception as e:
#         rospy.logerr("Error in main %s", e)
