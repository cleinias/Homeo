/*
 * File:         khepera_bus.c
 * Date:         September 4th, 2006
 * Description:  A controller for the Khepera robot intended to be
 *               cross-compiled in order to run on the real robot.
 * Author:       Simon Blanchoud
 * Modifications:
 *
 * Copyright (c) 2008 Cyberbotics - www.cyberbotics.com
 */

#include <webots/robot.h>
#include <webots/differential_wheels.h>
#include <webots/distance_sensor.h>
#include <webots/light_sensor.h>
#include <webots/emitter.h>
#include <webots/receiver.h>
#include <string.h>
#include <stdio.h>

#define FORWARD_SPEED 8
#define TURN_SPEED 5
#define SENSOR_THRESHOLD 150
#define NB_SENSOR 8
#define TIME_STEP 64

static WbDeviceTag ds[NB_SENSOR];

/* 
 * The RS232 communication system is useful to send commands to a real    
 * Khepera robot using the Khepera protocol, this way, it is possible for 
 * example to retrive information from custom extension turret using the  
 * "T" protocol command. The example here shows how the Khepera robot     
 * answers to the "B" command, asking for software versions.              
 * This system will be ignored in simulation and with the cross-compiled  
 * version of this controller.                                            
 */

#ifndef KROS_COMPILATION
static WbDeviceTag rs232_out, rs232_in;
#endif

int main()
{
    short left_speed, right_speed;
    unsigned short ds_value[NB_SENSOR];
    int left_encoder, right_encoder;
    char text[4];
    int i;
#ifndef KROS_COMPILATION
    const char command[] = "B\n";
#endif

    left_speed = 0;
    right_speed = 0;

    wb_robot_init();

    text[1] = 's';
    text[3] = '\0';
    for (i = 0; i < NB_SENSOR; i++) {
        text[0] = 'd';
        text[2] = '0' + i;
        ds[i] = wb_robot_get_device(text); /* distance sensors */
    }

#ifndef KROS_COMPILATION
    rs232_out = wb_robot_get_device("rs232_out");
    rs232_in = wb_robot_get_device("rs232_in");
#endif
    for (i = 0; i < NB_SENSOR; i++)
      wb_distance_sensor_enable(ds[i], TIME_STEP);
#ifndef KROS_COMPILATION
    wb_receiver_enable(rs232_in, TIME_STEP);
#endif
    wb_differential_wheels_enable_encoders(TIME_STEP);

    for (;;) {                  /* The robot never dies! */
        ds_value[1] = wb_distance_sensor_get_value(ds[1]);
        ds_value[2] = wb_distance_sensor_get_value(ds[2]);
        ds_value[3] = wb_distance_sensor_get_value(ds[3]);
        ds_value[4] = wb_distance_sensor_get_value(ds[4]);

        if (ds_value[2] > SENSOR_THRESHOLD 
            && ds_value[3] > SENSOR_THRESHOLD) {
            left_speed = -TURN_SPEED;   /* go backwards */
            right_speed = -TURN_SPEED;
        } else if (ds_value[1] < SENSOR_THRESHOLD
                   && ds_value[2] < SENSOR_THRESHOLD
                   && ds_value[3] < SENSOR_THRESHOLD
                   && ds_value[4] < SENSOR_THRESHOLD) {
            left_speed = FORWARD_SPEED; /* go forward */
            right_speed = FORWARD_SPEED;
        } else if (ds_value[3] > SENSOR_THRESHOLD
                   || ds_value[4] > SENSOR_THRESHOLD) {
            left_speed = -TURN_SPEED;   /* turn left */
            right_speed = TURN_SPEED;
        }

        if (ds_value[1] > SENSOR_THRESHOLD || ds_value[2] > SENSOR_THRESHOLD) {
            right_speed = -TURN_SPEED;  /* turn right */
            left_speed = TURN_SPEED;
        }

        left_encoder = wb_differential_wheels_get_left_encoder();
        right_encoder = wb_differential_wheels_get_right_encoder();

        if (left_encoder > 9000) {
            wb_differential_wheels_set_encoders(0, right_encoder);
        }

        if (right_encoder > 1000) {
            wb_differential_wheels_set_encoders(left_encoder, 0);
#ifndef KROS_COMPILATION
            wb_emitter_send(rs232_out, command, strlen(command) + 1);
#endif
        }
        wb_differential_wheels_set_speed(left_speed, right_speed); /* Set the motor speeds */

        wb_robot_step(TIME_STEP);         /* run one step */

#ifndef KROS_COMPILATION
        if (wb_receiver_get_queue_length(rs232_in) > 0) {
            printf("received %s\n", (const char *)wb_receiver_get_data(rs232_in));
            wb_receiver_next_packet(rs232_in);
        }
#endif
    }

    return 0;
}
