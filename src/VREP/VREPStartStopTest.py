import vrep
from time import sleep

vrep.simxFinish(-1)
simulID = vrep.simxStart('127.0.0.1',19997,True,True, 5000,5)
vrep.simxSynchronous(simulID, True)


for i in xrange(5):
    print "starting no : ", i
    print "now starting"
    vrep.simxStartSimulation(simulID, vrep.simx_opmode_oneshot_wait)
    vrep.simxSynchronousTrigger(simulID)
    sleep(4)
    print "now stopping"
    vrep.simxStopSimulation(simulID, vrep.simx_opmode_oneshot_wait)
    vrep.simxSynchronousTrigger(simulID)
    sleep(2)
    print "done with run no: ", i
