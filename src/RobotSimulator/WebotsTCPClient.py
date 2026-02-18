'''
Created on Sep 17, 2013

@author: stefano
'''
import socket  
from time import sleep
from Helpers.ExceptionAndDebugClasses import TCPConnectionError
import sys
from Helpers.ExceptionAndDebugClasses import hDebug

class WebotsTCPClient(object):
    '''WebotsTCPClient manages a connection to a Webots robot running a server controller
    Instance variables:
    ip_address    defaults to localhost
    port          port the robot is listening on
    clientSocket  the socket for the communication with the robot
    ''' 
    def __init__(self, ip='localhost', port = None):
        'Basic setup'
        self._ip_address = ip
        self._clientSocket = None
        self._clientPort = port
         
    def getClientSocket(self):
        'return a socket if present, otherwise try to connect and create one'
        if self._clientSocket is not None:
                return self._clientSocket
        else:
            self.clientConnect()
            return self._clientSocket

    
    def clientConnect(self):
        'Try a few times to create a connection if not connected already. Store the returned socket in clientSocket'
        connected = False
        connectAttempts = 10
        sleepTime = 0.1
        retries = 3
        retrySleepTime = 1
        if self._clientSocket is not None:
            hDebug('network', 'Already connected! Use the socket stored in clientSocket')
            #self.close()
        else:
            if connected == False:
                try:
                    for i in range(connectAttempts):
                        try:
                            self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            self._clientSocket.connect((self._ip_address, self._clientPort))
                            hDebug('network', ('Success! Connected to server at %s on port %u' % (self._ip_address, self._clientPort)))
                            connected = True
                            break
                        except socket.error:
                            hDebug('network', ('Cannot connect to server at %s on port %u' % (self._ip_address, self._clientPort)))
                            hDebug('network', "Waiting %f seconds and then going for attempt number %d" % (sleepTime,i+2))
                            sleep(sleepTime)
                    if connected == False:
                        hDebug('network', "I could not connect to server at %s on port %u after %d attempts" % (self._ip_address, self._clientPort, connectAttempts))
                        hDebug('network', 'Destroying socket')
                        self._clientSocket = None
                        raise socket.error
                except socket.error:
                    raise TCPConnectionError("I could NOT connect to server")
                      
    def close(self):
        'Closes the connection and set socket to None'
        if self._clientSocket is not None:
            try:
                self._clientSocket.close()
                self._clientSocket = None
            except socket.error:
                print('Cannot close socket!')
        