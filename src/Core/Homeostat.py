'''
Created on Mar 13, 2013

@author: stefano



'''

class Homeostat(object):
    '''
    Homeostat manages the complete homeostat by taking care of the communication between the units and between the Units and the Uniselector.
    It stores a collection of units, and some state variables representing the general state of the Homeostat at any point in time. 
    "Starting" (an instance of) this class is equivalent to turning the switch on the electro-mechanical machine built by Ashby. 
    Notice that this is typically done by the application class HomeoSimulation, which offers facilities for adding units, 
    adding connections, selecting parameters pertaining to the homeostat (weights, etcetera) and pertaining to the simulation 
    (number of iterations, print out and/or display of data, etcetera). Homeostat collaborates with DataCollector 
    (an instance of which it holds) to record its states for any instant of time it goes through. However, it does not contain any facility
     for visualizing the data themselves.  If operated manually, an instance of Homeostat requires manually setting up the various 
    parameters and does not offer any output.
    
    Instance Variables:
        homeoUnits           <Collection>     the collection of homeoUnits making up the homeostat
        microTime            <aNumber>        the temporal scale regulating the communication among units (typically identical to the unit time)
        time                 <aNumber>        the current time index (i.e., t)
        dataCollector        <aDataCollector> the object recording the states of the homeostat
        collectsData         <aBoolean>       whether or not the homeostat collects data about its run
        slowingFactor:       <milliseconds>   it slows down the simulation by inserting a slowingFactor wait after each cycle.
        isRunning            <aBoolean>       whether the homeostat is running
    '''


    def __init__(self):
        '''
        Constructor
        '''
        