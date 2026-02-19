'''
Created on Dec 26, 2014

@author: stefano
 * Simple supervisor worker that responds to a few one-letter commands over a TCP/IP connection
 * Default port is 10021
 *
 * Accepted commmands and corresponding webots functions are:
 * R - Reset the Simulation to initial conditions           --> simulationRevert()
 * P - Reset the Simulation's physics to initial conditions --> simulationResetPhysics()
 * Q - Quit Webots                                          --> simulationQuit(int status);
 * D - Return distance between robot and target (yet to implement)
'''
import socket 
from controller import Supervisor

TCP_IP = 'localhost'
TCP_PORT = 10021
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

class supervisorController(Supervisor):
    '''
    Simple class implementing a daemon that listen to the TCP/IP host on port TCP_PORT
    for commands controlling the Webots simulation
    '''
    
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        print('Connection address:', addr)
        while 1:
            data = conn.recv(BUFFER_SIZE)
            #    if not data: break
            #    print "received data:", data
            if data[0]:   
                conn.send(data)  # echo
        conn.close()
        
controller = supervisorController()
controller.run()