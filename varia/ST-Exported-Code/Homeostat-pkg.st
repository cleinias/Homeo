<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:07:24 am</time-stamp>
<!-- Package Homeostat* -->


<component-property>
<name>Homeostat</name> <type>package</type>
<property>prerequisiteParcels</property> <value>#(#('SUnit' '') #('MondrianBase' '') #('BOSS' '') #('Jun-OpenGL-Chart' '') #('Numerical Methods' ''))</value>
</component-property>

<component-property>
<name>Homeostat</name> <type>package</type>
<property>developmentPrerequisites</property> <value>#(#(#any 'SUnit' '') #(#any 'MondrianBase' '') #(#any 'BOSS' '') #(#any 'Jun-OpenGL-Chart' '') #(#any 'Numerical Methods' ''))</value>
</component-property>

<component-property>
<name>Homeostat</name> <type>package</type>
<property>comment</property> <value>'The Homeostat package contains all the code for Homeo, a sofware simulation of WR Ashby''s Homeostat as described in his Design for a Brain (1960, second ed.)'</value>
</component-property>

<class>
<name>PluggableRangeAdaptor</name>
<environment>UI</environment>
<super>UI.PluggableAdaptor</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>rangeStart rangeStop </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Interface-Models</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>UI.PluggableRangeAdaptor</class-id>
<body>A modification of Pluggable Adaptor that maintains two instance variables for minimum and maximum value (like RangeAdaptor, but without the grid). Like Range adaptor it is meant to be used with a slider control. However, the conversions between the model's values and the adaptor values must be explicitly done on the blocks (putBlock and SetBlock). The iVar are  useful because allow dynamic manipulation of the range at runtime. All other behavior is inherited from Pluggable adaptor."

Instance Variables:
	rangeStart	&lt;Arithmetic value&gt;	the lower bound of the adaptor's range
	rangeStop	&lt;Arithmetic value&gt;	the higher bound of the adaptor's range
</body>
</comment>

<class>
<name>WebotsConnectionTest</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>ipAddress port socketAccessor stream </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoNoiseTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit noise </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoSimulationTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>simulation </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoNoise</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>current noise mode distribution ratio randomGen </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoNoise</class-id>
<body>HomeoNoise is a utility class that provides different algorithms to deal with the computation of how noise affects the transmission of current between units 
and the flicker noise  that may affect the units' internal values. 

Instance variables:

current       &lt;aNumber&gt;    The value of the current affected by the noise
noise         &lt;aNumber&gt;     The value of the noise affecting the transmission of the current. This value is typically between 0 (no noise) and 1 (channel so noisy to block communication)
mode          &lt;aString&gt;       Mode of the noise. Possible values: 'distorting' 'degrading', indicates how the noise affects the currentWhether the noise is a		
distribution  &lt;aString&gt;		Probability distribution of the actual noise with respect to the noise value. Possible values: 'constant', 'uniform', 'normal'
ratio 		 &lt;aString&gt;        Ratio of the noise to the affected current. Possible values: 'linear' 'proportional'

It is a singleton class,  its unique instance being held in class variable NoiseCalculator. The only class creation method is newWithCurrent: andNoise: which simply updates the values of 
the instance variables if the unique instance exists already.

The noise-computing algorithm is selected by changing the valies of the three iVars mode, distribution, and ration, and then calling the method getNoise. This method constructs a selector string from the values of the ivar and calls the corresponding method. 

</body>
</comment>

<class>
<name>HomeoUnit</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>name currentOutput viscosity density maxDeviation outputRange inputConnections nextDeviation criticalDeviation noise potentiometer switch uniselector time uniselectorTimeInterval uniselectorTime uniselectorActive needleCompMethod inputTorque active status debugMode showUniselectorAction uniselectorActivated currentVelocity needleUnit physicalParameters </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUnit</class-id>
<body>HomeoUnit represents a basic unit of Ashby's Homeostat (see Ashby's Design for a Brain, 1960, chp. 8). HomeoUnit does not know about its connections to other units (including itself). The connections are managed by class Homeostat, which holds a collection of HomeoConnection, each one representing a connection between two different HomeoUnits.

HomeoUnit holds the  values describing the state of the unit at time t, as specified by Ashby.
The design of this simulation of the Homeostat  has been influenced by the C simulation described by Alice Eldridge in "Ashby's Homeostat in Simulation," unpublished, 2002, available at: http://www.informatics.sussex.ac.uk/users/alicee/NEWSITE/ecila_files/content/papers/ACEhom.pdf 

Instance Variables:
	criticalDeviation		&lt;Object&gt;	deviation of the needle from equilibrium (0 state). In Ashby's original electromechanical model, this value is a function of the input 	current applied to the magnet that operates 									the needle AND the possible manual operation on the needle itself
	currentOutput		&lt;Object&gt;	current  the unit outputs at time t. This value is proportional to criticalDeviation and typically between 0 and 1.
	inputConnections	&lt;OrderedCollectiont&gt;	a collection of HomeoConnections storing the units the presents unit is connected to and the associated weights. Includes a connection to itself. 
	maxDeviation		&lt;Object&gt;	maximum deviation from equilibrium
	nextDeviation		&lt;Object&gt;	the needle's deviation the unit will assume at at t+1. This is a function of criticalDeviation, viscosity (as a dampener), and potentiometer. It is limited at both ends by maxDeviation 									(i.e. maxDeviation negated &lt; nextDeviation &lt; maxDeviation)
	outputRange			&lt;Dictionary&gt;	range of the output current, keyed as low and high. Default is 0 to 1.
	viscosity				&lt;Object&gt;	viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. Acts as a dampening agent on the change of output
	density:                     &lt;Object&gt;    the density  of the medium in which the metallic needle of the original Ashbian unit is free to move. Used to compute the drag at high velocities, if needed
	noise				&lt;Object&gt;	As per Ashby's implementation, it represents the noise in the transmission medium of the unit's connection to itself. In our implementation it is always identical to the noise of a unit's first 									connection 
	potentiometer 		&lt;Object&gt;	As per Ashby's implementation, it represents the weight of the unit's connection to itself. In our implementation it is always identical to the weight of a unit's first 									connection,---Check Design for a Brain, chp.8  for details
	switch 				&lt;Object&gt; 	As per Ashby's implementation, it represents the polarity of the connection of the unit to itself.  In our implementation it is always identical to the polarity of a unit's first 									connection,
	time					&lt;integer&gt; 	the internal tick counter
	uniselectorTime 		&lt;Integer&gt;       the internal tick counter for activation of the uniselector
	uniselectorTimeInterval &lt;iInteger&gt;   the number of ticks that specifies how often to check that the output is in range and eventually activate uniselector
	uniselector	                 &lt;Uniselector&gt; the uniselector that can modifiy the weights of input values coming from other units
	uniselectorActive         &lt;Boolean&gt;   whether the uniselector mechanism is active or not
	needleCompMethod   &lt;String&gt;		whether the unit's needle's displacement depends of the sum of its input, or on the ratio bettween the sum of the inputs and the maxDeviation. possible values are 'linear' and 									'proportional', default is 'linear'.
	inputTorque                 &lt;aValue&gt;       represents the input force derived from the weighed sum of the inputs (as computed by computeTorque)
	active 				&lt;aString&gt; 	whether the unit is active or not (on or off)
	status  				&lt;aString&gt;      Active, Non Active, or other possible status
	debugMode 			&lt;aBoolean&gt; controls whether the running methods print out debugging information
	showUniselectorAction &lt;aBoolean&gt; controls whether the running methods print out when the uniselector kicks into action
	currentVelocity:					the current velocity of the needle moving in the trough
	needleUnit 						Holds an instance of HomeoNeedleUnit, the class containing the parameters of the needle used by the unit (mass, area, etc.)

	physicalParameters    &lt;aDictionary&gt;     a dictionary containing equivalence factors between the simulation units and real  physicalParameters


A HomeoUnit knows how to:

- compute its next output on the basis of the input (received through connections stored in inputConnections) and its internal parameters
- add a connection with a given unit as the incoming unit
- periodically check that its outputValue has not become critical (outside the acceptable range) 
- ask the uniselector to reset che weight of its inputConnections
- print a description of itself with the values of all its parameters</body>
</comment>

<class>
<name>HomeoUnitNewtonian</name>
<environment>Smalltalk</environment>
<super>HomeoUnit</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoDataUnit</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>name output criticalDeviation maxDeviation connectedTo uniselectorState uniselectorActivated </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoDataUnit</class-id>
<body>HomeoDataUnit holds the 'photograph' of a HomeoUnit unit at a certain time instant t. It contains a representation of all the variablle affecting the unit's functioning.
It knows how to read these values from a unit and how to print itself (in various ways) on a stream. Consistently with Ashby's, the time itself is not recorded, because we are assuming that the unit is in time always, and the data unit represents a particular splice of the unit's behavior.

Instance Variables:
	connectedTo			&lt;aDictionary&gt;	indexed by unit's name: it contains weight, switch, and state for every unit connected to.
	criticalDeviation		&lt;aNumber&gt;		the critical value of the unit at t
	maxDeviation 		&lt;anObject&gt;           the  maximum deviation of the unit
	name				&lt;aString&gt;		name of the unit
	output				&lt;aNumber&gt;		output value at t
	uniselectorState		&lt;aString&gt;		state of the unit's uniselector
	uniselectorActive         &lt;aNumber&gt;           indicates whether the uniselector is active at time t (thus potentially changing connections' weight for time t+1) 

</body>
</comment>

<class>
<name>HomeoUnitAristotelian</name>
<environment>Smalltalk</environment>
<super>HomeoUnit</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUnitNewtonianTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit homeostat </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoNeedleUnit</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>mass surfaceArea dragCoefficient </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoNeedleUnit</class-id>
<body>HomeoNeedleUnit holds parameters and methods describing the needle unit component of a homeostat unit

Instance Variables:
	dragCoefficient 	&lt;Object&gt;	The drag coefficient of the needle (dimensionless)
	mass			      &lt;Object&gt;	The mass of the needle in internal units. The conversion to physical units, if necessary, is done by HomeoUnits via its PhysicalParameters dictionary
	surfaceArea		&lt;Object&gt;	The surface area of the needle, in direction of travel through  fluid in the trough.  surfaceArea is expressed in  in internal units.The conversion to physical units, if necessary, is done by HomeoUnits via its PhysicalParameters dictionary.

</body>
</comment>

<class>
<name>HomeostatTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>homeostat </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>PlayerRobot</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>port robot host </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>PlayerRobot</class-id>
<body>PlayerRobot defines Player/Stage Robot objects. It contains only the most basic features necessary to interact with robot simulated in the Player/Stage environment through the JavaClient library, accessed through JavaConnect: the port and host to communicate through and  the handle to the robot. All the other interfaces (effectors, receptors, etcetera) must be provided by subclasses of this class.

Note also that the Player/Stage environment must be running with suitable configuration and world files, and the JavaPlayer Java classes must have been loaded through JavaConnect (i.e. Java virtual machine started, AND classes loaded) 

Instance Variables:

     host     &lt;aString&gt;  host on which player/client is running. default is 'localhost'

	port	&lt;Integer&gt;	the port through which the communication with the Player/Stage robot happens. The port is defined in the configuration (.cfg) file player is called with. Default is 6665

	robot	     &lt;JavaWorld.javaclient3.PlayerClient &gt;	Handle to the the Player/Stage interface of the robot, reached through a JavaConnect interface to the JavaPlayer client of the Player/Stage simulation environment

	


</body>
</comment>

<class>
<name>Vehicle</name>
<environment>Smalltalk</environment>
<super>PlayerRobot</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>leftEye rightEye position rightSpeed leftSpeed wheelSep </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>Vehicle</class-id>
<body>Vehicle is the basic Braitenberg vehicle, with two motors and two "eyes" (represented by fiducial detectors in the Player/Stage simulation). Notice that access to the motors is provided by the position2D JavaClient interface not by separate instance variables.

Instance Variables:
      position      &lt;JavaWorld.javaclient3.Position2DInterface&gt;	Handle to the the Player/Stage position interface of the robot, reached through a JavaConnect interface to the JavaPlayer client of the Player/Stage simulation environment

	leftEye	      &lt;JavaWorld.javaclient3.FiducialInterface&gt;		Handle to the the Player/Stage fiducial finder interface of the robot, reached through a JavaConnect interface to the JavaPlayer client of the Player/Stage simulation environment
	rightEye	&lt;JavaWorld.javaclient3.FiducialInterface&gt;		Handle to the the Player/Stage  fiducial finder interface of the robot, reached through a JavaConnect interface to the JavaPlayer client of the Player/Stage simulation environment

      rightSpeed &lt;aNumber&gt;  The current speed of the right wheel motor 
      
     leftSpeed    &lt;aNumber&gt;  The current speed of the left wheel motor
  
     wheelSep   &lt;aNumber&gt;  The separation, in meters, between the two wheels, used to convert right- and left- speeds to the forwardSpeed and yaw angle expected by player/stage

</body>
</comment>

<class>
<name>HomeoDataUnitTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>dataUnit unit1 </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUniselectorTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>uniselector </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUniselectorUniformRandomTest</name>
<environment>Smalltalk</environment>
<super>HomeoUniselectorTest</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUniselectorAshbyTest</name>
<environment>Smalltalk</environment>
<super>HomeoUniselectorTest</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit homeostat </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoSimulation</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>maxRuns homeostat datafile </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoSimulation</class-id>
<body>HomeoSimulation is the class that manages a complete run of the Homeostat. It takes care of the administrative task: setting up the initial conditions, starting and stopping the simulation. It also knows how to read initial conditions from a file (for repeated experiments). The real work of simulating the Homeostat is done by the Homeostat class---an instance of which is held by the simulation---and its components.

Instance Variables:
	homeostat		&lt;aHomeostat&gt;		description of homeostat
	maxRuns		&lt;anInteger&gt;		description of maxRuns
	dataFile           &lt;aString&gt;              the string corresponding to the filename the simulation data should be saved on. 


</body>
</comment>

<class>
<name>HomeostatStandardGUI</name>
<environment>Smalltalk</environment>
<super>UI.ApplicationModel</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>homeostat dataAreSaved datafile maxRuns slowingFactor currentRun uniselectorActiveChoices simulProcess dataChart controlPanelBuilder debugMode showUniselectorActionMode graphicView </inst-vars>
<class-inst-vars>maxRuns </class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeostatStandardGUI</class-id>
<body>HomeostatStandardGUI holds alll the data necessary to run a simulation of a standard 4-unit Ashby homeostat. In addition, it allows complete interactive access to the units' parameters and some facilities for saving and charting the simulation's data.
The simulation emulates real time operation of the homeostat by running through a series of discrete time steps. The delay between these discrete steps is set by default at 1 millisecond, to allow a smooth redrawing of the visual interface, but it may be changed by the user

The simulation itself is run   separate process (held in simulProcess) at a lower priority level than the interface. 

Instance Variables:
	currentRun					&lt;Object&gt;		current time step. 
	dataAreSaved				&lt;Boolean&gt;		flag to mark whether the simulaiton's data have been saved to disk (Boss out)
	dataChart					&lt;JunChartLine&gt;	the Jun object responsible for charting the data
	datafile						&lt;Symbol&gt;		the filename to save the simulation's data to
	homeostat					&lt;Homeostat&gt;	the homeostat that is being simulated
	maxRuns					&lt;ValueModel&gt;	the number of time steps we are running the simulation for.
	simulProcess				&lt;Process&gt;	        the process holding the simulation run
	slowingFactor				&lt;ValueHolder&gt;	How long (in millisecond) we are waiting between two time steps.
	uniselectorActiveChoices		&lt;Object&gt;		description of uniselectorActiveChoices
	debugMode  				&lt;Boolean&gt;		controls whether info about the units are written out to screen (slows down simulation considerably)
	showUniselectorActionMode 	&lt;Boolean&gt;		controls whether info about the uniselector action is written out to screen (slows down simulation considerably)
</body>
</comment>

<class>
<name>HomeoConnection</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>incomingUnit outgoingUnit weight switch noise state active status </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoConnection</class-id>
<body>HomeoConnection represents a connection between two HomeoUnits and holds the incoming unit (the unit the signal is coming from), the receiving unit (the unit the signal goes to---typically the unit that is holding the connection),  the weight of the connection, and the polarity of the connection.

Instance Variables:
	incomingUnit	&lt;HomeoUnit&gt;	the HomeoUnit the signal is coming from
	receivingUnit        &lt;HomeoUnit&gt;        the HomeoUnit the signal is going to (typically the unit holding on to this HomeoCnnection)
	switch			&lt;Object&gt;		polarity of the connection ( +1 or -1)
	weight			&lt;Object&gt;		weight of the connection : between 0 and 1
	noise:			&lt;Object&gt;		possible noise on the connection (between 0--no noise - to 1, so noisy to break the connection)
      state                 &lt;aString&gt;                   determines whether the connection is governed by weight and switch or by the uniselector. The value can only be "manual" or "uniselector"
	status 			&lt;aString&gt;		whether the connection is active or not. Values can be 'Yes' or 'No'
	active                &lt;aBoolean&gt;   whether or not the connection is active
</body>
</comment>

<class>
<name>PlayerTests</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoDataCollectorTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>dataCollector homeostat </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUnitTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUnitTest</class-id>
<body>HomeoUnitTest tests the HomeoUnit class

Instance Variables:
	unit	&lt;HomeoUnit&gt;	a mock object: a HomeoUnit for testing purposes

</body>
</comment>

<class>
<name>HomeoDataCollector</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>states </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoDataCollector</class-id>
<body>DataCollector collects the data for the Homestat simulation. It can output them on a variety of media (file, screen, etc) and formats, write them to file or read them from file. DataCollector DOES NOT collect the data about the homeostat itself---i.e. the engine that has produced the data. The homeostat class knows how to save itself and, conversely, how to read its data and parameters from a  saved instance.

Instance Variables:
	states	&lt;aDictionary&gt;		a collection recording a description of the states of all units, indexed by time t. It is a Dictionary indexed by time t, with each elements containing a collection of HomeoDataUnits indexed by unit's name. It cannot be an Array because the index cannot be restrained to positive numbers (1--n). Indeed, the simulation usually starts at 0, but it could reasonably start in the past. 

</body>
</comment>

<class>
<name>HomeoMinimalGUI</name>
<environment>Smalltalk</environment>
<super>UI.ApplicationModel</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoUniselector</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>lowerBound upperBound beeps </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUniselector</class-id>
<body>Uniselector is the abstract class for different kinds of mechanisms producing random values for the connection between two units. UniselectorAshby replicate as much as possible the original stepping mechanism described by Ashby. UniselectorRandom provides a simpler mechanism that simply produces a random value in the admitted interval. Other mechanism can be added by subclassing Uniselector and providing an alternative method produceNewValue.
 
Instance Variables:

	lowerBound           the lower bound of the weight, default is 0
	upperBound          the uperbound of the weight, default is 1
	beeps                    aBoolean that control whether the uniselector beeps when activated.
</body>
</comment>

<class>
<name>HomeoUniselectorUniformRandom</name>
<environment>Smalltalk</environment>
<super>HomeoUniselector</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUniselectorUniformRandom</class-id>
<body>HomeoUniselectorUniformRandom is a Uniselector that does NOT follow Ashby's model. It provides a random value uniformly distributed in the interval [lowerbound, upperBound], 
which is symmetric around 0, i.e. lowerbound = upperBound negated.
The default values for the interval are [-1, +1], but other values can be chosen. However, the accessors of lowerBound and upperBound enforce the constraint by refusing positive (resp. negative) values 
for lowerBound (resp. upperBound) and changing upperBound (resp. lowerBound) to the negated value of lowerBound (resp. upperBound). </body>
</comment>

<class>
<name>HomeoUniselectorAshbyOld</name>
<environment>Smalltalk</environment>
<super>HomeoUniselector</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>interval steps index matrix unitsControlled </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUniselectorAshbyOld</class-id>
<body>UniselectorAshby represents a Uniselector (or a 'stepping switch') as described by Ashby in Design for a Brain, sec 8/2. It divides the range of possible outputs in a number of values and steps in a random sequence through them.  Notice that Ashby's mechanism is actually the opposite: his uniselector steps sequentially through a series of random values. Ashby does not specify how he chose these numbers, except by saying that they were taken from Fisher and Yates' Table of Random Numbers. It is plausible to assume that Ashby's values cover the whole range of possible values, i.e. from -1 to +1. Ashby specifies that the uniselector had 25 possible positions, and we interprete that number as representing 12 possible negative values, 0, and 12 possible positive values. Therefore, we construct, in the default case,  a list of 25 equally spaced values from -1 to +1, we randomize the list, and produce the next value from the list at any iteration..



interval 			aNumber   		       a fraction of the acceptable range for the output weight, default is 1/12
index      		      anInteger  		       the value last chosen
steps      			anInteger  		      the number of intervals the range of possible output values is divided into, default is 12.
matrix 		     	      aMatrix  			the matrix holding the values for the sequence through the steps (one row per step, one column per connection)  
</body>
</comment>

<class>
<name>HomeoUniselectorAshby</name>
<environment>Smalltalk</environment>
<super>HomeoUniselector</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unitIndex ashbyKind interval steps index matrix unitsControlled </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUniselectorAshby</class-id>
<body>HomeoUniselectorAshby2 is a different implementation of Ashby's (sparsely decribed!) algorithm.  It simulates a stepping switch (or Uniselector) that advances one step every time it is activated. At every step the uniselector produces weight values ofr the HomeoUnits connections. The simulation is implemented  with a m x n matrix (the ivar sequence) where m are the steps of the uniselector, and n are the number of connected units. In Ashby's clasical homeosta m= 25, n = 3.  The values in the matrix are produced according to three different algorithms, each a different intepretation of Ashby's original idea. the string deciding which production method to use is held in ashbyKind.

Instance Variables:
	unitsControlled &lt;anInteger&gt;	The maximum number of units this uniselector controls. Default values is 10. It will be incremented in 10-units increment if needed
	unitIndex         &lt;anInteger&gt;      The index keeping track of which unit's connection we are currently producing a value (a weight) for.
	ashbyKind       &lt;aString&gt;          The string determining which initialization (and re-initialization) method to use.  

</body>
</comment>

<class>
<name>HomeoUniselectorAshbyTest2</name>
<environment>Smalltalk</environment>
<super>HomeoUniselectorAshbyTest</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars></inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>HomeoConnectionTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit1 unit2 connection uniSelector </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<class>
<name>Homeostat</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>time homeoUnits microTime dataCollector collectsData isRunning slowingFactor </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>Homeostat</class-id>
<body>Homeostat manages the complete homeostat by taking care of the communication between the units and between the Units and the Uniselector. It stores a collection of units, and some state variables representing the general state of the Homeostat at any point in time. "Starting" (an instance of) this class is equivalent to turning the switch on  the electro-mechanical machine built by Ashby. Notice that this is typically done by the application class HomeoSimulation, which offers facilities for adding units, adding connections, selecting parameters pertaining to the homeostat (weights, etcetera) and pertaining to the simulation (number of iterations, print out and/or display of data, etcetera). Homeostat collaborates with DataCollector (an instance of which it holds) to record its states for any instant of time it goes through. However, it does not contain any facility for visualizing the data themselves.  If operated manually, an instance of Homeostat requires manually setting up the various parameters and does not offer any output.

Instance Variables:
	homeoUnits			&lt;Collection&gt;		the collection of homeoUnits making up the homeostat
	microTime			&lt;aNumber&gt;		the temporal scale regulating the communication among units (typically identical to the unit time)
	time					&lt;aNumber&gt;		the current time index (i.e., t)
	dataCollector 		&lt;aDataCollector&gt; the object recording the states of the homeostat
	collectsData 		&lt;aBoolean&gt;		whether or not the homeostat collects data about its run
	slowingFactor:		&lt;milliseconds&gt;     it slows down the simulation by inserting a slowingFactor wait after each cycle.
		
</body>
</comment>










<shared-variable>
<name>DefaultParameters</name>
<environment>HomeoNeedleUnit</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>






<shared-variable>
<name>NoiseCalculator</name>
<environment>HomeoNoise</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<initializer></initializer>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>
























<shared-variable>
<name>DefaultParameters</name>
<environment>HomeoUnit</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<initializer>Dictionary new</initializer>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>


<shared-variable>
<name>Names</name>
<environment>HomeoUnit</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<initializer>Set new: 5</initializer>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>



<methods>
<class-id>HomeoDataCollector</class-id> <category>converting</category>

<body package="Homeostat" selector="criticalDevAsCollectionForUnit:">criticalDevAsCollectionForUnit: aHomeoUnit 
	"Extracts the Critical Deviaton values for aHomeoUnits and returns them as an Ordered Collection"

	| aCollection |
	aCollection := OrderedCollection new.
	states do: 
			[:each | 
			each isNil 
				ifFalse: 
					[each keysAndValuesDo: 
							[:key :value | 
							key = aHomeoUnit name ifTrue: [ aCollection add: (value criticalDeviation)]]]].
	^aCollection</body>

<body package="Homeostat" selector="uniselectorActivatedAsCollectionOfArraysForAllUnits">uniselectorActivatedAsCollectionOfArraysForAllUnits 
	"Extracts the data about the activation of the uniselector  for all units  and returns them as an Ordered Collection of Arrays. Each array has all the values for a point in time"

	| aCollection  |
	aCollection := OrderedCollection new.
	states do: 
			[:each | 
			each isNil 
				ifFalse: 
					[
					  | dataPoint | 
					   dataPoint := OrderedCollection new .
					   each do: 
							[:value | 
							dataPoint add: value uniselectorActivated].
			aCollection add: dataPoint asArray]].




	^aCollection.</body>

<body package="Homeostat" selector="criticalDevAsCollectionOfArraysForAllUnits">criticalDevAsCollectionOfArraysForAllUnits 
	"Extracts the Critical Deviaton homeoDataunits for all units  and returns them as an Ordered Collection of Arrays. Each array has all the homeoDataunits for a point in time"

	| aCollection  |
	aCollection := OrderedCollection new.
	states do: 
			[:stateAtTick | 
			stateAtTick isNil 
				ifFalse: 
					[
					  | dataPoint | 
					   dataPoint := OrderedCollection new .
					   stateAtTick do: 
							[:homeoDataunit | 
							dataPoint add: homeoDataunit criticalDeviation.
							dataPoint add: homeoDataunit uniselectorActivated].
			aCollection add: dataPoint asArray]].




	^aCollection.</body>
</methods>

<methods>
<class-id>HomeoDataCollector</class-id> <category>saving</category>

<body package="Homeostat" selector="saveDeviationOn:forUnit:">saveDeviationOn: aStream forUnit: aUnit

"Saves the output of the simulation on a stream (typically associated to a file by the calling app) as a series of lines, one per time tick, each comprising the critical deviation  value for aUnit.
Need to strip the type information (the trailing 'd') from the text representation of a double produced by printString "

| str |

states do: [
	:timeItem |
	timeItem do: [
		:dataUnit |
		(dataUnit = aUnit)
			ifTrue: 
				[str := ReadStream on: (dataUnit  output printString).
				aStream nextPutAll: (str upTo: $d)].
				aStream nextPut: Graphics.TextConstants.CR]]</body>

<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename

"save itself on a new boss file opened on aFilename. It will erase the old content of aFilename"
| boss |
boss := BinaryObjectStorage onNew: aFilename writeStream.
boss nextPut: self.
boss close.</body>

<body package="Homeostat" selector="saveEssentialsOn:separator:">saveEssentialsOn: aStream separator: aCharacter

"Saves the output of the simulation on a stream (typically associated to a file by the calling app) as a series of lines, one per time tick, each comprising a row of output values separated by aCharacter.
Need to strip the type information (the trailing 'd') from the text representation of a double produced by printString "

| str |
states do: [
	:timeItem |
	timeItem do: [
		:dataUnit |
		str := ReadStream on: (dataUnit  output printString).
		aStream nextPutAll: (str upTo: $d); 
				 nextPut: aCharacter.].
	aStream nextPut: Graphics.TextConstants.CR.
	]</body>
</methods>

<methods>
<class-id>HomeoDataCollector</class-id> <category>accessing</category>

<body package="Homeostat" selector="states">states
	^states</body>

<body package="Homeostat" selector="at:addDataUnitFor:">at: timeIndex addDataUnitFor: aHomeoUnit

"adds a dataunit for aHomeoUnit representing the latter state at time timeIndex"

states isNil ifTrue: [states := Dictionary new].

(states includesKey:  timeIndex) ifFalse: [states at: timeIndex put: Dictionary new].

(states at: timeIndex) at: (aHomeoUnit name) put: (HomeoDataUnit newUnitFor: aHomeoUnit).</body>

<body package="Homeostat" selector="states:">states: anObject
	states := anObject</body>
</methods>

<methods>
<class-id>HomeoDataCollector</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>

<methods>
<class-id>HomeoDataCollector</class-id> <category>printing</category>

<body package="Homeostat" selector="printPlottingDataOn:withSeparator:">printPlottingDataOn: aStream withSeparator: aCharacter

"appends to aStream a multi-column  representation of its data, suitable for plotting. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  |

unitNames := OrderedCollection new.
states size &lt; 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPutAll: '# '.
unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData do: [ :timeSlice |
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>

<body package="Homeostat" selector="printEssentialDataForUnit:On:">printEssentialDataForUnit: aHomeoUnit On: aStream

"appends to aStream a brief representation of  aHomeoUnit data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name ifTrue: [
						aStream nextPutAll: 'time: ';
						nextPutAll: timeIndex printString;
						nextPutAll: '  ';
						nextPutAll: (value name) , ': '.
						value printEssentialVariableOn:  aStream]].
				timeIndex := timeIndex + 1.]].</body>

<body package="Homeostat" selector="printCompleteDataOn:">printCompleteDataOn: aStream


"appends to aStream a complete representation of its data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each do: [
					:value |
					aStream nextPutAll: 'time: ';
					nextPutAll: timeIndex printString;
					nextPutAll: '  '.
					value printDataOn:  aStream].
			timeIndex := timeIndex + 1.]].</body>

<body package="Homeostat" selector="printCriticalDevForUnit:On:">printCriticalDevForUnit: aHomeoUnit On: aStream

"appends to aStream the values for Critical Deviation of aHomeoUnit "


states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name 
						ifTrue: [
							value printCriticalDeviationOn:  aStream]]]].</body>

<body package="Homeostat" selector="printPlottingDataForGgobiOn:">printPlottingDataForGgobiOn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit 
Notice that we convert datapoints  to a fixed number of decimal and we strip the trailing s that VisualWorks appends to the literal represntation of a fixed Number "




| criticDevData unitNames  aCharacter decimals|

decimals := 8.    "The number of fixed decimals we keep. Data points are double and may have up to 15 digits, sometimes expressed in exponential notation"

aCharacter := $,.

unitNames := OrderedCollection new.
states size &lt; 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.


"Print  the column headers"
aStream nextPutAll: 'Time,'.
unitNames do: [:name |
				 aStream nextPutAll: (name printStringNoQuotes);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printStringNoQuotes), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData doWithIndex: [ :timeSlice : index  |
			aStream nextPutAll: index printString;
					 nextPut: aCharacter.
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: (dataPoint asFixedPoint: decimals)  printString) upTo: $s); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>

<body package="Homeostat" selector="printEssentialDataOn:">printEssentialDataOn: aStream

"appends to aStream a brief representation of its data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each do: [
					:value |
					aStream nextPutAll: 'time: ';
					nextPutAll: timeIndex printString;
					nextPutAll: '  ';
					nextPutAll: (value name) , ': '.
					value printEssentialVariableOn:  aStream].
			timeIndex := timeIndex + 1.]].</body>

<body package="Homeostat" selector="printPlottingDataForROn:">printPlottingDataForROn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting with the R softwre package. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  aCharacter |

aCharacter := $,.

unitNames := OrderedCollection new.
states size &lt; 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr).

"Print  the column headers, preceded by the 'Time' Header"
aStream nextPutAll:  'Time';  nextPut: aCharacter.

unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData doWithIndex: [ :timeSlice : index  |
			aStream nextPutAll: index printString;
					 nextPut: aCharacter.
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>

<body package="Homeostat" selector="printPlottingDataOn:">printPlottingDataOn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting. The format includes:

first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  |

unitNames := OrderedCollection new.
states size &lt; 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPutAll: '# '.
unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPut: Character tab]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData do: [ :timeSlice |
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
											nextPut: (Character tab);
											nextPut: (Character tab);
											nextPut: (Character tab)].
			aStream nextPut: (Character cr)].
aStream close.</body>

<body package="Homeostat" selector="printCompleteDataForUnit:On:">printCompleteDataForUnit: aHomeoUnit On: aStream

"appends to aStream a brief representation of  aHomeoUnit data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name ifTrue: [
						aStream nextPutAll: 'time: ';
						nextPutAll: timeIndex printString;
						nextPutAll: '  '.
						value printDataOn:  aStream]].
				timeIndex := timeIndex + 1.]].</body>
</methods>


<methods>
<class-id>Homeostat class</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="new">new

^ super new initialize
</body>
</methods>

<methods>
<class-id>Homeostat class</class-id> <category>private-saving</category>

<body package="Homeostat" selector="homeoUnits:microTime:dataCollector:collectsData:">homeoUnits: homeostatHomeoUnits microTime: homeostatMicroTime dataCollector: homeostatDataCollector collectsData: homeostatCollectsData
	"used by the Boss mechanism to store a homeostat on a boss file"

^self new
	setHomeoUnits: homeostatHomeoUnits
	microTime: homeostatMicroTime
	dataCollector: homeostatDataCollector
	collectsData: homeostatCollectsData</body>
</methods>


<methods>
<class-id>Homeostat</class-id> <category>testing</category>

<body package="Homeostat" selector="hasUnit:">hasUnit: aHomeoUnit

"check whether the Homeostat includes aHomeoUnit"

^homeoUnits includes: aHomeoUnit</body>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo
	"Checks that the homeostat has all the needed elements to start the simulation:
 - at least 1 homeoUnit
 - the homeoUnits are not missing any essential parameter
 - (Other conditions that are not fully clear yet to be added later)
"

	^self homeoUnitsArePresent and: [self homeoUnitsAreReady]</body>

<body package="Homeostat" selector="isConnectedFrom:to:">isConnectedFrom: aHomeoUnit to: anotherUnit 


	((homeoUnits includes: aHomeoUnit) and: [homeoUnits includes: anotherUnit]) 
		ifTrue: [^anotherUnit isConnectedTo: aHomeoUnit]</body>

<body package="Homeostat" selector="sameAs:">sameAs: aHomeostat
	"checks whether two homeostats are equivalent"


| result |

result := true.
"receiver is a homeostat"

( aHomeostat class = Homeostat)
	ifFalse: [^false].

"Same number of units"

(self homeoUnits size = aHomeostat homeoUnits size)
	ifFalse: [^false].

"equivalent units"

self homeoUnits 
	with: (aHomeostat homeoUnits)
		do: 
		[ :firstUnit :secondUnit |
		result := result and: [firstUnit sameAs: secondUnit]].


^result</body>

<body package="Homeostat" selector="homeoUnitsAreReady">homeoUnitsAreReady

"checks that all units are ready"

^ homeoUnits inject: true into:  [:aBoolResult :unit | aBoolResult	and: [unit isReadyToGo]].</body>

<body package="Homeostat" selector="homeoUnitsArePresent">homeoUnitsArePresent
	"Checks that the minimun number of units are present. This is set to one, but the method is here so it can be overriden in subclasses and/or changed in the future."

	^homeoUnits size &gt; 0.</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>running</category>

<body package="Homeostat" selector="timeReset">timeReset
"resets time to 0. Does not change the external values of the units or their connections, but do change their internal, computational values: input, nextdeviation, etcetera"

	self time: 0.
	homeoUnits do: [ :unit |
				unit clearFutureValues]</body>

<body package="Homeostat" selector="runOnce">runOnce

"advance the simulation by one tick"
| upTo |

upTo := time + 1.
self runFor: upTo.</body>

<body package="Homeostat" selector="fullReset">fullReset
"Resets the values of the units and  their connections to random values. resets time to 0."

self timeReset.
self randomizeValuesforAllUnits.
</body>

<body package="Homeostat" selector="stop">stop

"stop the homeostat's running by changing the value of the isRunning ivar to false. This procedure is equivalent, and indeed wants to simulate, turning the switch off on the physical equivalent of the homeostat"

isRunning := false.</body>

<body package="Homeostat" selector="runFor:">runFor: ticks
	"start the simulation by setting the units 'in motion' and runs for a certain number of ticks. This involves cycling though the units and asking them to update themselves, then collecting data for each unit
 	First checks that it has enough data to start"


| delay |
delay := Delay forMilliseconds: slowingFactor.

	self isReadyToGo 
		ifTrue: 
			[time isNil ifTrue: [time := 0].
			"TESTING
			Transcript show: 'INITIAL DATA AT TIME: '; 
					   show: time printString; 
					    show: 'and tick: '; show: ticks printString; cr.
	
	        	homeoUnits do: [:unit |           
					Transcript show: unit name printString;  show: '   '; 
				                           show: unit currentOutput printString; show: '    ';
							   show: 'dev: ';
							   show: unit criticalDeviation printString;  cr].
			END TESTING"
			[time &lt; (ticks)] whileTrue: [
				homeoUnits do: 
						[:unit | 
						collectsData ifTrue: [dataCollector at: time addDataUnitFor: unit.
						unit time: time.
						unit isActive ifTrue: [unit selfUpdate].
						]].
				self time: (self time + 1).
				delay wait ]]
		ifFalse: [Transcript show: 'Warning: Homeostat is not ready to start'].
	"TESTING
		Transcript show: 'FINAL DATA AT TIME: '; show: time  printString; show: 'and tick: '; show: ticks printString; cr.
		homeoUnits do: [:unit | Transcript show: unit name printString;  show: '   '; 
									    show: unit currentOutput printString; show: '    ';
									    show: 'dev: ';
									    show: unit criticalDeviation printString;  cr].
	END TESTING"</body>

<body package="Homeostat" selector="start">start
	"start the simulation by setting the units 'in motion'. This involves cycling though the units and asking them to update themselves, then collecting data for each unit
 	First checks that it has enough data to start
	Notice that once started the Homeostat goes on forever. The only way to stop it is to send it the message stop."

	self isReadyToGo 
		ifTrue: 
			[time isNil ifTrue: [time := 0].
			isRunning := true.
			[isRunning] whileTrue: [
				homeoUnits do: 
						[:unit | 
						unit time: time.
						unit selfUpdate.
						collectsData ifTrue: [dataCollector at: time addDataUnitFor: unit].
						self time: (self time + 1)]]]
		ifFalse: [Transcript show: 'Warning: Homeostat is not ready to start']</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Sets the time to 0, and microTime to 0 as well, reflecting the default conditions of a Homeostat. Sets also some physical equivalence parameters"

	time := 0.
	microTime := 0.
	homeoUnits := OrderedCollection new.
	dataCollector := HomeoDataCollector new.
	collectsData := true. "default is to collect data. Can be turned off via accessor."
	slowingFactor := 10.


	 
	^self</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>printing</category>

<body package="Homeostat" selector="printOn:">printOn: aStream
	"personalized view of the homeostat. Default begavior so far."


super printOn: aStream.
</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>adding</category>

