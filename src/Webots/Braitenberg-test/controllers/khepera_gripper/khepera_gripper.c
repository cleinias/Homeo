/*
 * File:          khepera_gripper.c
 * Description:   A controller for the Khepera robot equipped with a gripper.
 * Author:        Simon Blanchoud
 * Modifications: November 9, 2009 by Yvan Bourquin:
 *                Replaced Gripper device with two "linear" Motors
 *                Switched from a kinematic to a physics simulation
 *                
 * Copyright (c) 2009 Cyberbotics - www.cyberbotics.com
 */

#include <webots/robot.h>
#include <webots/differential_wheels.h>
#include <webots/distance_sensor.h>
#include <webots/motor.h>
#include <stdio.h>
#include <string.h>

#define TIME_STEP 50
#define OPEN_GRIP 0.03
#define CLOSED_GRIP 0.005

static WbDeviceTag motor, left_grip, right_grip, ds;

static void set_grip_position(double pos) {
  wb_motor_set_position(left_grip, pos);
  wb_motor_set_position(right_grip, pos);
}

int main() {

  int i=0;

  wb_robot_init();

  motor      = wb_robot_get_device("motor");
  left_grip  = wb_robot_get_device("left grip");
  right_grip = wb_robot_get_device("right grip");
  ds         = wb_robot_get_device("ds");    /* distance sensor in the gripper */
  
  wb_motor_enable_position(motor, TIME_STEP);
  wb_distance_sensor_enable(ds, TIME_STEP);

  while (wb_robot_step(TIME_STEP)!=1) {
    if (i == 0)
      set_grip_position(OPEN_GRIP);   /* open the gripper */
    else if (i == 20)
      wb_motor_set_position(motor, 0.0); /* arm down */
    else if (i == 40)
      set_grip_position(CLOSED_GRIP);   /* close the gripper */
    else if (i == 80)
      wb_motor_set_position(motor, -1.4);   /* arm up */
    else if (i == 100)
      wb_differential_wheels_set_speed(-2, 2);   /* turn */
    else if (i == 140)
      wb_differential_wheels_set_speed(10, 10);  /* forward */
    else if (i == 160)
      wb_differential_wheels_set_speed(-2, 2);   /* turn */
    else if (i == 200) {
      wb_differential_wheels_set_speed(0, 0);    /* stops   */
      wb_motor_set_position(motor, 0.0); /* arm down */
    }
    else if (i == 240)
      set_grip_position(OPEN_GRIP);   /* open the gripper */
    else if (i == 260)
      wb_motor_set_position(motor, -1.4);   /* arm up */

    if (i++ == 280) {
      i = 0;
    }
  }

  wb_robot_cleanup();

  return 0;
}
