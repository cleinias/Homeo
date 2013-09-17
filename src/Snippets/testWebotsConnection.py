'''
Created on Sep 17, 2013

@author: stefano
'''

from RobotSimulator.WebotsTCPClient import WebotsTCPClient

testClient = WebotsTCPClient()
testClient._clientPort = 10020
testSocket = testClient.getClientSocket()
testClient.close()

if __name__ == "__main__":
    pass