<body package="Homeostat" selector="addUnit:">addUnit: aHomeoUnit 
	"adds a new unit to the homeostat"

	homeoUnits isNil ifTrue: [homeoUnits := OrderedCollection new].
	(homeoUnits includes: aHomeoUnit) 
		ifFalse: 
			[homeoUnits add: aHomeoUnit.
			self changed: #numberOfUnits]</body>

<body package="Homeostat" selector="addFullyConnectedUnit:">addFullyConnectedUnit: aHomeoUnit 
	"adds aHomeoUnit to the homeostat and creates connections between the new units and all other HomeoUnits already present. This latter task is actually delegated to the units themselves. Notice that the connection are uni-directional, and we need to add connections twice: from the new unit to the existing ones and from the exiting one to the new unit."

	homeoUnits do: 
			[:each | 
			each addConnectionWithRandomValues: aHomeoUnit.
			aHomeoUnit addConnectionWithRandomValues: each.
			each maxConnectedUnits: (homeoUnits size) + 1].		   "let the old units know that there may be a new connected unit."		
	aHomeoUnit maxConnectedUnits: homeoUnits size.                       "let the new unit know how many other units there may be."
	self addUnit: aHomeoUnit.
	self changed: #numberOfUnits</body>

<body package="Homeostat" selector="addConnectionWithRandomValuesFrom:to:">addConnectionWithRandomValuesFrom: unit1 to: unit2 
	"checks that the units exist, and adds a connection with random values by asking the receving unit to do the job"

	((homeoUnits includes: unit1) and: [homeoUnits includes: unit2]) 
		ifTrue: [unit2 addConnectionWithRandomValues: unit1]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>accessing</category>

<body package="Homeostat" selector="collectsData:">collectsData: anObject
	collectsData := anObject</body>

<body package="Homeostat" selector="slowingFactor:">slowingFactor: anObject
	slowingFactor := anObject.
	self changed: #slowingFactor.</body>

<body package="Homeostat" selector="microTime:">microTime: anObject
	microTime := anObject</body>

<body package="Homeostat" selector="slowingFactor">slowingFactor
	^slowingFactor</body>

<body package="Homeostat" selector="homeoUnits:">homeoUnits: anObject
	homeoUnits := anObject</body>

<body package="Homeostat" selector="microTime">microTime
	^microTime</body>

<body package="Homeostat" selector="numberOfUnits">numberOfUnits

^ homeoUnits size</body>

<body package="Homeostat" selector="isRunning">isRunning
	^isRunning</body>

<body package="Homeostat" selector="dataCollector:">dataCollector: anObject
	dataCollector := anObject</body>

<body package="Homeostat" selector="collectsData">collectsData
	^collectsData</body>

<body package="Homeostat" selector="isRunning:">isRunning: anObject
	isRunning := anObject</body>

<body package="Homeostat" selector="time:">time: anObject
	time := anObject.
	self changed: #time</body>

<body package="Homeostat" selector="dataCollector">dataCollector
	^dataCollector</body>

<body package="Homeostat" selector="time">time
	^time</body>

<body package="Homeostat" selector="homeoUnits">homeoUnits
	^homeoUnits</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>private-saving</category>

<body package="Homeostat" selector="setHomeoUnits:microTime:dataCollector:collectsData:">setHomeoUnits: homeostatHomeoUnits microTime: homeostatMicroTime dataCollector: homeostatDataCollector collectsData: homeostatCollectsData
	"used by the Boss mechanism to store a homeostat on a boss file"

homeoUnits := homeostatHomeoUnits. 
microTime:= homeostatMicroTime.
dataCollector := homeostatDataCollector.
collectsData := homeostatCollectsData.</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>private-updating</category>

<body package="Homeostat" selector="allChanged">allChanged
	"informs all dependentss that each aspect may have changed"

	self changed: #slowingFactor.
	self changed: #time.
	self changed: #numberOfUnits.
	homeoUnits 
		do:[
			:unit |
			unit allChanged]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>removing</category>

<body package="Homeostat" selector="removeConnectionFrom:to:">removeConnectionFrom: unit1 to: unit2 
	"removes a connections between two units by asking the receiving unit (unit2) to remove the inmputConnection coming from unit1"

	((homeoUnits includes: unit1) and: [homeoUnits includes: unit2]) 
		ifTrue: 
			[(self isConnectedFrom: unit1 to: unit2) 
				ifTrue: [unit2 removeConnectionFromUnit: unit1]]</body>

<body package="Homeostat" selector="removeUnit:">removeUnit: aHomeoUnit 
	"remove a unit from the homeostat. Must also remove all the connections originating from the unit"

	(homeoUnits includes: aHomeoUnit) 
		ifTrue: 
			[homeoUnits remove: aHomeoUnit.
			homeoUnits do: [:each | each removeConnectionFromUnit: aHomeoUnit].
			self changed: #numberOfUnits]
		ifFalse: [Transcript show: 'Warning: trying to remove the unit ', (aHomeoUnit name), ', which is not part of  the Homeostat';cr]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>units managing</category>

<body package="Homeostat" selector="randomizeValuesforAllUnits">randomizeValuesforAllUnits
"resets all units to random values"

homeoUnits do: [:each | 
				self randomizeValuesFor: each. 
				each randomizeAllConnectionValues].</body>

<body package="Homeostat" selector="randomizeValuesFor:">randomizeValuesFor: aHomeoUnit 
	"resets the values of a unit to random values"

	(homeoUnits includes: aHomeoUnit) 
		ifFalse: [^self]
		ifTrue: [(homeoUnits detect: [:unit | unit = aHomeoUnit]) setRandomValues]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>saving</category>

<body package="Homeostat" selector="flushData">flushData

"clears all data from aDataCollector"

self initializeDataCollection.
</body>

<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename 
	"bosses itself out on a file opened on aFilename. It will erase the old content of aFilename."

	| boss homeoCopy |
	homeoCopy := self copyWithoutDependents.
	boss := BinaryObjectStorage onNew: aFilename writeStream.
	[boss nextPut: homeoCopy] ensure: [boss close]</body>

<body package="Homeostat" selector="initializeDataCollection">initializeDataCollection

"trashes the dataCollector, effectively flushing all collected data"

dataCollector := HomeoDataCollector new.</body>

<body package="Homeostat" selector="copyWithoutDependents">copyWithoutDependents
	"returns a copy of the homeostat with no dependents in the homeostat, homeoUnits, or homeoConnections"

	| trueCopy homeoCopy |
	trueCopy := self generalCopy.
	homeoCopy := trueCopy copy breakDependents.
	homeoCopy homeoUnits do: 
			[:unit | 
			unit inputConnections do: 
					[:conn | 
"					|  connCachedDeps incomingUnitCachedDeps |
					connCachedDeps := conn dependents.
					incomingUnitCachedDeps := conn incomingUnit dependents.
"					conn incomingUnit breakDependents.
					conn breakDependents].
			unit breakDependents].
	^homeoCopy</body>
</methods>


<methods>
<class-id>HomeoMinimalGUI class</class-id> <category>interface specs</category>

<body package="Homeostat" selector="windowSpec">windowSpec
	"Tools.UIPainter new openOnClass: self andSelector: #windowSpec"

	&lt;resource: #canvas&gt;
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#label: 'Simulation general settings' 
			#bounds: #(#{Graphics.Rectangle} 512 384 792 544 ) ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 193 122 246 142 ) 
					#name: #OKButton 
					#label: 'Apply' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 122 122 175 142 ) 
					#name: #CancelButton 
					#label: 'Cancel' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 24 ) 
					#name: #maxRunsLabel 
					#label: 'Maximum runs' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 51 ) 
					#name: #dataFileLabel 
					#label: 'Results saved on:' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 79 ) 
					#name: #UnitNumberLabel 
					#label: 'Number of units: ' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 21 245 43 ) 
					#name: #maxRuns ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 48 245 70 ) 
					#name: #datafile ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 76 245 98 ) 
					#name: #unitsNumber ) ) ) )</body>
</methods>


<methods>
<class-id>HomeoConnection class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"creates a new connection with  initialized values"

	^ super new initialize.
	</body>

<body package="Homeostat" selector="incomingUnit:weight:switch:noise:state:active:">incomingUnit: aUnit weight: aWeight switch: aSwitch noise: aNoise state: aState active: anActive


^self new 
	setIncomingUnit:  aUnit 
	weight: aWeight 
	switch: aSwitch 
	noise: aNoise 
	state: aState 
	active: anActive.</body>

<body package="Homeostat" selector="incomingUnit:receivingUnit:weight:switch:noise:state:active:">incomingUnit: aUnit receivingUnit: anotherUnit weight: aWeight switch: aSwitch noise: aNoise state: aState active: anActive


^self new 
	setIncomingUnit:  aUnit 
      
	weight: aWeight 
	switch: aSwitch 
	noise: aNoise 
	state: aState 
	active: anActive.</body>

<body package="Homeostat" selector="newFrom:to:">newFrom: aHomeoUnit to: anotherUnit
	"creates a new connection with  the incoming and outgoing units "

	| conn |
	conn := super new initialize.
	conn outgoingUnit: aHomeoUnit.
	conn incomingUnit: anotherUnit.
	^conn.</body>
</methods>


<methods>
<class-id>HomeoConnection</class-id> <category>testing</category>

<body package="Homeostat" selector="isActive">isActive

^status = 'Yes'</body>

<body package="Homeostat" selector="sameAs:">sameAs: aConnection 
	"tests if two connections are the same, which means:

	- same parameters, 

	- same incoming Unit  (first level parameters only)

	Notice that since incoming units have, in turn, input connections, we cannot pursue the testing that deep because we may enter into a loop. We only check the first level parameters"

	^weight = aConnection weight and: 
			[switch = aConnection switch and: 
					[noise = aConnection noise and: 
							[state = aConnection state and: 
									[status = aConnection status 
										and: [incomingUnit sameFirstLevelParamsAs: aConnection incomingUnit]]]]]</body>
</methods>

<methods>
<class-id>HomeoConnection</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="randomizeConnectionValues">randomizeConnectionValues
	" initialize the connection to some random value for noise and weight, set the default state to 'uniselector'"

	| randWeight randNoise randSwitch |
	randWeight := Random new nextBetween: 0 and: 1.
	randNoise := Random new nextBetween: 0 and: 0.1.
	randSwitch := (Random new nextBetween: -1 and: 1) sign.
	noise := randNoise.
	self changed: #noise.
	weight := randWeight.
	self changed: #weight.
	state := 'uniselector'.
	switch := randSwitch.
	self changed: #switch.

	active := true.
	status := 'Yes'.
	self changed: #status.</body>

<body package="Homeostat" selector="initialize">initialize

self randomizeConnectionValues</body>
</methods>

<methods>
<class-id>HomeoConnection</class-id> <category>accessing</category>

<body package="Homeostat" selector="activate">activate

active:= true.
self changed: #active.</body>

<body package="Homeostat" selector="outgoingUnit:">outgoingUnit: aHomeoUnit
	"Adds the receiving unit to the connection"

	outgoingUnit := aHomeoUnit.
	self changed: #outgoingUnit.</body>

<body package="Homeostat" selector="output">output
	"outputs the value of the connection times the weight, possibly switched,  and it includes  the noise. The latter is computed with the help of the HomeoNoise utility class. Several different algorithms are available, see the instance methods of HomeoNoise for details. "

| newNoise  |

newNoise := (HomeoNoise newWithCurrent: (incomingUnit currentOutput)  andNoise: noise).

newNoise normal.          "select noise as normally (Gaussian)  distributed around the value for the unit's connection noise"
newNoise distorting.    "select  noise as distorting the current"
newNoise proportional. "consider the noise on the communication line as a ration of the current being transmitted"

^ (incomingUnit currentOutput * switch * weight) + newNoise getNoise.</body>

<body package="Homeostat" selector="incomingUnit">incomingUnit
	^incomingUnit</body>

<body package="Homeostat" selector="noise">noise
	^noise</body>

<body package="Homeostat" selector="status:">status: anObject
	status := anObject</body>

<body package="Homeostat" selector="disactivate">disactivate

active:= false.
self changed: #active.</body>

<body package="Homeostat" selector="outgoingUnit">outgoingUnit
	^receivingUnit</body>

<body package="Homeostat" selector="switch">switch
^ switch</body>

<body package="Homeostat" selector="noise:">noise: anObject

noise := anObject.
self changed: #noise</body>

<body package="Homeostat" selector="switchToManual">switchToManual
	"changes the state of the connection to manual"

	state := 'manual'.
	self changed: #state</body>

<body package="Homeostat" selector="state:">state: aString
		
	"raise an exception if the input value is neither 'manual' or 'uniselector'"

(aString = 'manual' or: [aString = 'uniselector'] ) ifTrue: [state := aString] ifFalse: [Error raiseSignal: 'Only accepted values are: "uniselector" or "manual" '].
self changed: #state</body>

<body package="Homeostat" selector="switchToUniselector">switchToUniselector
	"changes the state of the connection to uniselector"

	state := 'uniselector'.
	self changed: #state</body>

<body package="Homeostat" selector="newWeight:">newWeight: aWeight

	"updates weight and switch on the basis-1 &lt;=  aWeight &lt;= 1"

weight:= aWeight abs.
switch := aWeight sign.

self changed: #switch.
self changed: #weight.</body>

<body package="Homeostat" selector="weight">weight
	^weight</body>

<body package="Homeostat" selector="weight:">weight: anObject
	
"this should not be used. The correct method is newWeight: a value, which takes care of absolute value and polarity (switch)"
weight := anObject.
self changed: #weight</body>

<body package="Homeostat" selector="switch:">switch: anObject
	switch := anObject</body>

<body package="Homeostat" selector="state">state
	^state</body>

<body package="Homeostat" selector="incomingUnit:">incomingUnit: aHomeoUnit
	"Adds the incoming unit to the connection"

	incomingUnit := aHomeoUnit.
	self changed: #incomingUnit.</body>

<body package="Homeostat" selector="active:">active: anObject
	active := anObject</body>

<body package="Homeostat" selector="active">active
	^active</body>

<body package="Homeostat" selector="status">status
	^status</body>
</methods>

<methods>
<class-id>HomeoConnection</class-id> <category>private-saving</category>

<body package="Homeostat" selector="setIncomingUnit:weight:switch:noise:state:active:">setIncomingUnit:  aUnit weight: aWeight switch: aSwitch noise: aNoise  state: aState active: anActive

"used by Boss for saving purposes (to recreate an instance of the class as MessageSend)"


incomingUnit :=  aUnit.
 weight := aWeight.
 switch := aSwitch.
 noise := aNoise.
 state := aState.
 active := anActive.</body>

<body package="Homeostat" selector="setIncomingUnit:setOutgoingUnit:weight:switch:noise:state:active:">setIncomingUnit:  aUnit setOutgoingUnit: anotherUnit weight: aWeight switch: aSwitch noise: aNoise  state: aState active: anActive

"used by Boss for saving purposes (to recreate an instance of the class as MessageSend)"


incomingUnit :=  aUnit.
outgoingUnit := anotherUnit.
 weight := aWeight.
 switch := aSwitch.
 noise := aNoise.
 state := aState.
 active := anActive.</body>
</methods>


<methods>
<class-id>HomeoSimulationTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoSimulationTest</class-id> <category>running</category>

<body package="Homeostat" selector="testDataFileIsPresent">testDataFileIsPresent

self assert: (simulation datafile notNil)</body>

<body package="Homeostat" selector="testAddConnection">testAddConnection
|unit1 unit2 |	

unit1 := HomeoUnit new.
unit2 := HomeoUnit new.


simulation homeostat addUnit: unit1.	"create a  2-unit homeostat"
simulation homeostat addUnit: unit2.	
1 to: 2 do: [:i | self assert: (simulation homeostat homeoUnits at: i) inputConnections size = 1].	"all units are self-connected and self-connected only"


	"add a connection from the second unit to first one"
	simulation homeostat addConnectionWithRandomValuesFrom: unit2 to: unit1.
	"check that the first unit has now two connections"
	self assert: ((simulation homeostat homeoUnits at: 1) inputConnections size = 2).	"all units are self-connected and self-connected only"
	self assert: ((unit1 inputConnections size) = 2)</body>

<body package="Homeostat" selector="testReadConditionsFromFile">testReadConditionsFromFile

self assert: false.</body>

<body package="Homeostat" selector="testAddFullyConnectedUnit">testAddFullyConnectedUnit

| unitsAdded| 
unitsAdded := 5.
simulation addFullyConnectedUnit: HomeoUnit new.
self assert: (simulation homeostat homeoUnits size = 1).
self assert: ((simulation homeostat homeoUnits at: 1) inputConnections size = 1).
unitsAdded timesRepeat:  [simulation addFullyConnectedUnit: HomeoUnit new].
simulation homeostat homeoUnits 
		do: [:unit |
			(unit inputConnections size = (1+ unitsAdded))]</body>

<body package="Homeostat" selector="testRemoveConnection">testRemoveConnection

|unit1 unit2 |	

unit1 := HomeoUnit new.
unit2 := HomeoUnit new.


simulation homeostat addUnit: unit1.	"create a  2-unit homeostat"
simulation homeostat addUnit: unit2.	
1 to: 2 do: [:i | self assert: (simulation homeostat homeoUnits at: i) inputConnections size = 1].	"all units are self-connected and self-connected only"


	"add a connection from the second unit to first one"
	simulation homeostat addConnectionWithRandomValuesFrom: unit2 to: unit1.
	"check that the first unit has now two connections"
	self assert: ((simulation homeostat homeoUnits at: 1) inputConnections size = 2).	"all units are self-connected and self-connected only"
	self assert: ((unit1 inputConnections size) = 2).

	"remove the connection from the second unit to the first one"
	simulation homeostat removeConnectionFrom: unit2 to: unit1.

	"check  number of connections for unit1 is back to 1 (self-connection)"
	self assert: ((unit1 inputConnections size) = 1).</body>

<body package="Homeostat" selector="testStart">testStart

|simulationCycles|

4 timesRepeat: [simulation homeostat addFullyConnectedUnit: HomeoUnit new].
simulationCycles := 30.
simulation maxRuns: simulationCycles .

simulation start.  "runs for the default number of cycles"

self assert: (simulationCycles = simulation homeostat time).</body>

<body package="Homeostat" selector="testRemoveUnit">testRemoveUnit

| unitsAdded unit|
unit := HomeoUnit new. 
unitsAdded := 3.
simulation addUnit: unit.
self assert: (simulation homeostat homeoUnits size = 1).
unitsAdded timesRepeat:  [simulation addUnit: HomeoUnit new].
self assert: (simulation homeostat homeoUnits size = (1 + unitsAdded)).

simulation homeostat removeUnit: unit.
self assert: (simulation homeostat homeoUnits size = unitsAdded).</body>

<body package="Homeostat" selector="testDataFile">testDataFile
"either the datafile exists and it is writable or it does not exist yet."

self assert: ((simulation datafile asFilename definitelyExists and: [simulation datafile asFilename definitelyExists  isWritable])
			or: [ simulation datafile asFilename definitelyExists not])</body>

<body package="Homeostat" selector="testSaveToFile">testSaveToFile

self assert: false.</body>

<body package="Homeostat" selector="testStop">testStop


|simulationCycles|

4 timesRepeat: [simulation homeostat addFullyConnectedUnit: HomeoUnit new].
simulationCycles := 1000.
simulation maxRuns: simulationCycles .

simulation start.
(Delay forMilliseconds: 100) wait.  "wait one second"
simulation stop.


self assert: ((simulationCycles = simulation homeostat time) not).</body>

<body package="Homeostat" selector="testAddUnit">testAddUnit

| unitsAdded| 
unitsAdded := 5.
simulation addUnit: HomeoUnit new.
self assert: (simulation homeostat homeoUnits size = 1).
unitsAdded timesRepeat:  [simulation addUnit: HomeoUnit new].
self assert: (simulation homeostat homeoUnits size = (1 + unitsAdded)).</body>
</methods>

<methods>
<class-id>HomeoSimulationTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="tearDown">tearDown
	"ensure that homeostat is always new and initialized between successive runs, including of the same test.;"
simulation := HomeoSimulation new.</body>

<body package="Homeostat" selector="setUp">setUp

simulation := HomeoSimulation new.</body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>PlayerRobot class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>PlayerRobot</class-id> <category>accessing</category>

<body package="Homeostat" selector="port">port
	^port</body>

<body package="Homeostat" selector="host:">host: aString
	host := aString</body>

<body package="Homeostat" selector="robot:">robot: aJavaPlayerPlayerClient
	robot := aJavaPlayerPlayerClient</body>

<body package="Homeostat" selector="robot">robot

" outputs the handle to the Player/Stage robot"
	^robot</body>

<body package="Homeostat" selector="port:">port: anInteger

"port number to communicate with Player/Stage"
	port := anInteger</body>

<body package="Homeostat" selector="host">host
	^host</body>
</methods>

<methods>
<class-id>PlayerRobot</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="disconnect">disconnect

	"breaks the connection to the player/stage simulator"
 robot close.</body>

<body package="Homeostat" selector="connect">connect
	"Connect the instance to the Player/Stage simulation through the JavaPlayer client and get the position2D interface"

	
	self robot:  (JavaWorld.javaclient3.PlayerClient new_String: host int: port).
     </body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" initializes port and host to default values: 6665 and 'localhhost' "
	^self host: 'localhost'; port: 6665 </body>
</methods>

<methods>
<class-id>PlayerRobot</class-id> <category>controlling</category>

<body package="Homeostat" selector="run">run
	"run the client proxy in threaded mode. 
      long is the number of miliseconds to sleep between calls
     int is the number of nanoseconds to sleep between calls" 

robot runThreaded_long: -1 int: -1.</body>
</methods>


<methods>
<class-id>Vehicle class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>Vehicle</class-id> <category>sensing</category>

<body package="Homeostat" selector="leftEyeStimulusFor:">leftEyeStimulusFor: aFiducialID 
	"Calls the stimulus method on the right Eye"


^self eyeStimulusForEye: leftEye and: aFiducialID</body>

<body package="Homeostat" selector="rightEyeStimulusFor:">rightEyeStimulusFor: aFiducialID 
	"Calls the stimulus method on the right Eye"


^self eyeStimulusForEye: rightEye and: aFiducialID
	</body>

<body package="Homeostat" selector="eyeStimulusForEye:and:">eyeStimulusForEye: anEye and: aFiducialID 
	"returns the stimulus hitting the  right eye as the sum of the energies coming from fiducial  markers with Id = to with aFiduciaId.
       on the basis of the inverse square law E = I/d^2
       Assume the intensity of the fiducial markers is always equal to 100.

        TO DO : saturation (max value"

	| fidItems stimulus i saturationValue |
	i := 100.	"conventional intensity of light sources in absence of real lights in player/stage"
	saturationValue := 100.	"conventional maximum (saturation) value of the stimulus"
	stimulus := 0.
	anEye isDataReady 
		ifFalse: [^0]
		ifTrue: [fidItems := anEye getData getFiducials asSmalltalkValue].
	fidItems do: 
			[:item | 
			| e dsq |
			item getId = aFiducialID 
				ifTrue: 
					[dsq := item getPose getPx squared + item getPose getPy squared 
								+ item getPose getPz squared.
					e := i / dsq.
					stimulus := stimulus + e.
					Transcript show: 'FidItem with distance: ' , dsq printString , ' and energy: ' , e printString;cr]].
	(stimulus &lt; saturationValue) ifTrue: [^stimulus] ifFalse: [^saturationValue]</body>
</methods>

<methods>
<class-id>Vehicle</class-id> <category>accessing</category>

<body package="Homeostat" selector="position:">position: anobject
	"Does nothing. Initialization of position is done by the connect method"

^ self.</body>

<body package="Homeostat" selector="position">position
	^position</body>

<body package="Homeostat" selector="leftEye">leftEye
	^leftEye</body>

<body package="Homeostat" selector="leftEye:">leftEye: anObject
	"Does nothing. Initialization of leftEye is done by the connect method"
  ^self</body>

<body package="Homeostat" selector="rightEye">rightEye
	^rightEye</body>

<body package="Homeostat" selector="rightEye:">rightEye: anObject
	"Does nothing. Initialization of rightEye is done by the connect method"
 ^ self.</body>
</methods>

<methods>
<class-id>Vehicle</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="connect">connect
	"Connect an initialized  Vehicle to the correct position interface (for motors) and  'eyes. "
      
	super connect. " connect the vehcle to the simulation environment"
	position := (robot requestInterfacePosition2D_int: 0 int: 1).
      rightEye := (robot requestInterfaceFiducial_int: 0 int: 1).   "first integer is the index of the fiducial sensor, the second one is the MODE. 1 = OPEN_MODE"
      leftEye :=   (robot requestInterfaceFiducial_int: 1 int: 1).
  </body>

<body package="Homeostat" selector="initialize">initialize
	"initialization of connections to motors and 'eyes'  is done in method connect, while initialization of  host, port, etcetera, is done in super connect"
     wheelSep := 0.604.   "Default Wheel separation in meters used in the Braitenberg vehicle"
     leftSpeed := 0.        
     rightSpeed := 0.
     ^ super initialize.</body>
</methods>

<methods>
<class-id>Vehicle</class-id> <category>motor control</category>

<body package="Homeostat" selector="move">move
	"operate the motors on the basis of the current right wheel speed and left wheel speed, by converting them into 
       a forward speed and yaw angle (on the basis of the separition between the wheels"

	| forwardSpeed yawAngle |
	leftSpeed = rightSpeed 
		ifTrue: 
			[forwardSpeed := rightSpeed.
			yawAngle := 0].
	leftSpeed &gt; rightSpeed 
		ifTrue: 
			[forwardSpeed := rightSpeed.
			yawAngle := (leftSpeed - rightSpeed) / wheelSep]
		ifFalse: 
			[forwardSpeed := leftSpeed.
			yawAngle := (rightSpeed - leftSpeed) / wheelSep].
	^self position setSpeed_double: forwardSpeed double: yawAngle</body>

<body package="Homeostat" selector="stop">stop

  "stops the motors"

   rightSpeed := 0.
   leftSpeed := 0.
   self move.</body>

<body package="Homeostat" selector="leftMotorSpeed:">leftMotorSpeed: aNumber

  "sets the current speed of the left motor"

    leftSpeed := aNumber
   </body>

<body package="Homeostat" selector="rightMotorSpeed:">rightMotorSpeed: aNumber

  "sets the speed of the right motor"


    rightSpeed := aNumber.</body>
</methods>


<methods>
<class-id>HomeoDataCollectorTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoDataCollectorTest</class-id> <category>running</category>

<body package="Homeostat" selector="testBossOut">testBossOut
"saves the complete run to  a Boss file for later rereading and analysis "


"produce some data"
	| unit1 unit2 unit3 file newDataCollector boss|

	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.


file := Filename named: 'pippo.sts'.
dataCollector bossOutOn: file. 



boss :=  BinaryObjectStorage onOldNoScan: (Filename named: 'pippo.sts') readStream.
newDataCollector := boss next.
boss close.

self assert: (dataCollector states size = newDataCollector states size).

"checks that  the saved dataCollector has, for each time tick, a dicitonary indexed by the same unit names as the original dataCollector"
dataCollector states values asArray with: (newDataCollector states values  asArray) 
		do:[
			:firstDic :secDic |
			firstDic keys asSortedCollection asArray with: ( secDic keys asSortedCollection asArray)
					do: [
						:origName :savedName |
					  	self assert: (origName = savedName)]]</body>

<body package="Homeostat" selector="testSaveCriticalDeviationDataforOneUnitOnFile">testSaveCriticalDeviationDataforOneUnitOnFile

"produce some data"
	|  datafile firstUnitName aStream dataReadBack  |

"initializing and setting up the homeostat run the ouput file and the data collections" 
	
	firstUnitName := (homeostat homeoUnits at: 1) name.
	datafile := 'testing-datafile.txt' asFilename.
	aStream := datafile writeStream.
	dataReadBack := OrderedCollection new.


	homeostat runFor: 100.
	homeostat dataCollector printCompleteDataOn: aStream.

self assert: false.</body>

<body package="Homeostat" selector="testSaveDeviationForUnit">testSaveDeviationForUnit
	"write out the essential data for the simulation, i.e. the output values"

	"produce some data"

	| unit1 unit2 unit3 aStream file |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.
	file := Filename named: 'pippo.txt'.
	aStream := file writeStream.
	dataCollector saveDeviationOn: aStream forUnit: unit1.
	aStream close.
	"here we need to read back the data saved out, do some parsing, and random checking to test consistency."

	"STILL TO DO!"

self assert: false.</body>

<body package="Homeostat" selector="testSaveEssentialsAsSV">testSaveEssentialsAsSV
	"write out the essential data for the simulation, i.e. the output values"

	"produce some data"

	| unit1 unit2 unit3 aStream file |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.
	file := Filename named: 'pippo.txt'.
	aStream := file writeStream.
	dataCollector saveEssentialsOn: aStream
		separator: $,.
	aStream close.
	"here we need to read back the data saved out, do some parsing, and random checking to test consistency."

	"STILL TO DO!"

self assert: false.</body>

<body package="Homeostat" selector="testPrintCriticalDeviationDataforGGobiOnFile">testPrintCriticalDeviationDataforGGobiOnFile
	"produce some data"

	"initializing and setting up the homeostat run the ouput file and the data collections"

	| datafile aStream lines dataReadBack columns originalData testResults unitNames epsilon|

	epsilon := 0.0000001.           "we take numbers as equal if their difference is less than epsilon"
	(homeostat homeoUnits at: 1) name.
	datafile := 'testing-datafile.txt' asFilename.
	aStream := datafile writeStream.
	lines := OrderedCollection new.
	columns := OrderedCollection new.
	dataReadBack := OrderedCollection new.
	testResults := OrderedCollection new.

	"running the homeostat and saving the data"
	homeostat runFor: 50000.
	homeostat dataCollector printPlottingDataForGgobiOn: aStream.

	"reading back the data and comparing to original data"
	aStream := datafile readStream.
	[aStream atEnd] whileFalse: [lines add: (aStream upTo: Character cr)].
	aStream close.
	aStream := ReadStream on: (lines at: 1).
	[aStream atEnd] whileFalse: 
			[| colTitle |
			colTitle := aStream upTo: $,.
			columns add: colTitle].
	aStream close.
	columns  do: 
			[ :elem| dataReadBack add: OrderedCollection new.].

	lines do: 
			[:line | 
			| index |
			index := 1.
			aStream := line readStream.
			[aStream atEnd] whileFalse: 
					[(dataReadBack at: index) add: (aStream upTo: $,).
					index := index + 1]].

unitNames := (homeostat homeoUnits collect: [:unit | unit name]).
dataReadBack removeAllSuchThat: [:dataColumn |  (unitNames includes: (dataColumn at: 1)) not].


originalData := OrderedCollection new.

homeostat homeoUnits do: [:unit | | data | 
						   data  :=  (homeostat dataCollector criticalDevAsCollectionForUnit: unit). 						
						   data addFirst: unit name.
						    originalData add: data]. 


dataReadBack doWithIndex: [:dataColumnReadBack :index |
				   originalData do: [ :origDataColumn |
								((dataColumnReadBack at: 1) = (origDataColumn at: 1)) 
									 ifTrue: [ (origDataColumn allButFirst: 1) with: (dataColumnReadBack allButFirst: 1) 
											do:  [:orig :readBack | 
													(((orig asNumber) - ((readBack, 'd') asNumber)) &lt; epsilon)
													 ifFalse: [testResults add: (Array with: orig 
																				  with: readBack 
																				  with: (((orig asNumber) - ((readBack, 'd') asNumber))) 
																			    	  with: index)]]]]].

self assert: (testResults size = 0).</body>

<body package="Homeostat" selector="testExtractCriticalDevAsCollectionForUnit">testExtractCriticalDevAsCollectionForUnit
	"produce some data"

	"initializing and setting up the homeostat run  and the data collections"

	|  extractedData originalData testResultCollection |

	testResultCollection := OrderedCollection new.
	homeostat runFor: 1000.


	"extracting data and comparing to the original" 
	homeostat homeoUnits do: 
			[:unit | 
			extractedData := homeostat dataCollector criticalDevAsCollectionForUnit: unit.
			originalData := homeostat dataCollector states collect: [:tick | (tick at: unit name) criticalDeviation].
			self assert: extractedData size = originalData size.
			1 to: originalData size
				do: 
					[:index | 
					testResultCollection add: ( (extractedData at: index) = (extractedData at: index)) not].    "collecting all instances in which the data differ"
			self assert: (testResultCollection includes: true) not]</body>

<body package="Homeostat" selector="testPrintOutCompleteDataForUnit">testPrintOutCompleteDataForUnit

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printCompleteDataForUnit: unit1 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printCompleteDataForUnit: unit2 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printCompleteDataForUnit: unit3 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.

"quick hack"
Transcript clear; show: aString.


self assert: false.
aStream close.</body>

<body package="Homeostat" selector="testPrintOutCompleteData">testPrintOutCompleteData

"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printCompleteDataOn: aStream.

"quick hack"
Transcript clear; show: aString.

self assert: false.</body>

<body package="Homeostat" selector="testAddStateForUnit">testAddStateForUnit
	" DataCollector adds a DataUnit for a  HomeoUnit for time t"

	| unit1 unit2 unit3 |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.

	unit1 time: 0.
	unit2 time: 0.
	unit3 time: 0.
	dataCollector at: 0 addDataUnitFor: unit1.
	dataCollector at: 0 addDataUnitFor: unit2.
	dataCollector at: 0 addDataUnitFor: unit3.

	unit1 time: 1.
	unit2 time: 1.
	unit3 time: 1.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.

	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

	unit1 time: -1.
	unit2 time: -1.
	unit3 time: -1.
	dataCollector at: -1 addDataUnitFor: unit1.
	dataCollector at: -1 addDataUnitFor: unit2.
	dataCollector at: -1 addDataUnitFor: unit3.

"self halt."
	"Checks that the dictionary contains DataUnits for all the units]"
	dataCollector states do: 
			[:dataDic | 
			dataDic isNil 
				ifFalse: 
					[self assert: (dataDic includesKey: unit1 name).
					self assert: (dataDic includesKey: unit2 name).
					self assert: (dataDic includesKey: unit3 name).
					self assert: (((dataDic at: unit1 name ) name)= unit1 name).				
]].</body>

<body package="Homeostat" selector="testPrintOutEssentialData">testPrintOutEssentialData

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printEssentialDataOn: aStream.

"quick hack"
Transcript clear; show: aString.

self assert: false.</body>

<body package="Homeostat" selector="testConvertCriticalDevForUnit">testConvertCriticalDevForUnit



"produce some data"
	| unit1 unit2 unit3   coll|
	coll := OrderedCollection new.
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.


coll := dataCollector criticalDevAsCollectionForUnit: unit1.

"quick hack"

Transcript clear. coll do: [:elem | Transcript show: elem printString; cr].

self assert: false.</body>

<body package="Homeostat" selector="testPrintOutEssentialDataForUnit">testPrintOutEssentialDataForUnit

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printEssentialDataForUnit: unit1 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printEssentialDataForUnit: unit2 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printEssentialDataForUnit: unit3 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.

"quick hack"
Transcript clear; show: aString.

self assert: false.

aStream close.</body>
</methods>

<methods>
<class-id>HomeoDataCollectorTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp

dataCollector := HomeoDataCollector new.

"setup a standard Ashby 4 units homeostat to be used in various tests"
	
	homeostat := Homeostat new.
	4 timesRepeat: 
			[| unit |
			unit := HomeoUnit new setRandomValues.
			homeostat addFullyConnectedUnit: unit].
	homeostat slowingFactor: 0.</body>
</methods>


<methods>
<class-id>HomeoDataUnit class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>

<body package="Homeostat" selector="newUnitFor:">newUnitFor: aHomeoUnit

"creates a new instance, reads the state from aHomeoUnit and returns it.
  This is just a convenience, but it is useful becaue it is the most common use of HomeoDataUnit"

| dataUnit |

dataUnit := super new initialize.

^dataUnit readStateFrom: aHomeoUnit.

</body>
</methods>


<methods>
<class-id>HomeoDataUnit</class-id> <category>comparing</category>

<body package="Homeostat" selector="sameValuesAs:">sameValuesAs: dataUnit

"answers true if the values in the two data units are the same. It does not check the values of the connections"


^ self name = dataUnit name &amp;
self output = dataUnit output &amp;
self maxDeviation = dataUnit maxDeviation &amp;
self uniselectorState = dataUnit uniselectorState</body>
</methods>

<methods>
<class-id>HomeoDataUnit</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	connectedTo := Dictionary new.</body>
</methods>

<methods>
<class-id>HomeoDataUnit</class-id> <category>printing</category>

<body package="Homeostat" selector="printEssentialVariableOn:">printEssentialVariableOn: aStream 
	"prints  just the DataUnit's output values on stream. Useful for graphing and compact representations."


	aStream nextPutAll: (output printString); cr.</body>

<body package="Homeostat" selector="printCriticalDeviationOn:">printCriticalDeviationOn: aStream 
	"prints  just the DataUnit's criticalDeviation values on stream. Useful for graphing and compact representations."


	aStream nextPutAll: (criticalDeviation printString); cr.</body>

<body package="Homeostat" selector="printDataOn:">printDataOn: aStream 
	"Output a complete representation of its data"

	aStream
		nextPutAll: 'name: ';
		nextPutAll: name;
		nextPutAll: '     ';
		nextPutAll: 'output: ';
		nextPutAll: output printString;
		nextPutAll: '     ';
		nextPutAll: 'uniselector: ';
		nextPutAll: uniselectorState printString;
		nextPutAll: '     '.
	connectedTo keysAndValuesDo: 
			[:connName :connValue | 
			aStream
				nextPutAll: 'Connct to: ';
				nextPutAll: name;
				nextPutAll: '     ';
				nextPutAll: 'weight: ';
				nextPutAll: ((connValue at: 1) printString);
				nextPutAll: '     ';
				nextPutAll: 'switch: ';
				nextPutAll: ((connValue at: 2) printString);
				nextPutAll: '     ';
				nextPutAll: 'unis.: ';
				nextPutAll: ((connValue at: 3) printString);
				nextPutAll: '     ';
				nextPutAll: 'noise: ';
				nextPutAll: ((connValue at: 4) printString)].
	aStream nextPut: Graphics.TextConstants.CR</body>

<body package="Homeostat" selector="printUniselectorActivatedOn:">printUniselectorActivatedOn: aStream 
	"prints  just the data about whether the DataUnit's uniselctor has been activated"


aStream nextPutAll: (uniselectorActivated printString); cr.</body>
</methods>

<methods>
<class-id>HomeoDataUnit</class-id> <category>accessing</category>

<body package="Homeostat" selector="criticalDeviation">criticalDeviation
	^criticalDeviation</body>

<body package="Homeostat" selector="maxDeviation">maxDeviation
	^maxDeviation</body>

<body package="Homeostat" selector="criticalDeviation:">criticalDeviation: anObject
	criticalDeviation := anObject</body>

<body package="Homeostat" selector="readStateFrom:">readStateFrom: aHomeoUnit

"reads the fundamental variables of the unit's state from the unit itself."

name := aHomeoUnit name.
output :=aHomeoUnit currentOutput.
uniselectorState := aHomeoUnit uniselectorActive.
maxDeviation :=  aHomeoUnit maxDeviation.
criticalDeviation := aHomeoUnit criticalDeviation.
uniselectorActivated := aHomeoUnit uniselectorActivated.
aHomeoUnit inputConnections do: [ :conn | connectedTo at: (conn incomingUnit name) put: (Array with: (conn weight) with: (conn switch) with: (conn state) with: (conn noise))].</body>

<body package="Homeostat" selector="uniselectorActivated:">uniselectorActivated: anObject
	uniselectorActivated := anObject</body>

<body package="Homeostat" selector="name:">name: anObject
	name := anObject</body>

<body package="Homeostat" selector="connectedTo">connectedTo
	^connectedTo</body>

<body package="Homeostat" selector="output:">output: anObject
	output := anObject</body>

<body package="Homeostat" selector="uniselectorState">uniselectorState
	^uniselectorState</body>

<body package="Homeostat" selector="connectedTo:">connectedTo: anObject
	connectedTo := anObject</body>

<body package="Homeostat" selector="output">output
	^output</body>

<body package="Homeostat" selector="name">name
	^name</body>

<body package="Homeostat" selector="maxDeviation:">maxDeviation: anObject
	maxDeviation := anObject</body>

<body package="Homeostat" selector="uniselectorState:">uniselectorState: anObject
	uniselectorState := anObject</body>

<body package="Homeostat" selector="uniselectorActivated">uniselectorActivated
	^uniselectorActivated</body>
</methods>


<methods>
<class-id>HomeoConnectionTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoConnectionTest</class-id> <category>running</category>

<body package="Homeostat" selector="testDefaults">testDefaults
	"comment stating purpose of message"

	self assert: ((connection weight) between: 0 and: 1).
	self assert: ((connection noise) between: 0 and: 0.1).
	self assert: ((connection switch) notNil).</body>

<body package="Homeostat" selector="testAddConnection">testAddConnection

self assert: ((connection incomingUnit) = unit1).</body>

<body package="Homeostat" selector="testSameAs">testSameAs

|connection2 |
unit1 := HomeoUnit new.
unit1 setRandomValues.

unit2 := HomeoUnit new.
unit2 setRandomValues.

connection randomizeConnectionValues.
connection incomingUnit: unit1.

connection2 := connection copy.

self assert: (connection sameAs: connection2).

connection incomingUnit: unit2.

self deny: (connection sameAs: connection2).</body>

<body package="Homeostat" selector="testWeight">testWeight


	| outputWeighed  inputUnit errorTolerance noiseLevel|
	noiseLevel := 0.1.
	errorTolerance := 0.00001.
	outputWeighed := connection output.
	inputUnit := connection incomingUnit.
	connection noise: 0.                               "eliminate noise"
	self assert: (outputWeighed -
				 (inputUnit currentOutput * connection weight * connection switch - connection noise) &lt; errorTolerance).

	"accounting for noise"
	connection noise: noiseLevel.                               "set noise"
	
	"the differnece between the weighed connection output and the unit's value is at most eual to noise (plus the tolerance"
	self assert: ((outputWeighed -
				 (inputUnit currentOutput * connection weight * connection switch - connection noise)) abs &lt; (noiseLevel + errorTolerance)).</body>

<body package="Homeostat" selector="testState">testState

"test default state of the connection  units" 
self assert: ((connection state) = 'uniselector'). 

"switching from manual to uniselector and back"

connection switchToUniselector.
self assert: ((connection state) = 'uniselector').

connection switchToManual.
self assert: ((connection state) = 'manual').</body>

<body package="Homeostat" selector="testValueOfState">testValueOfState
	""

self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

connection state: 'manual'.
self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

connection state: 'uniselector'.
self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

self should: [connection state:  'wrongValue']  raise: Error.</body>
</methods>

<methods>
<class-id>HomeoConnectionTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="setUp">setUp
	"comment stating purpose of message"

	unit1 := HomeoUnit new.
	unit1 selfUpdate.              "allows the unit to have some values in its slots"
	connection := HomeoConnection new.
	connection incomingUnit: unit1.</body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>HomeoUnit class</class-id> <category>testing</category>

<body package="Homeostat" selector="defaultParameters">defaultParameters
	"returns the dictionary (shared variable) containing the default parameters of the class"

self initialize.
^DefaultParameters.</body>
</methods>

<methods>
<class-id>HomeoUnit class</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Sets DefaultParameters, the class variable holding the  default values of all the various parameters of future created units.
	   HomeoUnit initialize "
	| range |
	range := Dictionary new.
	range at: 'high' put: 1; at: 'low' put: -1.		"output range is by default -1  to 1, to express the proportion of the needle's deviation"
	DefaultParameters := Dictionary new.
	DefaultParameters 	at: 'viscosity' 				put: 1;   
						at: 'maxDeviation' 				put: 10;
						at: 'outputRange' 				put: range;
						at: 'noise' 						put:  0;
						at: 'potentiometer'				put:  1;
						at: 'time'						put: 0;
						at: 'inputValue'					put: 0;
						at: 'uniselectorTime'			put: 0;	
						at: 'uniselectorTimeInterval' 	put: 10; "How often the uniselector checks the thresholds, in number of ticks"
						at: 'needleCompMethod'	 	put: 'linear' ; "switches between linear and proportional computation of displacement"
						at: 'uniselectorActivated'      	put: 0;
					      at: 'density'			       		put: 1;   "density of water"
						at: 'maxViscosity'				put: (10 raisedTo: 6) asDouble.

	Names := Set new: 5.</body>
</methods>

<methods>
<class-id>HomeoUnit class</class-id> <category>private-saving</category>

<body package="Homeostat" selector="name:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:outputRange:inputConnections:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">name: unitName 
viscosity: unitViscosity 
maxDeviation: unitMaxDeviation 
criticalDeviation: unitCriticalDeviation
noise: unitNoise 
potentiometer: unitPotentiometer 
switch: unitSwitch 
outputRange: unitOutputRange 
inputConnections: unitInputConnections 
uniselector: unitUniselector 
uniselectorTimeInterval: unitUniselectorTimeInterval 
uniselectorActive: unitUniselectorActive 
needleCompMethod: unitNeedleCompMethod 
active: unitActive

	"create a new HomeoUnit  and sets the instance variable to the given parameters"

^self new
	setName:  unitName 
	viscosity: unitViscosity 
	maxDeviation: unitMaxDeviation 
	criticalDeviation: unitCriticalDeviation 
	noise: unitNoise 
	potentiometer: unitPotentiometer 
	switch: unitSwitch 
	outputRange:  unitOutputRange
	inputConnections:  unitInputConnections
	uniselector: unitUniselector 
	uniselectorTimeInterval: unitUniselectorTimeInterval 
	uniselectorActive: unitUniselectorActive 
	needleCompMethod: unitNeedleCompMethod 
	active: unitActive.</body>

<body package="Homeostat" selector="name:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">name: unitName viscosity: unitViscosity maxDeviation: unitMaxDeviation criticalDeviation: unitCriticalDeviation noise: unitNoise potentiometer: unitPotentiometer switch: unitSwitch uniselector: unitUniselector uniselectorTimeInterval: unitUniselectorTimeInterval uniselectorActive: unitUniselectorActive needleCompMethod: unitNeedleCompMethod active: unitActive

	"create a new HomeoUnit  and sets the instance variable to the given parameters"

^self new
	setName:  unitName 
	viscosity: unitViscosity 
	maxDeviation: unitMaxDeviation 
	criticalDeviation: unitCriticalDeviation 
	noise: unitNoise 
	potentiometer: unitPotentiometer 
	switch: unitSwitch 
	uniselector: unitUniselector 
	uniselectorTimeInterval: unitUniselectorTimeInterval 
	uniselectorActive: unitUniselectorActive 
	needleCompMethod: unitNeedleCompMethod 
	active: unitActive.</body>
</methods>

<methods>
<class-id>HomeoUnit class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."
	
	"self initialize. "
	^ super new initialize.</body>
</methods>


<methods>
<class-id>HomeoUnit</class-id> <category>testing</category>

<body package="Homeostat" selector="sameFirstLevelParamsAs:">sameFirstLevelParamsAs: aHomeoUnit 
	"Checks whether the first level parameters of two units (i.e. not the connections) are the same. Does not include dynamic parameters (output, currentOutput, nextDeviation, crticalDeviation, time, uniselectorTime, inputTorque"

	^name = aHomeoUnit name and: 
			[viscosity = aHomeoUnit viscosity and: 
					[maxDeviation = aHomeoUnit maxDeviation and: 
							[(outputRange at: 'high') = (aHomeoUnit outputRange at: 'high') and: 
								[(outputRange at: 'low') = (aHomeoUnit outputRange at: 'low') and: 
									[noise = aHomeoUnit noise and: 
											[potentiometer = aHomeoUnit potentiometer and: 
													[switch = aHomeoUnit switch and: 
															[(uniselector sameKindAs: (aHomeoUnit uniselector)) and:                                     "do not check uniselector transition tables, only kind of device"
																	[uniselectorTimeInterval = aHomeoUnit uniselectorTimeInterval and: 
																			[uniselectorActive = aHomeoUnit uniselectorActive and: 
																					[needleCompMethod = aHomeoUnit needleCompMethod 
																						and: [status = aHomeoUnit status]]]]]]]]]]]]</body>

<body package="Homeostat" selector="isConnectedTo:">isConnectedTo: aHomeoUnit 
	"tests whether there is a connection coming from aHomeoUnit"

| connectedUnits |
	
connectedUnits:= inputConnections collect: [:each | each incomingUnit].
^connectedUnits includes: aHomeoUnit.</body>

<body package="Homeostat" selector="sameConnectionsAs:">sameConnectionsAs: aHomeoUnit 
	"checks that two units have the same connections"

	| connSame |
	connSame := true.
	self inputConnections size = aHomeoUnit inputConnections size 
		ifFalse: [^false]
		ifTrue: 
			[inputConnections with: aHomeoUnit inputConnections
				do: [:conn1 :conn2 | (conn1 sameAs: conn2) ifFalse: [connSame := false]]].
	^connSame</body>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo
	"makes sure that unit has all the parameters it needs to operate properly:

criticalDeviation	is notNil and
maxDeviation	is notNil 
outputRange		is notNil 
viscosity			is notNil
noise			is notNil
potentiometer 	is notNil	 

if  uniselectorActive is true then	
uniselector 				is notNil
uniselectorTime 	  		is notNil
uniselectorTimeInterval  	is notNil"

	| uniselectorConditions |
	uniselectorActive 
		ifFalse: [uniselectorConditions := true]
		ifTrue: 
			[uniselectorConditions := uniselector notNil &amp; uniselectorTime notNil 
						&amp; uniselectorTimeInterval notNil].
	^criticalDeviation notNil &amp; maxDeviation notNil &amp; outputRange notNil 
		&amp; viscosity notNil &amp; noise notNil 
		&amp; potentiometer notNil 
		&amp; uniselectorConditions</body>

<body package="Homeostat" selector="isActive">isActive

^status = 'Active'</body>

<body package="Homeostat" selector="sameAs:">sameAs: aHomeoUnit

"tests whether two units are the same, by checking (by delegating the actual checks):
1. name and other first-level parameters (potentiometer, switch, etcetera

2. the number of connections

3. the parameters of each  connection

4. the names of the connected units"


^(self sameFirstLevelParamsAs: aHomeoUnit)  and: [ self  sameConnectionsAs: aHomeoUnit]</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize the HomeoUnit with the default parameters found in the Class variable DefaultParameters.
	Assign a random but unique name and sets the output to some value around 0, i.e. at equilibrium
	These values are supposed to be overridden in normal practice, because the values are set  by the  simulation 
	(an an instance of HomeoSimulation or by the graphic interface)"




	| activeNames |														"generates a random name for the unit"
	activeNames := Set new.												"this is a hack to clear out unused names from the class variable Names."
	self class allInstancesDo: [:each | activeNames add: each name].
	Names := activeNames.

	"reads default parameters"
	viscosity := DefaultParameters at: 'viscosity'.
	maxDeviation := DefaultParameters at: 'maxDeviation'. 	"set the critical deviation at time 0 to 0."
	outputRange := DefaultParameters at: 'outputRange'.
	noise := DefaultParameters at: 'noise'.
	potentiometer := DefaultParameters at: 'potentiometer'.
	time := DefaultParameters at: 'time'.
	uniselectorTime := DefaultParameters at: 'uniselectorTime'.
	uniselectorTimeInterval := DefaultParameters at: 'uniselectorTimeInterval'.
	needleCompMethod	:= DefaultParameters at: 'needleCompMethod'.
	uniselectorActivated := DefaultParameters at: 'uniselectorActivated'.

	currentVelocity := 0. "a New unit is turned off, hence its velocity is 0"

	needleUnit := HomeoNeedleUnit new.



		"sets the correspondence between the simulation units and real physical units"
	physicalParameters := Dictionary new.

	physicalParameters at: 'timeEquivalence'    put: 1 	    asDouble; 	"1 simulation tick corresponds to 1 second of physical time"
					        at: 'lengthEquivalence' put:  0.01 asDouble; 		"1 unit of displacement corresponds to 1 cm (expressed in meters)"
					        at: 'massEquivalence'  put:  0.001 asDouble.       "1 unit of mass equals one gram, or 0.001 kg"
	
	"creates the connection collection and connects the unit to itself in manual mode with a negative feedback"
	inputConnections := OrderedCollection new.
	self setDefaultSelfConnection.

	"sets default uniselector settings."
	self setDefaultUniselectorSettings.
	self setUnitName.



	"generates a random output to set the unit close to equilibrium"
	self setDefaultOutputAndDeviation.

	"turn the unit on"
	self status: 'Active'.

	debugMode := false.

	showUniselectorAction := false.</body>

<body package="Homeostat" selector="setDefaultOutputAndDeviation">setDefaultOutputAndDeviation
	

	| randOutput |


	randOutput := Random new nextBetween: 0 and: 0.5.	"generates a random output to set the unit close to equilibrium"
	currentOutput := randOutput.

	"set the critical deviation at time 0 to 0."
	criticalDeviation := 0</body>

<body package="Homeostat" selector="randomizeAllConnectionValues">randomizeAllConnectionValues
	"resets the weight, switch, and noise of all connections to random values (see HomeoConnection for details).
Does not touch the self connection of the unit to itself.  
Does not change the uniselector operation"

	2 to: (inputConnections size) 
				do: [
					:conn | 
					(inputConnections at: conn) randomizeConnectionValues]</body>

<body package="Homeostat" selector="setDefaultUniselectorSettings">setDefaultUniselectorSettings
	"sets default uniselector settings."

	uniselector := HomeoUniselectorAshby new.
	uniselectorActive := true</body>

<body package="Homeostat" selector="setUnitName">setUnitName
	"assigns a unique name to the unit with the help of  an auxiliary method"



name := self produceNewName.</body>

<body package="Homeostat" selector="setRandomValues">setRandomValues
	"sets up the unit with random values"

	| unitRange unitLimit rand switchSign|

rand := Random new.
unitRange := Dictionary new. 
unitLimit := 1.
unitRange at: 'high' put: unitLimit; at: 'low' put: -1.                   "output is always between -1 and 1"
self outputRange: unitRange.

self viscosity: (rand nextBetween: 0.8 and: 1).
self noise: (rand nextBetween: 0 and: 0.1).
self potentiometer: (rand nextBetween: 0 and: 1).

switchSign := (rand nextBetween: -1 and: 1) sign. "sets the polarity of the self-connection, avoid  0"
switchSign = 0 ifTrue: [switchSign := 1].
self switch: 	switchSign. 

self currentOutput:   (rand nextBetween: 0 and: 1).	"generates a random output  over the whole range" 														
self criticalDeviation:  (rand nextBetween: (unitRange at: 'low') and: (unitRange at: 'high')). "set the critical deviation to a random value over the whole range"</body>

<body package="Homeostat" selector="setDefaultSelfConnection">setDefaultSelfConnection
	"creates the connection collection and connects the unit to itself in manual mode with a negative feedback"
	

self 
		addConnection: self
		withWeight: (self potentiometer)
		andPolarity: -1
		andNoise: 0
		andState: 'manual'</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>printing</category>

<body package="Homeostat" selector="printOn:">printOn: aStream
	"Prints a brief description of the unit for inspectors, etc"

super printOn: aStream.
aStream nextPutAll: ': ', self name.</body>

<body package="Homeostat" selector="printDescription">printDescription
	"Prints a text representation of the unit"

	| aString aStream temp |
	aString := String new.
	aStream := WriteStream on: aString.
	aStream nextPutAll: 'aHomeoUnit with values:'; cr.
	self class instVarNames do: [ :ivar | aStream nextPutAll:  ivar, ': '; tab.
										temp := (self perform: (ivar asSymbol)).
										temp isNil ifTrue: [aStream nextPutAll: 'nil'] ifFalse: [aStream nextPutAll: (temp printString)].
										aStream  cr.].
	aStream close.
	^ aString.</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>running</category>

<body package="Homeostat" selector="selfUpdate">selfUpdate
	"This is the master loop for the unit. It goes through the following sequence:
	1. compute new needle's deviation (nextDeviation (includes reading inputs))
	2. updates the current output on the basis of the deviation.
	3. check whether it's time to check the essential value and if so do it and  update the counter (uniselectorTime) [this might change the weight of the connections]
	4. Move the needle to new position and compute new output"

	"1. compute where the needle should move to"
"Testing"
debugMode ifTrue: [Transcript show: 'current Deviat. at time: ';  show: time printString; show: ' for unit: '; show: self name; show: ' is ' ; show: criticalDeviation printString; cr.].

	self computeNextDeviation.

	"2. update times"
	self updateTime.
	self updateUniselectorTime.

	"3. check whether it's time to check the uniselector/detection mechanism and if so do it. 
	       Register that the uniselector is active in aninstance variable"
	(uniselectorTime &gt;= uniselectorTimeInterval and: [uniselectorActive]) 
		ifTrue: [self essentialVariableIsCritical ifTrue: [self operateUniselector.
												   uniselectorActivated := 1]]
		ifFalse: [uniselectorActivated:= 0].	      

	"4. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"
	self criticalDeviation: (self clipDeviation: nextDeviation).
	self computeOutput.
	nextDeviation := 0</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>accessing</category>

<body package="Homeostat" selector="potentiometer">potentiometer
	^potentiometer

</body>

<body package="Homeostat" selector="name:">name: aString
	

	(Names includes: aString) 
			ifFalse: [
  				name := aString.
				self broadcast: #changed: with: #name.].</body>

<body package="Homeostat" selector="inputConnections:">inputConnections: anObject
	inputConnections := anObject.
	self changed:  #inputConnections</body>

<body package="Homeostat" selector="inputConnections">inputConnections
	^inputConnections</body>

<body package="Homeostat" selector="uniselectorActivated">uniselectorActivated
	^uniselectorActivated</body>

<body package="Homeostat" selector="maxDeviation:">maxDeviation: aNumber
"Max deviation is always positive, because the unit's deviation is centered around 0. Ignore negatve numbers"
	
	(aNumber &gt; 0) 
		ifTrue: [
			maxDeviation := aNumber.
			self changed: #maxDeviation]</body>

<body package="Homeostat" selector="outputRange:">outputRange: anObject
	outputRange := anObject</body>

<body package="Homeostat" selector="inputTorque">inputTorque
	^inputTorque</body>

<body package="Homeostat" selector="active:">active: anObject
	active := anObject.
	self changed: #active.</body>

<body package="Homeostat" selector="uniselectorActivated:">uniselectorActivated: anObject
	uniselectorActivated := anObject</body>

<body package="Homeostat" selector="currentOutput:">currentOutput: anObject 
	currentOutput := anObject.

	"testing
	Transcript
		show: currentOutput printString;
		cr."
"	self halt.
"
	self changed: #currentOutput</body>

<body package="Homeostat" selector="removeConnectionFromUnit:">removeConnectionFromUnit: aHomeoUnit 
	"removes the connection originating from  aHomeoUnit"

| collection |
collection := inputConnections copy.

collection do: [
	:each |
	each incomingUnit = aHomeoUnit ifTrue: [inputConnections  remove: each]].

self changed: #inputConnections.</body>

<body package="Homeostat" selector="viscosity">viscosity
	^viscosity</body>

<body package="Homeostat" selector="time">time
	^time</body>

<body package="Homeostat" selector="disactivate">disactivate

active := false.
self changed: #active.</body>

<body package="Homeostat" selector="needleCompMethod">needleCompMethod
	^needleCompMethod</body>

<body package="Homeostat" selector="viscosity:">viscosity: anObject 
	viscosity := anObject.
	self changed: #viscosity</body>

<body package="Homeostat" selector="uniselector">uniselector
	^uniselector</body>

<body package="Homeostat" selector="density:">density: anObject
	density := anObject</body>

<body package="Homeostat" selector="toggleDebugMode">toggleDebugMode
	"controls whether the running methods print out debug information"

	debugMode ifTrue: [debugMode := false] ifFalse: [debugMode := true]</body>

<body package="Homeostat" selector="switch">switch
	^switch</body>

<body package="Homeostat" selector="addConnectionWithRandomValues:">addConnectionWithRandomValues: aHomeoUnit 

"adds a new connection to the unit. Uses the random values (weight, noise, and polarity) selected by the initialization method of HomeoConnection.
Notice that you always connect the unit starting from the destination, i.e. from the input side, and never from the output side.
In fact units don't know anything at all about where their output goes.
If the parameters are not within the expected values, the accessor methods of HomeoConnection will raise exceptions
"

| aNewConnection| 
aNewConnection := HomeoConnection new.        "The initialize method of HomeoConnection sets random weights"
aNewConnection incomingUnit: aHomeoUnit; outgoingUnit: self.
inputConnections add: aNewConnection.
self changed: #addConnection</body>

<body package="Homeostat" selector="currentVelocity:">currentVelocity: anObject
	currentVelocity := anObject</body>

<body package="Homeostat" selector="nextDeviation:">nextDeviation: anObject
	nextDeviation := anObject</body>

<body package="Homeostat" selector="uniselector:">uniselector: anObject
	uniselector := anObject
	self changed: #uniselector</body>

<body package="Homeostat" selector="minDeviation:">minDeviation: aNumber

"Deviation is always centered around 0. Min deviation must be less than 0 and equal to maxDeviation negated. If we change the minimum we must change the maximum as well"
	(aNumber &lt; 0) 
		ifTrue: [
			maxDeviation := aNumber negated
			self changed: #maxDeviation]</body>

<body package="Homeostat" selector="highRange">highRange

^outputRange at: 'high'</body>

<body package="Homeostat" selector="potentiometer:">potentiometer: aValue 
"changing the value of the potentiometer affects the unit's connection to itself (which is always at 1 in the inputConnections collection)"
	potentiometer := aValue.
	(inputConnections at: 1) weight: aValue.
	self changed: #potentiometer</body>

<body package="Homeostat" selector="uniselectorTimeInterval">uniselectorTimeInterval
	^uniselectorTimeInterval</body>

<body package="Homeostat" selector="currentOutput">currentOutput
	^currentOutput</body>

<body package="Homeostat" selector="maxDeviation">maxDeviation
	^maxDeviation</body>

<body package="Homeostat" selector="inputTorque:">inputTorque: anObject
	inputTorque := anObject</body>

<body package="Homeostat" selector="currentVelocity">currentVelocity
	^currentVelocity</body>

<body package="Homeostat" selector="maxConnectedUnits:">maxConnectedUnits: anInteger

"changes the parameter to the Uniselector for the maximun number of connected units"

uniselector unitsControlled: anInteger</body>

<body package="Homeostat" selector="criticalDeviation">criticalDeviation
	^criticalDeviation</body>

<body package="Homeostat" selector="criticalDeviation:">criticalDeviation: anObject
	criticalDeviation := anObject.
	self changed: #criticalDeviation</body>

<body package="Homeostat" selector="lowRange">lowRange

^outputRange at: 'low'</body>

<body package="Homeostat" selector="needleUnit">needleUnit
	^needleUnit</body>

<body package="Homeostat" selector="noise">noise
	^noise</body>

<body package="Homeostat" selector="switch:">switch: aNumber
	"sets the polarity of the unit's self-connection. aNumber must be either -1 or +1, otherwise method default to a positive connection (i.e. 1)
	  Notice that  changing the value of the unit's switch  affects the unit's connection to itself (which is always at 1 in the inputConnections collection)"

| accValues |
accValues := Array with: -1 with: 1.
switch :=  aNumber.

(accValues includes: aNumber)
		 ifTrue: [ (inputConnections at: 1) switch: aNumber] 
		ifFalse: [ (inputConnections at: 1) switch: 1].
self changed: #switch.</body>

<body package="Homeostat" selector="density">density
	^density</body>

<body package="Homeostat" selector="highRange:">highRange: aValue

outputRange at: 'high' put: aValue.
self changed: #range</body>

<body package="Homeostat" selector="minDeviation">minDeviation
	"Deviation is always centered around 0. Min deviation is less than 0 and equal to maxDeviation negated."

	^maxDeviation negated</body>

<body package="Homeostat" selector="addConnection:withWeight:andPolarity:andState:">addConnection: aHomeoUnit withWeight: aNumber andPolarity: aValue andState: aString

"adds a new connection to the unit. Notice that you always connect the unit starting from the destination, i.e. from the input side, and never from the output side.
In fact units don't know anything at all about where their output goes.
If the parameters are not within the expected values, the accessor methods of HomeoConnection will raise exceptions
"

| aNewConnection| 
aNewConnection := HomeoConnection new.

aNewConnection incomingUnit: aHomeoUnit;
				outgoingUnit: self;
				weight:		 aNumber;  "must be between 0 and 1"
				switch: 		aValue;      "must be -1 or 1"
				state:		aString.      "must be 'manual' or 'uniselector'"
				

inputConnections add: aNewConnection.
self changed: #addConnection</body>

<body package="Homeostat" selector="activate">activate

active := true.
self changed: #active.</body>

<body package="Homeostat" selector="status">status
	^status</body>

<body package="Homeostat" selector="uniselectorTime:">uniselectorTime: anObject
	uniselectorTime := anObject.
	self changed: #uniselectorTime</body>

<body package="Homeostat" selector="toggleShowUniselectorAction">toggleShowUniselectorAction
	"controls whether the running methods print out  when the uniselector kicks into action"

	showUniselectorAction 
		ifTrue: [showUniselectorAction := false]
		ifFalse: [showUniselectorAction := true]</body>

<body package="Homeostat" selector="needleUnit:">needleUnit: anObject
	needleUnit := anObject</body>

<body package="Homeostat" selector="uniselectorActive">uniselectorActive
	^uniselectorActive</body>

<body package="Homeostat" selector="status:">status: anObject
	status := anObject.
	self changed: #status</body>

<body package="Homeostat" selector="active">active
	^active</body>

<body package="Homeostat" selector="lowRange:">lowRange: aValue

outputRange at: 'low' put: aValue.
self changed: #range.</body>

<body package="Homeostat" selector="time:">time: anObject
	time := anObject</body>

<body package="Homeostat" selector="needleCompMethod:">needleCompMethod: anObject
	needleCompMethod := anObject.
	self changed: #needleCompMethod</body>

<body package="Homeostat" selector="noise:">noise: aValue 
"changes the value of the unit's internal noise. As noise must always be between 0 and 1 clip it if outside those bounds"
	

	aValue &gt; 1
		 ifFalse: [aValue &lt;0
			ifFalse: [noise := aValue]
			ifTrue:   [noise := 0]]
		ifTrue: [noise := 1].	

	self changed: #noise</body>

<body package="Homeostat" selector="addConnection:withWeight:andPolarity:andNoise:andState:">addConnection: aHomeoUnit withWeight: aNumber andPolarity: aValue andNoise: aNumber2 andState: aString

"adds a new connection to the unit. Notice that you always connect the unit starting from the destination, i.e. from the input side, and never from the output side.
In fact units don't know anything at all about where their output goes.
If the parameters are not within the expected values, the accessor methods of HomeoConnection will raise exceptions
"

| aNewConnection| 
aNewConnection := HomeoConnection new.

aNewConnection incomingUnit: aHomeoUnit;
				outgoingUnit: self;
				weight:		 aNumber;  "must be between 0 and 1"
				switch: 		aValue;      "must be -1 or 1"
				noise:		aNumber2; "must be between 0 and 1"
				state:		aString.      "must be 'manual' or 'uniselector'"
				

inputConnections add: aNewConnection.
self changed: #addConnection</body>

<body package="Homeostat" selector="uniselectorTime">uniselectorTime
	^uniselectorTime</body>

<body package="Homeostat" selector="uniselectorChangeType:">uniselectorChangeType: uniselectorType

"switches the uniselector type of the unit"
 |uniselectorClass|

((HomeoUniselector includesType: 'HomeoUniselector', uniselectorType) or: [(HomeoUniselector includesType: uniselectorType)]) 
    ifTrue:   [uniselectorClass := Smalltalk at: uniselectorType ifAbsent: [uniselectorClass := Smalltalk at: 'HomeoUniselector', uniselectorType]].
    
uniselectorClass isNil
	ifFalse:[ uniselector := uniselectorClass new.
			 self uniselectorTime: 0.
			  self changed: #uniselector].</body>

<body package="Homeostat" selector="uniselectorActive:">uniselectorActive: aBoolean
	uniselectorActive := aBoolean.
	self changed: #uniselectorActive</body>

<body package="Homeostat" selector="uniselectorTimeInterval:">uniselectorTimeInterval: anObject
	uniselectorTimeInterval := anObject.
	self changed: #uniselectorTiming
	</body>

<body package="Homeostat" selector="nextDeviation">nextDeviation
	^nextDeviation</body>

<body package="Homeostat" selector="name">name
	^name</body>

<body package="Homeostat" selector="outputRange">outputRange
	^outputRange</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>private-saving</category>

<body package="Homeostat" selector="setName:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:outputRange:inputConnections:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">setName:  unitName viscosity: unitViscosity maxDeviation: unitMaxDeviation criticalDeviation: unitCriticalDeviation noise: unitNoise potentiometer: unitPotentiometer switch: unitSwitch outputRange: unitOutputRange inputConnections: unitInputConnections uniselector: unitUniselector uniselectorTimeInterval: unitUniselectorTimeInterval uniselectorActive: unitUniselectorActive needleCompMethod: unitNeedleCompMethod active: unitActive

	"sets the unit's instance variable vlaues to the given parameters. Used by Boss to serialize the object"

	name:=  unitName. 
	viscosity:= unitViscosity. 
	maxDeviation:= unitMaxDeviation. 
	criticalDeviation:= unitCriticalDeviation .
	noise:= unitNoise. 
	potentiometer:= unitPotentiometer. 
	switch:= unitSwitch. 
	outputRange :=  unitOutputRange.
	inputConnections :=  unitInputConnections.
	uniselector:= unitUniselector .
	uniselectorTimeInterval:= unitUniselectorTimeInterval .
	uniselectorActive:= unitUniselectorActive .
	needleCompMethod:= unitNeedleCompMethod .
	active:= unitActive.

			</body>

<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename

"bosses itself out on a file opened on aFilename. It will erase the old content of aFilename."

| boss |
boss := BinaryObjectStorage onNew: aFilename writeStream.
[boss nextPut: self]
	ensure: [boss close].</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>private-updating</category>

<body package="Homeostat" selector="allChanged">allChanged
	"broadcast all the #changed messages.
	Used when a new homeostat is used"


	self changed: #active.
	self changed: #addConnection.
	self changed: #criticalDeviation.
	self changed: #currentOutput.
	self changed: #range.
	self changed:  #inputConnections.
	self changed: #maxDeviation.
	self broadcast: #changed: with: #name.
	self changed: #noise.
	self changed: #potentiometer.
	self changed: #switch.
	self changed: #uniselector.
	self changed: #uniselectorActive.
	self changed: #uniselectorTime.
	self changed: #uniselectorTiming.
	self changed: #viscosity.
	self changed: #status</body>
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>private-running</category>

<body package="Homeostat" selector="computeNextDeviation">computeNextDeviation
	"Computes the output current at time t+1 on the basis of the current input and the various parameters
	  this basic function mimicks Asbhy's original device by the following procedure:

	1. Try to move the needle to a new position (on the basis of  the input values computed by computeTorque) 
	     (the details of this operation are in method HomeoUnit &gt;&gt; newNeedlePosition: aValue and in HomeoUnit&gt;&gt;computeTorque
	 2. clip value if it is outside maxRange
	 3. put new value in criticalDeviation

	One possibility would have been  to use a minimal function like the one used by A Eldridge in her simulation (see Eldridge 2000, p.20): 
	nextOutput := (input(j) * weight(j) * ) + noise           (with j ranging over  all units connected to the current unit)

	This approach simplifies considerably the simulation, but has the disadvantage of  reducing the role of the unit to nil. In fact, all the work  (in Eldridge's simulation)  is done by the system, which reads, for every tick of time, the outputs from the various connected units, computes new outputs, and updates the units. In other words, this approach reduces the homeostat's units to simple data structures (which is literally what they are in her C program), deprived of any possiblity of 'action', i.e. of any behavior. Our approach here will be different, by allowing a partial separation between homeostat, units, and connections. It follows that the computation of the unit's next value is internal to unit itself, even if it considers  values (obtained from inputConnections) that may have been deposited from the outside. 
	This approach allows the possibilty that different units may have different behaviors, etc. and it also allows for the possibility of having the units being operated upon by means other than the input  coming from other homeoUnits. For instance, input coming directly from the environment, like the direct manipulation of the needles. It also forces the simulation to provide a closer resemblance of Ashby's original electro-mechanical device. Furthermore, Eldridge's simple approach can be easily recovered by reducing the computation of the unit's next output to the sum of values stored in inputConnections, and by setting the range of the needles' deviation (maxDeviation) to 1. In short: Eldridge's model as reimplemented here would have the following method: 
HomeoUnit&gt;&gt;computeNextOuput 
nextOutput := inputsCollection inject: 0 into: [ :tempSum :conn | tempSum + conn output]

Our method is close to hers and basically reduces to this behavior when all the parameters specific to the unit are ininfluent. That is, when: noise = 0, viscosity = 0, and  there is no direct outside influence. Nonetheless, encapsulating the computation inside the unit allows for a much more flexible system that can be easily extended to encompass more sophisticated behavior."
	
	"first update the current value of critical deviation with the unit's internal noise"
	self updateDeviationWithNoise.
	" then update the deviation"
	nextDeviation  := self newNeedlePosition: self computeTorque.</body>

<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
	"see method newNeedlePosition for an extended comment on how to compute the displacement of the needle. Briefly, here we just sum aTorqueValue to the current deviation."" 
       "  

	"since the noise is a distortion randomly select either a positive or negative value for noise"

	"compute a value for noise by choosing a normally distributed random value centered around 0."

	"consider noise as the ration of the current affected by noise"

	| totalForce newVelocity |
	
	totalForce := aTorqueValue.	"NOTE: it does not  compute the net force acting on the needle by adding the (negative) force produced by the drag and/ or frictional forces). Only subclasses of HomeoUnit do it"
	newVelocity := totalForce / needleUnit mass.	"In an Aristotelian model, the change in displacement (= the velocity) is equal to the force affecting the unit divided by the  mass: F = mv or v = F/m"
	"Testing"
	debugMode 
		ifTrue: 
			[Transcript
				show: ' new position at time: ';
				show: (time + 1) printString;
				show: ' for unit: ';
				show: self name;
				show: ' will be ';
				show: (criticalDeviation + (aTorqueValue * viscosity)) printString;
				cr;
				cr].
	^criticalDeviation + newVelocity	" In an Aristotelian model, new displacement is old displacement plus velocity: x = x0 + vt, with t obviously = 1 in our case."</body>

<body package="Homeostat" selector="newRandomNeedlePosition">newRandomNeedlePosition
	"computes a random value for the needle position within the accepted range "

	^ (UniformDistribution from: (self minDeviation) to: (self maxDeviation)) random.</body>

<body package="Homeostat" selector="newProportionalNeedlePosition:">newProportionalNeedlePosition: aValue 
	"see method newNeedlePosition for an extended comment on how to compute the displacement of the needle"

	| torque |
	torque := aValue / (maxDeviation *2).
	^criticalDeviation + (torque * viscosity)</body>

<body package="Homeostat" selector="computeTorque">computeTorque
	
" In order to closely simulate Asbhy's implementation, computeTorque would have to compute the torque affecting the needle by solving a set of differential equations whose coefficients represents the weighted values of the input connections. This is the approach followed by Capehart (1967) in his simulaton of the Homeostat in Fortran. See the comment to the method newNeedlePosition for a discussion.
Here we simply compute the sum of the weighted input values extracted from  the inputsCollection on all the connections that are active"
| activeConnections |

activeConnections := inputConnections select: [:each | (each isActive) and: [ each incomingUnit isActive]].


inputTorque := activeConnections inject: 0 into: [ :tempSum :conn | 
								tempSum + (conn  output)].
"Testing"
debugMode ifTrue: [ Transcript show: 'current torque at time: ';  show: time printString; show: ' for unit: '; show: self name; show: ' is ' ; show: inputTorque printString; cr.].

self changed: #inputTorque.

^inputTorque</body>

<body package="Homeostat" selector="newNeedlePosition:">newNeedlePosition: aTorqueValue 
	"computes the new needle position on the basis of aTorqueValue, which represents the torque applied to the unit's needle. This method is marquedly different from Ashby's implementation, even if it captures its intent. A long discussion is appended  below."

	needleCompMethod = 'linear' 
		ifTrue: [^self newLinearNeedlePosition: aTorqueValue]
		ifFalse: [ (needleCompMethod = 'proportional')
					ifTrue: [^self newProportionalNeedlePosition: aTorqueValue]
					ifFalse: [^self newRandomNeedlePosition]]       "defaults to a random computation method if the method is not specified"





"In Asbhy's original implementation, each incoming connection corresponded to a coil  around the unit's magnet. The sum of the input currents flowing through the coils produced  a torque on the magnet, which, in turn, moved the needle in the trough.
 In order to closely simulate Asbhy's implementation, newNeedlePosition would have to compute the torque affecting the needle by solving a set of differential equations whose coefficients represent the weighted values of the input connections. This is the approach followed by Capehart (1967) in his simulaton of the Homeostat in Fortran.

However, it seems pointless to use differential equations to model a physical mechanism which was originally devised to model a physiological system. After all, as Capehart himself acknowledges, the Homeostat is a kind of analogue computer set up to compute the fundamental features of the system it models.. We might as well use a different kind of computer, assuming we are able to capture the essential features as accurately. In this respect, we follow Ashby's suggestion that 'the torque on the magnet [ i.e. the needle] is approximately proportional to the algebraic sum of the currents in A, B, and C' (Ashby 1960:102, sec 8/2), where the coils A, B, C, (and D, i.e. the unit itself) carry a current equal to the weighted input. Thus, this method produces a value that is proportional to the inputValue.

However,  it might be argued (for instance by a dynamic system theorist) that a thoroughly digital simulation of the Homeostat like this one loses what is most essential to it: the continuity of real-valued variables operating in real time. Anyone accepting this objection may partially meet it by:
- subclassing HomeoUnit, 
- adding a method that produces differential equation describing the Torque
- and replacing the two methods computeTorque and newNeedlePosition: aTorqueValue with numeric computations of the solutions of the diff equations.

See Ashby, Design for a Brain, chps. 19-22 for a mathematical treatment of the Homeostat and Capehart 1967 for suggestions on a possible implementation (which requires a Runge-Kutta diff solution routine or equivalent and Hutwitz convergence test on the coefficient matrix

Our method(s) assumes:

1. that the torque is simply the sum of the input connections, hence a value included in +/-  (inputConnections size) (since the max value of any unit's output  and hence  of any input,  is 1 and the minimum  -1)

2. the torque represents the force that displaces the needle from its current position. The value of this displacement is obviously directly proportional to the force. However, the constant of proportionality is important: if the displacement is simply equal to the torque, which, in turn, is equal to the sum of inputs, then the ***potential displacement*** grows linearly with the connected units. If, instead, the displacement is equal to the ratio between the maximum torque and the maximum deviation, then the ***potential displacement*** is independent from the number of connected units and will depend more directly on the values of the incoming units rather than their number. It is obvious that the behavior of a collection of units, i.e. a homeostat, will be different in either case. Ashby's probably followed the former model, as evidenced by his (widely reported)  comments about the direct relation between instability and number of units (see also Capehart 1967 for comments to the same effect). It muct be admitted, however, that a careful manipulation of the weights of the connection may reduce the difference between the two methods: one would have to uniformly reduce the weights whenever a new conenction is added to transform the first ('Ashby's') approach into the second.

In order to allow experimentation with either approach, we include both methods: HomeoUnit&gt;&gt;newLinearNeedlePosition: and HomeoUnit&gt;&gt;newProportionalNeedlePosition: 
The choice between the two is determined by the value of the instance variable needleCompMethod. Default (stored in the class variable) is linear.

The viscosity is between 0 and 1, with 0 being the maximum (needle unable to move) and 1 being the minimum (no effect on movement)"</body>

<body package="Homeostat" selector="clearFutureValues">clearFutureValues
	"sets to 0 the internal values used for computing future states. "


self nextDeviation: 0.
self inputTorque: 0.
self currentOutput: 0</body>

<body package="Homeostat" selector="isNeedleWithinLimits:">isNeedleWithinLimits: aValue
	"Checks whether the proposed value exceeds the unit's range (both + and -)"

	^aValue between:  (maxDeviation negated) and: maxDeviation.</body>

<body package="Homeostat" selector="essentialVariableIsCritical">essentialVariableIsCritical

"Checks if the next output is critical, i.e. too close to the limit of the  acceptable range, stored in maxDeviation."

| allowedRange |


allowedRange := maxDeviation * 0.9.

^ (nextDeviation between: (allowedRange negated) and: allowedRange) not</body>

<body package="Homeostat" selector="produceNewName">produceNewName
	"produces a name made up of  'Unit'  plus an integer representing the current number  of existing units plus 1"


^ 'Unit', (self class allInstances size + 1) printString.
</body>

<body package="Homeostat" selector="updateUniselectorTime">updateUniselectorTime

"updates the tick counter fore the uniselector"

uniselectorTime := uniselectorTime + 1.</body>

<body package="Homeostat" selector="computeOutput">computeOutput
	"converts the current criticalDeviation into a a value scaled to the output range.
	 clips the output to within the allowed output range."

	| outRange out lowDev devRange |
	outRange := (outputRange at: 'high') - (outputRange at: 'low').
	lowDev := self minDeviation.
	devRange := maxDeviation - lowDev.
	out := (criticalDeviation - lowDev)*(outRange / devRange ) + (outputRange at: 'low').

	(out between: (outputRange at: 'low') and: (outputRange at: 'high')) 
		ifTrue: [self currentOutput: out]
		ifFalse: 
			[out &gt; 0 
				ifTrue: [self currentOutput: (outputRange at: 'high')]
				ifFalse: [self currentOutput: (outputRange at: 'low')]]</body>

<body package="Homeostat" selector="updateDeviationWithNoise">updateDeviationWithNoise
	"apply the unit's internal noise to the critical deviation and update accordingly.  Computation of noise uses the utility HomeoNoise class"	
| newNoise |

	newNoise := HomeoNoise newWithCurrent: criticalDeviation andNoise: noise.
	newNoise distorting.	"since the noise is a distortion randomly select either a positive or negative value for noise"
	newNoise normal.	"compute a value for noise by choosing a normally distributed random value centered around 0."
	newNoise proportional.	"consider noise as the ration of the current affected by noise"
	criticalDeviation := criticalDeviation + newNoise getNoise.	"apply the noise to the critical deviation value"</body>

<body package="Homeostat" selector="clipDeviation:">clipDeviation: aValue 
	"clips the unit's criticalDeviation value if it exceeds its maximum or minimum. Preserve the sign of  aValue."



	(self isNeedleWithinLimits: aValue)
			 ifTrue: [^aValue] 
			ifFalse: [^(maxDeviation * aValue sign)]</body>

<body package="Homeostat" selector="physicalVelocity">physicalVelocity
	"convert the velocity of the unit into a vlaue expressed in physical units (m/s) according to the physical equivalence parameters"


^currentVelocity * (physicalParameters at: 'lengthEquivalence') / (physicalParameters at: 'timeEquivalence')</body>

<body package="Homeostat" selector="updateTime">updateTime

""

"Do nothing. In the current model, time is updated by the homeostat, the homeounit are basically computing machine with no knowledge of time"

^self</body>

<body package="Homeostat" selector="operateUniselector">operateUniselector
	"Activates the uniselector to randomly change the weights of the input connections (excluding the self connection)
	  reset the tick count of uniselector activation to 0"

| weightChanges change|

weightChanges := OrderedCollection new.



	inputConnections do: 
			[:conn | 
			  | changedWeight  |
			   conn incomingUnit = self 
				ifFalse: 
					[(conn state = 'uniselector' and: [conn active]) 
						ifTrue: [
							change := OrderedCollection new.
							change add: conn incomingUnit name; add: conn weight.
							changedWeight := uniselector produceNewValue.
							change add: changedWeight.
							weightChanges add: change.
							conn newWeight: changedWeight]]].
	uniselectorTime := 0.
	uniselector advance.

	

"For debugging"

showUniselectorAction 
		ifTrue: 
			[
			  weightChanges do: [
			  :connChange |
				Transcript
				show: ' At time: ';
				show: (time + 1) printString;
				show: ' unit: ';
				show: self name;
				show: ' activated uniselector  for unit ';
				show: (connChange at: 1);
				show: ' switching weight from: ';
				show: (connChange at: 2) printString ;
				show: ' to: ';
				show: (connChange at: 3) printString;
				cr;
				cr].]</body>
</methods>


<methods>
<class-id>HomeoUnitAristotelian</class-id> <category>private-running</category>

<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
	"see method newNeedlePosition for an extended comment on how to compute the displacement of the needle. Briefly, here we just sum aTorqueValue to the current deviation. "

| totalForce  newVelocity |

totalForce := aTorqueValue + (self dragOn:  aTorqueValue) .					" computes the net force acting on the needle by adding the (negative) force produduced by the drag and/ or frictional forces)"

newVelocity := (totalForce / needleUnit mass).							  "In an Aristotelian model, the change in displacement (= the velocity) is equal to the force affecting the unit divided by the  mass: F = mv or v = F/m"
"Testing"
debugMode ifTrue: [Transcript show: ' new position at time: ';  show: (time + 1) printString; show: ' for unit: '; show: self name; show: ' will be ' ; show: (criticalDeviation + (aTorqueValue * viscosity) ) printString; cr;cr.].

	^criticalDeviation + newVelocity                                                               " In an Aristotelian model, new displacement is old displacement plus velocity: x = x0 + vt, with t obviously = 1."</body>

<body package="Homeostat" selector="dragOn:">dragOn: aForce
	"computes the frictional forces acting on the Aristotelian unit. Only considers the viscosity of the medium in the trough the needle moves through, disregarding other possible frictional forces"
| viscRatio |
"converts the actual viscosity to a ratio"

viscRatio := viscosity / (DefaultParameters at: 'maxViscosity').
^( aForce * viscRatio ) negated.</body>
</methods>

<methods>
<class-id>HomeoUnitAristotelian</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>HomeoUnitNewtonianTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoUnitNewtonianTest</class-id> <category>running</category>

<body package="Homeostat" selector="testComputeNextVelocityWithConnections">testComputeNextVelocityWithConnections
	| testRuns oldVelocity anotherUnit errorTolerance maxDelta counter |
	errorTolerance := 10 raisedTo: -14.
	testRuns := 1000.
	anotherUnit := HomeoUnitNewtonian new.
	unit addConnectionWithRandomValues: anotherUnit.
	(unit inputConnections at: 2) noise: 0.
	"Transcript clear."
	unit criticalDeviation: 0.
	unit noise: 0.
	"Transcript show: 'Testing velocity with 1 connection, starting with unit at: ', unit criticalDeviation printString; cr."
	100 timesRepeat: 
			[counter := 0.
			maxDelta := 0.
			1 to: testRuns
				do: 
					[:i | 
					"		Transcript show: 'Test run number: ', i printString, ' '."

					| torque velocityDelta computedVelocity |
					unit needleUnit mass: (UniformDistribution from: 1 to: 1000) random.
					oldVelocity := unit currentVelocity.
					torque := (unit inputConnections 
								select: [:each | each isActive and: [each incomingUnit isActive]]) 
									inject: 0
									into: [:tempSum :conn | tempSum + conn output].		"compute the torque as sum of the output coming from connected units"
					torque := torque + unit drag.											"consider the drag affecting the force."
					computedVelocity := oldVelocity + (torque / unit needleUnit mass).	"velocity value according to  Newtonian dynamics: v = v0 +at (where a is force / mass)"
					unit selfUpdate.
					"Do not compare calculations when the unit's needle would have gone over the maximum limit, because the actual displacement is clipped at the maximum value. 
			Since actual velocity is computed on the basis of actual displacement (as it should be), the theoretical value is bound to be off"
					(unit criticalDeviation &gt;= unit maxDeviation 
						or: [unit criticalDeviation &lt;= unit maxDeviation negated]) 
							ifTrue: [velocityDelta := 0]
							ifFalse: [velocityDelta := (unit currentVelocity - computedVelocity) abs].
					velocityDelta &lt; errorTolerance 
						ifFalse: 
							["Transcript
								show: 'Failed on: ' , velocityDelta printString , ' at run: ' 
											, i printString;
								cr."
							counter := counter + 1].
					"Transcript
						show: 'delta between theoretical velocity and computed velocity is: ' 
									, velocityDelta printString , ' and test is: ' 
									, (velocityDelta &lt; errorTolerance) printString;
						cr."
					velocityDelta &gt; maxDelta ifTrue: [maxDelta := velocityDelta].
					self assert: velocityDelta &lt; errorTolerance].
			"Transcript
				show: 'MaxDelta was: ' , maxDelta printString , ' and I failed ' 
							, counter printString , ' test over: ' 
							, testRuns printString , ' or about: ' 
							, (counter / testRuns * 100) asFloat printString , '%';
				cr"]</body>

<body package="Homeostat" selector="testComputeNextDeviationLinear">testComputeNextDeviationLinear
	

| oldDev oldVelocity torque |

unit criticalDeviation: 0.
1000 timesRepeat: 
		[torque := (UniformDistribution from: -1 to: 1) random.
		unit needleUnit mass: (UniformDistribution from:  1 to: 10000) random.
		oldDev := unit criticalDeviation.
		oldVelocity := unit currentVelocity.
		unit criticalDeviation: (unit newLinearNeedlePosition: torque).
		self assert: ((unit criticalDeviation) = (oldDev  + oldVelocity + (1/2 * (torque/ unit needleUnit mass))))].      "Check the computation is correct according to Newtonian dynamics"</body>

<body package="Homeostat" selector="testDragEquationDrag">testDragEquationDrag
	"The Drag equation comptutes drag force on a surface of area A as
	 Drag = Area * 1/2 * DragCoefficient * density * velocity^2
	  We actually need to convert the unit's current velocity
	   to real physical units to have a minimun of plausibility.
	  HomeoUnit&gt;&gt;physicalVelocity does that on the basis of conversion parameters
	 stored in the iVar physicalParameters"

|dragForce errorTolerance testRuns delta|

errorTolerance := 0.000000001.

testRuns := 1000.

"When the unit is started, velocity is zero, and dragForce should be zero"
unit currentVelocity: 0.
testRuns timesRepeat: [
	
	unit density: (UniformDistribution from: 1 to: 1000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	unit needleUnit dragCoefficient: (UniformDistribution from: 0.3 to: 2) random.

	dragForce := unit dragEquationDrag.
	self assert: (dragForce = 0).].

"When Velocity is not zero, Drag Force follows drag's equation.
 We briefly test with random velocities,  random densities,  random surface areas, and random coefficients"

testRuns timesRepeat: [

	unit currentVelocity: (UniformDistribution from: -10 to: 10) random.
	unit density: (UniformDistribution from: 1 to: 1000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	unit needleUnit dragCoefficient: (UniformDistribution from: 0.3 to: 2) random.

	dragForce := unit dragEquationDrag.
	delta := (dragForce - (1/2 * unit needleUnit surfaceArea * unit needleUnit dragCoefficient * unit density * unit physicalVelocity squared)) abs.
	self assert: delta &lt; errorTolerance. ]</body>

<body package="Homeostat" selector="testComputeNextVelocityWithoutConnections">testComputeNextVelocityWithoutConnections
	

| testRuns oldVelocity  errorTolerance maxDelta counter|

errorTolerance :=10 raisedTo: -13 .
testRuns := 100.

"Transcript clear."
unit criticalDeviation: 0.
unit noise: 0.
unit currentOutput: 0.1.
"unit toggleDebugMode."
(unit inputConnections at: 1)  noise: 0.
"Transcript show: 'Testing velocity with no connections, starting with unit at: ', unit criticalDeviation printString; cr."
1000 timesRepeat:[
	counter := 0.
	maxDelta := 0.
	1 to: testRuns do: 
		[:i |
		| torque velocityDelta computedVelocity |

"		Transcript show: 'Test run number: ', i printString, ' '."
		unit needleUnit mass: (UniformDistribution from:  1 to: 1000) random.
		"unit needleUnit mass: 1."
		oldVelocity := unit currentVelocity.
		torque :=  
            (unit  inputConnections select: [:each | (each isActive) and: [ each incomingUnit isActive]])
		 inject: 0 into: [ :tempSum :conn | tempSum + (conn  output)].  "compute the torque as sum of the output coming from connected units"	
		torque := torque + unit drag.      "include drag affecting the force"
		computedVelocity := (oldVelocity + (torque / unit needleUnit mass)).  "velocity value according to  Newtonian dynamics: v = v0 +at (where a is force / mass)"
		unit selfUpdate.
		"Do not compare calculations when the unit's needle would have gone over the maximum limit, because the actual displacement is clipped at the maximum value. 
		Since actual velocity is computed on the basis of actual displacement (as it should be), the theoretical value is bound to be off"
		((unit criticalDeviation &gt;= unit maxDeviation)	or: [unit criticalDeviation &lt;= unit maxDeviation negated]) 
			ifTrue: [ velocityDelta := 0]
			ifFalse:[velocityDelta := ((unit currentVelocity) - computedVelocity) abs] .      
		velocityDelta &lt; errorTolerance  ifFalse: ["Transcript show: 'Failed on: ', velocityDelta printString, ' at run: ', i printString; cr. " counter := counter + 1.].
"		Transcript show: 'delta between theoretical velocity and computed velocity is: ', velocityDelta printString,  ' and test is: ', (velocityDelta &lt; errorTolerance) printString; cr."
		velocityDelta &gt; maxDelta ifTrue: [maxDelta := velocityDelta].
		"velocityDelta abs &gt; errorTolerance ifTrue: [ Transcript show: 'Run number: ', i printString, ' delta: ', velocityDelta printString, ' updated comp vel.: ', unit currentVelocity printString, ' theoretical vel.: ',  computedVelocity printString; cr]."
		self assert: (velocityDelta abs &lt; errorTolerance)].
	"Transcript show: 'MaxDelta was: ', maxDelta printString, ' and I failed ', counter printString, ' test over: ', testRuns printString, ' or about: ', (counter/testRuns*100) asFloat printString, '%'; cr"
]</body>

<body package="Homeostat" selector="testStokesDrag">testStokesDrag
	"Stokes's law computes drag force on a sphere of radius r  as 6* pi * radius * viscosity * velocity.
	 We use the radius of the surface area of the moving needle instead"

|dragForce  radius testRuns|
testRuns := 1000.
radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.

"When the unit is started, velocity is zero, and dragForce should be zero"
unit currentVelocity: 0.

testRuns timesRepeat: [	
	unit viscosity: (UniformDistribution from: 0.1 to: 100000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.
	dragForce := unit stokesLawDrag.
	self assert: (dragForce = 0)].

"When Velocity is not zero, Drag Force follows Stokes's law.
 We briefly test with random velocities,  random densities, and random surface areas"


testRuns timesRepeat: [
	unit currentVelocity: (UniformDistribution from: -10 to: 10) random.
	unit viscosity: (UniformDistribution from: 0.1 to: 100000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.
	dragForce := unit stokesLawDrag.
	self assert: ((dragForce = (6 * (Double pi) * radius * unit viscosity * unit currentVelocity) negated))].</body>
</methods>

<methods>
<class-id>HomeoUnitNewtonianTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Edit the following to properly initialize instance variables ***"
	unit := nil.
	homeostat := nil.
	" *** And replace this comment with additional initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
	"Initialize the HomeoUnit class and sets up a default HomeoUnit for testing"

"initialize the HomeoUnit class to clear all old names (held in the Names shared variable)"
HomeoUnit initialize.

unit := HomeoUnitNewtonian new.</body>
</methods>


<methods>
<class-id>PlayerTests class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>PlayerTests</class-id> <category>java player examples</category>

<body package="Homeostat" selector="spaceWanderer">spaceWanderer
	"PlayerTests new spaceWanderer
      (adapted  from the JavaPlayer example SpaceWanderer Example)
	Be sure to:
 	-  start the player server with the simple.cfg configuration file found
	in the JavaPlayer/Examples/SpaceWanderer directory
	- start the Java Virtual machine with the JavaConnect facilities and load the
	  JavaPLayer classes from the JavaConnect browser"

| robot posi soni sonarRanges speedConstant |

"set a speed constant to regulate robot's forward speed"

speedConstant := 2. 

"create the client proxy"
robot := JavaWorld.javaclient3.PlayerClient new_String: 'localhost' int: 6665.

"create the position proxy" 
posi := robot requestInterfacePosition2D_int: 0 int: 1.

"create the sonar proxy" 
soni := robot requestInterfaceRanger_int: 0 int: 1.

"run the client proxy" 
robot runThreaded_long: -1 int: -1. 

"initialize sonar interface" 
[soni isDataReady] whileFalse: []. 

"roam around bumping off walls" 
[true] whileTrue: [
			 | xSpeed yawSpeed rightSonar leftSonar |
			"read the sonar data" 
			 sonarRanges:= soni getData getRanges. 
			 rightSonar := sonarRanges asSmalltalkValue at: 1. 
			 leftSonar := sonarRanges asSmalltalkValue at: 2.
		
			 "set forward speed and turning"
			 xSpeed := ((leftSonar + rightSonar) /2) /speedConstant. 
			 yawSpeed := ((leftSonar -rightSonar)/speedConstant) * (180/Double pi). 

			 "set the robot to go forward" 
			 posi setSpeed_double: xSpeed double: yawSpeed.]</body>
</methods>

<methods>
<class-id>PlayerTests</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>HomeoNoise class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="newWithCurrent:andNoise:">newWithCurrent: aNumber andNoise: anotherNumber
	"Answer a newly created and initialized instance."


	NoiseCalculator isNil ifTrue: [
		NoiseCalculator := super new initialize].
		
		NoiseCalculator current: aNumber.
		NoiseCalculator noise: anotherNumber.

	^NoiseCalculator

</body>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."


	NoiseCalculator isNil ifTrue: [
		NoiseCalculator := super new initialize].

	^NoiseCalculator			
</body>
</methods>


<methods>
<class-id>HomeoNoise</class-id> <category>noiseAlgorithms</category>

<body package="Homeostat" selector="getCurrentLinearlyAffected">getCurrentLinearlyAffected
	"Returns a value representing a current linearly affected by the noise."



| currentSign |
	currentSign := current sign.
	currentSign = 0 ifTrue: [currentSign := 1].

^((current abs)  - noise ) * currentSign</body>

<body package="Homeostat" selector="getCurrentPropAffected">getCurrentPropAffected
	"Returns a value representing a current proportionally affected by the noise."


| currentSign |
	currentSign := current sign.
	currentSign = 0 ifTrue: [currentSign := 1].

^(current abs * (1- noise )) * currentSign</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>constant noise algorithms</category>

<body package="Homeostat" selector="constDistortLinearNoise">constDistortLinearNoise
	"Returns a value representing a constant distorting noise affecting linearly  the current . Assumes the noise is a number between 0 and 1"

|sign noiseSign|

noiseSign := (Random new nextBetween: -1 and: 1) sign.
sign := current sign.

^((current abs) - (noise * noiseSign)) *sign 

</body>

<body package="Homeostat" selector="constDistortPropNoise">constDistortPropNoise
	"Returns a value representing a constant distorting noise affecting proportionally  the current . Assumes the noise is a number between 0 and 1, i. e. the percentage of current lost to noise"

|sign noiseSign|

noiseSign := (Random new nextBetween: -1 and: 1) sign.
sign := current sign.

^((current abs) - (noise * (current abs) * noiseSign)) *sign</body>

<body package="Homeostat" selector="constDegradLinearNoise">constDegradLinearNoise
	"Returns a value representing a constant degrading noise affecting linearly  the current .
	 Assumes noise is a value between 0 and 1"

 | sign |

sign := current sign.

sign = 0 ifTrue: [sign := 1].   "make sure we don't lose the current when noise is 0"

^((current abs) - noise) * sign</body>

<body package="Homeostat" selector="constDegradPropNoise">constDegradPropNoise
	"Returns a value representing a constant degrading noise affecting the current proportionally. Assumes noise is a value between 0 and 1, i. e. the percentage of current lost to noise"

	| sign |

	sign := current sign.
	sign = 0 ifTrue: [sign := 1].   "make sure we don't lose the current when noise is 0"


	^(current abs - (noise * current abs)) * sign</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>accessing</category>

<body package="Homeostat" selector="proportional">proportional


ratio := 'Proportional'</body>

<body package="Homeostat" selector="uniform">uniform
distribution := 'Uniform'</body>

<body package="Homeostat" selector="degrading">degrading
mode := 'Degrading'</body>

<body package="Homeostat" selector="current">current
	^current</body>

<body package="Homeostat" selector="linear">linear


ratio := 'Linear'</body>

<body package="Homeostat" selector="normal">normal
	distribution := 'Normal'.</body>

<body package="Homeostat" selector="constant">constant
	
	distribution := 'Constant'</body>

<body package="Homeostat" selector="getNoise">getNoise
	"select the correct noise algorithm according to the values of mode, distribution and ratio and returns the noise value."

| noiseAlg |

noiseAlg := 'getNoise', mode , distribution , ratio.
^ self perform: noiseAlg asSymbol.</body>

<body package="Homeostat" selector="current:">current: anObject
	current := anObject</body>

<body package="Homeostat" selector="noise:">noise: anObject
	noise := anObject</body>

<body package="Homeostat" selector="distorting">distorting


mode := 'Distorting'.</body>

<body package="Homeostat" selector="noise">noise
	^noise</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize the NoiceCalculator to a current of 1 and noise of 0, representing a full current and no noise. These values are typically overriden by class creation methods."


	current := 1.
	noise := 0.

"default values for noise parameters"
	mode := 'Distorting'.
	distribution := 'Normal'.
	ratio := 'Proportional'.

"add the random number generator"

randomGen := Random new.
	^self</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>private-noiseAlgorithms</category>

<body package="Homeostat" selector="testNormalDistrib">testNormalDistrib
	
	"replaces noise with a random value normally distributed around noise, and with a standard distribution of noise/3"
	 noise := (NormalDistribution new: noise sigma: noise / 3) random.</body>

<body package="Homeostat" selector="getNoiseDegradingNormalProportional">getNoiseDegradingNormalProportional
	"returns a degrading noise (with sign always opposite to affected current), and normally distributed value in the interval [0, 2*noiseParameter]"

| noiseAbsValue  minAbsNoise maxAbsNoise  noiseSign |

noiseSign := current sign negated.
minAbsNoise :=0.
maxAbsNoise := noise * current abs *2.

noiseAbsValue := (NormalDistribution new: maxAbsNoise / 2  sigma: maxAbsNoise / 6) random.
"trim noise within the interval {0, 2 *noise *current abs}"
noiseAbsValue &gt; maxAbsNoise ifTrue: [ noiseAbsValue := maxAbsNoise].
noiseAbsValue &lt;  minAbsNoise  ifTrue: [noiseAbsValue := minAbsNoise].

^ noiseAbsValue * noiseSign</body>

<body package="Homeostat" selector="getNoiseDistortingNormalProportional">getNoiseDistortingNormalProportional
	"returns a distorting noise (centered around 0) normally distributed and porportional to the absolute magnitude of the affected current"

	

| noiseValue minNoise maxNoise|
minNoise := noise negated * current abs.
maxNoise := noise * current abs.

noiseValue := (NormalDistribution new: 0 sigma: maxNoise / 3) random.
"trim noise within the interval {0, 2 *noise}"
noiseValue &gt; maxNoise ifTrue: [ noiseValue := maxNoise].
noiseValue &lt; minNoise  ifTrue: [noiseValue :=  minNoise].

^ noiseValue</body>

<body package="Homeostat" selector="getNoiseDegradingConstantProportional">getNoiseDegradingConstantProportional
	"returns a degrading noise (with sign always opposite to affected current), and constant value equal to the ratio between the noise parameter and the affected current"





^ (noise*(current abs))  * current sign *-1</body>

<body package="Homeostat" selector="getNoiseDistortingUniformProportional">getNoiseDistortingUniformProportional
	"returns a distorting noise (centered around 0) uniformly  distributed in the interval [0, noise/current]."



| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise * current abs.
noiseAbsValue := (UniformDistribution new initialize: maxNoise negated to:  maxNoise) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDegradingUniformLinear">getNoiseDegradingUniformLinear
	"returns a degrading noise (sign always opposite to current) uniformly distributed and proportional to the  absolute magnitude of the noise parameter"

| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise.
noiseAbsValue := (UniformDistribution new initialize: 0 to: (2 * maxNoise)) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDistortingUniformLinear">getNoiseDistortingUniformLinear
	"returns a distorting noise (centered around 0) uniformly  distributed in the interval [-noise, noise]."


| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise.
noiseAbsValue := (UniformDistribution new initialize: maxNoise negated to:  maxNoise) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDistortingConstantLinear">getNoiseDistortingConstantLinear
	"returns a distorting noise (centered around 0),  with absolute value equal to the noise parameter"


| randomSign |

randomSign := (UniformDistribution  new initialize: -1 to: 1) random  sign .


^ noise * current sign *randomSign.</body>

<body package="Homeostat" selector="getNoiseDegradingNormalLinear">getNoiseDegradingNormalLinear
	"returns a degrading noise (sign always opposite to current) normally distributed and proportional to the  absolute magnitude of the noise parameter"

	

| noiseAbsValue noiseSign |

noiseSign := current sign negated.
noiseAbsValue := (NormalDistribution new: noise sigma: noise *1 /3) random.

"trim noise within the interval {0, 2 *noise}"
noiseAbsValue &gt; (2 * noise) ifTrue: [ noiseAbsValue := 2* noise].
noiseAbsValue &lt; 0 ifTrue: [noiseAbsValue := 0].
^ noiseAbsValue * noiseSign.</body>

<body package="Homeostat" selector="getNoiseDistortingConstantProportional">getNoiseDistortingConstantProportional
	"returns a distorting noise (centered around 0),  equal to the ratio between the absolute magnitude of the affected current and the noise parameter"

| randomSign |

randomSign := (UniformDistribution  new initialize: -1 to: 1) random  sign .


^ (noise * (current abs)) * current sign *randomSign.</body>

<body package="Homeostat" selector="getNoiseDegradingConstantLinear">getNoiseDegradingConstantLinear
	"returns a degrading noise (with sign always opposite to affected current), and constant value equal to the noise parameter"





^ noise * current sign *-1</body>

<body package="Homeostat" selector="getNoiseDegradingUniformProportional">getNoiseDegradingUniformProportional
	"returns a degrading noise (with sign always opposite to affected current), and uniformly distributed value in the interval [0, (2*noiseParameter) * current ]"

| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := 2 * (noise * (current abs)).
noiseAbsValue := (UniformDistribution new initialize: 0 to:  maxNoise) random.
^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDistortingNormalLinear">getNoiseDistortingNormalLinear
	"returns a distorting noise (centered around 0) normally distributed and proportional to the  absolute magnitude of the noise parameter"
	

| noiseValue |

noiseValue := (NormalDistribution new: 0 sigma: noise / 3) random.
"trim noise within the interval { -noise, noise}"
noiseValue &gt; noise ifTrue: [ noiseValue := noise.].
noiseValue &lt; (noise negated)  ifTrue: [noiseValue :=  noise negated.].

^ noiseValue</body>
</methods>


<methods>
<class-id>HomeoUniselector class</class-id> <category>testing class hierarchy</category>

<body package="Homeostat" selector="includesType:">includesType: aString

"answers true if aString represents the HomeoUniselector class or one of its subclasses"

|uniselectorClasses|

uniselectorClasses := Set new.

(HomeoUniselector withAllSubclasses) do: [:class | uniselectorClasses add: class name asString].

^uniselectorClasses includes: aString</body>
</methods>

<methods>
<class-id>HomeoUniselector class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"comment stating purpose of message"

^ super new initialize</body>
</methods>


<methods>
<class-id>HomeoUniselector</class-id> <category>selection-functions</category>

<body package="Homeostat" selector="simpleRandom">simpleRandom</body>

<body package="Homeostat" selector="ashbyRandom">ashbyRandom

"produces 1 of a possible 25 different values for the weight by selecting at random a 25th of the interval defined by lowerBound and upperBound "

| intervalSegment randValue sign|

intervalSegment := (upperBound - lowerBound) / 25.
randValue := ((Random new) nextBetween: 0 and: 25) rounded.
sign := ((Random new) nextBetween: -1 and: 1) rounded.

^ randValue*intervalSegment * sign.</body>
</methods>

<methods>
<class-id>HomeoUniselector</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="setDefaults">setDefaults

"sets the defaults for the uniselector weights. Can be (and usually is) overidden by subclasses"

lowerBound := 0.
upperBound := 1.

beeps:= false.</body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

self setDefaults.</body>
</methods>

<methods>
<class-id>HomeoUniselector</class-id> <category>accessing</category>

<body package="Homeostat" selector="lowerBound:">lowerBound: anObject
	lowerBound := anObject</body>

<body package="Homeostat" selector="beeps">beeps
	^beeps</body>

<body package="Homeostat" selector="lowerBound">lowerBound
	^lowerBound</body>

<body package="Homeostat" selector="upperBound:">upperBound: anObject
	upperBound := anObject</body>

<body package="Homeostat" selector="advance">advance

"control how to advance to the next position of the uniselector. Each subclass implements different mechanisms"
self subclassResponsibility</body>

<body package="Homeostat" selector="upperBound">upperBound
	^upperBound</body>

<body package="Homeostat" selector="toggleBeeping">toggleBeeping
	"toggle sound"

beeps isNil
	ifFalse: [beeps:= beeps not]
	ifTrue:  [beeps := true].
self changed: #uniselectorSound</body>
</methods>


<methods>
<class-id>HomeoUniselectorAshbyOld</class-id> <category>testing</category>

<body package="Homeostat" selector="sameAs:">sameAs: aUniselector 
	

		self class = aUniselector class 
			ifFalse: [^false] 
			ifTrue: [
				^lowerBound = aUniselector lowerBound and:
					[upperBound = aUniselector upperBound and:
					 	[interval = aUniselector interval]]]</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyOld</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	" initializes the interval and the steps to default values. The lowerBound and upperBound are always 0 and 1, as per Ashby's implementation, becasue they represent the fraction of the input to reach the unit (sse Design for a Brain sec 8/2, p. 102 (1960 ed."
      
	lowerBound := 0.
	upperBound:= 1.
	self setDefaults.
	index := 0.
	steps := 12.
	interval := (upperBound - lowerBound) / steps.
	unitsControlled := 10.
	self produceSequence.</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyOld</class-id> <category>accessing</category>

<body package="Homeostat" selector="interval">interval
	^interval</body>

<body package="Homeostat" selector="produceNewValueAndSound">produceNewValueAndSound

"produce the next value in the sequence, randomize the sign,  and updates the index. Ring the sytem bell when done"
Screen default ringBell.
^self produceNewValue.</body>

<body package="Homeostat" selector="steps:">steps: aPositiveNumber

"Must always be an integer &gt; 0" 

aPositiveNumber &gt; 0 ifTrue: [steps := aPositiveNumber asInteger]</body>

<body package="Homeostat" selector="advance">advance
"does nothing because this uniselector advance automatically each time it is called (by increasing its index)"
^self</body>

<body package="Homeostat" selector="unitsControlled">unitsControlled
	^unitsControlled</body>

<body package="Homeostat" selector="lowerBound:">lowerBound: aNumber

"Do nothing, lowerBound is always 0."

^self.</body>

<body package="Homeostat" selector="index:">index: anObject
	index := anObject</body>

<body package="Homeostat" selector="sequence:">sequence: anObject
	matrix := anObject</body>

<body package="Homeostat" selector="steps">steps
	^steps</body>

<body package="Homeostat" selector="sequence">sequence
	^matrix</body>

<body package="Homeostat" selector="produceNewValue">produceNewValue

"produces the next value in the sequence and updates the index."
| value |
(index = (matrix size)) ifTrue: [index := 1 ]
				                 ifFalse: [index := index + 1].
       
value:=  matrix at: index.

"Transcript show: ' new Value is: ', value printString, '  and new index is: ', index printString; cr."
^value</body>

<body package="Homeostat" selector="index">index
	^index</body>

<body package="Homeostat" selector="unitsControlled:">unitsControlled: aNumber

"The uniselector is initialized to to control  10 maximum connections and it initializes its transition matrix (sequence) accordingly. When the required number of max connections increases, it goes up in 10 units step increments and produces a new transition matrix."

aNumber &gt; unitsControlled 
		ifTrue: [unitsControlled := unitsControlled + 10].
self produceSequence.</body>

<body package="Homeostat" selector="upperBound:">upperBound: aNumber

"Do nothing, upperBound is always 1"

^self.</body>

<body package="Homeostat" selector="interval:">interval: anObject
	interval := anObject</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyOld</class-id> <category>private</category>

<body package="Homeostat" selector="produceRandomIntervalsCollection">produceRandomIntervalsCollection
	"Produces a randomizes sequence of integers of size steps * 2 + 1, representing the number of possible values of the uniselector"

	| orderedSequence |
	orderedSequence:= OrderedCollection new: (steps * 2) + 1.
	orderedSequence add: 0.
	1 to: steps do: [:i | orderedSequence add: i * interval.
					     orderedSequence add: i * interval * -1].
	matrix := orderedSequence shuffled.</body>

<body package="Homeostat" selector="produceSequence">produceSequence

self produceRandomIntervalsCollection</body>
</methods>


<methods>
<class-id>HomeoUniselectorUniformRandom</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setDefaults">setDefaults

"sets the defaults for the uniselector weights. Can be ovveridden by subclasses"

lowerBound := -1.
upperBound := 1.

beeps:= false.</body>
</methods>

<methods>
<class-id>HomeoUniselectorUniformRandom</class-id> <category>accessing</category>

<body package="Homeostat" selector="produceNewValue">produceNewValue
"produce a new random value uniformly distributed in the interval [lowerBoud, upperBound]"


beeps ifTrue: [Screen default ringBell].
^ (UniformDistribution from: lowerBound to: upperBound) random.</body>

<body package="Homeostat" selector="advance">advance
"does nothing because this uniselector has no concept of an index---it produces a new uniformly distributed  random value every time it  is called "
^self</body>

<body package="Homeostat" selector="lowerBound:">lowerBound: aNumber
	"The lowerBound of the interval the uniselector value is chosen from. The interval must be symmetric around 0"

aNumber &lt;= 0 ifTrue: [lowerBound := aNumber.
					      upperBound := lowerBound negated]
				ifFalse: [Transcript show: 'Uniselector received a wrong (positive) value for its lowerBound. Value was ignored.'; cr.].</body>

<body package="Homeostat" selector="upperBound:">upperBound: aNumber
	"The upperBound of the interval the uniselector value is chosen from. The interval must be symmetric around 0"

aNumber &gt;= 0 ifTrue: [upperBound := aNumber.
					      lowerBound := upperBound negated]
				ifFalse: [Transcript show: 'Uniselector received a wrong (negative) value for its lowerBound. Value was ignored.'; cr].</body>
</methods>


<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>testing</category>

<body package="Homeostat" selector="sameAs:">sameAs: aUniselector 
	

		self class = aUniselector class 
			ifFalse: [^false] 
			ifTrue: [
				^(ashbyKind = aUniselector ashbyKind) 					                  "uniselectors have same ashby kind"
					and: [(self sequence  - aUniselector sequence) isZero]].			"and Transition matrices are the same"</body>

<body package="Homeostat" selector="sameKindAs:">sameKindAs: aUniselector 
	

		self class = aUniselector class 
			ifFalse: [^false] 
			ifTrue: [
				^ashbyKind = aUniselector ashbyKind   ]</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
		" initializes the interval and the steps to default values. The lowerBound and upperBound are always 0 and 1, as per Ashby's implementation, because they represent the fraction of the input to reach the unit (sse Design for a Brain sec 8/2, p. 102 (1960 ed.)"
   
	lowerBound := 0.
	upperBound:= 1.
	self setDefaults.
	index := 1.
	steps := 12.
	unitsControlled := 10.
	unitIndex := 0.
	ashbyKind := 'RandomizedValues'.
	self produceSequence</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>accessing</category>

<body package="Homeostat" selector="equallySpaced">equallySpaced
	"set initialization procedure to equally spaced values )see method produceEquallySapcedValues for details"

ashbyKind := 'EquallySpacedValues'</body>

<body package="Homeostat" selector="ashbyKind">ashbyKind
	^ashbyKind</body>

<body package="Homeostat" selector="advance">advance

"advance the uniselector to the next position."
(index = (matrix numberOfRows)) ifTrue: [index := 1 ]
				                 ifFalse: [index := index + 1].
unitIndex := 0.</body>

<body package="Homeostat" selector="randomized">randomized
	"set initialization procedure to  randomized  values (see method produceRandomizedValues for details)"

ashbyKind := 'RandomizedValues'</body>

<body package="Homeostat" selector="unitsControlled">unitsControlled
	^unitsControlled</body>

<body package="Homeostat" selector="lowerBound:">lowerBound: aNumber

"Do nothing, lowerBound is always 0."

^self.</body>

<body package="Homeostat" selector="sequence:">sequence: anObject
	matrix := anObject</body>

<body package="Homeostat" selector="steps">steps
	^steps</body>

<body package="Homeostat" selector="produceNewValue">produceNewValue

"returns the weight for the next connection and advances the unitIndex"
unitIndex + 1 &gt; unitsControlled
			 ifFalse: [beeps
					  ifTrue: [Screen default ringBell].
					  unitIndex := unitIndex + 1.
					 ^matrix rowAt: index columnAt: unitIndex]
			 ifTrue: [Error raiseSignal: 'Too many units for the uniselector to control'].</body>

<body package="Homeostat" selector="sequence">sequence
	^matrix</body>

<body package="Homeostat" selector="unitsControlled:">unitsControlled: aNumber

"The uniselector is initialized to to control  10 maximum connections and it initializes its transition matrix (sequence) accordingly. When the required number of max connections increases, it goes up in 10 units step increments and produces a new transition matrix."

aNumber &gt; unitsControlled 
		ifTrue: [unitsControlled := unitsControlled + 10].
self produceSequence.</body>

<body package="Homeostat" selector="upperBound:">upperBound: aNumber

"Do nothing, upperBound is always 1"

^self.</body>

<body package="Homeostat" selector="independentlyRandomized">independentlyRandomized
	"set initialization procedure to independentely randomized  values (see method produceIndependentlyRandomizedValues for details)"

ashbyKind := 'IndependentlyRandomizedValues'</body>

<body package="Homeostat" selector="steps:">steps: aPositiveNumber

"Must always be an integer &gt; 0" 

aPositiveNumber &gt; 0 ifTrue: [steps := aPositiveNumber asInteger]</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>private</category>

<body package="Homeostat" selector="produceIndependentRandomizedValues">produceIndependentRandomizedValues

"produces a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25), n = maximum number of units controlled by the Uniselector. Notice that in this implementation, all connections have ***different***  random values. This DOES NOT seem to capture the original homeostat, where random values were implemented in hardware and could not be changed. Initializing the uniselector with produceRandomized Sequence, on the other hand, produces a matrix in which all rows (connections) share the same  random values"

| rows row |

rows :=  Array new: ((steps *2 ) + 1).
1 to: ((steps * 2) + 1) 
	do: [:r |
		row:= Array new: unitsControlled.
		1 to: unitsControlled 
			do: [ :c | 
				 row at: c put: ((UniformDistribution from: -1 to: 1) random)].
		rows at: r put: row].
	       
matrix := (Matrix rows: rows).</body>

<body package="Homeostat" selector="produceEquallySpacedValues">produceEquallySpacedValues

"produces a m x n Matrix, where m = number of equally spaced values (default = 25), n = maximum number of units controlled by the Uniselector."

| spacedValues tempSeq |

tempSeq := Array new: unitsControlled.
spacedValues := OrderedCollection new.
spacedValues add: 0.
1 to: steps do: [:i | spacedValues add: i * interval.
			       spacedValues add: i * interval * -1].	
1 to: unitsControlled 
		do: [:i  |  tempSeq at: 1 put:  (spacedValues copy shuffled) asArray].

matrix := (Matrix rows: tempSeq) transpose.</body>

<body package="Homeostat" selector="produceSequence">produceSequence

"produces the matrix containing the vlaues for the uniselector switch according to the kind of Ashby uniselector specified in ashbyKind"

self perform: ('produce',ashbyKind) asSymbol.</body>

<body package="Homeostat" selector="produceRandomizedValues">produceRandomizedValues

"produces a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25), n = maximum number of units controlled by the Uniselector. Notice that in this implementation, all connections share the same space of 25 random values, although they go through them in a different sequence. This seems to capture (one of the interpretations) of the original homeostat, where random values were implemented in hardware and could not be changed. Initializing the uniselector with produceIndependentRandomized Sequence, on the othe4r hand, produces a matrix in which all rows have (a highly likelihood of being) completely different values"

| randomValues tempSeq |

tempSeq := Array new: unitsControlled.
randomValues:= OrderedCollection new.
1 to: ((steps *2 ) + 1)  do: [:i | randomValues add: (UniformDistribution from: -1 to: 1) random].	
1 to: unitsControlled 
		do: [:i  |  tempSeq at: i put:  (randomValues shuffled) asArray].

matrix := (Matrix rows: tempSeq) transpose.</body>
</methods>


<methods>
<class-id>HomeostatTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeostatTest</class-id> <category>running</category>

<body package="Homeostat" selector="testRunningwithDelays">testRunningwithDelays

| unitA unitB unitC unitD  timeAtStart timeAtEnd delay|
	
	unitA := HomeoUnit new.
	unitB := HomeoUnit new.
	unitC := HomeoUnit new.
	unitD := HomeoUnit new.

	delay := 10.
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.

	homeostat slowingFactor: delay.
	5 timesRepeat: [
			timeAtStart := Time  millisecondClockValue.
			homeostat runOnce.
			timeAtEnd :=  Time  millisecondClockValue.
			self assert: ((timeAtEnd -timeAtStart) &gt;= delay).]</body>

<body package="Homeostat" selector="testRun">testRun

"| unitA unitB unitC unitD |
	
	unitA := HomeoUnit new.
	unitB := HomeoUnit new.
	unitC := HomeoUnit new.
	unitD := HomeoUnit new.
	
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.

homeostat start.

"</body>

<body package="Homeostat" selector="testHomeostatSaveInitialConditions">testHomeostatSaveInitialConditions
	
	| unitA unitB unitC unitD file boss newHomeostat |
	
	unitA := HomeoUnit new.
	unitB := HomeoUnit new.
	unitC := HomeoUnit new.
	unitD := HomeoUnit new.
	
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.

	file := Filename named: 'pippo.sts'.
	homeostat  bossOutOn: file. 

	boss :=  BinaryObjectStorage onOldNoScan: (Filename named: 'pippo.sts') readStream.
	newHomeostat := boss next.
	boss close.
	self assert: (homeostat sameAs: newHomeostat).</body>

<body package="Homeostat" selector="testRunForTicks">testRunForTicks

| unitA unitB unitC unitD ticks |
	
	unitA := HomeoUnit new.
	unitB := HomeoUnit new.
	unitC := HomeoUnit new.
	unitD := HomeoUnit new.

	ticks := 100.
	
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.

homeostat runFor: ticks.

"checks that it has a number of data points equal to ticks, and for all the units."

self assert: (homeostat dataCollector states size = ticks).
homeostat dataCollector states 
		do: [
			:dataCollec |
			homeostat homeoUnits 
				do: [
					:unit |
					self assert: (dataCollec keys includes: unit name)]]</body>

<body package="Homeostat" selector="testAddFullyConnectedUnit">testAddFullyConnectedUnit
	| unit1 unit2 unit3 coll1 coll2 |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	coll1 := Array 
				with: unit1
				with: unit2
				with: unit3.
	coll2 := coll1 copy.
	homeostat addFullyConnectedUnit: unit1.
	homeostat addFullyConnectedUnit: unit2.
	homeostat addFullyConnectedUnit: unit3.
	self assert: (homeostat hasUnit: unit1).
	self assert: (homeostat hasUnit: unit3).
	self assert: (homeostat hasUnit:  unit2).
	coll1 do: 
			[:firstIndex | 
			coll2 do: 
					[:secondIndex | 
					self assert: (homeostat isConnectedFrom: secondIndex to: firstIndex)]]</body>

<body package="Homeostat" selector="testSetupRandomValueFor">testSetupRandomValueFor

	| unit1 unit2 unit3  oldOutput  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	homeostat addFullyConnectedUnit: unit1.
	homeostat addFullyConnectedUnit: unit2.
	homeostat addFullyConnectedUnit: unit3.
	
"	homeostat homeoUnits detect: [: each | each = unit1]
"

	oldOutput := unit1 currentOutput.
	homeostat randomizeValuesFor: unit1.
	self deny: (oldOutput = unit1 currentOutput).</body>

<body package="Homeostat" selector="testBossOutHomeostat">testBossOutHomeostat
	"comment stating purpose of message"



	| boss newHomeostat  filename |
	filename := 'pippo.unit' asFilename.
	
	homeostat  bossOutOn: filename. 

	boss :=  BinaryObjectStorage onOldNoScan: filename readStream.
	newHomeostat:= boss next.
	boss close.

	self assert: (homeostat sameAs: newHomeostat ).</body>

<body package="Homeostat" selector="testStop">testStop


self assert: false.</body>

<body package="Homeostat" selector="testHomeostatReadyToGo">testHomeostatReadyToGo
	
	| unitA unitB unitC unitD |
	
	unitA := HomeoUnit new.
	unitB := HomeoUnit new.
	unitC := HomeoUnit new.
	unitD := HomeoUnit new.
	
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.
	
	self assert: homeostat isReadyToGo</body>

<body package="Homeostat" selector="testRemoveUnit">testRemoveUnit

| unit1 | 
unit1 := HomeoUnit new.

"teat remove an existinng unit"

homeostat addUnit: unit1.
homeostat removeUnit: unit1.
self deny: (homeostat hasUnit: unit1).

"test removing a non existing unit"

self shouldnt: [homeostat removeUnit: unit1] raise: (Error).</body>

<body package="Homeostat" selector="testIsConnectedAUnitToAnotherUnit">testIsConnectedAUnitToAnotherUnit

| unit1 unit2 |


unit1 := HomeoUnit new.
unit2 := HomeoUnit new.

homeostat addUnit: unit1.
homeostat addUnit: unit2.

homeostat addConnectionWithRandomValuesFrom: unit1 to: unit2.

self assert: (homeostat isConnectedFrom: unit1 to: unit2).

homeostat removeConnectionFrom: unit1 to: unit2.

self deny: ( homeostat isConnectedFrom: unit1 to: unit2).</body>

<body package="Homeostat" selector="testRemoveConnection">testRemoveConnection

| unit1 unit2 unit3|
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	homeostat addFullyConnectedUnit: unit1.
	homeostat addFullyConnectedUnit: unit2.
	homeostat addFullyConnectedUnit: unit3.

	homeostat removeConnectionFrom: unit1 to: unit2.
	homeostat removeConnectionFrom: unit1 to: unit2.

	homeostat removeConnectionFrom: unit2 to: unit3.


	self assert: (homeostat isConnectedFrom: unit2 to: unit1).
	self deny: (homeostat isConnectedFrom: unit1 to: unit2).
	self deny: (homeostat isConnectedFrom: unit2 to: unit3).
</body>

<body package="Homeostat" selector="testRunForTicksWithRandomValues">testRunForTicksWithRandomValues

| unitA unitB unitC unitD ticks string stream|

string := String new.
stream := WriteStream on: string.
	
	unitA := HomeoUnit new setRandomValues.
	unitB := HomeoUnit new setRandomValues.
	unitC := HomeoUnit new setRandomValues.
	unitD := HomeoUnit new setRandomValues.

	ticks := 100.
	
	homeostat addFullyConnectedUnit: unitA.
	homeostat addFullyConnectedUnit: unitB.
	homeostat addFullyConnectedUnit: unitC.
	homeostat addFullyConnectedUnit: unitD.

homeostat runFor: ticks.

"checks that it has a number of data points equal to ticks, and for all the units."

self assert: (homeostat dataCollector states size = ticks).
homeostat dataCollector states 
		do: [
			:dataCollec |
			homeostat homeoUnits 
				do: [
					:unit |
					self assert: (dataCollec keys includes: unit name)]].
"testing output"

homeostat dataCollector printEssentialDataOn: stream.
stream close.
Transcript clear; show: string.</body>

<body package="Homeostat" selector="testSameAs">testSameAs


| anotherHomeostat |

anotherHomeostat := homeostat copy.

self assert: (homeostat sameAs: anotherHomeostat)</body>

<body package="Homeostat" selector="testAddUnit">testAddUnit

| unit1 |
unit1 := HomeoUnit new.
"test adding a new unit"
homeostat addUnit: unit1.
self assert: (homeostat hasUnit: unit1).

"test adding an already exisitng unit"
homeostat addUnit: unit1.
self assert: ((homeostat homeoUnits size) = 1).</body>
</methods>

<methods>
<class-id>HomeostatTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp

homeostat := Homeostat new.</body>
</methods>


<methods>
<class-id>HomeoNoiseTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoNoiseTest</class-id> <category>running</category>

<body package="Homeostat" selector="testDegradingNormalLinearNoise">testDegradingNormalLinearNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	2 * (unit noise) * tolerance.
	2* (unit noise) * (1 - tolerance).


	noise
		normal;
		degrading;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


"Check if noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: (((noiseValue sign) = (unit criticalDeviation sign * -1)) or: [noiseValue = 0])].


values first &gt;= 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].


"Check mean"
self assert: ((mean &gt;= (unit noise * (1 - tolerance))) and: [mean &lt;= (unit noise * (1+ tolerance))]).


"Check all values within {0, 2* noise} interval"
self assert: (minAbsNoise &gt;= 0 and: [maxAbsNoise &lt;= (2 * unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {1/3 noise, 5/3 * noise}, with mu= noise and sigma = 1/3 noise (which is what I need to have all values between 0 and 2* noise"

coll := values select: [:noiseValue | noiseValue abs &gt; (unit noise * 1/3) and: [noiseValue abs &lt;= (unit noise * 5/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {2/3 * noise, 4/3 noise}"

coll := values select: [:noiseValue | noiseValue abs &gt; (unit noise * 2/3) and: [noiseValue abs &lt;= (unit noise * 4/3)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDegradingConstantLinearNoise">testDegradingConstantLinearNoise


|  values tests |

values := SortedCollection new.
unit setRandomValues.
tests := 100.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.

noise constant; degrading; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].

self assert: (values size) = tests.
self assert: (values first sign) = (unit criticalDeviation sign * -1).
self assert:	((values first abs) = (unit noise)).
self assert:	((values last abs) = (unit noise)).</body>

<body package="Homeostat" selector="testDistortingUniformLinearNoise">testDistortingUniformLinearNoise


|  values tests tolerance mean minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.




noise uniform; distorting; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"checks min and max values of noise values are within boundaries of distribution, i.e. [- unit noise , unit noise] "
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise &gt;= unit noise negated).
self assert: (maxAbsNoise &lt;= unit noise). 

"checks the mean of the noise values are about equal to 0"
self assert:  ((mean &gt;= (0  - tolerance)) 
			and: [mean &lt;= (0+  tolerance )]).</body>

<body package="Homeostat" selector="testDegradingConstantProportionalNoise">testDegradingConstantProportionalNoise


|  values  tests|

tests := 100.
values := SortedCollection new.
unit setRandomValues.

noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.

noise constant; degrading; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.
self assert: (values first  sign) = (unit criticalDeviation sign * -1).
self assert:	((values first abs) = ((unit noise)*unit criticalDeviation abs)).
self assert:	((values last abs) = ((unit noise)*unit criticalDeviation abs)).</body>

<body package="Homeostat" selector="testDistortingConstantProportionalNoise">testDistortingConstantProportionalNoise
	
| values signs tests positives tolerance |
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.07.
	unit setRandomValues.
	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	noise
		constant;
		distorting;
		proportional.
	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.

	"test whether the sign of the noise value is about 50% of the times positive and 50% negative. Chooses 'tolerance' as  threshold"
	positives := (signs select: [:item | item = 1]) size.
	(signs select: [:item | item = -1]) size.
	self assert: (positives / (signs size / 2) &gt;= (1 - tolerance) 
				and: [positives / (signs size / 2) &lt;= (1 + tolerance)]).

	"test the value of the noise produced"
	self assert:	((values first abs) = ((unit noise)*unit criticalDeviation abs)).
	self assert:	((values last abs) = ((unit noise)*unit criticalDeviation abs)).</body>

<body package="Homeostat" selector="testDistortingUniformProportionalNoise">testDistortingUniformProportionalNoise


|  values tests tolerance mean minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.




noise uniform; distorting; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"checks min and max values of noise values are within boundaries of distribution, i.e. [- unit noise *current abs, unit noise *current abs] "
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise &gt;= (unit noise negated * unit criticalDeviation abs)).
self assert: (maxAbsNoise &lt;= (unit noise  * unit criticalDeviation abs)). 

"checks the mean of the noise values are about equal to 0"
self assert:  ((mean &gt;= (0  - tolerance)) 
			and: [mean &lt;= (0+  tolerance )]).</body>

<body package="Homeostat" selector="testDegradingNormalProportionalNoise">testDegradingNormalProportionalNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	2 * (unit noise) * tolerance.
	2* (unit noise) * (1 - tolerance).


	noise
		normal;
		degrading;
		proportional.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


"Check if noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: (((noiseValue sign) = (unit criticalDeviation sign * -1)) or: [noiseValue = 0])].


values first &gt;= 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].


"Check mean---should be noise * current abs (+/- tolerance) "
self assert: ((mean &gt;= ((unit noise * unit criticalDeviation abs) * (1 - tolerance))) and: [mean &lt;= ((unit noise * unit criticalDeviation abs) * (1+ tolerance))]).


"Check all values within {0, 2* noise*current abs} interval"
self assert: (minAbsNoise &gt;= 0 and: [maxAbsNoise &lt;= (2 * unit noise* unit criticalDeviation abs)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {1/3 noise * current abs, 5/3 * noise* current abs}, with mu= noise and sigma = 1/3 noise * current abs(which is what I need to have all values between 0 and 2* noise"

coll := values select: [:noiseValue | noiseValue abs&gt; (unit noise * 1/3* unit criticalDeviation abs) and: [noiseValue abs &lt;= (unit noise * 5/3 *unit criticalDeviation abs)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {2/3 * noise*current abs, 4/3 noise * current abs}"

coll := values select: [:noiseValue | noiseValue abs&gt; (unit noise * 2/3 *unit criticalDeviation abs) and: [noiseValue abs &lt;= (unit noise * 4/3 *unit criticalDeviation abs)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDegradingUniformLinearNoise">testDegradingUniformLinearNoise


|  values tests tolerance mean lowThreshold highThreshold minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.
lowThreshold :=  2 * (unit noise) * tolerance.
highThreshold := 2* (unit noise) * (1 - tolerance).



noise uniform; degrading; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"Check noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: ((noiseValue sign) = (unit criticalDeviation sign * -1)).].

"checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*unit noise,   (with a tolerance indicated by 'tolerance'')"
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	((minAbsNoise &gt;= 0)  and: [minAbsNoise &lt;= lowThreshold]).
self assert: ((maxAbsNoise &lt;= (2 * unit noise)) and: [ maxAbsNoise &gt;= highThreshold]). 

"checks the mean of the noise values are about equal to unit noise"
self assert:  ((mean &gt;= ((unit noise ) * (1 - tolerance)))
 
			and: [mean &lt;= ((unit noise) * (1+ tolerance ))]).</body>

<body package="Homeostat" selector="testDistortingNormalProportionalNoise">testDistortingNormalProportionalNoise
| values signs tests  tolerance  mean minNoise maxNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		proportional.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minNoise := values first.
maxNoise := values last.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {(current * -noise), (current * noise} interval"
self assert: (minNoise &gt;= ((unit noise negated)* unit criticalDeviation abs)  and: [maxNoise &lt;= ((unit noise) * (unit criticalDeviation abs) )]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 * noise * current, 2/3 * noise * current }, with mu= 0 and sigma = 1/3 noise * current (which is what I need to have all values between -noise * current  and +noise * current"

coll := values select: [:noiseValue | noiseValue &gt; ((unit noise * 2/3* -1) * (unit criticalDeviation abs)) and: [noiseValue &lt;= ((unit noise * 2/3) * (unit criticalDeviation abs))]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise * current, 1/3 noise * current}"

coll := values select: [:noiseValue | noiseValue &gt; ((unit noise * 1/3* -1) * (unit criticalDeviation abs)) and: [noiseValue &lt;=  ((unit noise * 1/3) * (unit criticalDeviation abs))]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingNormalLinearlNoise">testDistortingNormalLinearlNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minAbsNoise := values first abs.
maxAbsNoise := values last abs.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {-noise, +noise} interval"
self assert: (minAbsNoise &gt;= (unit noise negated)  and: [maxAbsNoise &lt;= (unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 noise, 2/3 * noise}, with mu= 0 and sigma = 1/3 noise (which is what I need to have all values between -noise and +noise"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 2/3 negated) and: [noiseValue &lt;= (unit noise * 2/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise, 1/3 noise}"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 1/3 negated) and: [noiseValue &lt;= (unit noise * 1/3)]].
self assert: (((coll size/ tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingNormalLinearNoise">testDistortingNormalLinearNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minAbsNoise := values first abs.
maxAbsNoise := values last abs.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {-noise, +noise} interval"
self assert: (minAbsNoise &gt;= (unit noise negated)  and: [maxAbsNoise &lt;= (unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 noise, 2/3 * noise}, with mu= 0 and sigma = 1/3 noise (which is what I need to have all values between -noise and +noise"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 2/3* -1) and: [noiseValue &lt;= (unit noise * 2/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise, 1/3 noise}"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 1/3 negated) and: [noiseValue &lt;= (unit noise * 1/3)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingConstantLinearNoise">testDistortingConstantLinearNoise
	
| values signs tests positives tolerance |
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.07.
	unit setRandomValues.
	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	noise
		constant;
		distorting;
		linear.
	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.

	"test whether the sign of the noise value is about 50% of the times positive and 50% negative. Chooses 'tolerance' as  threshold"
	positives := (signs select: [:item | item = 1]) size.
	(signs select: [:item | item = -1]) size.
	self assert: (positives / (signs size / 2) &gt;= (1 - tolerance) 
				and: [positives / (signs size / 2) &lt;= (1 + tolerance)]).

	"test the value of the noise produced"
	self assert: values first abs = unit noise.
	self assert: values last abs = unit noise</body>

<body package="Homeostat" selector="testDegradingUniformProportionalNoise">testDegradingUniformProportionalNoise


|  values tests tolerance mean lowThreshold highThreshold minAbsNoise maxAbsNoise |
tolerance := 0.05.
values:= SortedCollection new.
unit setRandomValues.

tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.
lowThreshold :=  2 * (unit noise * (unit criticalDeviation abs)) * tolerance.
highThreshold := 2* (unit noise*(unit criticalDeviation abs)) * (1 - tolerance).



noise uniform; degrading; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"Check noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: ((noiseValue sign) = (unit criticalDeviation sign * -1)).].


"checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*(unit noise/unit noise current abs),   (with a tolerance indicated by 'tolerance'')"
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise&gt;= 0  and: [minAbsNoise &lt;= lowThreshold]).
self assert: ((maxAbsNoise &lt;= (2 * unit noise)) and: [ maxAbsNoise &gt;= highThreshold]).

"checks the mean of the noise values are about equal to unit noise"
self assert:  ((mean &gt;= ((unit noise *(unit criticalDeviation abs )) * (1 - tolerance)) )
 
			and: [mean &lt;= ((unit noise*(unit criticalDeviation abs)) * (1+ tolerance ))]).</body>
</methods>

<methods>
<class-id>HomeoNoiseTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
	"sets up the test with a Homeostat unit and a noise object"

unit := HomeoUnit new.
noise := HomeoNoise new.</body>
</methods>


<methods>
<class-id>HomeoSimulation class</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="new">new

^ super new initialize</body>
</methods>


<methods>
<class-id>HomeoSimulation</class-id> <category>running</category>

<body package="Homeostat" selector="stop">stop 

homeostat stop</body>

<body package="Homeostat" selector="runForever">runForever

"start the homeostat and runs it indefinitely. The homeostat can be stopped by sending #stop to the simulation"

homeostat start</body>

<body package="Homeostat" selector="start">start
"runs the homeostat for the number of runs specified in maxRuns"

homeostat runFor: maxRuns.</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>testing</category>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo

"checks that the homeostat is ready to go and that the maxRuns and datafile are present"

^ (homeostat isReadyToGo and: [maxRuns notNil]) and: [datafile asFilename isWritable]</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"initializes the instance with a new homestat and a default number of runs."

	homeostat := Homeostat new.
	maxRuns:= 1000.
	datafile := self createDefaultDatafile.
	^self</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>adding</category>

<body package="Homeostat" selector="addFullyConnectedUnit:">addFullyConnectedUnit: aHomeoUnit

homeostat addFullyConnectedUnit: aHomeoUnit.
self changed: #units</body>

<body package="Homeostat" selector="addUnit:">addUnit: aHomeoUnit

homeostat addUnit: aHomeoUnit
</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>accessing</category>

<body package="Homeostat" selector="homeostat:">homeostat: anObject
	homeostat := anObject</body>

<body package="Homeostat" selector="homeostat">homeostat
	^homeostat</body>

<body package="Homeostat" selector="maxRuns">maxRuns
	^maxRuns</body>

<body package="Homeostat" selector="datafile:">datafile: anObject
	datafile := anObject</body>

<body package="Homeostat" selector="maxRuns:">maxRuns: anObject
	maxRuns := anObject</body>

<body package="Homeostat" selector="units">units

^homeostat homeoUnits size </body>

<body package="Homeostat" selector="datafile">datafile
	^datafile</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>saving</category>

<body package="Homeostat" selector="saveEssentialDataOnFile">saveEssentialDataOnFile
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := WriteStream on: datafile asFilename.
	homeostat dataCollector printEssentialDataOn: stream.
	stream close</body>

<body package="Homeostat" selector="saveEssentialDataOnFileWithSeparator:">saveEssentialDataOnFileWithSeparator: aCharacter
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := datafile asFilename writeStream.
	

	homeostat dataCollector saveEssentialsOn:  stream separator: aCharacter.
	stream close</body>

<body package="Homeostat" selector="createDefaultDatafile">createDefaultDatafile

"creates a default strings corresponding to the datafile. Checks that no file with same name exists in current directory"
|name dateString number completeName now|

now := Timestamp now.
dateString:=  now month printString, '-', now day printString, '-',now year printString.
name := 'HomeoSimulationData'.

number := 1.
completeName := name,'-',dateString,'-',number printString.

[completeName asFilename definitelyExists]
	whileTrue: [number := number+1.
				completeName := name,'-',dateString,'-',number].

^completeName</body>

<body package="Homeostat" selector="saveCompleteRunOnFile">saveCompleteRunOnFile
	"asks the datacollector of the homestat to save all data on datafile"

	| stream |
	stream := WriteStream on: datafile asFilename.
	homeostat dataCollector printCompleteDataOn: stream.
	stream close</body>
</methods>


<methods>
<class-id>HomeoUnitTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoUnitTest</class-id> <category>running</category>

<body package="Homeostat" selector="testAddConnection">testAddConnection

 | newUnit  weight polarity |

newUnit := HomeoUnit new.
weight := 0.5.
polarity := 1.

unit addConnection: newUnit withWeight: weight andPolarity: polarity andState: 'manual'.

self assert: (unit inputConnections notNil).
self assert: (unit inputConnections last incomingUnit = newUnit).
self assert: (unit inputConnections last weight = weight).
self assert: (unit inputConnections last switch = polarity).
self assert: (unit inputConnections last state = 'manual').</body>

<body package="Homeostat" selector="testComputeNextDeviationLinear">testComputeNextDeviationLinear

| tempDev errorTolerance|

errorTolerance := 0.00000001.               "Need to use a tolerance threshold for comparison, due to floating point math"


"the polarity of the output controls the change in the criticalDeviation through simple summation.
We  check that it runs up toward positive infinity (1) and negative infinity (2) (with linear increases)"
" We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works."

unit needleCompMethod: 'linear'.
unit needleUnit mass: 1.                 "the force acting on a Aristotelian unit is always inversely proportional to the mass. set it to 1 to exclude complications from this test."

"1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, the deviation increases by the ratio criticalDeviation/maxDeviation every cycle if it starts positive, because output is ALWAYS proportional to the unit's range. Eventually it will go up to infinity, i..e to maxDeviation." 

unit potentiometer: 1.     "this sets the value of the self-connection"
(unit inputConnections at: 1) switch: 1. "self-connection is positive"
unit noise:	0.							"No noise present to simplify calculations"
unit viscosity: 1.
unit criticalDeviation: 1.
unit currentOutput: 1.
unit selfUpdate.
self assert: (unit criticalDeviation = 2).
unit selfUpdate.
self assert: (unit criticalDeviation = (2 + (2/ unit maxDeviation))).
tempDev := unit criticalDeviation.
10 timesRepeat:	[unit selfUpdate. tempDev := tempDev + (tempDev/unit maxDeviation) ].
self assert: (((unit criticalDeviation)  - tempDev) abs &lt;errorTolerance).     
100 timesRepeat: [unit selfUpdate].
self assert: (unit criticalDeviation = unit maxDeviation).



"2. with starting point negative we will run up to negative infinity, because the output will become negative after the first iteration."
unit criticalDeviation: -3.
unit currentOutput: 1.
unit selfUpdate.
self assert: (unit criticalDeviation = -2).
tempDev := unit criticalDeviation.
10 timesRepeat:	[unit selfUpdate. tempDev := tempDev + (tempDev/unit maxDeviation) ].
self assert: (((unit criticalDeviation)  - tempDev) abs &lt;errorTolerance).     
100 timesRepeat: [unit selfUpdate].
self assert: (unit criticalDeviation = unit maxDeviation negated).



"3. with polarity reversed  the unit will tend to stabilize itself around 0, because the output will always counteract the unit's deviation. "
(unit inputConnections at: 1) switch: -1. "self-connection's switch is negative: unit's output is reinputted with reverse polarity"


unit criticalDeviation: -2.
unit currentOutput: -1.
unit selfUpdate.
self assert: (unit criticalDeviation = -1).
200 timesRepeat: [unit selfUpdate].
self assert: (unit criticalDeviation &lt; errorTolerance abs).

"4." 
unit criticalDeviation: 2.
unit currentOutput: -1.
unit selfUpdate.
self assert: (unit criticalDeviation = 3).
200 timesRepeat: [unit selfUpdate].
self assert: (unit criticalDeviation &lt; errorTolerance abs).</body>

<body package="Homeostat" selector="testComputeNextDeviationLinearConnected">testComputeNextDeviationLinearConnected
	"A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
	 critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)

	The basic formula is complicated by taking into consideration:
	1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
	2. viscosity of the medium
	3. clipping, which limits the maximum/minimum values of critDeviation
	4. The mass of the unit 

	In this series of tests  we check the basic formula only. Viscosity and clipping have their own tests, see the HomeoNoise Class for noise testing. We set the mass to 1 simplify the computation"

	"This test  checks a self-connected unit connected to another unit."


|deviation  errorTolerance testRuns anotherUnit|

errorTolerance := 10 raisedTo:-14.  "Cannot get a result better than 10^-14. Consistently fails on smaller values"
testRuns := 100.
anotherUnit := HomeoUnit new.


unit needleCompMethod: 'linear';
      noise: 0.                              "Eliminate flicker noise to simplify test"
unit needleUnit mass: 1.
	
unit addConnectionWithRandomValues: anotherUnit.
unit inputConnections do: [:conn | conn noise: 0].   "the self-connection and the connection to anotherUnit are noise-free"

1 to: testRuns do:
	[ :i | | exceeded |
	unit criticalDeviation: (UniformDistribution from: -10 to: 10) random.
	unit computeOutput.
	unit potentiometer: (UniformDistribution from: 0 to: 1) random.
	unit switch: (UniformDistribution from: -1 to: 1) random sign.
	deviation := unit criticalDeviation.	 
	1 to: 10 do: 
		[ :k | |input|
		input := (unit inputConnections at: 2) output.
		deviation  := deviation  + (unit currentOutput * unit potentiometer * unit switch) + input.
		exceeded := deviation abs &gt; unit maxDeviation. 
		unit selfUpdate.
	      exceeded 
			ifTrue: [  self assert: true.]                                                    "If criticalDeviation value went at anytime  beyond clipping limits don't check. This test is carried out in other unit tests"
			ifFalse:[ self assert: ((deviation - unit criticalDeviation) abs &lt; errorTolerance)]]]</body>

<body package="Homeostat" selector="testRemoveConnection">testRemoveConnection

 | newUnit  weight polarity |

newUnit := HomeoUnit new.
weight := 0.5.
polarity := 1.

unit addConnection: newUnit withWeight: weight andPolarity: polarity andState: 'manual'.

unit removeConnectionFromUnit: newUnit.
self deny: (unit isConnectedTo: newUnit).</body>

<body package="Homeostat" selector="testIstReadyToGo">testIstReadyToGo

"this really tests this method against the conditions set in the initialization procedure and assumes that the latter is correct"

self assert: (unit isReadyToGo)</body>

<body package="Homeostat" selector="testNewNeedlePosition">testNewNeedlePosition
	"test correct computation of needle movement. Ignore noise, as it is computed within the unit itself"

	| newNeedlePosition correctValue maxInput minInput torqueValue |
	unit needleUnit mass: 1.
	maxInput := 3.	"typical of the 4 units Homeostat"
	minInput := maxInput negated.
	100 timesRepeat: 
			[unit criticalDeviation: 1.
			unit needleCompMethod: 'linear'.
			unit noise: 0.
			unit viscosity: 1.
			torqueValue := Random new nextBetween: minInput and: maxInput.
			newNeedlePosition := unit newNeedlePosition: torqueValue.
			correctValue := unit criticalDeviation + (torqueValue * unit viscosity) 
						- unit noise.
"			Transcript
				show: newNeedlePosition printString;
				show: '   ' , 'critical Dev. ' , unit criticalDeviation printString;
				cr."
"			Transcript show: unit printDescription."
			self assert: newNeedlePosition = correctValue]</body>

<body package="Homeostat" selector="testComputeNextDeviationLinearUnconnected">testComputeNextDeviationLinearUnconnected
	"A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
	 critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)

	The basic formula is complicated by taking into consideration:
	1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
	2. viscosity of the medium
	3. clipping, which limits the maximum/minimum values of critDeviation
	4. The unit's mass

	In this series of tests  we check the basic formula only. Viscosity and clipping have their own tests, see the HomeoNois Class for noise testing."

	"This test  checks  a single unconnected unit. The value will always remain at its initial value"


|tempDev testRuns|

testRuns := 1000.

unit needleCompMethod: 'linear'.

unit potentiometer: 0.  "put the weight of the self-connection to zero."

testRuns timesRepeat:
	[unit criticalDeviation: (UniformDistribution from: unit maxDeviation negated to: unit maxDeviation) random.
	 unit needleUnit mass: (UniformDistribution from: 0.0001 to: 10000) random.
	 unit viscosity: (UniformDistribution from: 0 to: 1) random.
	tempDev := unit criticalDeviation.	 
	10 timesRepeat: [unit selfUpdate].
	self assert: (tempDev = unit criticalDeviation)].</body>

<body package="Homeostat" selector="testFirstLevelParamSameAs">testFirstLevelParamSameAs

| anotherUnit param newRandomName ws|


ws := WriteStream on: String new.
"build a random name, because units accept new names only if they have never used before (or they have not been garbage collected yet"
15 timesRepeat: [ws nextPut: ((UniformDistribution from: 65 to: (65+ 26)) random truncated asCharacter)].
newRandomName := ws contents.


unit setRandomValues.
anotherUnit := unit copy.

self assert: (unit sameFirstLevelParamsAs: anotherUnit).

param := unit name.

unit name: newRandomName.
self deny:  (unit sameFirstLevelParamsAs: anotherUnit).
unit name: param.

self assert: (unit sameFirstLevelParamsAs: anotherUnit).

anotherUnit potentiometer: (anotherUnit potentiometer + 0.1).

self deny: (unit sameFirstLevelParamsAs: anotherUnit).</body>

<body package="Homeostat" selector="testSelfUpdate">testSelfUpdate
	

	| oldUniselectorTime |

unit time.
oldUniselectorTime := unit uniselectorTime.

unit selfUpdate.
self assert: (unit uniselectorTime = (oldUniselectorTime +1)).</body>

<body package="Homeostat" selector="testNeedleWithinLimit">testNeedleWithinLimit
	"testing the clipping function operating on a unit's critical deviation's value"

	| highVal lowVal aValue |
	
	highVal := unit maxDeviation.
	lowVal := unit maxDeviation negated.

	aValue := highVal * 1.1.
	self deny: (unit isNeedleWithinLimits: aValue).

	aValue := highVal *0.9.
	self assert: (unit isNeedleWithinLimits: aValue).

	aValue := lowVal *1.1.
	self deny: (unit isNeedleWithinLimits: aValue).

	aValue := lowVal *0.9.
	self assert: (unit isNeedleWithinLimits: aValue).</body>

<body package="Homeostat" selector="testComputeNextDeviationLinear2">testComputeNextDeviationLinear2
	"A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
	 critDeviation (n+1) = criticalDev(n) + sum(input * weight)

	The basic formula is complicated by taking into consideration:
	1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
	2. viscosity of the medium
	3. clipping, which limits the maximum/minimum values of critDeviation

	Here we test the basic formula. Viscosity and clipping have their own tests, see the HomeoNois Class for noise testing."

|tempDev errorTolerance|

errorTolerance := 0.


unit needleCompMethod: 'linear'.
unit needleUnit mass: 1.</body>

<body package="Homeostat" selector="testRandomizeValues">testRandomizeValues

| oldOutput |
unit setRandomValues.
oldOutput := unit currentOutput.
unit setRandomValues.
self deny: (oldOutput = unit currentOutput).</body>

<body package="Homeostat" selector="testUnitNameExist">testUnitNameExist
	"comment stating purpose of message"


self assert: ((unit name) notNil).
	</body>

<body package="Homeostat" selector="testPotentiometer">testPotentiometer
	
	| selfConnWeight poten |
	
	poten := unit potentiometer.
	selfConnWeight := (unit inputConnections at: 1) weight.
	self assert: poten = selfConnWeight.
	
	unit potentiometer: 1.
	self assert: poten = selfConnWeight.
	
	10 timesRepeat: 
			[unit potentiometer: Random new next.
			self assert: poten = selfConnWeight]</body>

<body package="Homeostat" selector="testComputeNextOutputWithDefaults">testComputeNextOutputWithDefaults

"checks:
1. that it computes a new value and puts it in the correct iVar
2. that the value is within the unit's limits

tests are performed  with default values "

| highRange lowRange  oldOutput  |

highRange := (unit outputRange) at:'high'.
lowRange := (unit outputRange) at: 'low'.


oldOutput := unit currentOutput.
unit selfUpdate.

"1 " self assert: ((oldOutput = (unit currentOutput)) not).
"2" self assert: ( unit currentOutput between: lowRange and:	highRange).</body>

<body package="Homeostat" selector="testOutputRange">testOutputRange
	"comment stating purpose of message"

	| highRange lowRange |
	highRange := unit outputRange at: 'high'.
	lowRange := unit outputRange at: 'low'.
	100 timesRepeat: 
			[unit selfUpdate.
			self assert: (unit currentOutput &lt; highRange 
						and: [unit currentOutput &gt; lowRange])]</body>

<body package="Homeostat" selector="testUnitNameUnique">testUnitNameUnique
	"comment stating purpose of message"

| secondUnit  |

secondUnit := HomeoUnit new.

self deny: ((unit name) = (secondUnit name)).
</body>

<body package="Homeostat" selector="testViscosity">testViscosity
	"viscosity reduces the effect of  the outside force on the unit's needle movement."

"When viscosity = 0, the force affecting the unit  is unchanged"

self assert: false.


"When viscosity &gt; 0, the force  changes according to drag. Real tests of drag laws performed in drag unit tests. Here we just check that it is lower than when viscosity +0"

self assert: false</body>

<body package="Homeostat" selector="testInitializationDefaults">testInitializationDefaults
	"test that the class default values are properly inserted in the instance's variable"
	| defViscosity defMaxDeviation defOutputRange defNoise defPotentiometer defTime defUniselectorTime defUniselectorTimeInterval |
	
	defViscosity := HomeoUnit defaultParameters at: 'viscosity'.
	self assert: (unit viscosity) == defViscosity.
	
	defMaxDeviation := HomeoUnit defaultParameters at: 'maxDeviation'.
	self assert: (unit maxDeviation) = defMaxDeviation.

	defNoise := HomeoUnit defaultParameters at: 'noise'.
	self assert: (unit noise) = defNoise.

	defPotentiometer := HomeoUnit defaultParameters at: 'potentiometer'.
	self assert: (unit potentiometer) = defPotentiometer.

	defOutputRange := HomeoUnit defaultParameters at: 'outputRange'.
	self assert: ((unit outputRange at: 'high' ) = (defOutputRange at: 'high')).

	defOutputRange := HomeoUnit defaultParameters at: 'outputRange'.
	self assert: ((unit outputRange at: 'low' ) = (defOutputRange at: 'low')).

	defTime := HomeoUnit defaultParameters at: 'time'.
	self assert: (unit time = defTime).

	defUniselectorTime := HomeoUnit defaultParameters at: 'uniselectorTime'.
	self assert: (unit uniselectorTime = defUniselectorTime).

	defUniselectorTimeInterval := HomeoUnit defaultParameters at: 'uniselectorTimeInterval'.
	self assert: (unit uniselectorTimeInterval = defUniselectorTimeInterval).
  </body>

<body package="Homeostat" selector="testComputeNextDeviationLinearSelfconnected">testComputeNextDeviationLinearSelfconnected
	"A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
	 critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)

	The basic formula is complicated by taking into consideration:
	1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
	2. viscosity of the medium
	3. clipping, which limits the maximum/minimum values of critDeviation
	4. The mass of the unit 

	In this series of tests  we check the basic formula only. Viscosity and clipping have their own tests, see the HomeoNoise Class for noise testing. We set the mass to 1 simplify the computation"

	"This test  checks  a single self-connected unit."

	| deviation errorTolerance testRuns |
	errorTolerance := 0.
	testRuns := 1000.
	unit
		needleCompMethod: 'linear';
		maxDeviation: 100;
		noise: 0.	"initially set the unit uncinnected to correctly initialize value of output."
	unit needleUnit mass: 1.
	(unit inputConnections at: 1) noise: 0.	"the self-connection is noise-free"
	1 to: testRuns
		do: 
			[:i | 
			| exceeded |
			unit criticalDeviation: (UniformDistribution from: unit maxDeviation negated  to: unit maxDeviation) random.
			unit computeOutput.
			unit criticalDeviation.
			unit potentiometer: (UniformDistribution from: 0 to: 1) random.
			unit switch: (UniformDistribution from: -1 to: 1) random sign.
			deviation := unit criticalDeviation.
			1 to: 10 do: 
					[:k | 
					deviation := deviation + (unit currentOutput * unit potentiometer * unit switch).
					exceeded := deviation abs &gt; unit maxDeviation.
					unit selfUpdate.].
			exceeded 
				ifTrue: 
					[self assert: true.]
				ifFalse: 
					[self assert: (deviation = unit criticalDeviation)]].</body>

<body package="Homeostat" selector="testApplicationInternalNoise">testApplicationInternalNoise
	"Check that in presence of noise the unit's critical deviation is changed and not changed when noise = 0. A more comprehensive test should check that the noise value applied is uniformly distributing, proportional and distorting."


unit setRandomValues.
unit noise: 0.1.

10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
				    unit updateDeviationWithNoise.
                            self deny: (oldDeviation = unit criticalDeviation)].


unit noise: 0.
10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
                            self assert:(oldDeviation = unit criticalDeviation)].</body>

<body package="Homeostat" selector="testComputeNextDeviationLinearConnectedTo10Units">testComputeNextDeviationLinearConnectedTo10Units
	"A standard HomeoUnit increases its value (critiDeviation) at each computational step by the basic formula:
	 critDeviation (n+1) = criticalDev(n) + (sum(input * weight)/ unit mass)

	The basic formula is complicated by taking into consideration:
	1. noise, which affects both the stability of a unit's critDeviation (as flickering), and the connections to other units (as distortions)
	2. viscosity of the medium
	3. clipping, which limits the maximum/minimum values of critDeviation
	4. The mass of the unit 

	In this series of tests  we check the basic formula only. Viscosity and clipping have their own tests, see the HomeoNoise Class for noise testing. We set the mass to 1 simplify the computation"

	"This test  checks a self-connected unit connected to another unit."


|deviation  errorTolerance testRuns|

errorTolerance := 10 raisedTo: -14.  "Cannot get a result better than 10^-14. Consistently fails on smaller values"
testRuns := 1.

10 timesRepeat: [ | aUnit | aUnit := HomeoUnit new.
							unit addConnectionWithRandomValues: aUnit]. 

unit needleCompMethod: 'linear';
      noise: 0.                              "Eliminate flicker noise to simplify test"
unit needleUnit mass: 1.
	

unit inputConnections do: [:conn | conn noise: 0].   "the self-connection and the connections to all other units  are noise-free"

1 to: testRuns do:
	[ :i | | exceeded |
	unit criticalDeviation: (UniformDistribution from: unit maxDeviation negated to: unit maxDeviation) random.
	unit computeOutput.
	unit potentiometer: (UniformDistribution from: 0 to: 1) random.
	unit switch: (UniformDistribution from: -1 to: 1) random sign.
	deviation := unit criticalDeviation.	 
	1 to: 100 do: 
		[ :k | |input|
		input := 0.
		2 to: (unit inputConnections size) do: [ :index | input := input + (unit inputConnections	at: index) output ].  "only sum the input from external units"
		deviation  := deviation  + (unit currentOutput * unit potentiometer * unit switch) + input.
		exceeded := deviation abs &gt; unit maxDeviation. 
		unit selfUpdate.
      	exceeded ifTrue: [  self assert: true.
							deviation := unit criticalDeviation]                                                    "If criticalDeviation value went at anytime  beyond clipping limits don't check. (This test is carried out in other unit tests) Reset computing deviation to avoid carrying the error over to next cycles"
			ifFalse:[self assert:  ((deviation - unit criticalDeviation) abs &lt; errorTolerance)]]]</body>

<body package="Homeostat" selector="testComputeTorqueWithinLimits">testComputeTorqueWithinLimits

| unit2 unit3 unit4 |

unit2 := HomeoUnit new.
unit3 := HomeoUnit new.
unit4 := HomeoUnit new.

unit addConnectionWithRandomValues: unit2.
unit addConnectionWithRandomValues: unit3.
unit addConnectionWithRandomValues: unit4.

self assert: ((unit computeTorque) between: -3 and: 3).</body>

<body package="Homeostat" selector="testComputeNextDeviationRandom">testComputeNextDeviationRandom


| oldDeviation |
unit needleCompMethod: ''.  "empty string should trigger the random method"

"check that the critical deviation values are always different"

1000 timesRepeat: [
		oldDeviation := unit criticalDeviation.
		unit selfUpdate.
		self assert: ((unit criticalDeviation = oldDeviation) not)]</body>

<body package="Homeostat" selector="testIsConnectedTo">testIsConnectedTo


 | newUnit  weight polarity |

newUnit := HomeoUnit new.
weight := 0.5.
polarity := 1.

self deny: (unit isConnectedTo: newUnit).
unit addConnection: newUnit withWeight: weight andPolarity: polarity andState: 'manual'.
self assert: (unit isConnectedTo: newUnit).</body>

<body package="Homeostat" selector="testSavingPrivateMethods">testSavingPrivateMethods

| newUnit newUnit2 dict |
 dict := Dictionary new.
dict at: 'low' put: -1; at: 'high' put: 1 .

newUnit := HomeoUnit name: 'pippo'
					 	viscosity: 0.5
			 			maxDeviation: 20
						criticalDeviation: 0
					 	noise: 0.1
					 	potentiometer: 0.2
					 	switch: -1
						outputRange: dict
						inputConnections: OrderedCollection new
					 	uniselector: (HomeoUniselectorAshby new)
					 	uniselectorTimeInterval: 10
					 	uniselectorActive: true
					 	needleCompMethod: 'linear' 
						active: true.


newUnit2 := HomeoUnit name: 'pippo'
					 	viscosity: 0.5
			 			maxDeviation: 20
						criticalDeviation: 0
					 	noise: 0.1
					 	potentiometer: 0.2
					 	switch: -1 
						outputRange: dict
						inputConnections: OrderedCollection new
					 	uniselector: (HomeoUniselectorAshby new)
					 	uniselectorTimeInterval: 10
					 	uniselectorActive: true
					 	needleCompMethod: 'linear' 
						active: true.

self assert: (newUnit sameAs: newUnit2).</body>

<body package="Homeostat" selector="testComputeNextDeviationWithDefaults">testComputeNextDeviationWithDefaults

"checks:
1. that it computes a new value and puts it in the correct iVar
2. that the value is within the unit's limits

tests are performed  with default values "

| highRange lowRange  oldNextDeviation |

highRange := unit maxDeviation.
lowRange := highRange negated.


oldNextDeviation := unit criticalDeviation.
unit selfUpdate.

"1 " self assert: ((oldNextDeviation = (unit criticalDeviation)) not).
"2" self assert: ( unit criticalDeviation between: lowRange and: highRange).</body>

<body package="Homeostat" selector="testDeviationComputationsDontTouchInstanceVariables">testDeviationComputationsDontTouchInstanceVariables
	"Check that the various methods used to compute the critical deviation simply output a value and do not indeed chacge the actual value of deviation stored in the instance variable"
|aTorqueValue|

unit setRandomValues.
aTorqueValue := (UniformDistribution from: -1 to: 1) random.

unit needleCompMethod: 'linear'.
10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
				    unit newNeedlePosition: aTorqueValue.
                            self assert:(oldDeviation = unit criticalDeviation).
				    aTorqueValue := (UniformDistribution from: -1 to: 1) random].


unit needleCompMethod: 'proportional'.
10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
				    unit newNeedlePosition: aTorqueValue.
                            self assert:(oldDeviation = unit criticalDeviation).
				    aTorqueValue := (UniformDistribution from: -1 to: 1) random].

unit needleCompMethod: 'random'.
10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
				    unit newNeedlePosition: aTorqueValue.
                            self assert:(oldDeviation = unit criticalDeviation).
				    aTorqueValue := (UniformDistribution from: -1 to: 1) random].

unit needleCompMethod: ''.
10 timesRepeat: [|oldDeviation|
				    oldDeviation := unit criticalDeviation.
				    unit newNeedlePosition: aTorqueValue.
                            self assert:(oldDeviation = unit criticalDeviation).
				    aTorqueValue := (UniformDistribution from: -1 to: 1) random].</body>

<body package="Homeostat" selector="testComputeNextDeviationProportional">testComputeNextDeviationProportional

"the polarity of the output controls the change in the criticalDeviation through  simple summation. However, the change is proportional to the range of deviation of the output. 

Here we are checking the runup toward positive infinity (1) and negative infinity (2) (with linear increases)"

unit needleCompMethod: 'proportional'.

" We set noises to 0, viscosity to 1, potentiometer to 1, etc, to check that the basic mechanism works."


"1. with self connection to 1, noise at 0, viscosity to 1 and the unit not connected to other units, the deviation should increase by 1 every cycle if it starts positive" 

unit potentiometer: 1.     "this sets the weight of the self-connection"
unit switch: 1.		 "this sets the polarity of the self-connection"
unit noise:	0.
unit viscosity: 1.
unit criticalDeviation: 1.
unit currentOutput: 2.
unit maxDeviation: 10.
unit selfUpdate.
self assert: (unit criticalDeviation = (1 + (2/ 20)) ).

"2 with starting point negative we still run up to positive infinity"
unit criticalDeviation: -1.
unit currentOutput: 2.
unit maxDeviation: 10.
unit selfUpdate.
self assert: (unit criticalDeviation =( -1 + (2/20))).</body>

<body package="Homeostat" selector="testOutputAndDeviationInRange">testOutputAndDeviationInRange
	"repeated test with fully connected units on outputs values and critical deviation values within their ranges"

	| highOut lowOut highDev lowDev unit2 unit3 unit4 |

	

	highOut := (unit outputRange) at: 'high'.
	lowOut   := (unit outputRange) at: 'low'.
	highDev := unit maxDeviation.
	lowDev := highDev negated.

	unit2 := HomeoUnit new.
	unit2 setRandomValues.
	unit3 := HomeoUnit new.
	unit3 setRandomValues.
	unit4 := HomeoUnit new.
	unit4 setRandomValues.

	unit addConnectionWithRandomValues: unit2.
	unit addConnectionWithRandomValues: unit3.
	unit addConnectionWithRandomValues: unit4.

	100000 timesRepeat: [
		unit selfUpdate.
"		(unit currentOutput between: lowOut and: highOut) not ifTrue: [self halt].
"		self assert: (unit currentOutput between: lowOut and: highOut).
		self assert: (unit criticalDeviation between: lowDev and: highDev)]</body>

<body package="Homeostat" selector="testChangeUniselectorType">testChangeUniselectorType

|goodUniselectors badUniselectors|


goodUniselectors := OrderedCollection new.
badUniselectors := OrderedCollection new.

HomeoUniselector withAllSubclasses do: [:class | goodUniselectors add: class name asString].
badUniselectors add: 'Ashby'; add: 'UniformRandom'; add: 'HomeoUnit'.
unit setDefaultUniselectorSettings.
goodUniselectors 
		do: [ :string|
			unit uniselectorChangeType: string.
			self assert: (unit uniselector class name asString = string).].

unit setDefaultUniselectorSettings.
badUniselectors 
	do: [ :string|
			unit uniselectorChangeType: string.
			self deny: (unit uniselector class name asString = string).].</body>

<body package="Homeostat" selector="testClassDefaults">testClassDefaults
	"test that  the class has its appropriate dictionary of Defaults and that the values are not empty"
| defParam range|


defParam := HomeoUnit defaultParameters.

self assert: (defParam includesKey: 'viscosity').
self assert: (defParam includesKey: 'maxDeviation').
self assert: (defParam includesKey: 'outputRange').
self assert: (defParam includesKey: 'noise').
self assert: (defParam includesKey: 'potentiometer').
self assert: (defParam includesKey: 'time').
self assert: (defParam includesKey: 'uniselectorTimeInterval').
self assert: (defParam includesKey: 'uniselectorTime').
self assert: (defParam includesKey: 'needleCompMethod').

self assert: ((defParam at: 'viscosity') notNil).
self assert: ((defParam at: 'maxDeviation') notNil).
self assert: ((defParam at: 'noise') notNil).
self assert: ((defParam at: 'potentiometer' ) notNil).
self assert: ((defParam at: 'time') notNil).
self assert: ((defParam at: 'uniselectorTimeInterval') notNil).
self assert: ((defParam at: 'uniselectorTime') notNil).
self assert: ((defParam at:  'needleCompMethod')  notNil).

range := defParam at: 'outputRange'.

self assert: (range includesKey: 'high').
self assert: ((range at: 'high') notNil).

self assert: (range includesKey: 'low').
self assert: ((range at: 'low') notNil).</body>

<body package="Homeostat" selector="testBossOutHomeoUnit">testBossOutHomeoUnit
	"comment stating purpose of message"



	| boss newUnit  filename |
	filename := 'pippo.unit' asFilename.
	
	unit  bossOutOn: filename. 

	boss :=  BinaryObjectStorage onOldNoScan: filename readStream.
	newUnit:= boss next.
	boss close.
	self assert: (newUnit class = HomeoUnit).

	self assert: (unit sameAs: newUnit).</body>

<body package="Homeostat" selector="testSameAs">testSameAs
 | unit2 unit3 unit4 param |


unit setRandomValues.
unit2 := HomeoUnit new setRandomValues.
unit3 := HomeoUnit new setRandomValues.
unit4 := HomeoUnit new setRandomValues.
HomeoUnit new setRandomValues.

unit addConnectionWithRandomValues: unit2.
unit addConnectionWithRandomValues: unit3.

unit4 := unit copy.

self assert: (unit sameAs: unit4).

param := unit4 name. 
unit4 name: param, 'pippo'.
self deny: (unit sameAs: unit4).
unit   := HomeoUnit new.
unit4 := HomeoUnit new.

self deny: (unit sameAs: unit4).</body>

<body package="Homeostat" selector="testComputeTorque">testComputeTorque
	| unit2 unit3 unit4 |
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	unit4 := HomeoUnit new.
	
"1. test torque when unit is not connected to anything. Should be 0"
unit removeConnectionFromUnit: unit.

self assert: (unit inputConnections size = 0).
self assert: (unit computeTorque = 0).

"2. add a self connection at 1 and another connection at 1. torque should be 2"

unit addConnection: unit withWeight: 1 andPolarity: 1 andNoise: 0 andState: 'manual'.
unit currentOutput: 1.
unit2 currentOutput: 1.
unit addConnection: unit2 withWeight: 1 andPolarity: 1 andNoise: 0 andState: 'manual'.
self assert: (unit inputConnections size = 2).
self assert: (unit computeTorque = 2).

"3. Add a pair of connections at -1. check again"

unit addConnection: unit3 withWeight: 1 andPolarity: -1 andNoise: 0 andState: 'manual'.
unit3 currentOutput: 1.
unit4 currentOutput: 1.
unit addConnection: unit4 withWeight: 1 andPolarity: -1 andNoise: 0 andState: 'manual'.
self assert: (unit inputConnections size = 4).
self assert: (unit computeTorque = 0).</body>
</methods>

<methods>
<class-id>HomeoUnitTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
	"Initialize the HomeoUnit class and sets up a default HomeoUnit for testing"

"initialize the HomeoUnit class to clear all old names (held in the Names shared variable)"
HomeoUnit initialize.

unit := HomeoUnit new.</body>
</methods>


<methods>
<class-id>HomeoNeedleUnit class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>

<body package="Homeostat" selector="initialize">initialize
	"Sets DefaultParameters, the class variable holding the  default values of all the various parameters of future needle units.
	 All 'physical' values are expressed in internal units.  Conversion to real physical units, if necessary,  done by Physical parameters dictionary in HomeoUnit
	   HomeoUnit initialize "
	
	DefaultParameters := Dictionary new.
	DefaultParameters 	at: 'mass' 				      put: 1 asDouble;  "mass expressed in internal units."
							at: 'surfaceArea' 			put: (1/ Double pi) asDouble ; "in  internal units. This is the area equivalent to a circle whose radius is 1 unit. "
							at: 'dragCoefficient' 		put:  1 asDouble.  "dimensionless, of course. Used to compute drag according to general drag law (for high velocities)"</body>
</methods>


<methods>
<class-id>HomeoNeedleUnit</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
"Initialize the HomeoNeedleUnit with the default parameters found in the Class variable DefaultParameters."


	"reads default parameters"

	mass := DefaultParameters at: 'mass'.
	surfaceArea := DefaultParameters at: 'surfaceArea'. 	
	dragCoefficient := DefaultParameters at: 'dragCoefficient'.</body>
</methods>

<methods>
<class-id>HomeoNeedleUnit</class-id> <category>accessing</category>

<body package="Homeostat" selector="dragCoefficient:">dragCoefficient: anObject
	dragCoefficient := anObject</body>

<body package="Homeostat" selector="surfaceArea">surfaceArea
	^surfaceArea</body>

<body package="Homeostat" selector="mass:">mass: anObject
	mass := anObject</body>

<body package="Homeostat" selector="mass">mass
	^mass</body>

<body package="Homeostat" selector="surfaceArea:">surfaceArea: anObject
	surfaceArea := anObject</body>

<body package="Homeostat" selector="dragCoefficient">dragCoefficient
	^dragCoefficient</body>
</methods>


<methods>
<class-id>HomeoUnitNewtonian</class-id> <category>private-running</category>

<body package="Homeostat" selector="selfUpdate">selfUpdate
	"This is the master loop for the unit. It goes through the following sequence:
	1. compute new needle's deviation (nextDeviation (includes reading inputs))
	2. updates the current output on the basis of the deviation.
	3. check whether it's time to check the essential value and if so do it and  update the counter (uniselectorTime) [this might change the weight of the connections]
	4. Compute the new velocity on the basis of the displacement
	5. Move the needle to new position and compute new output
	"


| newDeviation|

	"1. compute where the needle should move to"

	self computeNextDeviation.

	"2. update times"
	self updateTime.
	self updateUniselectorTime.

	"3. check whether it's time to check the uniselector/detection mechanism and if so do it. 
	       Register that the uniselector is active in an instance variable"
	(uniselectorTime &gt;= uniselectorTimeInterval and: [uniselectorActive]) 
		ifTrue: [self essentialVariableIsCritical ifTrue: [self operateUniselector.
												   uniselectorActivated := 1]]
		ifFalse: [uniselectorActivated:= 0].	      


	"4. Compute new current velocity according to classic Newtonian formula: x-x0 = 1/2t (v-v0)  where:
		x0 = criticalDeviation
		x = newDeviation
		v0 = currentVelocity
		Solving for v we get: v = 2(x-x0) -v0"
	
  	newDeviation := (self clipDeviation: nextDeviation).
"	currentVelocity := newDeviation-criticalDeviation."             "old version"
	currentVelocity := 2* (newDeviation -criticalDeviation) - currentVelocity.

	"5. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"
	
	self criticalDeviation: newDeviation.
	self computeOutput.
	nextDeviation := 0</body>

<body package="Homeostat" selector="reynoldsNumber">reynoldsNumber
	"computes the Reynolds number of the physical flow (the needle in the trough), according to the formula:
	Re = 2 a rho v / eta"

| viscosityInSiUnits |


viscosityInSiUnits := viscosity / 1000. "convert viscosity from centiPoise to Pascal/second"

^ 2 * needleUnit surfaceArea * density * self physicalVelocity / viscosityInSiUnits.</body>

<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
	"  Computes the new position of the needle taking into consideration (a simplified version of) the forces acting on the needle. "

	"self halt."

	| totalForce acceleration displacement |
	totalForce := aTorqueValue + self drag.		"add to the  force acting on the needle the drag force produced by the fluid in the trough the  needle is moving through. 
													In the original Homeostat,  other factors related to the  physical characteristics of the device, affect the net force affecting the needle,  
													including the potential through the trough, the friction at the vane, etc. 
												    These factors are ignored here"

	acceleration := totalForce / needleUnit mass.	"As per  Newton's second law"
	displacement := currentVelocity + (1 / 2 * acceleration) asDouble.	" x - x0 = v0t + 1/2 a t, with t obviously =  1"
	
	"Testing"
"	debugMode 
		ifTrue: 
			[Transcript
				show: ' time: ';
				show: (time + 1) printString;
				show: '  unit: ';
				show: self name;
				show: '     curr, pos:';
				show: (criticalDeviation asFixedPoint: 3) printString;
				show: '     new, pos:';
				show: (criticalDeviation + newVelocity asFixedPoint: 3) printString;
				show: '   curr. vel.: ';
				show: (currentVelocity asFixedPoint: 3) printString;
				show: '           new vel.: ';
				show: (newVelocity asFixedPoint: 3) printString;
				show: '    acc.:   ';
				show: (acceleration asFixedPoint: 3) printString;
				show: ' torque: ', (aTorqueValue asFixedPoint: 3)  printString;
				cr;
				cr]."
debugMode 
	ifTrue: [ 
		 (((criticalDeviation + displacement) &gt; maxDeviation) or: [(criticalDeviation + displacement) &lt; maxDeviation negated])
			ifTrue: 
				[Transcript show:
				'NEW CRITICAL DEVIATION WOULD BE OVER LIMITS AT: ', ((criticalDeviation + displacement) asFixedPoint: 3) printString; cr]].
	^criticalDeviation + displacement</body>

<body package="Homeostat" selector="drag">drag
	"output the drag force acting on the unit as a result of the viscosity in the trough and the velocity of the needle."

^ self stokesLawDrag.              </body>

<body package="Homeostat" selector="dragDummy">dragDummy
	"Used for testing purposes"

^ 0</body>

<body package="Homeostat" selector="clearFutureValues">clearFutureValues
	"sets to 0 the internal values used for computing future states. "


self nextDeviation: 0.
self inputTorque: 0.
self currentOutput: 0.
self currentVelocity: 0.</body>

<body package="Homeostat" selector="newNeedlePosition:">newNeedlePosition: aTorqueValue 
	"computes the new needle position on the basis of aTorqueValue, which represents the torque applied to the unit's needle. "




	
	needleCompMethod = 'linear' 
		ifTrue: [^self newLinearNeedlePosition: aTorqueValue]
		ifFalse: [^self newRandomNeedlePosition]       "defaults to a random computation method if the method is not specified"</body>

<body package="Homeostat" selector="physicalForce:">physicalForce: torqueValue
	"converts the torque coming into a unit into a force expressed in real physical units n(i.e. Newtons)"


^ torqueValue * (physicalParameters at: 'massEquivalent') * (physicalParameters at: 'lengthEquivalent') / ((physicalParameters at: 'timeEquivalent') squared)</body>

<body package="Homeostat" selector="stokesLawDrag">stokesLawDrag

	"Compute the physical drag on the needle according to Stokes equation: D = 6 pi r eta v.
	Output is negated, since Drag's sign is always  opposite  to velocity.
	Instead of the radius of the sphere (as in Stokes' law), it uses the surface area of the needle."

^ ( 6 * Double pi * ((needleUnit surfaceArea * Double pi ) sqrt) * viscosity * currentVelocity) negated.</body>

<body package="Homeostat" selector="dragEquationDrag">dragEquationDrag

	"Compute the drag on the needle according to the drag equation for high Reynolds numbers: 
	D = 1/2  C A rho  v^2.
	Outputs a number representing the drag expressed as force measured in Newtons"


	^ 1/2  * density * needleUnit dragCoefficient * (self physicalVelocity squared) * (needleUnit surfaceArea) .</body>
</methods>

<methods>
<class-id>HomeoUnitNewtonian</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	
	super initialize.
	self needleUnit mass: 1000.                  "default mass for Newttonian units to avoid the needle shooting up or down"</body>
</methods>


<methods>
<class-id>WebotsConnectionTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>WebotsConnectionTest</class-id> <category>run</category>

<body package="Homeostat" selector="runCommand:">runCommand: aKheperaCommand

"executes a Khepera command on the connection to the Webot simulator
 if the command returns values writes them to the Transcript"

Transcript show: 'The command I am about to execute is: ', aKheperaCommand; cr.
stream nextPutAll: aKheperaCommand; cr; commit.
Transcript nextPutAll: (stream upTo: Character cr); cr; flush.</body>

<body package="Homeostat" selector="run">run
	"accepts messages in a dialog and passes them on to the Webots Controller.
	 Prints outputs to Transcript.
	exits with cancel from the dialog"

	|command|

self openConnection.
command := ''.
self halt.
[command ~= 'Exit']  whileTrue: [
	command := Dialog request: 'Enter a command' initialAnswer: ''.
	self runCommand: command.].

self closeConnection.</body>

<body package="Homeostat" selector="run2">run2
	"accepts messages in a dialog and passes them on to the Webots Controller.
	 Prints outputs to Transcript.
	exits with emptyString from the dialog
	From SocketProgramming/Basic Libraries p.9-19"

	| sockAddr command inputBuffer outputBuffer outProc outStream inProc inStream |
	socketAccessor := SocketAccessor family: SocketAccessor AF_INET
				type: SocketAccessor SOCK_STREAM.
	sockAddr := IPSocketAddress hostName: ipAddress port: port.
	socketAccessor connectTo: sockAddr.
	outputBuffer := ByteArray new: 100.
	inputBuffer := ByteArray new: 100.
	outProc := 
			[[(command := Dialog request: 'Enter a command' initialAnswer: '') isEmpty] 
				whileFalse: 
					[socketAccessor writeWait.
					outStream := (outputBuffer withEncoding: #UTF_8) writeStream.
					outStream
						nextPutAll: command;
						cr.
					socketAccessor 
						sendTo: sockAddr
						buffer: outputBuffer
						start: 1
						for: command size + 1]] 
					forkAt: Processor activePriority - 1.
	inProc := 
			[
			[| size |
			socketAccessor readWait.
			size := socketAccessor receiveFrom: sockAddr buffer: inputBuffer.
			inStream := (inputBuffer withEncoding: #UTF_8) readStream.
			1 to: size
				do: 
					[:x | 
					"next line should use ForkedUI"

					Transcript
						nextPut: inStream next;
						flush]] 
					repeat] 
					forkAt: Processor activePriority - 1.</body>

<body package="Homeostat" selector="closeConnection">closeConnection
	
stream close.</body>
</methods>

<methods>
<class-id>WebotsConnectionTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
ipAddress := 'localhost'.
port := 10020.
	^self</body>

<body package="Homeostat" selector="openConnection">openConnection

| sockAddr|
sockAddr := IPSocketAddress hostName: ipAddress port: port.
socketAccessor := SocketAccessor  family: SocketAccessor AF_INET
 	type: SocketAccessor SOCK_STREAM.
socketAccessor soReuseaddr: true.
socketAccessor connectTo: sockAddr.
stream := socketAccessor readAppendStream.</body>
</methods>


<methods>
<class-id>HomeostatStandardGUI class</class-id> <category>interface opening</category>

<body package="Homeostat" selector="new">new

"open a new homeostat"

| app |

app := super new initialize.
"app openBothWindows."
app openThreeWindows.</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI class</class-id> <category>interface specs</category>

<body package="Homeostat" selector="windowSpec">windowSpec
	"Tools.UIPainter new openOnClass: self andSelector: #windowSpec"


"NEED TO WRITE THE WINDOW ALLOWING SELECTION OF DIFFERENT KINDS OF SIMULATION"</body>

<body package="Homeostat" selector="homeoControlSpec">homeoControlSpec
	"Tools.UIPainter new openOnClass: self andSelector: #homeoControlSpec"

	&lt;resource: #canvas&gt;
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#properties: #(#{UI.PropertyListDictionary} #sizeAutoSave true #positionAutoSave true #sizeType #lastSavedSize #openType #advanced #positionType #lastSavedPosition ) 
			#label: 'Homeostat control panel' 
			#min: #(#{Core.Point} 515 200 ) 
			#max: #(#{Core.Point} 515 200 ) 
			#bounds: #(#{Graphics.Rectangle} 640 128 1155 328 ) 
			#flags: 8 ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 9 4 ) 
					#name: #Label1 
					#label: 'Homeostat:' 
					#style: #systemDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 9 24 204 41 ) 
					#name: #datafileInputField 
					#model: #datafile 
					#style: #systemDefault 
					#isReadOnly: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 137 100 158 ) 
					#name: #ActionButton1 
					#model: #saveHomeostatOnFile 
					#label: 'Save' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 110 100 131 ) 
					#name: #ActionButton2 
					#model: #readHomeostat 
					#label: 'Load' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 137 206 158 ) 
					#name: #ActionButton3 
					#model: #simulationGraph 
					#label: 'Graph' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 6 ) 
					#name: #Label2 
					#label: 'Max runs' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 6 368 23 ) 
					#name: #maxRunsInputField 
					#model: #maxRuns 
					#type: #number 
					#formatString: '#,##0' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 165 100 186 ) 
					#name: #ActionButton4 
					#model: #homeostatInspect 
					#label: 'Inspect' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 27 ) 
					#name: #Label3 
					#label: 'Current time' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 30 368 47 ) 
					#name: #currentRunInputField 
					#model: #currentRun2 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 30 497 51 ) 
					#name: #ActionButton5 
					#model: #resetTime 
					#label: 'Reset time' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 6 38 ) 
					#name: #Label4 
					#label: 'No. of units' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 82 39 112 60 ) 
					#name: #InputField4 
					#flags: 0 
					#model: #homeoUnits 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 51 ) 
					#name: #Label5 
					#label: 'Slowing factor' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 54 368 71 ) 
					#name: #slowingFactorInputField 
					#model: #slowingFactor 
					#type: #number ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 6 497 27 ) 
					#name: #ActionButton6 
					#model: #resetUnitValues 
					#label: 'Reset unit values' 
					#style: #default 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 232 165 305 185 ) 
					#name: #ActionButton7 
					#model: #stopProcess 
					#label: 'Stop' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 329 165 402 185 ) 
					#name: #ActionButton8 
					#model: #startNewProcess 
					#label: 'Go' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 426 165 499 185 ) 
					#name: #ActionButton9 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #black ) 
						#setBackgroundColor: #(#{Graphics.ColorValue} 1024 4607 8191 ) ) 
					#model: #stepSimulation 
					#label: 'Step' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 70 ) 
					#name: #Label6 
					#label: '(millisec.)' ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 213 4 217 184 ) 
					#name: #Divider1 
					#orientation: #vertical ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 54 497 75 ) 
					#name: #DebugModeActionButton 
					#model: #toggleDebugMode 
					#label: 'Debug Mode' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 80 497 107 ) 
					#name: #showUniselectorActionButton 
					#model: #toggleShowUniselectorAction 
					#label: 'Show Unis. Action' 
					#defaultable: true ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 375 176 391 ) 
					#name: #ComboBox1 
					#model: #Unit2ConnectStatusUnit24 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 357 176 373 ) 
					#name: #ComboBox2 
					#model: #Unit2ConnectStatusUnit23 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 338 176 354 ) 
					#name: #ComboBox3 
					#model: #Unit2ConnectStatusUnit22 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 319 176 335 ) 
					#name: #ComboBox4 
					#model: #Unit2ConnectStatusUnit21 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 109 206 130 ) 
					#name: #ActionButton11 
					#model: #savePlotDataOnFile 
					#label: 'Save plot data' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 6 57 ) 
					#name: #Label7 
					#label: 'Homeostat actions' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 130 57 ) 
					#name: #Label8 
					#label: 'Data actions' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 82 206 103 ) 
					#name: #ActionButton10 
					#model: #saveAllDataOnFile 
					#label: 'Save all data' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 81 100 102 ) 
					#name: #NewHomeostatActionButton 
					#model: #newHomeostat 
					#label: 'New' 
					#defaultable: true ) ) ) )</body>

<body package="Homeostat" selector="homeostatSpec">homeostatSpec
	"Tools.UIPainter new openOnClass: self andSelector: #homeostatSpec"

	&lt;resource: #canvas&gt;
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#properties: #(#{UI.PropertyListDictionary} #sizeType #specifiedSize #positionType #screenCenter #openType #advanced ) 
			#label: 'Homeostat Standard' 
			#min: #(#{Core.Point} 20 20 ) 
			#max: #(#{Core.Point} 0 0 ) 
			#bounds: #(#{Graphics.Rectangle} 1608 352 2258 1142 ) ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} -158 -219 ) 
					#name: #Label 
					#label: 'State' ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 46 598 198 ) 
					#name: #Unit1DeviationSlider 
					#model: #Unit1SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 96 565 113 ) 
					#name: #Unit1CriticalDeviationField 
					#model: #Unit1Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 82 107 99 ) 
					#name: #Unit1OuputInputID 
					#model: #Unit1Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 80 ) 
					#name: #Unit1OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 25 110 50 ) 
					#name: #Unit1NameInput 
					#model: #unit1Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 80 ) 
					#name: #Unit1DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 47 571 63 ) 
					#name: #UnitHighRangeInput 
					#flags: 0 
					#model: #unit1HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 184 571 200 ) 
					#name: #UnitLowRangeInput 
					#flags: 0 
					#model: #unit1LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 129 112 145 ) 
					#name: #Unit1ConnectUnit11InputID 
					#model: #Unit1ConnectUnit11 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 147 112 163 ) 
					#name: #Unit1ConnectUnit12InputID 
					#model: #Unit1ConnectUnit12 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 166 112 182 ) 
					#name: #Unit1ConnectUnit13InputID 
					#model: #Unit1ConnectUnit13 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 184 112 200 ) 
					#name: #Unit1ConnectUnit14InputID 
					#model: #Unit1ConnectUnit14 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 113 ) 
					#name: #Unit1ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 112 ) 
					#name: #Unit1ConnectionsLabel 
					#label: 'Name' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 131 272 145 ) 
					#name: #Unit1WeightSpin11ID 
					#model: #Unit1WeightSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 168 272 182 ) 
					#name: #Unit1WeightSpin12ID 
					#model: #Unit1WeightSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 186 272 200 ) 
					#name: #Unit1WeightSpin14ID 
					#model: #Unit1WeightSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 149 272 163 ) 
					#name: #Unit1WeightSpin12ID 
					#model: #Unit1WeightSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 113 ) 
					#name: #Unit1ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 114 ) 
					#name: #Unit1ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 132 430 146 ) 
					#name: #Unit1NoiseSpin11ID 
					#model: #Unit1NoiseSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 150 430 164 ) 
					#name: #Unit1NoiseSpin12 
					#model: #Unit1NoiseSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 169 430 183 ) 
					#name: #Unit1NoiseSpin13ID 
					#model: #Unit1NoiseSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 187 430 201 ) 
					#name: #Unit1NoiseSpin14ID 
					#model: #Unit1NoiseSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 114 ) 
					#name: #Unit1ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 114 ) 
					#name: #Unit1ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 132 350 146 ) 
					#name: #Unit1SwitchtSpin11ID 
					#model: #Unit1SwitchSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 150 350 164 ) 
					#name: #Unit1SwitchtSpin12ID 
					#model: #Unit1SwitchSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 169 350 183 ) 
					#name: #Unit1SwitchtSpin13ID 
					#model: #Unit1SwitchSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 187 350 201 ) 
					#name: #Unit1SwitchtSpin14ID 
					#model: #Unit1SwitchSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 186 538 201 ) 
					#name: #Unit1UniselectorActiveCombo14 
					#model: #Unit1UniselectorActive14 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 168 538 183 ) 
					#name: #Unit1UniselectorActiveCombo13 
					#model: #Unit1UniselectorActive13 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 149 538 164 ) 
					#name: #Unit1UniselectorActiveCombo12 
					#model: #Unit1UniselectorActive12 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 131 538 146 ) 
					#name: #Unit1UniselectorComboActive11 
					#model: #Unit1UniselectorActive11 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 0 207 619 211 ) 
					#name: #Divider2 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} -2 399 617 403 ) 
					#name: #Divider3 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 2 591 621 595 ) 
					#name: #Divider4 ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 216 109 241 ) 
					#name: #Unit2NameInput 
					#model: #unit2Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 271 ) 
					#name: #Unit2OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 271 107 288 ) 
					#name: #Unit2OutputInputID 
					#model: #Unit2Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 238 571 254 ) 
					#name: #unit2HighRangeInput 
					#flags: 0 
					#model: #unit2HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 240 598 392 ) 
					#name: #Unit2DeviationSlider 
					#model: #Unit2SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 271 ) 
					#name: #Unit2DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 287 565 304 ) 
					#name: #Unit2CriticalDeviationField 
					#model: #Unit2Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 305 ) 
					#name: #Unit2ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 322 538 337 ) 
					#name: #Unit2UniselectorComboActive21 
					#model: #Unit2UniselectorActive21 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 340 538 355 ) 
					#name: #Unit2UniselectorComboActive12 
					#model: #Unit2UniselectorActive22 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 359 538 374 ) 
					#name: #Unit2UniselectorComboActive23 
					#model: #Unit2UniselectorActive23 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 377 538 392 ) 
					#name: #Unit2UniselectorComboActive24 
					#model: #Unit2UniselectorActive24 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 305 ) 
					#name: #Unit2ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 323 430 337 ) 
					#name: #Unit2NoiseSpin21ID 
					#model: #Unit2NoiseSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 341 430 355 ) 
					#name: #Unit2NoiseSpin22ID 
					#model: #Unit2NoiseSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 360 430 374 ) 
					#name: #Unit2NoiseSpin23ID 
					#model: #Unit2NoiseSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 378 430 392 ) 
					#name: #Unit2NoiseSpin24ID 
					#model: #Unit2NoiseSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 305 ) 
					#name: #Unit2ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 323 350 337 ) 
					#name: #Unit2SwitchSpin21ID 
					#model: #Unit2SwitchSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 341 350 355 ) 
					#name: #Unit2SwitchSpin22ID 
					#model: #Unit2SwitchSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 360 350 374 ) 
					#name: #Unit2SwitchSpin23ID 
					#model: #Unit2SwitchSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 378 350 392 ) 
					#name: #Unit2SwitchSpin24ID 
					#model: #Unit2SwitchSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 304 ) 
					#name: #Unit2ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 322 272 336 ) 
					#name: #Unit2WeightSpin21ID 
					#model: #Unit2WeightSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 340 272 354 ) 
					#name: #Unit2WeightSpin22ID 
					#model: #Unit2WeightSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 359 272 373 ) 
					#name: #Unit2WeightSpin23ID 
					#model: #Unit2WeightSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 377 272 391 ) 
					#name: #Unit2WeightSpin24ID 
					#model: #Unit2WeightSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 304 ) 
					#name: #Unit2ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 303 ) 
					#name: #Unit2ConnectionsLabel 
					#label: 'Name' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 319 112 335 ) 
					#name: #Unit2ConnectUnit11InputID 
					#model: #Unit2ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 338 112 354 ) 
					#name: #Unit2ConnectUnit12InputID 
					#model: #Unit2ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 357 112 373 ) 
					#name: #Unit2ConnectUnit13InputID 
					#model: #Unit2ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 375 112 391 ) 
					#name: #Unit2ConnectUnit14InputID 
					#model: #Unit2ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 539 375 573 391 ) 
					#name: #unit2LowRangeInput 
					#flags: 0 
					#model: #unit2LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 407 110 432 ) 
					#name: #unit3NameInput 
					#model: #unit3Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 462 ) 
					#name: #Unit3OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 464 107 481 ) 
					#name: #Unit3OutputInputID 
					#model: #Unit3Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 429 571 445 ) 
					#name: #unit3HighRangeInput 
					#flags: 0 
					#model: #unit3HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 431 598 583 ) 
					#name: #Unit3DeviationSlider 
					#model: #Unit3SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 462 ) 
					#name: #Unit3DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 478 565 495 ) 
					#name: #Unit3CriticalDeviationField 
					#model: #Unit3Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 539 566 573 582 ) 
					#name: #unit3LowRangeInput 
					#flags: 0 
					#model: #unit3LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 496 ) 
					#name: #Unit2ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 513 538 528 ) 
					#name: #Unit3UniselectorComboActive31 
					#model: #Unit3UniselectorActive31 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 531 538 546 ) 
					#name: #Unit3UniselectorComboActive32 
					#model: #Unit3UniselectorActive32 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 550 538 565 ) 
					#name: #Unit3UniselectorComboActive33 
					#model: #Unit3UniselectorActive33 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 568 538 583 ) 
					#name: #Unit3UniselectorComboActive34 
					#model: #Unit3UniselectorActive34 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 496 ) 
					#name: #Unit2ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 514 430 528 ) 
					#name: #Unit3NoiseSpin31ID 
					#model: #Unit3NoiseSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 532 430 546 ) 
					#name: #Unit3NoiseSpin32ID 
					#model: #Unit3NoiseSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 569 430 583 ) 
					#name: #Unit3NoiseSpin34ID 
					#model: #Unit3NoiseSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 569 350 583 ) 
					#name: #Unit3SwitchSpin34ID 
					#model: #Unit3SwitchSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 551 350 565 ) 
					#name: #Unit3SwitchSpin33ID 
					#model: #Unit3SwitchSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 532 350 546 ) 
					#name: #Unit3SwitchSpin32ID 
					#model: #Unit3SwitchSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 514 350 528 ) 
					#name: #Unit3SwitchSpin31ID 
					#model: #Unit3SwitchSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 568 272 582 ) 
					#name: #Unit3WeightSpin34ID 
					#model: #Unit3WeightSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 550 272 564 ) 
					#name: #Unit3WeightSpin33ID 
					#model: #Unit3WeightSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 531 272 545 ) 
					#name: #Unit3WeightSpin31ID 
					#model: #Unit3WeightSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 513 272 527 ) 
					#name: #Unit3WeightSpin31ID 
					#model: #Unit3WeightSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 495 ) 
					#name: #Unit3ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 496 ) 
					#name: #Unit3ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 495 ) 
					#name: #Unit3ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 566 113 582 ) 
					#name: #Unit3ConnectUnit14InputID 
					#model: #Unit3ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 548 113 564 ) 
					#name: #Unit3ConnectUnit13InputID 
					#model: #Unit3ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 529 113 545 ) 
					#name: #Unit3ConnectUnit12InputID 
					#model: #Unit3ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 511 113 527 ) 
					#name: #Unit3ConnectUnit11InputID 
					#model: #Unit3ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 494 ) 
					#name: #Label15 
					#label: 'Name' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 550 430 564 ) 
					#name: #Unit3NoiseSpin33ID 
					#model: #Unit3NoiseSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 13 599 108 624 ) 
					#name: #unit4NameInput 
					#model: #unit4Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 66 657 108 674 ) 
					#name: #Unit4OutputInputID 
					#model: #Unit4Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 655 ) 
					#name: #Label1 
					#label: 'Output' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 517 655 ) 
					#name: #Label9 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 524 671 566 688 ) 
					#name: #Unit4CriticalDeviationField 
					#model: #Unit4Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 538 622 572 638 ) 
					#name: #unit4HighRangeInput 
					#flags: 0 
					#model: #unit4HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 540 759 574 775 ) 
					#name: #unit4LowRangeInput 
					#flags: 0 
					#model: #unit4LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 574 624 599 776 ) 
					#name: #Unit4DeviationSlider 
					#model: #Unit4SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 761 539 776 ) 
					#name: #Unit4UniselectorComboActive44 
					#model: #Unit4UniselectorActive44 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 743 539 758 ) 
					#name: #Unit4UniselectorComboActive43 
					#model: #Unit4UniselectorActive43 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 724 539 739 ) 
					#name: #Unit4UniselectorComboActive42 
					#model: #Unit4UniselectorActive42 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 706 539 721 ) 
					#name: #Unit4UniselectorComboActive41 
					#model: #Unit4UniselectorActive41 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 444 689 ) 
					#name: #Label10 
					#label: 'Uniselector is:' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 762 431 776 ) 
					#name: #SpinButton1 
					#model: #Unit4NoiseSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 743 431 757 ) 
					#name: #SpinButton2 
					#model: #Unit4NoiseSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 725 431 739 ) 
					#name: #SpinButton3 
					#model: #Unit4NoiseSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 707 431 721 ) 
					#name: #SpinButton4 
					#model: #Unit4NoiseSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 374 689 ) 
					#name: #Label11 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 762 351 776 ) 
					#name: #Unit4SwitchSpin44ID 
					#model: #Unit4SwitchSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 744 351 758 ) 
					#name: #Unit4SwitchSpin43ID 
					#model: #Unit4SwitchSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 725 351 739 ) 
					#name: #Unit4SwitchSpin42ID 
					#model: #Unit4SwitchSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 707 351 721 ) 
					#name: #Unit4SwitchSpin41ID 
					#model: #Unit4SwitchSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 296 689 ) 
					#name: #Label12 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 761 273 775 ) 
					#name: #Unit4WeightSpin44ID 
					#model: #Unit4WeightSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 743 273 757 ) 
					#name: #Unit4WeightSpin43ID 
					#model: #Unit4WeightSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 724 273 738 ) 
					#name: #Unit4WeightSpin42ID 
					#model: #Unit4WeightSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 706 273 720 ) 
					#name: #Unit4WeightSpin41ID 
					#model: #Unit4WeightSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 209 688 ) 
					#name: #Label13 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 117 688 ) 
					#name: #Label14 
					#label: 'Connected?' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 759 113 775 ) 
					#name: #Unit3ConnectUnit12InputID 
					#model: #Unit4ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 741 113 757 ) 
					#name: #Unit4ConnectUnit12InputID 
					#model: #Unit4ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 722 113 738 ) 
					#name: #Unit4ConnectUnit12InputID 
					#model: #Unit4ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 704 113 720 ) 
					#name: #Unit4ConnectUnit11InputID 
					#model: #Unit4ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 39 687 ) 
					#name: #Label16 
					#label: 'Name' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 287 ) 
					#name: #Unit2InputLabel 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 288 107 305 ) 
					#name: #Unit2InputInputField 
					#model: #Unit2Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 97 ) 
					#name: #Label17 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 99 107 116 ) 
					#name: #Unit1InputInputField 
					#model: #Unit1Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 478 ) 
					#name: #Label18 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 481 107 498 ) 
					#name: #Unit3InputInputField 
					#model: #Unit3Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 671 ) 
					#name: #Label19 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 66 673 108 690 ) 
					#name: #Unit4InputInputField 
					#model: #Unit4Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 161 43 ) 
					#name: #Unit1PotentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 153 60 207 75 ) 
					#name: #Unit1PotentiometerInput 
					#model: #Unit1Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 153 77 207 92 ) 
					#name: #Unit1ViscosityInput 
					#model: #Unit1Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 77 272 92 ) 
					#name: #Unit1Switch 
					#model: #Unit1Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 60 272 75 ) 
					#name: #Unit1NoiseInput 
					#model: #Unit1Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 44 ) 
					#name: #Uni1NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 311 51 ) 
					#name: #Unit1UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 294 68 432 89 ) 
					#name: #Unit1UniselectorChoiceComboBox 
					#model: #Unit1UniselectorType 
					#alignment: #right 
					#isReadOnly: false 
					#type: #string 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 158 89 ) 
					#name: #Unit1ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 228 89 ) 
					#name: #Unit1SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 442 51 ) 
					#name: #Unit1UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 442 70 ) 
					#name: #Unit1UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit1UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 471 51 ) 
					#name: #Unit1UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 469 70 512 86 ) 
					#name: #Unit1UniselectorTimingInput 
					#model: #Unit1UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 158 235 ) 
					#name: #Unit2PotentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 151 251 205 266 ) 
					#name: #Unit2PotentiometerInput 
					#model: #Unit2Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 151 268 205 283 ) 
					#name: #Unit2ViscosityInput 
					#model: #Unit2Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 156 280 ) 
					#name: #Unit2ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 228 235 ) 
					#name: #Unit2NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 251 270 266 ) 
					#name: #Unit2NoiseInput 
					#model: #Unit2Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 268 270 283 ) 
					#name: #Unit2SwitchInput 
					#model: #Unit2Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 226 280 ) 
					#name: #Unit2SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 309 242 ) 
					#name: #Unit2UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 292 259 430 280 ) 
					#name: #Unit2UniselectorChoiceComboBox 
					#model: #Unit2UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 440 242 ) 
					#name: #Unit2UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 440 261 ) 
					#name: #Unit2UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit2UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 469 242 ) 
					#name: #Unit2UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 467 261 510 277 ) 
					#name: #Unit2UniselectorTimingInput 
					#model: #Unit2UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 157 618 ) 
					#name: #Label2 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 149 635 203 650 ) 
					#name: #Unit4PotentiometerInput 
					#model: #Unit4Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 149 652 203 667 ) 
					#name: #Unit4ViscosityInput 
					#model: #Unit4Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 154 664 ) 
					#name: #Label3 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 226 619 ) 
					#name: #Label5 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 635 268 650 ) 
					#name: #Unit4NoiseInput 
					#model: #Unit4Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 652 268 667 ) 
					#name: #Unit4SwitchInput 
					#model: #Unit4Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 224 664 ) 
					#name: #Label4 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 307 626 ) 
					#name: #Label6 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 290 643 428 664 ) 
					#name: #Unit4UniselectorChoiceComboBox 
					#model: #Unit4UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 438 626 ) 
					#name: #Label7 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 438 645 ) 
					#name: #Unit4UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit4UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 467 626 ) 
					#name: #Label8 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 465 645 508 661 ) 
					#name: #Unit4UniselectorTimingInput 
					#model: #Unit4UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 162 425 ) 
					#name: #Unit3PontentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 154 442 208 457 ) 
					#name: #Unit3PotentiometerInput 
					#model: #Unit3Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 154 459 208 474 ) 
					#name: #Unit3ViscosityInput 
					#model: #Unit3Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 159 471 ) 
					#name: #Unit3ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 231 426 ) 
					#name: #Unit3NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 219 442 273 457 ) 
					#name: #Unit3NoiseInput 
					#model: #Unit3Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 219 459 273 474 ) 
					#name: #Unit3SwitchInput 
					#model: #Unit3Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 229 471 ) 
					#name: #Unit3SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 312 433 ) 
					#name: #Unit3UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 295 450 433 471 ) 
					#name: #Unit3UniselectorChoiceComboBox 
					#model: #Unit3UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 433 ) 
					#name: #Unit3UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 443 452 ) 
					#name: #Unit3UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit3UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 472 433 ) 
					#name: #Unit3UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 470 452 513 468 ) 
					#name: #Unit3UniselectorTimingInput 
					#model: #Unit3UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 129 176 145 ) 
					#name: #unit1ConnStatus11ComboBox 
					#model: #Unit1ConnectStatusUnit11 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 14 625 108 644 ) 
					#name: #unit4ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit4Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 15 434 109 453 ) 
					#name: #unit3ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit3Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 14 243 108 262 ) 
					#name: #unit2ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit2Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 16 53 110 72 ) 
					#name: #unit1ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit1Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 184 176 200 ) 
					#name: #unit1ConnStatus14ComboBox 
					#model: #Unit1ConnectStatusUnit14 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 166 176 182 ) 
					#name: #unit1ConnStatus13ComboBox 
					#model: #Unit1ConnectStatusUnit13 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 148 176 164 ) 
					#name: #unit1ConnStatus12ComboBox 
					#model: #Unit1ConnectStatusUnit12 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 319 176 335 ) 
					#name: #unit2ConnStatus21ComboBox 
					#model: #Unit2ConnectStatusUnit21 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 338 176 354 ) 
					#name: #unit2ConnStatus22ComboBox 
					#model: #Unit2ConnectStatusUnit22 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 357 176 373 ) 
					#name: #unit2ConnStatus23ComboBox 
					#model: #Unit2ConnectStatusUnit23 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 375 176 391 ) 
					#name: #unit2ConnStatus24ComboBox 
					#model: #Unit2ConnectStatusUnit24 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 566 176 582 ) 
					#name: #unit3ConnStatus34ComboBox 
					#model: #Unit3ConnectStatusUnit34 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 548 176 564 ) 
					#name: #unit3ConnStatus33ComboBox 
					#model: #Unit3ConnectStatusUnit33 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 529 176 545 ) 
					#name: #unit3ConnStatus32ComboBox 
					#model: #Unit3ConnectStatusUnit32 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 511 176 527 ) 
					#name: #unit3ConnStatus31ComboBox 
					#model: #Unit3ConnectStatusUnit31 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 759 176 775 ) 
					#name: #unit4ConnStatus44ComboBox 
					#model: #Unit4ConnectStatusUnit44 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 741 176 757 ) 
					#name: #unit4ConnStatus43ComboBox 
					#model: #Unit4ConnectStatusUnit43 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 722 176 738 ) 
					#name: #unit4ConnStatus42ComboBox 
					#model: #Unit4ConnectStatusUnit42 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 704 176 720 ) 
					#name: #unit4ConnStatus41ComboBox 
					#model: #Unit4ConnectStatusUnit41 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 120 605 124 ) 
					#name: #Divider1 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 587 314 602 318 ) 
					#name: #Divider5 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 505 603 509 ) 
					#name: #Divider6 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 698 605 702 ) 
					#name: #Divider7 ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 30 272 45 ) 
					#name: #Unit1MassInput 
					#model: #Unit1Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 29 ) 
					#name: #Label20 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 224 ) 
					#name: #Label21 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 411 ) 
					#name: #Label22 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 170 604 ) 
					#name: #Label23 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 223 270 238 ) 
					#name: #Unit2MassInput 
					#model: #Unit2Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 220 411 274 426 ) 
					#name: #Unit3MassInput 
					#model: #Unit3Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 606 268 621 ) 
					#name: #Unit4MassInput 
					#model: #Unit4Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 442 93 ) 
					#name: #Unit1UniselectorSoundOnCheckBoxID 
					#model: #Unit1UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 440 284 ) 
					#name: #Unit2UniselectorSoundOnCheckBoxID 
					#model: #Unit2UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 443 474 ) 
					#name: #Unit3UniselectorSoundOnCheckBoxID 
					#model: #Unit3UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 438 667 ) 
					#name: #Unit4UniselectorSoundOnCheckBoxID 
					#model: #Unit4UniselectorSoundOn 
					#label: 'Sound' ) ) ) )</body>
</methods>


<methods>
<class-id>HomeostatStandardGUI</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initializeAshbySimulation">initializeAshbySimulation
"Adds four fully connected units with random values to the simulator (as per Ashby basic design)"
 
4 timesRepeat: [ | unit | unit := HomeoUnitNewtonian new setRandomValues. homeostat addFullyConnectedUnit: unit].</body>

<body package="Homeostat" selector="initialize">initialize
	homeostat := Homeostat new.
	graphicView := Mondrian.ViewRenderer new.
	maxRuns := 1000 asValue.
	self initializeAshbySimulation.
        self initializeGraphicView.

	dataAreSaved := true.
	datafile := 'newHomeostat.hst' asValue.
	datafile onChangeSend: #changedDatafile to: self.
	slowingFactor := 10 asValue.
	debugMode := false.
	showUniselectorActionMode := false.</body>

<body package="Homeostat" selector="activateConnectionCheckBoxes">activateConnectionCheckBoxes
	"construct the event triggers for all the checkboxes that activate or disactivate a connection.
As there are 4 connection for each of the 4 units, and each can be either active or inactive, we have to construct 32 event trigger handlers 
and set the default values for each to true (i.e. connection is active)

Notiice that this method assumes a classic Ashby homeostat in its starting configuration: 4 units completely connected."

	"activate connection handlers"

	1 to: 4 do: 
			[:i | 
			1 to: 4 do: 
					[:k | 
					| widgetID |
					widgetID := ('Unit' , i printString , 'ConnectedCheckBox' , i printString, k printString , 'ID') asSymbol.
					self 
						widget: widgetID
						when: #checked
						send: #activate
						to: ((homeostat homeoUnits at: i) inputConnections at: k).
					self 
						widget: widgetID
						when: #unchecked
						send: #disactivate
						to: ((homeostat homeoUnits at: i) inputConnections at: k).
					(self widgetAt: widgetID) model: (ValueHolder with: true)]]</body>

<body package="Homeostat" selector="openThreeWindows">openThreeWindows
	"open  the control panel, a new initialized Ashby homeostat window, and the Mondrian graphic view"


controlPanelBuilder := self openInterface: #homeoControlSpec.
self  openInterface:  #homeostatSpec.
graphicView open.</body>

<body package="Homeostat" selector="openBothWindows">openBothWindows
	"open both the control panel and a new initialized Ashby homeostat window"


controlPanelBuilder := self openInterface: #homeoControlSpec.
self  openInterface:  #homeostatSpec.</body>

<body package="Homeostat" selector="initializeGraphicView">initializeGraphicView

| activeUnits |

"builds the Mondrian-based graphic editor"


"choose active units"
activeUnits := homeostat homeoUnits select: [ :unit | unit isActive].

graphicView := Mondrian.ViewRenderer new.
graphicView nodes: activeUnits using: (Mondrian.Shape new
									 add:  (Mondrian.RectangleShape width: 100 height: 50 fillColor: Mondrian.Color red);
									 add:  (Mondrian.BorderShape new);
									 add:   (Mondrian.LabelShape align: #center label: #name)).


	 
"building edges in a double loop through units and units inputConnections"
activeUnits do: [:unit |
			     unit inputConnections do: [:conn | 
				
                             graphicView edge: unit  from: #yourself to: [:foo | conn incomingUnit ] using: ((Mondrian.LineShape new) decoratedWith: (Mondrian.ArrowShape new))]].									



"Choose the view Layout"

graphicView layout: ((Mondrian.RadialTreeLayout new)).



"set the window size and label"

</body>

<body package="Homeostat" selector="postBuildWith:">postBuildWith: aBuilder
	"comment stating purpose of message"

"	aBuilder windowSpec label = 'Homeostat Standard' 
		ifTrue:[ 
			self activateConnectionCheckBoxes.
			self activateUnitActiveCheckboxes]
"</body>

<body package="Homeostat" selector="activateUnitActiveCheckboxes">activateUnitActiveCheckboxes
	"construct the event triggers for all the checkboxes that activate or disactivate a unit.
As there are 4 units in a classic Ashby Homeostat  and each can be either active or inactive, we have to construct 8 event trigger handlers, and assign default values of true (active) to each unit

Notiice that this method assumes a classic Ashby homeostat in its starting configuration: 4 units completely connected."

	1 to: 4
		do: 
			[:i | 
			| widgetID |
			widgetID := ('Unit' , i printString , 'OperationalCheckBoxID') asSymbol.
			self 
				widget: widgetID
				when: #checked
				send: #activate
				to: (homeostat homeoUnits at: i).
			self 
				widget: widgetID
				when: #unchecked
				send: #disactivate
				to: (homeostat homeoUnits at: i).
			(self widgetAt: widgetID) model: (ValueHolder with: true)]</body>

<body package="Homeostat" selector="open">open

"as the correct opening method  is openBothWindows, issue by the method new, this method is redefined to do nothing"

^nil</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>testing</category>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo

"checks that the homeostat is ready to go and that the maxRuns and datafile are present"
datafile  isNil 
	ifTrue:
		 [Dialog warn: 'You have not entered a filename to save the simulation data'. 
		^false] 
	ifFalse: [
 		^(homeostat  isReadyToGo and: [maxRuns value notNil])]</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-adaptors units</category>

<body package="Homeostat" selector="adaptorForMass:">adaptorForMass: aNumber
"Private method that returns a pluggable adaptor for the  mass of the 4 units.
	use it , e.g., as:  ^adaptorForMass: 3 
	to obtain an adaptor for the  switch of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: aNumber) needleUnit).
adaptor 
	getBlock: [ :model |
		model mass ]
	putBlock: 
		[:model :value |
		 model mass: value]               								 
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (homeostat homeoUnits at: aNumber) needleUnit) &amp; (aspect = #mass)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForInputFor:">adaptorForInputFor: unitNumber

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: unitNumber).
adaptor 
	getBlock: [ :model |
		model inputTorque ]
	putBlock: 
		[:model :value |
		 ]               						"cannot be changed in the GUI"						 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: unitNumber)) &amp; (aspect = #inputTorque)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForInternallNoiseOfUnitNumber:">adaptorForInternallNoiseOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the internal noise of the 4 units.
	use it , e.g., as:  ^adaptorForInternallNoiseOfUnitNumber:  3 
	to obtain an adaptor for the  internal noise of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model noise ]
	putBlock: 
		[:model :value |
		 model noise: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #noise)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorIsOn:">adaptorForUniselectorIsOn: aNumber
"Private method that returns a pluggable adaptor for the  state of the Uniselector of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorIsOn: 3 
	to obtain an adaptor for the  stte of the unisellector of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | 
		model uniselectorActive ]
	putBlock: 
		[:model :value |
		 model uniselectorActive: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselectorActive)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForDeviationForUnit:">adaptorForDeviationForUnit: aUnitNumber

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aUnitNumber).
adaptor 
	getBlock: [ :model |
		model criticalDeviation ]
	putBlock: 
		[:model :value |
		 model criticalDeviation: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aUnitNumber)) &amp; (aspect = #criticalDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorTimingOfUnitNumber:">adaptorForUniselectorTimingOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  uniselector timing of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorTimingOfUnitNumber: 3 
	to obtain an adaptor for the  UniselectorTiming of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model uniselectorTimeInterval  ]
	putBlock: 
		[:model :value |
		 model uniselectorTimeInterval:  value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselectorTimeInterval )].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorTypeOfUnitNumber:">adaptorForUniselectorTypeOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  uniselector type  of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorTypeOfUnitNumber: 3 
	to obtain an adaptor for the  uniselector type  of the third unit"

"PUTBLOCK CHANGED ON 3/18/08"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | | string |
			    string := model uniselector class name asString.
                          (string  beginsWith: 'HomeoUniselector') 
				ifTrue: [string := string  copyFrom: ('HomeoUniselector' size) +1  to:  string  size]
				ifFalse: [ string]]
	putBlock: 
		[:model :value |
		model uniselectorChangeType: value]               				
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselector)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUnitActive:">adaptorForUnitActive: aNumber
"Private method that returns a pluggable adaptor for whether the unit is active.
	use it , e.g., as:  ^adaptorForUnitActive: 3 
	to obtain an adaptor for the  activity status of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | 
		model status]
	putBlock: 
		[:model :value |
		 model status: value ]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #status)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSliderDeviationFor:">adaptorForSliderDeviationFor: aUnitNumber

| adaptor rangeStop rangeStart|

rangeStart := (homeostat homeoUnits at: aUnitNumber) maxDeviation. 
rangeStop := (homeostat homeoUnits at: aUnitNumber) minDeviation. 

adaptor := PluggableRangeAdaptor on: (homeostat homeoUnits at: aUnitNumber).
adaptor rangeStart: rangeStart.
adaptor rangeStop: rangeStop.

adaptor 
	getBlock: 
		[ :model |
		rangeStart == rangeStop
		ifTrue: [0]
		ifFalse: [((model criticalDeviation)  - rangeStart) asFloat / (rangeStop - rangeStart) ]]
	putBlock: 
		[:model :value |
		 model criticalDeviation: ((value*(rangeStop-rangeStart))+rangeStart)]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aUnitNumber)) &amp; (aspect = #criticalDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForPotentiomOfUnitNumber:">adaptorForPotentiomOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  potentiometers of the 4 units.
	use it , e.g., as:  ^adaptorForPotentiomOfUnitNumber: 3 
	to obtain an adaptor for the  potentiometer of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model potentiometer ]
	putBlock: 
		[:model :value |
		 model potentiometer: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #potentiometer)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorSoundIsOn:">adaptorForUniselectorSoundIsOn: aNumber
"Private method that returns a pluggable adaptor for the  sound of the Uniselector of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorSoundIsOn: 3 
	to obtain an adaptor for the  state of the uniselector sound of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber) uniselector.
adaptor 
	getBlock: [ :model | 
		model beeps ]
	putBlock: 
		[:model :value |
		 model toggleBeeping]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber) uniselector) &amp; (aspect = #uniselectorSound)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForOutputSliderFor:">adaptorForOutputSliderFor: aNumber
"Private method that returns a pluggable adaptor for the  output of the 4 units, to be used in the slider.
	use it , e.g., as:  ^adaptorForOutputSlider: 3 
	to obtain an adaptor for the  output of the third unit"
	
| adaptor |
"
adaptor := RangeAdaptor
		on: (homeostat homeoUnits at: aNumber) currentOutput asValue
		start: ((homeostat homeoUnits at: aNumber) outputRange at: 'low')  
		stop: ((homeostat homeoUnits at: aNumber) outputRange at: 'high') 
		grid: nil.	

^adaptor


old code: 
"
adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model currentOutput ]
	putBlock: 
		[:model :value |
		 model currentOutput: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #currentOuput)].
self halt.
^adaptor</body>

<body package="Homeostat" selector="adaptorForViscosity:">adaptorForViscosity: aNumber
"Private method that returns a pluggable adaptor for the  viscosity of the 4 units.
	use it , e.g., as:  ^adaptorForNameOfUnitNumber: 3 
	to obtain an adaptor for the  viscosity of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model viscosity ]
	putBlock: 
		[:model :value |
		 model viscosity: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #viscosity)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNameOfUnitNumber:">adaptorForNameOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  names of the 4 units.
	use it , e.g., as:  ^adaptorForNameOfUnitNumber: 3 
	to obtain an adaptor for the  name of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model name ]
	putBlock: 
		[:model :value |
		 model name: value.
		 model changed: #name]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #name)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSwitch:">adaptorForSwitch: aNumber
"Private method that returns a pluggable adaptor for the  switch of the 4 units.
	use it , e.g., as:  ^adaptorForSwitch: 3 
	to obtain an adaptor for the  switch of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model switch ]
	putBlock: 
		[:model :value |
		 model switch: value]               								 
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #switch)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForOutputFor:">adaptorForOutputFor: unitNumber
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: unitNumber).
adaptor 
	getBlock: [ :model |
		model currentOutput ]
	putBlock: 
		[:model :value |
		 model currentOutput: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: unitNumber)) &amp; (aspect = #currentOutput)].
^adaptor</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>combobox helper methods</category>

<body package="Homeostat" selector="uniselectorTypeStringToClass:">uniselectorTypeStringToClass: aString
	"Converts the string describing the Uniselector type to the appropriate class"

|prefix className|

"aString contains the last part of the uniselector description, stripped of the initial HomeoUniselector prefix. Reconstruct the name and convert to a class."

prefix := 'HomeoUniselector'.

className := prefix, aString.

^className asSymbol</body>

<body package="Homeostat" selector="uniselectorTypeClassToString:">uniselectorTypeClassToString: aUniselectorTypeClass

	"Converts the Uniselector type class to a String"


"TEMP"
"Since the UniselectorChoices method returns a string already, just pass on the string."

^aUniselectorTypeClass</body>

<body package="Homeostat" selector="UniselectorChoices">UniselectorChoices
	"returns a list with of choices for the uniselector controlling the connected units."

	| uniChoices prefix |

	prefix := 'HomeoUniselector'.
	uniChoices:= SortedCollection new.
	HomeoUniselector allSubclasses do: [:each | |stream |
									stream := each name asString.
									(stream beginsWith: prefix) 
										ifTrue: [
											uniChoices add: (stream copyFrom: (prefix size) +1  to: stream size )]
										ifFalse: [
											uniChoices add: stream]]. 

		
	^uniChoices  asList  asValue.</body>

<body package="Homeostat" selector="booleanToString:">booleanToString: aBoolean

^aBoolean printString</body>

<body package="Homeostat" selector="uniselectorActiveChoices">uniselectorActiveChoices
	"returns a list with of choices for the uniselector controlling the connected units."

	| uniChoices |
	uniChoices := List new.
	uniChoices add: 'uniselector'; 
			      add: 'manual'.
	^uniChoices asValue.</body>

<body package="Homeostat" selector="activeStringToBoolean:">activeStringToBoolean: aString


aString = 'Active' 
	ifTrue: [^true].
aString = 'Non Active'
	ifTrue: [^false].
^nil

</body>

<body package="Homeostat" selector="unitActiveChoices">unitActiveChoices
	"returns a list  of boolean values"

	| list |
	list := List new.
	list add: 'Active'; 
	      add: 'Non Active'.
	^list asValue.</body>

<body package="Homeostat" selector="booleanToActiveString:">booleanToActiveString: aBoolean

aBoolean ifTrue: [^'Active'] ifFalse:[^'Non Active']</body>

<body package="Homeostat" selector="ConnectionActiveChoices">ConnectionActiveChoices
	"returns a list  of  values for the status of the connection"

	| list |
	list := List new.
	list add: 'Yes'; 
	      add: 'No'.
	^list asValue.</body>

<body package="Homeostat" selector="stringToBoolean:">stringToBoolean: aString


aString = 'true' 
	ifTrue: [^true].
aString = 'false'
	ifTrue: [^false].
^nil




</body>

<body package="Homeostat" selector="booleanValuesChoices">booleanValuesChoices
	"returns a list  of boolean values"

	| list |
	list := List new.
	list add: true; 
	      add: false.
	^list asValue.

</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>aspects</category>

<body package="Homeostat" selector="Unit1SwitchSpin11">Unit1SwitchSpin11
^self adaptorForSwitchOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="unit4Name">unit4Name

^self adaptorForNameOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit4Noise">Unit4Noise

^self adaptorForInternallNoiseOfUnitNumber:  4</body>

<body package="Homeostat" selector="Unit2SwitchSpin23">Unit2SwitchSpin23
^self adaptorForSwitchOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="unit2LowRange">unit2LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 2</body>

<body package="Homeostat" selector="Unit3SwitchSpin31">Unit3SwitchSpin31
^self adaptorForSwitchOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit2WeightSpin22">Unit2WeightSpin22

^self adaptorForWeightOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit3WeightSpin33">Unit3WeightSpin33

^self adaptorForWeightOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit4UniselectorOn">Unit4UniselectorOn
	

^self adaptorForUniselectorIsOn: 4</body>

<body package="Homeostat" selector="Unit1ConnectUnit13">Unit1ConnectUnit13

"connect the GUI to the name of the first connected unit of the third unit "
	

^self adaptorForNameOf: 3 forUnit: 1.</body>

<body package="Homeostat" selector="Unit4Potentiometer">Unit4Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 4</body>

<body package="Homeostat" selector="unit2HighRange">unit2HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 2</body>

<body package="Homeostat" selector="Unit2Input">Unit2Input

^self adaptorForInputFor: 2</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit43">Unit4ConnectStatusUnit43
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit3NoiseSpin31">Unit3NoiseSpin31


^self adaptorForNoiseOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit4SwitchSpin41">Unit4SwitchSpin41
^self adaptorForSwitchOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit3UniselectorSoundOn">Unit3UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 3</body>

<body package="Homeostat" selector="Unit1UniselectorType">Unit1UniselectorType
	

^self adaptorForUniselectorTypeOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive13">Unit1UniselectorActive13
 ^self adaptorForUniselectorOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit22">Unit2ConnectStatusUnit22
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2Noise">Unit2Noise

^self adaptorForInternallNoiseOfUnitNumber:  2</body>

<body package="Homeostat" selector="Unit1UniselectorSoundOn">Unit1UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 1</body>

<body package="Homeostat" selector="Unit2ConnectUnit12Input">Unit2ConnectUnit12Input

"connect the GUI to the name of the second connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 2.</body>

<body package="Homeostat" selector="Unit2SwitchSpin22">Unit2SwitchSpin22
^self adaptorForSwitchOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit3SwitchSpin34">Unit3SwitchSpin34
^self adaptorForSwitchOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive33">Unit3UniselectorActive33
 
^self adaptorForUniselectorOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit2SliderDeviation">Unit2SliderDeviation

^self adaptorForSliderDeviationFor: 2</body>

<body package="Homeostat" selector="unit4Active">unit4Active


^ self adaptorForUnitActive: 4</body>

<body package="Homeostat" selector="Unit4UniselectorTiming">Unit4UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit3Input">Unit3Input

^self adaptorForInputFor: 3</body>

<body package="Homeostat" selector="Unit1ConnectUnit12">Unit1ConnectUnit12

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 1.</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit44">Unit4ConnectStatusUnit44
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit1Viscosity">Unit1Viscosity
	
^self adaptorForViscosity: 1</body>

<body package="Homeostat" selector="Unit1SwitchSpin12">Unit1SwitchSpin12

^self adaptorForSwitchOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit2Mass">Unit2Mass
	
^self adaptorForMass: 2</body>

<body package="Homeostat" selector="Unit1UniselectorTiming">Unit1UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit3UniselectorActive34">Unit3UniselectorActive34
 
^self adaptorForUniselectorOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorTiming">Unit3UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit1Noise">Unit1Noise

^self adaptorForInternallNoiseOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit2NoiseSpin21">Unit2NoiseSpin21


^self adaptorForNoiseOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="slowingFactor">slowingFactor


| adaptor |

adaptor := PluggableAdaptor on: (homeostat).
adaptor 
	getBlock: [ :model |
		model slowingFactor ]
	putBlock: 
		[: model :value |
		 model slowingFactor: value]               								 
	updateBlock:									
		[ :model :aspect :parameter |
		aspect = #slowingFactor ].
^adaptor</body>

<body package="Homeostat" selector="Unit3ConnectUnit14Input">Unit3ConnectUnit14Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 4 forUnit: 3.</body>

<body package="Homeostat" selector="unit1Name">unit1Name

^self adaptorForNameOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit4NoiseSpin41">Unit4NoiseSpin41


^self adaptorForNoiseOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit2WeightSpin24">Unit2WeightSpin24

^self adaptorForWeightOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectUnit11Input">Unit2ConnectUnit11Input
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 2.</body>

<body package="Homeostat" selector="Unit3Operational">Unit3Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit3Operational isNil
		ifTrue:
			[Unit3Operational := false asValue]
		ifFalse:
			[Unit3Operational]</body>

<body package="Homeostat" selector="Unit1SwitchSpin14">Unit1SwitchSpin14

^self adaptorForSwitchOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit2Operational">Unit2Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit2Operational isNil
		ifTrue:
			[Unit2Operational := false asValue]
		ifFalse:
			[Unit2Operational]</body>

<body package="Homeostat" selector="Unit1SliderDeviation">Unit1SliderDeviation
^self adaptorForSliderDeviationFor: 1</body>

<body package="Homeostat" selector="unit1HighRange">unit1HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 1</body>

<body package="Homeostat" selector="unit3HighRange">unit3HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 3</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit41">Unit4ConnectStatusUnit41
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit2NoiseSpin22">Unit2NoiseSpin22


^self adaptorForNoiseOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit1Output">Unit1Output

^self adaptorForOutputFor: 1</body>

<body package="Homeostat" selector="Unit4ConnectUnit13Input">Unit4ConnectUnit13Input


^self adaptorForNameOf: 3 forUnit: 4.</body>

<body package="Homeostat" selector="Unit2Switch">Unit2Switch
	
^self adaptorForSwitch: 2</body>

<body package="Homeostat" selector="Unit4Output">Unit4Output

^self adaptorForOutputFor: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive43">Unit4UniselectorActive43
 
^self adaptorForUniselectorOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit2Viscosity">Unit2Viscosity
	
^self adaptorForViscosity: 2</body>

<body package="Homeostat" selector="Unit3SwitchSpin32">Unit3SwitchSpin32
^self adaptorForSwitchOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit1UniselectorActive14">Unit1UniselectorActive14
	

 ^self adaptorForUniselectorOf:4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin14">Unit1WeightSpin14
^self adaptorForWeightOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit2UniselectorActive24">Unit2UniselectorActive24
 
^self adaptorForUniselectorOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit1NoiseSpin11">Unit1NoiseSpin11


^self adaptorForNoiseOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit2UniselectorActive23">Unit2UniselectorActive23
 
^self adaptorForUniselectorOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2Potentiometer">Unit2Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit3SliderDeviation">Unit3SliderDeviation

^self adaptorForSliderDeviationFor: 3</body>

<body package="Homeostat" selector="Unit2WeightSpin23">Unit2WeightSpin23

^self adaptorForWeightOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit21">Unit2ConnectStatusUnit21
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit4WeightSpin44">Unit4WeightSpin44

^self adaptorForWeightOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit2Output">Unit2Output

^self adaptorForOutputFor: 2</body>

<body package="Homeostat" selector="Unit4Input">Unit4Input

^self adaptorForInputFor: 4</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit11">Unit1ConnectStatusUnit11
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit4SwitchSpin42">Unit4SwitchSpin42
^self adaptorForSwitchOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit3NoiseSpin32">Unit3NoiseSpin32


^self adaptorForNoiseOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="unit3Name">unit3Name

^self adaptorForNameOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit1Switch">Unit1Switch
	
^self adaptorForSwitch: 1</body>

<body package="Homeostat" selector="Unit4NoiseSpin43">Unit4NoiseSpin43


^self adaptorForNoiseOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit3WeightSpin32">Unit3WeightSpin32

^self adaptorForWeightOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3NoiseSpin33">Unit3NoiseSpin33


^self adaptorForNoiseOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit24">Unit2ConnectStatusUnit24
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit23">Unit2ConnectStatusUnit23
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit34">Unit3ConnectStatusUnit34
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit4Mass">Unit4Mass
	
^self adaptorForMass: 4</body>

<body package="Homeostat" selector="Unit1WeightSpin13">Unit1WeightSpin13
^self adaptorForWeightOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit3SwitchSpin33">Unit3SwitchSpin33
^self adaptorForSwitchOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive31">Unit3UniselectorActive31
 
^self adaptorForSelfUniselectorForUnit: 3</body>

<body package="Homeostat" selector="unit4HighRange">unit4HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 4</body>

<body package="Homeostat" selector="Unit3Deviation">Unit3Deviation

^self adaptorForDeviationForUnit: 3</body>

<body package="Homeostat" selector="Unit4Deviation">Unit4Deviation

^self adaptorForDeviationForUnit: 4</body>

<body package="Homeostat" selector="Unit1Input">Unit1Input

^self adaptorForInputFor: 1</body>

<body package="Homeostat" selector="Unit3Viscosity">Unit3Viscosity
	
^self adaptorForViscosity: 3</body>

<body package="Homeostat" selector="Unit1SwitchSpin13">Unit1SwitchSpin13

^self adaptorForSwitchOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="unit1Active">unit1Active


^self adaptorForUnitActive: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin12">Unit1WeightSpin12
^self adaptorForWeightOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="homeoUnits">homeoUnits
| adaptor |

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ :model |
		model homeoUnits size.]
	putBlock: 
		[: model :value |]                "number of Units cannot be changed in the GUI"
	updateBlock:
		[ :model :aspect :parameter |
		(model = homeostat) &amp; (aspect = #units)].
^adaptor</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit33">Unit3ConnectStatusUnit33
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit4ConnectUnit12Input">Unit4ConnectUnit12Input
	

^self adaptorForNameOf: 2 forUnit: 4.</body>

<body package="Homeostat" selector="Unit3NoiseSpin34">Unit3NoiseSpin34


^self adaptorForNoiseOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit2UniselectorActive22">Unit2UniselectorActive22
 
^self adaptorForUniselectorOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit3Output">Unit3Output

^self adaptorForOutputFor: 3</body>

<body package="Homeostat" selector="Unit1ConnectUnit11">Unit1ConnectUnit11
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 1.</body>

<body package="Homeostat" selector="Unit2UniselectorTiming">Unit2UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit3Potentiometer">Unit3Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit1ConnectUnit14">Unit1ConnectUnit14
	
"connect the GUI to the name of the first connected unit of the fourth unit "
	

^self adaptorForNameOf: 4 forUnit: 1.</body>

<body package="Homeostat" selector="Unit3Mass">Unit3Mass
	
^self adaptorForMass: 3</body>

<body package="Homeostat" selector="Unit3Noise">Unit3Noise

^self adaptorForInternallNoiseOfUnitNumber:  3</body>

<body package="Homeostat" selector="Unit1Potentiometer">Unit1Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit4SwitchSpin44">Unit4SwitchSpin44
^self adaptorForSwitchOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4NoiseSpin44">Unit4NoiseSpin44


^self adaptorForNoiseOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit1Deviation">Unit1Deviation
	^self adaptorForDeviationForUnit: 1</body>

<body package="Homeostat" selector="Unit4UniselectorActive44">Unit4UniselectorActive44
 
^self adaptorForUniselectorOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorSoundOn">Unit4UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 4</body>

<body package="Homeostat" selector="unit3Active">unit3Active


^self adaptorForUnitActive: 3</body>

<body package="Homeostat" selector="Unit3UniselectorType">Unit3UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit4SwitchSpin43">Unit4SwitchSpin43
^self adaptorForSwitchOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4Operational">Unit4Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit4Operational isNil
		ifTrue:
			[Unit4Operational := false asValue]
		ifFalse:
			[Unit4Operational]</body>

<body package="Homeostat" selector="Unit3ConnectUnit13Input">Unit3ConnectUnit13Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 3 forUnit: 3.</body>

<body package="Homeostat" selector="datafile">datafile
	

	^datafile isNil
		ifTrue:
			[datafile := 'newHomeostat.hst'  asValue]
		ifFalse:
			[datafile]</body>

<body package="Homeostat" selector="Unit2UniselectorSoundOn">Unit2UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 2</body>

<body package="Homeostat" selector="Unit1Mass">Unit1Mass
	
^self adaptorForMass: 1</body>

<body package="Homeostat" selector="unit3LowRange">unit3LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 3</body>

<body package="Homeostat" selector="Unit1UniselectorActive11">Unit1UniselectorActive11
 
^self adaptorForSelfUniselectorForUnit: 1</body>

<body package="Homeostat" selector="Unit3ConnectUnit11Input">Unit3ConnectUnit11Input
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 3.</body>

<body package="Homeostat" selector="Unit2Deviation">Unit2Deviation

^self adaptorForDeviationForUnit: 2</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit13">Unit1ConnectStatusUnit13
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit2ConnectUnit14Input">Unit2ConnectUnit14Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 4 forUnit: 2.</body>

<body package="Homeostat" selector="Unit4UniselectorActive41">Unit4UniselectorActive41
 
^self adaptorForSelfUniselectorForUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorType">Unit4UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit3ConnectUnit12Input">Unit3ConnectUnit12Input

"connect the GUI to the name of the second connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 3.</body>

<body package="Homeostat" selector="maxRuns">maxRuns
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^maxRuns isNil
		ifTrue:
			[maxRuns := 0 asValue]
		ifFalse:
			[maxRuns]</body>

<body package="Homeostat" selector="Unit1WeightSpin11">Unit1WeightSpin11

^self adaptorForWeightOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="unit4LowRange">unit4LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 4</body>

<body package="Homeostat" selector="Unit2WeightSpin21">Unit2WeightSpin21

^self adaptorForWeightOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit31">Unit3ConnectStatusUnit31
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit2NoiseSpin24">Unit2NoiseSpin24


^self adaptorForNoiseOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit32">Unit3ConnectStatusUnit32
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit2UniselectorType">Unit2UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit3WeightSpin34">Unit3WeightSpin34

^self adaptorForWeightOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive32">Unit3UniselectorActive32
 
^self adaptorForUniselectorOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="currentRun">currentRun

| adaptor |

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ :model |
		model time ]
	putBlock: 
		[:model :value |
		 ]               								 "GUI cannot jump to specific times"
	updateBlock:									
		[ :model :aspect :parameter |
		aspect = #time].
^adaptor</body>

<body package="Homeostat" selector="Unit4ConnectUnit11Input">Unit4ConnectUnit11Input
	

^self adaptorForNameOf: 1 forUnit: 4.</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit14">Unit1ConnectStatusUnit14
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive12">Unit1UniselectorActive12
 
^self adaptorForUniselectorOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin12">Unit1NoiseSpin12


^self adaptorForNoiseOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit2SwitchSpin24">Unit2SwitchSpin24
^self adaptorForSwitchOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit4ConnectUnit14Input">Unit4ConnectUnit14Input


^self adaptorForNameOf: 4 forUnit: 4.</body>

<body package="Homeostat" selector="unit1LowRange">unit1LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorOn">Unit1UniselectorOn
	

^self adaptorForUniselectorIsOn: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin14">Unit1NoiseSpin14


^self adaptorForNoiseOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit4WeightSpin42">Unit4WeightSpin42

^self adaptorForWeightOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit3Switch">Unit3Switch
	
^self adaptorForSwitch: 3</body>

<body package="Homeostat" selector="Unit2SwitchSpin21">Unit2SwitchSpin21
^self adaptorForSwitchOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="unit2Name">unit2Name

^self adaptorForNameOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit42">Unit4ConnectStatusUnit42
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit3UniselectorOn">Unit3UniselectorOn
	

^self adaptorForUniselectorIsOn: 3</body>

<body package="Homeostat" selector="Unit2UniselectorOn">Unit2UniselectorOn
	

^self adaptorForUniselectorIsOn: 2</body>

<body package="Homeostat" selector="Unit4Switch">Unit4Switch
	
^self adaptorForSwitch: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin41">Unit4WeightSpin41

^self adaptorForWeightOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit2UniselectorActive21">Unit2UniselectorActive21
 
^self adaptorForSelfUniselectorForUnit: 2</body>

<body package="Homeostat" selector="Unit1NoiseSpin13">Unit1NoiseSpin13


^self adaptorForNoiseOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="currentRun2">currentRun2


|adaptor|

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ 
		:model |
		model time]
	putBlock: [									"GUI cannot skip to a specific step"
		:model :value| 
		 ]
	updateBlock: [
		:model :aspect :parameter |
		 (model = homeostat) &amp; (aspect = #time)].

^adaptor</body>

<body package="Homeostat" selector="Unit2NoiseSpin23">Unit2NoiseSpin23


^self adaptorForNoiseOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit4SliderDeviation">Unit4SliderDeviation

^self adaptorForSliderDeviationFor: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive42">Unit4UniselectorActive42
 
^self adaptorForUniselectorOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin43">Unit4WeightSpin43

^self adaptorForWeightOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4Viscosity">Unit4Viscosity
	
^self adaptorForViscosity: 4</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit12">Unit1ConnectStatusUnit12
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="unit2Active">unit2Active


^self adaptorForUnitActive: 2</body>

<body package="Homeostat" selector="Unit3WeightSpin31">Unit3WeightSpin31

^self adaptorForWeightOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit4NoiseSpin42">Unit4NoiseSpin42


^self adaptorForNoiseOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit2ConnectUnit13Input">Unit2ConnectUnit13Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 3 forUnit: 2.</body>

<body package="Homeostat" selector="Unit1Operational">Unit1Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit1Operational isNil
		ifTrue:
			[Unit1Operational := false asValue]
		ifFalse:
			[Unit1Operational]</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>accessing</category>

<body package="Homeostat" selector="homeostat">homeostat
	^homeostat</body>

<body package="Homeostat" selector="dataAreSaved">dataAreSaved
	^dataAreSaved</body>

<body package="Homeostat" selector="homeostat:">homeostat: anObject
	homeostat := anObject</body>

<body package="Homeostat" selector="dataAreSaved:">dataAreSaved: anObject
	dataAreSaved := anObject</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-adaptors connections</category>

<body package="Homeostat" selector="adaptorForRange:forUnit:">adaptorForRange: highOrLow forUnit: aNumber
"Private method that returns a pluggable adaptor for the  range of the 4 units.
	use it , e.g., as:  ^adaptorForRange: #highRange forUnit: 1 
	to obtain an adaptor for the  high range  of the first unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber) .
adaptor 
	getBlock: [ :model |
		model perform: highOrLow ]
	putBlock: 
		[:model :value |
		 model perform: (highOrLow asString, ':') asSymbol with: value.]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #maxDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForWeightOf:forUnit:">adaptorForWeightOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  weight of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForWeightOf: 1 forUnit: 2
	to obtain an adaptor for the  weight of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model weight ]
	putBlock: 
		[:model :value |
		 model weight: value  ]               								
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #weight)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSwitchOf:forUnit:">adaptorForSwitchOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber

"Private method that returns a pluggable adaptor for the  switch of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForSwitchOf: 1 forUnit: 2
	to obtain an adaptor for the  switch of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model switch ]
	putBlock: 
		[:model :value |
		 model switch: value  ]               								
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #switch)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForConnectionStatusOf:forUnit:">adaptorForConnectionStatusOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  status  of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForConnectionStatusOf: 1 forUnit: 2
	to obtain an adaptor for the  connection status  of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model status ]
	putBlock: 
		[:model :value | 
		 model status: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		(model = ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber) ) &amp; aspect = #status].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNameOf:forUnit:">adaptorForNameOf: theConnectionDestiNumber forUnit: theConnectionOriginNumber
"Private method that returns a pluggable adaptor for the  names of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForNameOf: 1 forUnit: 2
	to obtain an adaptor for the  name of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model | 
		(model inputConnections at: theConnectionDestiNumber) incomingUnit name ]
	putBlock: 
		[:model :value |
		 ]               								 "cannot be changed in the GUI"
	updateBlock:
		[ :model :aspect :parameter | 
		 aspect = #name].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNoiseOf:forUnit:">adaptorForNoiseOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  noise of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForNoiseOf: 1 forUnit: 2
	to obtain an adaptor for the  noise of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model noise ]
	putBlock: 
		[:model :value | 
		 model noise: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		true].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorOf:forUnit:">adaptorForUniselectorOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  state of uniselector of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorOf: 1 forUnit: 2
	to obtain an adaptor for the  state of the Uniselector of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on:((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model state ]
	putBlock: 
		[:model :value |
		 model  state: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #state)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSelfUniselectorForUnit:">adaptorForSelfUniselectorForUnit: theConnectionDestiNumber

"Private method that returns a pluggable adaptor for the  state of uniselector on the connection between the unit and itself.
 Notice that the unit's self-connection is always the first of the connections.
  As the connection is always manual, the adaptor does not allow changing the value.
   Use it , e.g., as:  ^self adaptorForSelfUniselectoForUnit:2
to obtain an adaptor for the  state of the Uniselector of the self-connection of thesecond unit"

| adaptor |

adaptor := PluggableAdaptor on:((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: 1).
adaptor 
	getBlock: [ :model |
		model state ]
	putBlock: 
		[:model :value |
		  ]               								"GUI cannot change state of the unit's self-connection"
	updateBlock:
		[ :model :aspect :parameter |
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: 1)) &amp; (aspect = #state)].
^adaptor</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-events</category>

<body package="Homeostat" selector="redisplayDatafile">redisplayDatafile
	"update the display of the filename in the Control panel window"

(controlPanelBuilder componentAt: #datafileInputField) invalidate.</body>

<body package="Homeostat" selector="changeRequest">changeRequest

"check  user does not want to save data before closing"

^super changeRequest
		ifFalse: [false]
		ifTrue:  [dataAreSaved 
			ifFalse: 
				[(Dialog confirm: 'Save simulation data?') 
					ifTrue: [self saveCompleteRunOnFile. true]
					ifFalse:[true]]
			ifTrue: [true]]</body>

<body package="Homeostat" selector="newHomeostat">newHomeostat
	"closes the current window, flushes the homeostat and puts a new one in its place."

	"close the homeostat window and open a new one on the new homeostat"

	

	self mainWindow close.
	controlPanelBuilder window close.
	
	"switch to a new homeostat and initialize variables"
	
	self initialize.
	self openBothWindows.

	"update values"
	homeostat allChanged</body>

<body package="Homeostat" selector="redisplayFilename">redisplayFilename
	"update the display of the filename in the Control panel window"

(controlPanelBuilder componentAt: #datafileInputField) invalidate.</body>

<body package="Homeostat" selector="newHomeostat:">newHomeostat: anHomeostat 
	"swaps the current homeostat with anHomeostat, including all the components of the former,
	tells the new homeostat to updates the values in the GUI"

	"close the homeostat window and open a new one on the new homeostat"

	
	self mainWindow close.
	controlPanelBuilder window close.
	"switch to new homeostat"
	homeostat :=  anHomeostat.
	"Prepare the window and change its label  to the filename of the new homeostat"
	 self openBothWindows.
	 self builder window label: datafile value.
	"update values"
	homeostat allChanged</body>

<body package="Homeostat" selector="changedDatafile">changedDatafile

self redisplayDatafile</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>actions</category>

<body package="Homeostat" selector="resetTime">resetTime
	"start a new simulation: 
		resets simulation time to zero 	
		clear the simulation data
		set dataAreSaved to true"

	homeostat timeReset.
	homeostat flushData.
	simulProcess := nil.
	dataAreSaved := true.</body>

<body package="Homeostat" selector="simulationSave">simulationSave

"save the simulation data to file. Offer a choice between saving the complete simulation data and only a subset"

Dialog warn: 'Under construction. Not ready to to go quite yet'</body>

<body package="Homeostat" selector="homeostatInspect">homeostatInspect

	 homeostat inspect
	"homeostat inspect."</body>

<body package="Homeostat" selector="simulationGraph">simulationGraph

	"Open a JunChartLine graph window on the simulation data of the last run (since application started or since last 'reset time' command.
	  Needs  to be improved to :
		- include the data about the  uniselector's action
		- parametrize the values of the y axis to the current min and max values of the units
		- improve the graphic look by adding a legend and  making it less cartoonish" 

	|  junDataColl |



"1. obtain data"

junDataColl := OrderedCollection new.
junDataColl add: homeostat dataCollector criticalDevAsCollectionOfArraysForAllUnits.

"2 construct chart"

dataChart := JunChartLine samples: junDataColl.
dataChart valueRangeFrom: -10  to: 10.
dataChart lineWidth: 1.
dataChart showXAxis.
dataChart showYAxisWithLabels.



"4. display chart"
dataChart  open.</body>

<body package="Homeostat" selector="exit">exit
	dataAreSaved 
		ifFalse: 
			[(Dialog confirm: 'Save simulation data?') 
				ifTrue: [self saveCompleteRunOnFile]].
	self closeRequest</body>

<body package="Homeostat" selector="startNewProcess">startNewProcess
	"if no simulation is running starts one in  a new process and runs it. Otherwise resume suspended simulation"

	self isReadyToGo 
		ifTrue: 
			[dataAreSaved := false.
			simulProcess isNil 
				ifTrue: 
					[simulProcess := [homeostat runFor: maxRuns value] 
								forkAt: Processor userBackgroundPriority]
				ifFalse: [(Processor isPaused: simulProcess) ifTrue: [simulProcess resume]]]
		ifFalse: [Dialog warn: 'The homeostat simulation is not ready to go']</body>

<body package="Homeostat" selector="toggleDebugMode">toggleDebugMode
	"turns debug mode on or off by changing the value of the debugMode ivar of the homeoUnits. Changes the color of the button accordingly"

	| wrapper lookPref aColor |
	homeostat homeoUnits do: [:unit | unit toggleDebugMode].
	debugMode 
		ifTrue: 
			[aColor := ColorValue black.
			debugMode := false]
		ifFalse: 
			[aColor := ColorValue red.
			debugMode := true].
	wrapper := controlPanelBuilder componentAt: #DebugModeActionButton.
	lookPref := wrapper lookPreferences foregroundColor: aColor.
	wrapper lookPreferences: lookPref</body>

<body package="Homeostat" selector="stopProcess">stopProcess
"stops the simulation"

simulProcess isNil
		ifFalse: [
			simulProcess terminate.
			simulProcess :=  nil]</body>

<body package="Homeostat" selector="start">start
	(self isReadyToGo)
		ifTrue: 
			[dataAreSaved := false.
			homeostat  runFor: maxRuns value]
		ifFalse: [Dialog warn: 'The homeostat simulation is not ready to go']</body>

<body package="Homeostat" selector="pauseProcess">pauseProcess
	"Pause the simulation and allows a restart. Needs to change the label of the start widget to 'restart'"

	simulProcess isNil 
		ifFalse: [(Processor isPaused: simulProcess) 
				ifFalse: [ simulProcess suspend]]</body>

<body package="Homeostat" selector="pause">pause

"Pause the simulation and allows a restart. Needs to change the label of the start widget to 'restart'"

simulRunning
	ifTrue: [ simulProcess suspend]</body>

<body package="Homeostat" selector="toggleShowUniselectorAction">toggleShowUniselectorAction
	"turns debug mode on or off by changing the value of the debugMode ivar of the homeoUnits. Changes the color of the button accordingly"

	| wrapper lookPref aColor |
	homeostat homeoUnits do: [:unit | unit toggleShowUniselectorAction].
	showUniselectorActionMode 
		ifTrue: 
			[aColor := ColorValue black.
			showUniselectorActionMode := false]
		ifFalse: 
			[aColor := ColorValue red.
			showUniselectorActionMode := true].
	wrapper := controlPanelBuilder componentAt: #showUniselectorActionButton.
	lookPref := wrapper lookPreferences foregroundColor: aColor.
	wrapper lookPreferences: lookPref</body>

<body package="Homeostat" selector="stop">stop
"stops the simulation"

homeostat stop</body>

<body package="Homeostat" selector="stepSimulation">stepSimulation

	homeostat runOnce</body>

<body package="Homeostat" selector="readHomeostat">readHomeostat
	"reads the initial conditions for a simulation, i.e. the homeostat, from a filename"

	| dialog filename boss bossedHomeostat |
	dialog := OpenFileDialog new.
	dialog
		windowTitle: 'Load a homeostat';
		acceptButtonLabel: 'Load';
		addFilterForAllFiles;
		addFirstFileFilter: 'Homeostat file (*.hst)' pattern: '*.hst';
		defaultExtension: '.hst';
		fileCondition: #mustBeOld.
	filename := dialog select.
	filename notNil 
				ifTrue: 
					[
					[boss := BinaryObjectStorage onOldNoScan: filename readStream.
					bossedHomeostat := boss next.
					boss close] 
							on: Exception
							do: [:ex | ^Dialog warn: 'I am sorry, the selected file is not a homeostat.'].
					bossedHomeostat class = Homeostat 
						ifFalse: [^Dialog warn: 'I am sorry, the selected file is not a homeostat']
						ifTrue: 
							[self datafile value: filename tail.
							self newHomeostat: bossedHomeostat]].
	</body>

<body package="Homeostat" selector="resetUnitValues">resetUnitValues

homeostat randomizeValuesforAllUnits.</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>saving</category>

<body package="Homeostat" selector="saveEssentialDataOnFile">saveEssentialDataOnFile
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := WriteStream on: (datafile, '.essential-simul-data') asFilename.
	homeostat  dataCollector printEssentialDataOn: stream.
	stream close</body>

<body package="Homeostat" selector="saveHomeostatOnFile">saveHomeostatOnFile
	"save on a file the homeostat itself, which includes all the units, their connections, etcetera. Does not save the data about the simulation's run"

	| dialog filename|
	dialog := SaveFileDialog new.
	dialog 
		windowTitle: 'Save the homeostat';
		addFirstFileFilter: 'Homeostat file (*.hst)' pattern: '*.hst';
		defaultExtension: '.hst';
		fileCondition: #new;
		defaultFilename: (datafile value) asFilename.
	
	filename := dialog select.
	self saveHomeostatOnFile: filename.
	datafile value:  filename tail.
	builder window label: filename tail.</body>

<body package="Homeostat" selector="saveAllDataOnFile:">saveAllDataOnFile: aFilename
	"save on aFilename a complete  version of the simulation data, suitable"

"TO DO"</body>

<body package="Homeostat" selector="saveHomeostatOnFile:">saveHomeostatOnFile: aFilename
	"save on aFilename the homeostat itself, which includes all the units, their connections, etcetera. Does not save the data about the simulation's run"

	aFilename isNil 
		ifTrue: 
			[^Dialog warn: 'Saving canceled']
		ifFalse: [homeostat bossOutOn: aFilename]</body>

<body package="Homeostat" selector="saveAllDataOnFile">saveAllDataOnFile
	"asks the datacollector of the homeostat to save all data on datafile"



Dialog warn: 'Sorry, not implemented yet'</body>

<body package="Homeostat" selector="saveEssentialDataOnFileWithSeparator:">saveEssentialDataOnFileWithSeparator: aCharacter
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := datafile asFilename writeStream.
	

	homeostat  dataCollector saveEssentialsOn:  stream separator: aCharacter.
	stream close</body>

<body package="Homeostat" selector="savePlotDataOnFile">savePlotDataOnFile
	"save on a file a stripped version of the simulation data, suitable for plotting. It onjly includes the data about the critical deviation of each unit."

	| dialog filename|
	dialog := SaveFileDialog new.
	dialog 
		windowTitle: 'Save plotting data';
		addFirstFileFilter: 'Homeostat data file (*.txt)' pattern: '*.txt';
		defaultExtension: '.data';
		fileCondition: #new;
		defaultFilename: 'simulation-data.txt' asFilename.
	filename := dialog select.
	self savePlotDataOnFile: filename.</body>

<body package="Homeostat" selector="savePlotDataOnFile:">savePlotDataOnFile: aFilename
	"save on aFilename a stripped version of the simulation data, suitable for plotting."

	| stream |
	aFilename isNil 
		ifTrue: 
			[^Dialog warn: 'Saving canceled']
		ifFalse: [stream :=   aFilename writeStream.
			       homeostat dataCollector printPlottingDataForGgobiOn: stream.
			       stream close].</body>
</methods>


<methods>
<class-id>HomeoDataUnitTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoDataUnitTest</class-id> <category>running</category>

<body package="Homeostat" selector="testPrintDataOnStream">testPrintDataOnStream

| aStream aString|
aString := String new.
aStream := ReadWriteStream on: aString.
dataUnit readStateFrom: unit1.
dataUnit printDataOn:	aStream.

"shortcut  to quickly  check the stream instead of parsing it and seeing whether it represent the unit. Will need to change this"
Transcript show: aString.

aStream close.

self assert: false.</body>

<body package="Homeostat" selector="testPrintEssentialVariableOn">testPrintEssentialVariableOn

| aStream aString|
aString := String new.
aStream := ReadWriteStream on: aString.
dataUnit readStateFrom: unit1.
dataUnit printEssentialVariableOn:	aStream.

"shortcut  to quickly  check the stream instead of parsing it and seeing whteher it represent the unit. Will need to change this"


Transcript show: aString.

aStream close.


self assert: false.</body>

<body package="Homeostat" selector="testSameValuesAs">testSameValuesAs


self assert: false.</body>

<body package="Homeostat" selector="testReadDataFromUnit">testReadDataFromUnit

	dataUnit readStateFrom: unit1.
	self assert: dataUnit name = unit1 name.
	self assert: dataUnit maxDeviation = unit1 maxDeviation.
	unit1 inputConnections do: 
			[:conn | 
			| connArray |
			connArray := dataUnit connectedTo at: conn incomingUnit name.
			self assert: (connArray at: 1) = conn weight.
			self assert: (connArray at: 2) = conn switch.
			self assert: (connArray at: 3) = conn state.
			self assert: (connArray at: 4) = conn noise].
	self assert: dataUnit output = unit1 currentOutput.
	self assert: dataUnit uniselectorState = unit1 uniselectorActive</body>

<body package="Homeostat" selector="testNewStateFor">testNewStateFor

| newDataUnit |

newDataUnit := HomeoDataUnit newUnitFor: unit1.
dataUnit := newDataUnit.
self assert: dataUnit name = unit1 name.
	self assert: dataUnit maxDeviation = unit1 maxDeviation.
	unit1 inputConnections do: 
			[:conn | 
			| connArray |
			connArray := dataUnit connectedTo at: conn incomingUnit name.
			self assert: (connArray at: 1) = conn weight.
			self assert: (connArray at: 2) = conn switch.
			self assert: (connArray at: 3) = conn state.
			self assert: (connArray at: 4) = conn noise].
	self assert: dataUnit output = unit1 currentOutput.
	self assert: dataUnit uniselectorState = unit1 uniselectorActive</body>
</methods>

<methods>
<class-id>HomeoDataUnitTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp

dataUnit := HomeoDataUnit new.
unit1 := HomeoUnit new.</body>
</methods>


<methods>
<class-id>HomeoUniselectorTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoUniselectorTest</class-id> <category>running</category>

<body package="Homeostat" selector="testHomeoUniselectorClassType">testHomeoUniselectorClassType

|currentClasses bogusClasses|

currentClasses := OrderedCollection new.
bogusClasses := OrderedCollection new.
HomeoUniselector withAllSubclasses do: [:class | currentClasses add: class name asString].
bogusClasses add: 'pippo'; add: 'HomeoUnit'; add: 'Object'.


bogusClasses do: [:string | self deny: (HomeoUniselector includesType: string)].
currentClasses do: [:string| self assert: (HomeoUniselector includesType: string)].</body>

<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds


self assert: ((uniselector upperBound) - (uniselector lowerBound)) &gt;= 0.</body>
</methods>

<methods>
<class-id>HomeoUniselectorTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselector new.</body>
</methods>


<methods>
<class-id>HomeoUniselectorUniformRandomTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoUniselectorUniformRandomTest</class-id> <category>running</category>

<body package="Homeostat" selector="testValueWithinIntervalBounds">testValueWithinIntervalBounds

| sortedValues tests|

tests:= 1000.

sortedValues := SortedCollection new.

tests timesRepeat:  [sortedValues add:  uniselector produceNewValue.].

self assert: (sortedValues last &lt;= uniselector upperBound).
self assert: (sortedValues first &gt;= uniselector lowerBound).</body>

<body package="Homeostat" selector="testProduceNewValue">testProduceNewValue
	| newValue values sortedValues tests |
	
      tests := 1000.
	values := OrderedCollection new.
	sortedValues := SortedCollection new.
	
"testing with default interval bounds"
	tests timesRepeat: 
			[newValue := uniselector produceNewValue.
			values add: newValue.
			sortedValues add: newValue].
	self assert: sortedValues asSet size = tests.	"no repeated values"


"testing with random values for interval"
sortedValues := SortedCollection new.
	10 timesRepeat: 
			[uniselector upperBound: (UniformDistribution from: -10 to: 10) random].
	tests timesRepeat: 
			[newValue := uniselector produceNewValue.
			values add: newValue.
			sortedValues add: newValue].
	self assert: sortedValues asSet size = tests	"no repeated values"</body>

<body package="Homeostat" selector="testDefaultIntervalBounds">testDefaultIntervalBounds
uniselector := HomeoUniselectorUniformRandom new.
self assert: (uniselector lowerBound = -1 and: [uniselector upperBound = 1]).</body>

<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds
"Interval bounds are always centered around 0, i.e. lowerbounds always = to upperBound negated"


uniselector := HomeoUniselectorUniformRandom new.

100 timesRepeat: [ 
					uniselector lowerBound:  ((UniformDistribution from: -10 to: 10) random).
					self assert: (uniselector lowerBound = uniselector upperBound negated).
					uniselector upperBound: ((UniformDistribution from: -10 to: 10) random).
					self assert: (uniselector lowerBound = uniselector upperBound negated)].</body>
</methods>

<methods>
<class-id>HomeoUniselectorUniformRandomTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="setUp">setUp

uniselector := HomeoUniselectorUniformRandom new.</body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>HomeoUniselectorAshbyTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>


<methods>
<class-id>HomeoUniselectorAshbyTest</class-id> <category>running</category>

<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds
"always 0 and 1"

100 timesRepeat: [ uniselector lowerBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector lowerBound = 0).
					uniselector upperBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector upperBound = 1)].

self assert: ((uniselector upperBound =1) and: [ uniselector lowerBound = 0]).</body>

<body package="Homeostat" selector="testNumberOfValuesProduced">testNumberOfValuesProduced
"always equal to steps (which would  make it  25 different values, as in Asby's original implementation, with the default value of steps =12)"


|valuesProduced expectedNumberOfValues|

expectedNumberOfValues := uniselector steps * 2 + 1.
valuesProduced := Set new.

1000 timesRepeat: [ valuesProduced add: uniselector produceNewValue].

self assert: ( valuesProduced size = expectedNumberOfValues).</body>

<body package="Homeostat" selector="testDefaultSteps">testDefaultSteps
"always 12 to reflect  Asby's original implementation's values of 25 (12 positive, 12 negative, plus 0)"

self assert: (uniselector steps = 12).</body>

<body package="Homeostat" selector="testValueOfValuesProduced">testValueOfValuesProduced

"the values are always "


|valuesProduced  |

valuesProduced := Set new.

1000 timesRepeat: [valuesProduced add: uniselector produceNewValue].
self assert: (valuesProduced asSortedCollection first = -1).
self assert: (valuesProduced asSortedCollection last = 1).

valuesProduced do: [ :value |  value class = Fraction ifTrue: [
							    			 self assert: ((uniselector steps \\ value denominator)   = 0). "The denominator is the number of steps or a submuiltiple thereof"
							     			 self assert: (value numerator &gt;= (uniselector steps negated) and: [value numerator &lt;= uniselector steps])]
													ifFalse: [self assert: ((value = 0) or: [value abs = 1])]].</body>

<body package="Homeostat" selector="testStep">testStep
"always positive"

self assert: (uniselector steps &gt; 0).

100 timesRepeat: [ uniselector steps: (UniformDistribution from: -100 to: 100) random asInteger.
					self assert: (uniselector steps &gt;  0).]</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselectorAshbyOld new.</body>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>HomeoUniselectorAshbyTest2</class-id> <category>running</category>

<body package="Homeostat" selector="testIndependentlyRandomizedValuesMatrix">testIndependentlyRandomizedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector independentlyRandomized.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>

<body package="Homeostat" selector="testStep">testStep
"always positive"

self assert: (uniselector steps &gt; 0).

100 timesRepeat: [ uniselector steps: (UniformDistribution from: -100 to: 100) random asInteger.
					self assert: (uniselector steps &gt;  0).]</body>

<body package="Homeostat" selector="testEquallySpacedValuesMatrix">testEquallySpacedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector equallySpaced.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>

<body package="Homeostat" selector="testRandomizedValuesMatrix">testRandomizedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector randomized.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>

<body package="Homeostat" selector="testValuesWithinBounds">testValuesWithinBounds
	"checks that  the Uniselector produces values that are always between the upper and lower bounds"

	| valuesProduced outOfBounds tests |
	outOfBounds := tests := 1000.
	valuesProduced := OrderedCollection new.
	tests timesRepeat: 
			[| values |
			values := OrderedCollection new.
			uniselector unitsControlled 
				timesRepeat: [values add: uniselector produceNewValue].
			valuesProduced add: values.
			uniselector advance].



	valuesProduced do: 
			[:valuesSet | 
			valuesSet do: 
					[:value | 
					(value &gt;= uniselector lowerBound and: [value &lt;= uniselector upperBound]) 
						ifFalse: [outOfBounds := 1]]].
	self assert: outOfBounds = 1</body>

<body package="Homeostat" selector="testProduceSound">testProduceSound
"checks that  the Uniselector produces a sound when toggleBeeping is toggled."




2 timesRepeat: [uniselector produceNewValue.
				   uniselector advance].

uniselector toggleBeeping.
2 timesRepeat: [uniselector produceNewValue.
				   uniselector advance].</body>

<body package="Homeostat" selector="testDefaultSteps">testDefaultSteps
"test Asby's original implementation's value: it must be 12, because Ashby had 25 steps overall, and we assume 12 positive values, 0, and 12 negative values"

self assert: (uniselector steps = 12).</body>

<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds
"always 0 and 1"

100 timesRepeat: [ uniselector lowerBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector lowerBound = 0).
					uniselector upperBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector upperBound = 1)].

self assert: ((uniselector upperBound =1) and: [ uniselector lowerBound = 0]).</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyTest2</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselectorAshby new.</body>
</methods>


<methods>
<class-id>UI.PluggableRangeAdaptor class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="on:start:stop:grid:">on: aModel start: aStart stop: aStop grid: aGrid

| inst |

	inst := self new.
	inst model: aModel.	
	inst rangeStart: aStart.
	inst rangeStop: aStop.
	inst grid: aGrid.
	^inst</body>
</methods>


<methods>
<class-id>UI.PluggableRangeAdaptor</class-id> <category>accessing</category>

<body package="Homeostat" selector="rangeStart">rangeStart
	^rangeStart</body>

<body package="Homeostat" selector="rangeStop:">rangeStop: anObject
	rangeStop := anObject</body>

<body package="Homeostat" selector="rangeStop">rangeStop
	^rangeStop</body>

<body package="Homeostat" selector="rangeStart:">rangeStart: anObject
	rangeStart := anObject</body>
</methods>

<methods>
<class-id>UI.PluggableRangeAdaptor</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>
</methods>


<methods>
<class-id>Core.Random</class-id> <category>accessing</category>

<body package="Homeostat" selector="nextBetween:and:">nextBetween: lowerBound and: upperBound
	"Answer the next random number between the two bounds"

	| rand range|

	range:= upperBound - lowerBound.
	rand := self next.

	^  lowerBound + (rand * range) .</body>

<body package="Homeostat" selector="nextInt:">nextInt: anInteger
	"Answer a random integer in the interval [1, anInteger]."

	anInteger strictlyPositive ifFalse: [ self error: 'Range must be positive' ].
	^ (self next * anInteger) truncated + 1</body>
</methods>


<methods>
<class-id>Core.SequenceableCollection</class-id> <category>copying</category>

<body package="Homeostat" selector="shuffled">shuffled

"reproduces the same algorithm as in Squeak. Originally from Knuth, vol 2 of  The Art of COmputer Programming. See http://c2.com/cgi/wiki?LinearShuffle for a complete discussion"

"Examples:
	($A to: $Z) shuffled
"
^ self shuffledBy: (Random new).
</body>

<body package="Homeostat" selector="shuffledBy:">shuffledBy: aRandom
	| copy | 
	copy := self shallowCopy.
	copy size to: 1 by: -1 do: 
		[:i | copy swap: i with: ((1 to: i) atRandom: aRandom)].
	^ copy</body>
</methods>

<methods>
<class-id>Core.SequenceableCollection</class-id> <category>accessing</category>

<body package="Homeostat" selector="atRandom:">atRandom: aRandomGenerator
	"Answer a random element of the receiver.  Uses aGenerator which
	should be kept by the user in a variable and used every time. Use
	this instead of #atRandom for better uniformity of random numbers 
	because only you use the generator.  Causes an error if self has no 
	elements."

	^ self at: (aRandomGenerator nextInt: self size)</body>
</methods>


<methods>
<class-id>Core.String</class-id> <category>printing</category>

<body package="Homeostat" selector="printOnNoQuotes:">printOnNoQuotes: aStream 
	"Append to the argument aStream a sequence of characters that identifies the receiver.
	IT DOES NOT Print inside string quotes, doubling embedded quotes."

	1 to: self size do:
		[:i |
		(aStream nextPut: (self at: i)) == $' ifTrue: [aStream nextPut: $']].
	</body>

<body package="Homeostat" selector="printStringNoQuotes">printStringNoQuotes
	"Answer a String whose characters are a description of the receiver WITHOUT ENCLOSING QUOTES."

	| aStream |
	aStream := WriteStream on: (String new: 16).
	self printOnNoQuotes: aStream.
	^aStream contents</body>
</methods>



<initialize>
<variable-id>HomeoNoise.NoiseCalculator</variable-id>
</initialize>

<initialize>
<variable-id>HomeoUnit.DefaultParameters</variable-id>
</initialize>

<initialize>
<variable-id>HomeoUnit.Names</variable-id>
</initialize>

<initialize>
<class-id>HomeoNeedleUnit</class-id>
</initialize>

<initialize>
<class-id>HomeoUnit</class-id>
</initialize>

</st-source>
