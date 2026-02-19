'''
Created on Sep 5, 2013

@author: stefano
 Simple supervisor worker that responds to a few one-letter commands over a TCP/IP connection
 Default port is 10021

 Accepted commmands and corresponding webots functions are:
  R - Reset the Simulation to initial conditions           --> simulationRevert()
  P - Reset the Simulation's physics to initial conditions --> simulationResetPhysics()
  Q - Quit Webots                                          --> simulationQuit(int status);
  D - Return distance between robot and target (yet to implement)
'''
import socket 

TCP_IP = 'localhost'
TCP_PORT = 10021
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print('Connection address:', addr)
while 1:
    data = conn.recv(BUFFER_SIZE)
#    if not data: break
#    print "received data:", data   
    conn.send(data)  # echo
conn.close()     