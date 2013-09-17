'''
Created on Sep 5, 2013

@author: stefano
Sample controller for a robot tcp ip server 
uses a minimal Khepera tcp/ip protocol:
 
 * B: read software version       Disabled                                           
 * D: set speed                   Active                                                       
 * G: set position counter        Disabled                                           
 * H: read position               Disabled                                           
 * L: change LED state            Disabled                                   
 * N: read proximity sensors      Disabled                                           
 * O: read ambient light sensors  Active                                           


'''
import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 5005
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print 'Connection address:', addr
while 1:
    data = conn.recv(BUFFER_SIZE)
#    if not data: break
#    print "received data:", data   
    conn.send(data)  # echo
conn.close()     