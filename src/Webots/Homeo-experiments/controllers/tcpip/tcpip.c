/*
 * File:         tcpip.c
 * Date:         October, 2003
 * Description:  A simple server program implementing a TCP/IP relay controller for
 *               interfacing Webots with any development environment able to
 *               use TCP/IP, including MathLab, Lisp, Java, C, C++, etc.
 * Author:       Darren Smith
 * Modifications: Stefano Franchi 2013
 *
 * Copyright (c) 2006 Cyberbotics - www.cyberbotics.com and 2013 Stefano Franchi
 */

/* The protocol used in this example is taken from the Khepera serial       
 * communication protocol. It only supports 2 commands:                              
 *                                                                           
 * D: set speed                                                              
 * O: read ambient light sensors                                             
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
#ifdef WIN32
#include <winsock.h>
#else
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>         /* definition of struct sockaddr_in */
#include <netdb.h>              /* definition of gethostbyname */
#include <arpa/inet.h>          /* definition of inet_ntoa */
#include <unistd.h>             /* definition of close */
#endif

#define SOCKET_PORT 10020
#define NB_IR_SENSOR 2
#define TIMESTEP 250

static WbDeviceTag distance[NB_IR_SENSOR];
static WbDeviceTag ambient[NB_IR_SENSOR];
static WbDeviceTag led[2];
static int fd;
static fd_set rfds;

static int accept_client(int server_fd)
{
    int cfd;
    struct sockaddr_in client;
#ifndef WIN32
    socklen_t asize;
#else
    int asize;
#endif 
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

#ifdef WIN32
    /* initialize the socket api */
    WSADATA info;

    rc = WSAStartup(MAKEWORD(1, 1), &info); /* Winsock 1.1 */
    if (rc != 0) {
        printf("cannot initialize Winsock\n");
        return -1;
    }
#endif
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

    /*  Disable distance sensors
    for (i = 0; i < NB_IR_SENSOR; i++) {
        sprintf(text, "ds%d", i);
        distance[i] = wb_robot_get_device(text);
        wb_distance_sensor_enable(distance[i], TIMESTEP);
    }
    */
    for (i = 0; i < NB_IR_SENSOR; i++) {
        sprintf(text, "ls%d", i);
        ambient[i] = wb_robot_get_device(text);
        wb_light_sensor_enable(ambient[i], TIMESTEP);
    }

    /* disable led's
    led[0] = wb_robot_get_device("led0");
    led[1] = wb_robot_get_device("led1");
    */

    /* Enable the wheel encoders measurements */
    /* Disabled
    wb_differential_wheels_enable_encoders(TIMESTEP);
    */
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
    short led_number, led_action;
    static short led_value[2] = { 0, 0 };   /* initially off */
    struct timeval tv = { 0, 0 };
    int number;
    int leftWheelEncoding;
    int rightWheelEncoding;

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
    printf("Received %d bytes: %s\n", n, buffer);

    if (buffer[0] == 'D') {     /* set the speed of the motors */
        sscanf(buffer, "D,%d,%d", &left_speed, &right_speed);
        wb_differential_wheels_set_speed(left_speed, right_speed);
        send(fd, "d\r\n", 3, 0);

    } else if (buffer[0] == 'O') {  /* read the ambient light sensor */
        sprintf(buffer, "o,%d,%d,%d,%d,%d,%d,%d,%d\r\n",
                (int)wb_light_sensor_get_value(ambient[0]),
                (int)wb_light_sensor_get_value(ambient[1]),
                (int)wb_light_sensor_get_value(ambient[2]),
                (int)wb_light_sensor_get_value(ambient[3]),
                (int)wb_light_sensor_get_value(ambient[4]),
                (int)wb_light_sensor_get_value(ambient[5]),
                (int)wb_light_sensor_get_value(ambient[6]),
                (int)wb_light_sensor_get_value(ambient[7]));
        send(fd, buffer, strlen(buffer), 0);

    } else if (strncmp(buffer, "exit", 4) == 0) {
        printf("connection closed\n");
#ifdef WIN32
        closesocket(fd);
        ret = WSACleanup();
#else
        ret = close(fd);
#endif
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
