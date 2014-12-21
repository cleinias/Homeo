'''
Created on Sep 17, 2013

@author: stefano
'''
import socket  
from time import sleep

class WebotsTCPClient(object):
    '''WebotsTCPClient manages a connection to a Webots robot running a server controller
    Instance variables:
    ip_address    defaults to localhost
    port          port the robot is listening on
    clientSocket  the socket for the communication with the robot
    ''' 
    def __init__(self, ip='127.0.0.1', port = None):
        'Basic setup'
        self._ip_address = ip
        print 'Set ip address'
        self._clientSocket = None
        print 'set clientSocket to None'
        self._clientPort = port
        print 'set clientPort'
         
    #===========================================================================
    # def setPort(self,aNumber):
    #     self._clientPort=aNumber
    #     print 'Set clientPort to %u' % aNumber
    # def getPort(self):
    #     return self._clientPort
    # clientPort = property(fget = lambda self: self.getPort(),
    #                       fset = lambda self, aNumber: self.setPort(aNumber))
    # 
    # def getClientSocket(self):
    #     'return a socket if present, otherwise try to connect and create one'
    #     try:
    #         if self._clientSocket is not None:
    #             return self._clientSocket
    #     except AttributeError:
    #         try:
    #             print 'Moving to connect method'
    #             self.clientConnect()
    #             print 'Exiting connect method'
    #             return self._clientSocket
    #         except socket.error:
    #             print 'Cannot connect to server at %s : %u' % (self._ip_address, self._clientPort)
    #             print 'Destroying socket'
    # 
    # def setClientSocket(self, aValue):
    #     'Does nothing, since the socket can only  be set by the getClientSocket method'
    #     return
    # 
    # clientSocket = property(fget = lambda self: self.getClientSocket(),
    #                         fset = lambda self, aValue: self.setClientSocket(aValue))
    #===========================================================================

    def getClientSocket(self):
        'return a socket if present, otherwise try to connect and create one'
        if self._clientSocket is not None:
                return self._clientSocket
        else:
            print 'Moving to connect method'
            self.clientConnect()
            print 'Exiting connect method'
            return self._clientSocket

    
    def clientConnect(self):
        'Try a few times to create a connection if not connected already. Store the returned socket in clientSocket'
        connected = False
        connectAttempts = 10
        sleepTime = 1
        if self._clientSocket is not None:
            print 'Already connected! Use the socket stored in clientSocket'
        else:
            for i in xrange(connectAttempts):
                try:
                    self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._clientSocket.connect((self._ip_address, self._clientPort))
                    print 'Success! Connected to server at %s at port %u' % (self._ip_address, self._clientPort)
                    connected = True
                    break
                except socket.error:
                    print 'Cannot connect to server at %s at port %u' % (self._ip_address, self._clientPort)
                    print "Waiting %d seconds and then going for attempt number %d" % (sleepTime,i+2)
                    sleep(sleepTime)
            if connected == False:
                print " I could not connect to server at %s at port %u after %d attempts" % (self._ip_address, self._clientPort, connectAttempts)
                print 'Destroying socket'
                self._clientSocket = None
                raise socket.error
                             
    def close(self):
        'Closes the connection and set socket to None'
        if self._clientSocket is not None:
            try:
                self._clientSocket.close()
                self._clientSocket = None
            except socket.error:
                print 'Cannot close socket!'
        