/*
 * File:         server-diff-2-light-sensors-2-motors.c
 * Date:         October, 2003
 * Description:  A simple server program implementing a TCP/IP relay controller
                 using a simplified version of the Khepera communication protocol
                 for a Khepera-like robot with 2 light sensors and 2 motors
 * Author:       Darren Smith
 * Modifications: Stefano Franchi 2013
 *
 * Copyright (c) 2006 Cyberbotics - www.cyberbotics.com and 2013 Stefano Franchi
 */

/* The protocol used in this example is modified from the Khepera serial       
 * communication protocol. It controls a Khepera-like robot
 * with only 2 light sensors, and it supports the following commands:
 *                                                                           
 * L; set left wheel speed
 * R: set right wheel speed
 * O: read ambient light sensors
 * M: read max speed                                             
 *                                                                           
 * Additionally, the server understands the string "exit", which terminates the connections                                                                         
 *                                                                           
 * Everything relies on standard POSIX TCP/IP sockets.                       
 */

#include <webots/robot.h>
#include <webots/differential_wheels.h>
#include <webots/distance_sensor.h>
#include <webots/light_sensor.h>
#include <webots/led.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>         /* definition of struct sockaddr_in */
#include <netdb.h>              /* definition of gethostbyname */
#include <arpa/inet.h>          /* definition of inet_ntoa */
#include <unistd.h>             /* definition of close */

#define SOCKET_PORT 10020
#define NB_IR_SENSOR 1
#define TIMESTEP 250

static WbDeviceTag ambient[NB_IR_SENSOR];
static int fd;
static fd_set rfds;

static int accept_client(int server_fd)
{
    int cfd;
    struct sockaddr_in client;
    int asize;
    struct hostent *client_info;

    asize = sizeof(struct sockaddr_in);

    cfd = accept(server_fd, (struct sockaddr *) &client, &asize);
    if (cfd == -1) {
        printf("cannot accept client\n");
        return -1;
    }
    client_info = gethostbyname((char *) inet_ntoa(client.sin_addr));
    printf("Accepted connection from: %s \n",
                         client_info->h_name);

    return cfd;
}

static int create_socket_server(int port)
{
    int sfd, rc;
    struct sockaddr_in address;

    /* create the socket */
    sfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sfd == -1) {
        printf("cannot create socket\n");
        return -1;
    }

    /* fill in socket address */
    memset(&address, 0, sizeof(struct sockaddr_in));
    address.sin_family = AF_INET;
    address.sin_port = htons((unsigned short) port);
    address.sin_addr.s_addr = INADDR_ANY;

    /* bind to port */
    rc = bind(sfd, (struct sockaddr *) &address, sizeof(struct sockaddr));
    if (rc == -1) {
        printf("cannot bind port %d\n", port);
        return -1;
    }

    /* listen for connections */
    if (listen(sfd, 1) == -1) {
        printf("cannot listen for connections\n");
        return -1;
    }
    printf("Waiting for a connection on port %d...\n", port);

    return accept_client(sfd);
}

static void initialize()
{
    int i;
    char text[32];

    for (i = 0; i < NB_IR_SENSOR; i++) {
        sprintf(text, "ls%d", i);
        ambient[i] = wb_robot_get_device(text);
        wb_light_sensor_enable(ambient[i], TIMESTEP);
    }

    printf("Khepera robot has been initialized by Webots\n");
    fd = create_socket_server(SOCKET_PORT);
    FD_ZERO(&rfds);
    FD_SET(fd, &rfds);
}

static void run()
{
    int n;
    int ret;
    char buffer[256];
    int left_speed, right_speed;
    struct timeval tv = { 0, 0 };
    int number;

    /* Set up the parameters used for the select statement */

    FD_ZERO(&rfds);
    FD_SET(fd, &rfds);

    /*
     * Watch TCPIP file descriptor to see when it has input.
     * No wait - polling as fast as possible 
     */
    number = select(fd + 1, &rfds, NULL, NULL, &tv);

    /* If there is no data at the socket, then redo loop */
    if (number == 0) {
        return;
    }

    /* ...otherwise, there is data to read, so read & process. */
    n = recv(fd, buffer, 256, 0);
    if (n < 0) {
        printf("error reading from socket\n");
    }
    buffer[n] = '\0';
//    printf("Received %d bytes: %s\n", n, buffer);
     
    if (buffer[0] == 'L') {     /* set the speed of the motor */
        sscanf(buffer, "L,%d", &left_speed);
        double right_speed = wb_differential_wheels_get_right_speed();
        wb_differential_wheels_set_speed(left_speed, right_speed);
        send(fd, "d\r\n", 3, 0);

    } else if (buffer[0] == 'R') {  /* set the speed of the motor */
        sscanf(buffer, "R,%d", &right_speed);
        double left_speed = wb_differential_wheels_get_left_speed();
        wb_differential_wheels_set_speed(left_speed, right_speed);
        send(fd, "d\r\n", 3, 0);

    } else if (buffer[0] == 'O') {  /* read the 2 ambient light sensor */
        sprintf(buffer, "o,%d,%d\r\n",
                (int)wb_light_sensor_get_value(ambient[0]),
                (int)wb_light_sensor_get_value(ambient[1]));
        send(fd, buffer, strlen(buffer), 0);

    } else if (buffer[0] == 'M') {  /* read the max speed */
        sprintf(buffer, "m,%d\r\n",
                (int)wb_differential_wheels_get_max_speed()),
        send(fd, buffer, strlen(buffer), 0);

    } else if (strncmp(buffer, "exit", 4) == 0) {
        printf("connection closed\n");
        ret = close(fd);
        if (ret != 0) {
            printf("Cannot close socket\n");
        }
        fd = 0;
    } else {
        send(fd, "\n", 1, 0);
    }
}

int main()
{
    wb_robot_init();

    initialize();

    while (1) {
      wb_robot_step(TIMESTEP);
      run();
    }
    
    wb_robot_cleanup();
    
    return 0;
}
