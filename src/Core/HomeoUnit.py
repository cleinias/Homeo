
class HomeoUnit:
    """
    Created on Feb 19, 2013

    @author: stefano

    Homeo Unit is the fundamental element of a Homeostat.
    
    HomeoUnit represents a basic unit of Ashby's Homeostat (see Ashby's Design for a Brain, 1960, chp. 8). HomeoUnit does know about its connections to other units (including itself). 

    HomeoUnit holds the  values describing the state of the unit at time t, as specified by Ashby.
   The design of this simulation of the Homeostat  has been influenced by the C simulation described by Alice Eldridge in "Ashby's Homeostat in Simulation," unpublished, 2002, available at: http://www.informatics.sussex.ac.uk/users/alicee/NEWSITE/ecila_files/content/papers/ACEhom.pdf 

 Instance Variables:
     criticalDeviation                <Object>    deviation of the needle from equilibrium (0 state). In Ashby's original electromechanical model, this value is a function of the input current applied to the magnet that operates                                     the needle AND the possible manual operation on the needle itself
     currentOutput                <Object>    current  the unit outputs at time t. This value is proportional to criticalDeviation and typically between 0 and 1.
     inputConnections            <List>    a collection of HomeoConnections storing the units the presents unit is connected to and the associated weights. Includes a connection to itself. 
     maxDeviation                    <Object>    maximum deviation from equilibrium
     nextDeviation                     <Object>    the needle's deviation the unit will assume at at t+1. This is a function of criticalDeviation, viscosity (as a dampener), and potentiometer. It is limited at both ends by maxDeviation                                     (i.e. maxDeviation negated < nextDeviation < maxDeviation)
     outputRange                    <Dictionary>    range of the output current, keyed as low and high. Default is 0 to 1.
     viscosity                        <Object>    viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. Acts as a dampening agent on the change of output
     density:                          <Object>    the density  of the medium in which the metallic needle of the original Ashbian unit is free to move. Used to compute the drag at high velocities, if needed
     noise                            <Object>    As per Ashby's implementation, it represents the noise in the transmission medium of the unit's connection to itself. In our implementation it is always identical to the noise of a unit's first                                     connection 
     potentiometer                 <Object>    As per Ashby's implementation, it represents the weight of the unit's connection to itself. In our implementation it is always identical to the weight of a unit's first                                     connection,---Check Design for a Brain, chp.8  for details
     switch                             <Object>     As per Ashby's implementation, it represents the polarity of the connection of the unit to itself.  In our implementation it is always identical to the polarity of a unit's first                                     connection,
     time                                <integer>     the internal tick counter
     uniselectorTime             <Integer>       the internal tick counter for activation of the uniselector
     uniselectorTimeInterval    <Integer>   the number of ticks that specifies how often to check that the output is in range and eventually activate uniselector
     uniselector                     <Uniselector> the uniselector that can modifiy the weights of input values coming from other units
    uniselectorActive             <Boolean>   whether the uniselector mechanism is active or not
    needleCompMethod          <String>        whether the unit's needle's displacement depends of the sum of its input, or on the ratio bettween the sum of the inputs and the maxDeviation. possible values are 'linear' and                                     'proportional', default is 'linear'.
    inputTorque                      <aValue>       represents the input force derived from the weighed sum of the inputs (as computed by computeTorque)
    active                                <aString>     whether the unit is active or not (on or off)
    status                                     <aString>      Active, Non Active, or other possible status
    debugMode                        <aBoolean> controls whether the running methods print out debugging information
    showUniselectorAction       <aBoolean> controls whether the running methods print out when the uniselector kicks into action
    currentVelocity:                    the current velocity of the needle moving in the trough
    needleUnit                         Holds an instance of HomeoNeedleUnit, the class containing the parameters of the needle used by the unit (mass, area, etc.)

    physicalParameters    <aDictionary>     a dictionary containing equivalence factors between the simulation units and real  physicalParameters


A HomeoUnit knows how to:

- compute its next output on the basis of the input (received through connections stored in inputConnections) and its internal parameters
- add a connection with a given unit as the incoming unit
- periodically check that its outputValue has not become critical (outside the acceptable range) 
- ask the uniselector to reset the weight of its inputConnections
- print a description of itself with the values of all its parameters
 """
    def __init__(self):
        criticalDeviation = 0
        currentOutput = 0
        inputConnections = []
        maxDeviation = 0
        
    pass

