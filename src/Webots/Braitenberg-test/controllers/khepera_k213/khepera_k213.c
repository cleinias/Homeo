/*
 * File:         khepera_k213.c
 * Date:         September 4th, 2006
 * Description:  A controller for the Khepera robot equipped with a K213
 *               camera device. This controller translates the informations
 *               of the camera into text and prints it into the log window.
 * Modifications:
 *
 * Copyright (c) 2006 Cyberbotics - www.cyberbotics.com
 */

#include <webots/robot.h>
#include <webots/differential_wheels.h>
#include <webots/camera.h>
#include <webots/distance_sensor.h>
#include <stdio.h>

#define FORWARD_SPEED 4
#define TURN_SPEED 2
#define SENSOR_THRESHOLD 150
#define NB_SENSOR 8
#define TIME_STEP 64

WbDeviceTag ds[NB_SENSOR], k213;

int main()
{
    int left_speed = 0, right_speed = 0;
    unsigned short ds_value[NB_SENSOR];
    const unsigned char *k213_image;
    unsigned char p;
    int i;
    char line[66];
    char text[4];

    wb_robot_init();

    text[1] = 's';
    text[3] = '\0';
    for (i = 0; i < NB_SENSOR; i++) {
        text[0] = 'd';
        text[2] = '0' + i;
        ds[i] = wb_robot_get_device(text); /* distance sensors */
        wb_distance_sensor_enable(ds[i], TIME_STEP);
    }

    k213 = wb_robot_get_device("k213");    /* K213 linear camera */
    wb_camera_enable(k213, TIME_STEP);

    printf("\nThis Khepera robot is equipped with a K213 camera "
         "device\nIn this example it will translate the informations of the camera "
         "into text in the log widow.\nThe translation is done using blank spaces "
         "for the black pixels and \"O\" characters for the white ones.\n");

    /* 
     * We wait a little bit before starting so that people have time to read
     * the previous message.
     */
    wb_robot_step(1000 * TIME_STEP);

    while (wb_robot_step(TIME_STEP) != -1) {
        
        /*
         * First we update the distance sensors values, then using them we
         * perform the obstacle avoidance and finally we convert the imageinto
         * text.
         */
        ds_value[1] = wb_distance_sensor_get_value(ds[1]);
        ds_value[2] = wb_distance_sensor_get_value(ds[2]);
        ds_value[3] = wb_distance_sensor_get_value(ds[3]);
        ds_value[4] = wb_distance_sensor_get_value(ds[4]);

        if (ds_value[2] > SENSOR_THRESHOLD && ds_value[3] > SENSOR_THRESHOLD) {
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

        k213_image = wb_camera_get_image(k213);

        for (i = 0; i < 64; i++) {
            p = wb_camera_image_get_grey(k213_image, 64, i, 0);
            if (p < 32) {
                line[i] = ' ';
            } else if (p < 64) {
                line[i] = '.';
            } else if (p < 96) {
                line[i] = '-';
            } else if (p < 128) {
                line[i] = '+';
            } else if (p < 160) {
                line[i] = 'o';
            } else if (p < 192) {
                line[i] = 'O';
            } else if (p < 224) {
                line[i] = 'X';
            } else {
                line[i] = 'W';
            }
        }

        line[i++] = '\n';
        line[i++] = '\0';

        printf("%s",line);

        /* Set the motor speeds. */
        wb_differential_wheels_set_speed(left_speed, right_speed);
    }
    
    wb_robot_cleanup();

    return 0;
}
