
class HomeoUnit:
    """
    Created on Feb 19, 2013

    @author: stefano

    Homeo Unit is the fundamental element of a Homeostat.
    
    HomeoUnit represents a basic unit of Ashby's Homeostat (see Ashby's Design for a Brain, 1960, chp. 8). 
    HomeoUnit does know about its connections to other units (including itself). 

    HomeoUnit holds the  values describing the state of the unit at time t, as specified by Ashby.
    The design of this simulation of the Homeostat  has been influenced by the C simulation described 
    by Alice Eldridge in "Ashby's Homeostat in Simulation," unpublished, 2002, 
    available at: http://www.informatics.sussex.ac.uk/users/alicee/NEWSITE/ecila_files/content/papers/ACEhom.pdf 

     Instance Variables:
     criticalDeviation        <Float>    Deviation of the needle from equilibrium (0 state). In Ashby's original electromechanical model, 
                                          this value is a function of the input current applied to the magnet that operates
                                          the needle AND the possible manual operation on the needle itself
     currentOutput            <Float>    The current  the unit outputs at time t. This value is proportional to criticalDeviation and typically between 0 and 1.
     inputConnections         <List>     A collection of HomeoConnections storing the units the presents unit is connected to and the associated weights. 
                                         It includes a connection to itself. 
     maxDeviation             <Float>    Maximum deviation from equilibrium
     nextDeviation            <Float>    The needle's deviation the unit will assume at at t+1. This is a function of criticalDeviation, 
                                         of viscosity (as a dampener), and potentiometer. It is limited at both ends by maxDeviation
                                         (i.e. maxDeviation negated < nextDeviation < maxDeviation)
     outputRange              <Dict>     The range of the output current, keyed as low and high. Default is 0 to 1.
     viscosity                <Float>    The viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. 
                                         It acts as a dampening agent on the change of output
     density                  <Float>    The density  of the medium in which the metallic needle of the original Ashbian unit is free to move. 
                                         Used to compute the drag at high velocities, if needed
     noise                    <Float>    As per Ashby's implementation, it represents the noise in the transmission medium 
                                         of the unit's connection to itself. In our implementation it is always identical 
                                         to the noise of a unit's first connection 
     potentiometer             <Float>   As per Ashby's implementation, it represents the weight of the unit's connection to itself. 
                                         In our implementation it is always identical to the weight of a unit's 
                                         first connection,---Check Design for a Brain, chp.8  for details
     switch                    <Integer>  As per Ashby's implementation, it represents the polarity of the connection of the unit to itself.  
                                          In our implementation it is always identical to the polarity of a unit's first connection,
     time                      <Integer>  The internal tick counter
     uniselectorTime            <Integer> The internal tick counter for activation of the uniselector
     uniselectorTimeInterval    <Integer> The number of ticks that specifies how often to check that the output is in range and eventually activate uniselector
     uniselector       <HomeoUniselector> The uniselector that can modify the weights of input values coming from other units
     uniselectorActive          <Boolean>  Whether the uniselector mechanism is active or not
     needleCompMethod          <String>    Whether the unit's needle's displacement depends of the sum of its input, 
                                          or on the ratio between the sum of the inputs and the maxDeviation. 
                                          Possible values are 'linear' and 'proportional', default is 'linear'.
    inputTorque                <Float>    It represents the input force derived from the weighed sum of the inputs (as computed by computeTorque)
    active                     <String>   Whether the unit is active or not (on or off)
    status                     <String>   Active, Non Active, or other possible status
    debugMode                  <Boolean>  It control whether the running methods print out debugging information
    showUniselectorAction      <Boolean>  It controls whether the running methods print out when the uniselector kicks into action
    currentVelocity            <Float>    The current velocity of the needle moving in the trough
    needleUnit         <HomeoNeedleUnit>  Holds an instance of HomeoNeedleUnit, the class containing the parameters 
                                          of the needle used by the unit (mass, area, etc.)
    physicalParameters        <Dict>      A dictionary containing equivalence factors between the simulation units and real physical parameters


    A HomeoUnit knows how to:

    - compute its next output on the basis of the input (received through connections stored in inputConnections) and its internal parameters
    - add a connection with a given unit as the incoming unit
    - periodically check that its outputValue has not become critical (outside the acceptable range) 
    - ask the uniselector to reset the weight of its inputConnections
    - print a description of itself with the values of all its parameters
     """

    "The unit's output range is by default -1  to 1 to express the proportion of the needle's deviation" 
    unitRange = {'high':1,'low':-1}               

#   "DefaultParameters is a class variable holding the  default values of all the various parameters of future created units."
    DefaultParameters  = dict(viscosity = 1,
                              maxDeviation=10,
                              outputRange = unitRange,
                              noise = 0,
                              potentiometer= 1,
                              time = 0,
                              inputValue=0,
                              uniselectorTime= 0,               # How often the uniselector checks the thresholds, in number of ticks
                              uniselectorTimeInterval = 10,
                              needleCompMethod= 'linear',       # switches between linear and proportional computation of displacement
                              uniselectorActivated = 0,
                              density = 1,                      # density of water
                              maxViscosity = (10^6))
    
##    Names := Set new: 5.
    
    
    def __init__(self):
        criticalDeviation = 0
        currentOutput = 0
        inputConnections = []
        maxDeviation = 0
        
    pass
