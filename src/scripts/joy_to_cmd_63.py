#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
import subprocess, os, time

manual_control = False
publish_time = 0.1
twist = Twist()
cmd_vel_pub = None

drive_process = None
button_press_start = {0: None, 1: None, 2: None}  # start time for each button
HOLD_TIME = 3  # seconds


def joy_callback(data):
    global twist, manual_control, drive_process, button_press_start

    # --- Detect button press duration ---
    for btn_idx in [0, 1, 2]:
        if data.buttons[btn_idx] == 1:
            # button pressed
            if button_press_start[btn_idx] is None:
                button_press_start[btn_idx] = time.time()
            elif time.time() - button_press_start[btn_idx] >= HOLD_TIME:
                handle_button_action(btn_idx)
                button_press_start[btn_idx] = None  # reset
        else:
            button_press_start[btn_idx] = None  # reset if released

    # --- Normal joystick control (same as before) ---
    axes_3, axes_4, axes_6, axes_7 = data.axes[3], data.axes[4], data.axes[6], data.axes[7]
    if axes_7 != 0 or axes_6 != 0 or axes_4 != 0 or axes_3 != 0:
        manual_control = True

    if manual_control:
        twist.linear.x = axes_7 if axes_7 != 0 else axes_4
        twist.angular.z = axes_6 if axes_6 != 0 else axes_3
    else:
        twist.linear.x = 0.0
        twist.angular.z = 0.0


def handle_button_action(btn_idx):
    global drive_process
    if btn_idx == 0:  # START
        if drive_process is None or drive_process.poll() is not None:
            rospy.loginfo("🚀 Starting drive node...")
            drive_process = subprocess.Popen(["rosrun", "montu", "drive_UGV_dual_serial_read_power_62.py"])
        else:
            rospy.loginfo("⚠️ Drive node already running.")
    elif btn_idx == 2:  # STOP
        if drive_process is not None and drive_process.poll() is None:
            rospy.loginfo("🛑 Stopping drive node...")
            drive_process.terminate()
            drive_process = None
        else:
            rospy.loginfo("⚠️ Drive node not running.")
    elif btn_idx == 1:  # SHUTDOWN
        rospy.logwarn("⚡ Shutting down system in 3 seconds...")
        rospy.sleep(3)
        os.system("sudo shutdown now")


def publish_command(event):
    cmd_vel_pub.publish(twist)


def joy_to_cmd_vel():
    rospy.init_node('joy_to_cmd_vel', anonymous=True)
    global cmd_vel_pub
    cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
    rospy.Subscriber('/joy', Joy, joy_callback)
    rospy.Timer(rospy.Duration(publish_time), publish_command)
    rospy.spin()


if __name__ == '__main__':
    try:
        joy_to_cmd_vel()
    except rospy.ROSInterruptException:
        pass
