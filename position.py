#!/usr/bin/env python

'''

This python file runs a ROS-node of name drone_control which holds the position of e-Drone on the given dummy.
This node publishes and subsribes the following topics:

		PUBLICATIONS			SUBSCRIPTIONS
		/drone_command			/whycon/poses
		/alt_error				/pid_tuning_altitude
		/pitch_error			/pid_tuning_pitch
		/roll_error				/pid_tuning_roll



Rather than using different variables, use list. eg : self.setpoint = [1,2,3], where index corresponds to x,y,z ...rather than defining self.x_setpoint = 1, self.y_setpoint = 2
CODE MODULARITY AND TECHNIQUES MENTIONED LIKE THIS WILL HELP YOU GAINING MORE MARKS WHILE CODE EVALUATION.
'''

# Importing the required libraries

from edrone_client.msg import *
from geometry_msgs.msg import PoseArray
from std_msgs.msg import Int16
from std_msgs.msg import Int64
from std_msgs.msg import Float64
from pid_tune.msg import PidTune
import rospy
import time


class Edrone():
	"""docstring for Edrone"""
	def __init__(self):

		rospy.init_node('drone_control')	# initializing ros node with name drone_control

		# This corresponds to your current position of drone. This value must be updated each time in your whycon callback
		# [x,y,z]
		self.drone_position = [0.0,0.0,0.0]

		# [x_setpoint, y_setpoint, z_setpoint]
		self.setpoint = [2,2,20] # whycon marker at the position of the dummy given in the scene. Make the whycon marker associated with position_to_hold dummy renderable and make changes accordingly


		#Declaring a cmd of message type edrone_msgs and initializing values
		self.cmd = edrone_msgs()
		self.cmd.rcRoll = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcThrottle = 1500
		self.cmd.rcAUX1 = 0
		self.cmd.rcAUX2 = 0
		self.cmd.rcAUX3 = 0
		self.cmd.rcAUX4 = 0


		#initial setting of Kp, Kd and ki for [roll, pitch, throttle]. eg: self.Kp[2] corresponds to Kp value in throttle axis
		#after tuning and computing corresponding PID parameters, change the parameters		
 		self.Kp = [48,55.2,65.92]#[0.12,0.12,0.16]
		self.Ki = [0.003,0.0035,0.0018]#[0.0006,0.0007,0.008]
		self.Kd = [3464.65,3552.05,11680]#[0.95,.95,1.2]
		self.prev_values=[0,0,0]
		self.min_values=[1000,1000,1000]
		self.max_values=[2000,2000,2000]
		self.out_pitch=0
		self.out_roll=0
		self.out_throttle=0
		self.error=[0,0,0]
		self.prev_error=[0,0,0]
		self.change_error=[0,0,0]
		self.iterm=[0,0,0]
		#self.Kp = [23,24,36.16]#[0.06,0.06,0.08]
		#self.Ki = [0.0028,0.009,0.056]#[0.0006,0.0007,0.008]
		#self.Kd = [1192.2,1232,1621]#[0.3,0.3,0.45]

		#-----------------------Add other required variables for pid here ----------------------------------------------








		# Hint : Add variables for storing previous errors in each axis, like self.prev_values = [0,0,0] where corresponds to [pitch, roll, throttle]
		#		 Add variables for limiting the values like self.max_values = [2000,2000,2000] corresponding to [roll, pitch, throttle]
		#	     self.min_values = [1000,1000,1000] corresponding to [pitch, roll, throttle]
	    #		You can change the upper limit and lower limit accordingly.
		#----------------------------------------------------------------------------------------------------------

		# # This is the sample time in which you need to run pid. Choose any time which you seem fit. Remember the stimulation step time is 50 ms
		# self.sample_time = 0.060 # in seconds
		self.sample_time=0.090

		# Publishing /drone_command, /alt_error, /pitch_error, /roll_error
		self.command_pub = rospy.Publisher('/drone_command', edrone_msgs, queue_size=1)
		self.command_alt=rospy.Publisher('/alt_error',Float64,queue_size=1)
		self.command_pitch=rospy.Publisher('/pitch_error',Float64,queue_size=1)
		self.command_roll=rospy.Publisher('/roll_error',Float64,queue_size=1)
		#-----------------------------------------------------------------------------------------------------------
		# Subscribing to /whycon/poses, /pid_tuning_altitude, /pid_tuning_pitch, pid_tuning_roll
		rospy.Subscriber('whycon/poses', PoseArray, self.whycon_callback)
		rospy.Subscriber('/pid_tuning_altitude',PidTune,self.altitude_set_pid)
		rospy.Subscriber('/pid_tuning_pitch',PidTune,self.pitch_set_pid)
		rospy.Subscriber('/pid_tuning_roll',PidTune,self.roll_set_pid)
		#------------------------------------------------------------------------------------------------------------
		self.arm() # ARMING THE DRONE
	# Disarming condition of the drone
	def disarm(self):
		self.cmd.rcAUX4 = 1100
		self.command_pub.publish(self.cmd)
		rospy.sleep(1)

	# Arming condition of the drone : Best practise is to disarm and then arm the drone.
	def arm(self):
		self.disarm()
		self.cmd.rcRoll = 1500
		self.cmd.rcYaw = 1500
		self.cmd.rcPitch = 1500
		self.cmd.rcThrottle = 1000
		self.cmd.rcAUX4 = 1500
		self.command_pub.publish(self.cmd)	# Publishing /drone_command
		rospy.sleep(1)
	# Whycon callback function
	# The function gets executed each time when /whycon node publishes /whycon/poses
	def whycon_callback(self,msg):
		self.drone_position[0] = msg.poses[0].position.x
		self.drone_position[1]=msg.poses[0].position.y
		self.drone_position[2]=msg.poses[0].position.z
		#---------------------------------------------------------------------------------------------------------------
	# Callback function for /pid_tuning_altitude
	# This function gets executed each time when /tune_pid publishes /pid_tuning_altitude
	def altitude_set_pid(self,alt):
		self.Kp[2] = alt.Kp * 0.16 # This is just for an example. You can change the ratio/fraction value accordingly
		self.Ki[2] = alt.Ki * 0.0003
		self.Kd[2] = alt.Kd * 2.5
        #------------------------------------------------------------------------------------------------------------

	def pitch_set_pid(self,pitch):
		self.Kp[1] = pitch.Kp * 0.12
		self.Ki[1] = pitch.Ki * 0.0007
		self.Kd[1] = pitch.Kd * 1.6
	#---------------------------------------------------------------------------------------------------------------

	def roll_set_pid(self,roll):
		self.Kp[0] = roll.Kp * 0.12
		self.Kd[0] = roll.Kd * 1.6
		self.Ki[0] = roll.Ki * 0.0007

	#----------------------------------------------------------------------------------------------------------------------


	def pid(self):
		self.error[0]=self.drone_position[0]-self.setpoint[0]
		self.error[1]=self.drone_position[1]-self.setpoint[1]
		self.error[2]=self.drone_position[2]-self.setpoint[2]
		self.change_error[0]=self.error[0]-self.prev_error[0]
		self.change_error[1]=self.error[1]-self.prev_error[1]
		self.change_error[2]=self.error[2]-self.prev_error[2]
		self.iterm[0]=self.error[0]+self.iterm[0]
		self.iterm[1]=self.error[1]+self.iterm[1]
		self.iterm[2]=self.error[2]+self.iterm[2]
		self.out_roll=self.Kp[0]*self.error[0]+self.Kd[0]*self.change_error[0]+self.Ki[0]*self.iterm[0]
		self.out_pitch=self.Kp[1]*self.error[1]+self.Kd[1]*self.change_error[1]+self.Ki[1]*self.iterm[1]
		self.out_throttle=self.Kp[2]*self.error[2]+self.Kd[2]*self.change_error[2]+self.Ki[2]*self.iterm[2]
		self.cmd.rcThrottle=1500+self.out_throttle
		self.cmd.rcRoll=1500-self.out_roll
		self.cmd.rcPitch=1500+self.out_pitch
		if self.cmd.rcPitch > self.max_values[1]:
			self.cmd.rcPitch = self.max_values[1]
		if self.cmd.rcRoll > self.max_values[0]:
			self.cmd.rcRoll = self.max_values[0]
		if self.cmd.rcThrottle > self.max_values[2]:
			self.cmd.rcThrottle = self.max_values[2]
		self.prev_error[1] = self.error[1]
		self.prev_error[0] = self.error[0]
		self.prev_error[2] = self.error[2]

		self.command_alt.publish(self.error[2])
		self.command_pitch.publish(self.error[1])
		self.command_roll.publish(self.error[0])
		self.command_pub.publish(self.cmd)

if __name__ == '__main__':

	e_drone = Edrone()
	r = rospy.Rate(90) #specify rate in Hz based upon your desired PID sampling time, i.e. if desired sample time is 33ms specify rate as 30Hz
	while not rospy.is_shutdown():
		e_drone.pid()
		r.sleep()
