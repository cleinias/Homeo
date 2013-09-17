'''
Created on Sep 11, 2013

@author: stefano

Sample client for tcp/ip robot controller

'''
from __future__ import division
from time import sleep

#!/usr/bin/env python

import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 10020
BUFFER_SIZE = 1024
MAXSPEED = 100
MINSPEED = 1

'''Connect to the server'''
print 'Connecting...'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
print 'Connected!'
for i in xrange(100000):
#    'read light values'
#    print 'Reading light values at cycle %u' % i
    s.send('O')   
#    print 'Command O sent' 
    "Webots Light values are from 0 (max light intensity) to 1000 (min light intensity)"
    light_values = s.recv(BUFFER_SIZE).rstrip('\r\n').split(',') 
#    print light_values
#    print 'Light values read!'
#    print 'light values are %s at cycle %u' % (light_values, i)
    
    """Convert light values into a sensed value going from 
       10 (max value) to 0.01 (min value)
    """
    if float(light_values[2]) == 0:
        right_eye = 1
    else:
        right_eye = (1/(float(light_values[2])/10))  
    
    if float(light_values[1])==0:
        left_eye = 1
    else:
        left_eye = (1/(float(light_values[1])/10))  
    print right_eye, left_eye
#    print 'right sensor value as float: %d right_eye: %e' % (float(light_values[2]),1/float(light_values[2]))
#    print 'left sensor value as float: %d left_eye: %e' % (float(light_values[1]), left_eye)
    '''Convert perceived intensities (in scale 0.01 - 10) 
       to speeds (in scale 1 - 100) by multiplying by 100 and truncating at MAXSPEED = 100)'''
    right_speed = int((left_eye*100))
    if right_speed > MAXSPEED:
        right_speed = MAXSPEED
    left_speed = int((right_eye*100))
    if left_speed > MAXSPEED:
        left_speed = MAXSPEED
    motor_command = 'D,'+ str(left_speed) + ',' + str(right_speed)
    print "%u - Left sensor: %s LeftEye: %d  LeftSpeed: %u Right sensor: %s RightEye: %d Right Speed: %u Moto command D built: %s" % (i, 
                                                                                                                                      light_values[1], 
                                                                                                                                      left_eye, 
                                                                                                                                      left_speed, 
                                                                                                                                      light_values[2], 
                                                                                                                                      right_eye, 
                                                                                                                                      right_speed, 
                                                                                                                                      motor_command)
    s.send(motor_command)
    motor_response = s.recv(BUFFER_SIZE)
    print "Motor command D built"
#    sleep(1)
s.send('D,0,0')
motor_response = s.recv(BUFFER_SIZE)
print 'Exiting interaction'
s.send('exit')
print 'closing the socket'
s.close()

