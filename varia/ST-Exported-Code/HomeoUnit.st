<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 8:45:18 am</time-stamp>


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

<initialize>
<variable-id>HomeoUnit.DefaultParameters</variable-id>
</initialize>

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

<initialize>
<variable-id>HomeoUnit.Names</variable-id>
</initialize>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUnit class</class-id> <category>testing</category>

DONE <!--<body package="Homeostat" selector="defaultParameters">defaultParameters
	"returns the dictionary (shared variable) containing the default parameters of the class"

self initialize.
^DefaultParameters.</body>
</methods>-->

<methods>
<class-id>HomeoUnit class</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
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

	Names := Set new: 5.</body>-->
</methods>

DONE Instance creation<methods>
<class-id>HomeoUnit class</class-id> <category>instance creation</category>

DONE <!--<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."
	
	"self initialize. "
	^ super new initialize.</body>
</methods>-->

DONE Private-saving<methods>
<class-id>HomeoUnit class</class-id> <category>private-saving</category>

DONE <!--<body package="Homeostat" selector="name:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:outputRange:inputConnections:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">name: unitName 
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
	active: unitActive.</body>-->

DONE <!--<body package="Homeostat" selector="name:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">name: unitName viscosity: unitViscosity maxDeviation: unitMaxDeviation criticalDeviation: unitCriticalDeviation noise: unitNoise potentiometer: unitPotentiometer switch: unitSwitch uniselector: unitUniselector uniselectorTimeInterval: unitUniselectorTimeInterval uniselectorActive: unitUniselectorActive needleCompMethod: unitNeedleCompMethod active: unitActive

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
</methods>-->

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


DONE Class comments<comment>
<class-id>HomeoUnit</class-id>
DONE <!--<body>HomeoUnit represents a basic unit of Ashby's Homeostat (see Ashby's Design for a Brain, 1960, chp. 8). HomeoUnit does not know about its connections to other units (including itself). The connections are managed by class Homeostat, which holds a collection of HomeoConnection, each one representing a connection between two different HomeoUnits.

HomeoUnit holds the  values describing the state of the unit at time t, as specified by Ashby.
The design of this simulation of the Homeostat  has been influenced by the C simulation described by Alice Eldridge in "Ashby's Homeostat in Simulation," unpublished, 2002, available at: http://www.informatics.sussex.ac.uk/users/alicee/NEWSITE/ecila_files/content/papers/ACEhom.pdf 

Instance Variables:
	criticalDeviation		<Object>	deviation of the needle from equilibrium (0 state). In Ashby's original electromechanical model, this value is a function of the input 	current applied to the magnet that operates 									the needle AND the possible manual operation on the needle itself
	currentOutput		<Object>	current  the unit outputs at time t. This value is proportional to criticalDeviation and typically between 0 and 1.
	inputConnections	<OrderedCollectiont>	a collection of HomeoConnections storing the units the presents unit is connected to and the associated weights. Includes a connection to itself. 
	maxDeviation		<Object>	maximum deviation from equilibrium
	nextDeviation		<Object>	the needle's deviation the unit will assume at at t+1. This is a function of criticalDeviation, viscosity (as a dampener), and potentiometer. It is limited at both ends by maxDeviation 									(i.e. maxDeviation negated < nextDeviation < maxDeviation)
	outputRange			<Dictionary>	range of the output current, keyed as low and high. Default is 0 to 1.
	viscosity				<Object>	viscosity of the medium in which the metallic needle of the original Ashbian unit is free to move. Acts as a dampening agent on the change of output
	density:                     <Object>    the density  of the medium in which the metallic needle of the original Ashbian unit is free to move. Used to compute the drag at high velocities, if needed
	noise				<Object>	As per Ashby's implementation, it represents the noise in the transmission medium of the unit's connection to itself. In our implementation it is always identical to the noise of a unit's first 									connection 
	potentiometer 		<Object>	As per Ashby's implementation, it represents the weight of the unit's connection to itself. In our implementation it is always identical to the weight of a unit's first 									connection,---Check Design for a Brain, chp.8  for details
	switch 				<Object> 	As per Ashby's implementation, it represents the polarity of the connection of the unit to itself.  In our implementation it is always identical to the polarity of a unit's first 									connection,
	time					<integer> 	the internal tick counter
	uniselectorTime 		<Integer>       the internal tick counter for activation of the uniselector
	uniselectorTimeInterval <iInteger>   the number of ticks that specifies how often to check that the output is in range and eventually activate uniselector
	uniselector	                 <Uniselector> the uniselector that can modifiy the weights of input values coming from other units
	uniselectorActive         <Boolean>   whether the uniselector mechanism is active or not
	needleCompMethod   <String>		whether the unit's needle's displacement depends of the sum of its input, or on the ratio bettween the sum of the inputs and the maxDeviation. possible values are 'linear' and 									'proportional', default is 'linear'.
	inputTorque                 <aValue>       represents the input force derived from the weighed sum of the inputs (as computed by computeTorque)
	active 				<aString> 	whether the unit is active or not (on or off)
	status  				<aString>      Active, Non Active, or other possible status
	debugMode 			<aBoolean> controls whether the running methods print out debugging information
	showUniselectorAction <aBoolean> controls whether the running methods print out when the uniselector kicks into action
	currentVelocity:					the current velocity of the needle moving in the trough
	needleUnit 						Holds an instance of HomeoNeedleUnit, the class containing the parameters of the needle used by the unit (mass, area, etc.)

	physicalParameters    <aDictionary>     a dictionary containing equivalence factors between the simulation units and real  physicalParameters


A HomeoUnit knows how to:

- compute its next output on the basis of the input (received through connections stored in inputConnections) and its internal parameters
- add a connection with a given unit as the incoming unit
- periodically check that its outputValue has not become critical (outside the acceptable range) 
- ask the uniselector to reset che weight of its inputConnections
- print a description of itself with the values of all its parameters</body>
</comment>-->

DONE Running<methods>
<class-id>HomeoUnit</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="selfUpdate">selfUpdate
	"This is the master loop for the unit. It goes through the following sequence:
	1. compute new needle's deviation (nextDeviation (includes reading inputs))
	2. update the current output on the basis of the deviation.
	3. check whether it's time to check the essential value and if so does it and  update the counter (uniselectorTime) [this might change the weight of the connections]
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
	(uniselectorTime >= uniselectorTimeInterval and: [uniselectorActive]) 
		ifTrue: [self essentialVariableIsCritical ifTrue: [self operateUniselector.
												   uniselectorActivated := 1]]
		ifFalse: [uniselectorActivated:= 0].	      

	"4. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"
	self criticalDeviation: (self clipDeviation: nextDeviation).
	self computeOutput.
	nextDeviation := 0</body>-->
</methods>

DONE Testing<methods>
<class-id>HomeoUnit</class-id> <category>testing</category>

DONE <!--<body package="Homeostat" selector="isActive">isActive

^status = 'Active'</body>-->

DONE <!--<body package="Homeostat" selector="isConnectedTo:">isConnectedTo: aHomeoUnit 
	"tests whether there is a connection coming from aHomeoUnit"

| connectedUnits |
	
connectedUnits:= inputConnections collect: [:each | each incomingUnit].
^connectedUnits includes: aHomeoUnit.</body>-->

DONE <!--<body package="Homeostat" selector="isReadyToGo">isReadyToGo
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
		&amp; uniselectorConditions</body>-->

DONE <!--<body package="Homeostat" selector="sameAs:">sameAs: aHomeoUnit

"tests whether two units are the same, by checking (by delegating the actual checks):
1. name and other first-level parameters (potentiometer, switch, etcetera

2. the number of connections

3. the parameters of each  connection

4. the names of the connected units"


^(self sameFirstLevelParamsAs: aHomeoUnit)  and: [ self  sameConnectionsAs: aHomeoUnit]</body>-->

DONE <!--<body package="Homeostat" selector="sameConnectionsAs:">sameConnectionsAs: aHomeoUnit 
	"checks that two units have the same connections"

	| connSame |
	connSame := true.
	self inputConnections size = aHomeoUnit inputConnections size 
		ifFalse: [^false]
		ifTrue: 
			[inputConnections with: aHomeoUnit inputConnections
				do: [:conn1 :conn2 | (conn1 sameAs: conn2) ifFalse: [connSame := false]]].
	^connSame</body>-->

DONE <!--<body package="Homeostat" selector="sameFirstLevelParamsAs:">sameFirstLevelParamsAs: aHomeoUnit 
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
																						and: [status = aHomeoUnit status]]]]]]]]]]]]</body>-->
</methods>

DONE Initialize-Release<methods>
<class-id>HomeoUnit</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
	"Initialize the HomeoUnit with the default parameters found in the Class variable DefaultParameters.
	Assign a random but unique name and sets the output to some value around 0, i.e. at equilibrium
	These values are supposed to be overridden in normal practice, because the values are set  by the  simulation 
	(an an instance of HomeoSimulation or by the graphic interface)"




	| activeNames |										"generates a random name for the unit"
	activeNames := Set new.									"this is a hack to clear out unused names from the class variable Names."
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

	showUniselectorAction := false.</body>-->

DONE <!--<body package="Homeostat" selector="randomizeAllConnectionValues">randomizeAllConnectionValues
	"resets the weight, switch, and noise of all connections to random values (see HomeoConnection for details).
Does not touch the self connection of the unit to itself.  
Does not change the uniselector operation"

	2 to: (inputConnections size) 
				do: [
					:conn | 
					(inputConnections at: conn) randomizeConnectionValues]</body>-->

DONE <!--<body package="Homeostat" selector="setDefaultOutputAndDeviation">setDefaultOutputAndDeviation
	

	| randOutput |


	randOutput := Random new nextBetween: 0 and: 0.5.	"generates a random output to set the unit close to equilibrium"
	currentOutput := randOutput.

	"set the critical deviation at time 0 to 0."
	criticalDeviation := 0</body>-->

DONE <!--<body package="Homeostat" selector="setDefaultSelfConnection">setDefaultSelfConnection
	"creates the connection collection and connects the unit to itself in manual mode with a negative feedback"
	

self 
		addConnection: self
		withWeight: (self potentiometer)
		andPolarity: -1
		andNoise: 0
		andState: 'manual'</body>-->

DONE <!--<body package="Homeostat" selector="setDefaultUniselectorSettings">setDefaultUniselectorSettings
	"sets default uniselector settings."

	uniselector := HomeoUniselectorAshby new.
	uniselectorActive := true</body>-->

DONE <!--<body package="Homeostat" selector="setRandomValues">setRandomValues
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
self criticalDeviation:  (rand nextBetween: (unitRange at: 'low') and: (unitRange at: 'high')). "set the critical deviation to a random value over the whole range"</body>-->

DONE <!--<body package="Homeostat" selector="setUnitName">setUnitName
	"assigns a unique name to the unit with the help of  an auxiliary method"

name := self produceNewName.</body>-->
</methods>

<methods>
<class-id>HomeoUnit</class-id> <category>printing</category>

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

<body package="Homeostat" selector="printOn:">printOn: aStream
	"Prints a brief description of the unit for inspectors, etc"

super printOn: aStream.
aStream nextPutAll: ': ', self name.</body>
</methods>

DONE Accessing <methods>
 <class-id>HomeoUnit</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="activate">activate

active := true.
self changed: #active.</body>-->

DONE <!--<body package="Homeostat" selector="active">active
	^active</body>-->

DONE <!--<body package="Homeostat" selector="active:">active: anObject
	active := anObject.
	self changed: #active.</body>-->

DONE <!--<body package="Homeostat" selector="addConnection:withWeight:andPolarity:andNoise:andState:">addConnection: aHomeoUnit withWeight: aNumber andPolarity: aValue andNoise: aNumber2 andState: aString

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
self changed: #addConnection</body>-->

DONE <!--<body package="Homeostat" selector="addConnection:withWeight:andPolarity:andState:">addConnection: aHomeoUnit withWeight: aNumber andPolarity: aValue andState: aString

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
self changed: #addConnection</body>-->

DONE <!--<body package="Homeostat" selector="addConnectionWithRandomValues:">addConnectionWithRandomValues: aHomeoUnit 

"adds a new connection to the unit. Uses the random values (weight, noise, and polarity) selected by the initialization method of HomeoConnection.
Notice that you always connect the unit starting from the destination, i.e. from the input side, and never from the output side.
In fact units don't know anything at all about where their output goes.
If the parameters are not within the expected values, the accessor methods of HomeoConnection will raise exceptions
"

| aNewConnection| 
aNewConnection := HomeoConnection new.        "The initialize method of HomeoConnection sets random weights"
aNewConnection incomingUnit: aHomeoUnit; outgoingUnit: self.
inputConnections add: aNewConnection.
self changed: #addConnection</body>-->

DONE <!--<body package="Homeostat" selector="criticalDeviation">criticalDeviation
	^criticalDeviation</body>-->

DONE <!--<body package="Homeostat" selector="criticalDeviation:">criticalDeviation: anObject
	criticalDeviation := anObject.
	self changed: #criticalDeviation</body>-->

DONE <!--<body package="Homeostat" selector="currentOutput">currentOutput
	^currentOutput</body>-->

DONE <!--<body package="Homeostat" selector="currentOutput:">currentOutput: anObject 
	currentOutput := anObject.

	"testing
	Transcript
		show: currentOutput printString;
		cr."
"	self halt.
"
	self changed: #currentOutput</body>-->

DONE <!--<body package="Homeostat" selector="currentVelocity">currentVelocity
	^currentVelocity</body>-->

DONE <!--<body package="Homeostat" selector="currentVelocity:">currentVelocity: anObject
	currentVelocity := anObject</body>-->

DONE <!--<body package="Homeostat" selector="density">density
	^density</body>-->

DONE <!--<body package="Homeostat" selector="density:">density: anObject
	density := anObject</body>-->

DONE <!--<body package="Homeostat" selector="disactivate">disactivate

active := false.
self changed: #active.</body>-->

DONE <!--<body package="Homeostat" selector="highRange">highRange

^outputRange at: 'high'</body>-->

DONE <!--<body package="Homeostat" selector="highRange:">highRange: aValue

outputRange at: 'high' put: aValue.
self changed: #range</body>-->

DONE <!--<body package="Homeostat" selector="inputConnections">inputConnections
	^inputConnections</body>-->

DONE <!--<body package="Homeostat" selector="inputConnections:">inputConnections: anObject
	inputConnections := anObject.
	self changed:  #inputConnections</body>-->

DONE <!--<body package="Homeostat" selector="inputTorque">inputTorque
	^inputTorque</body>-->

DONE <!--<body package="Homeostat" selector="inputTorque:">inputTorque: anObject
	inputTorque := anObject</body>-->

DONE <!--<body package="Homeostat" selector="lowRange">lowRange

^outputRange at: 'low'</body>-->

DONE <!--<body package="Homeostat" selector="lowRange:">lowRange: aValue

outputRange at: 'low' put: aValue.
self changed: #range.</body>-->

DONE <!--<body package="Homeostat" selector="maxConnectedUnits:">maxConnectedUnits: anInteger

"changes the parameter to the Uniselector for the maximun number of connected units"

uniselector unitsControlled: anInteger</body>-->

DONE <!--<body package="Homeostat" selector="maxDeviation">maxDeviation
	^maxDeviation</body>-->

DONE <!--<body package="Homeostat" selector="maxDeviation:">maxDeviation: aNumber
"Max deviation is always positive, because the unit's deviation is centered around 0. Ignore negatve numbers"
	
	(aNumber > 0) 
		ifTrue: [
			maxDeviation := aNumber.
			self changed: #maxDeviation]</body>-->

DONE <!--<body package="Homeostat" selector="minDeviation">minDeviation
	"Deviation is always centered around 0. Min deviation is less than 0 and equal to maxDeviation negated."

	^maxDeviation negated</body>-->

DONE <!--<body package="Homeostat" selector="minDeviation:">minDeviation: aNumber

"Deviation is always centered around 0. Min deviation must be less than 0 and equal to maxDeviation negated. If we change the minimum we must change the maximum as well"
	(aNumber < 0) 
		ifTrue: [
			maxDeviation := aNumber negated
			self changed: #maxDeviation]</body>-->

DONE <!--<body package="Homeostat" selector="name">name
	^name</body>-->

DONE <!--<body package="Homeostat" selector="name:">name: aString
	

	(Names includes: aString) 
			ifFalse: [
  				name := aString.
				self broadcast: #changed: with: #name.].</body>-->

DONE <!--<body package="Homeostat" selector="needleCompMethod">needleCompMethod
	^needleCompMethod</body>-->

DONE <!--<body package="Homeostat" selector="needleCompMethod:">needleCompMethod: anObject
	needleCompMethod := anObject.
	self changed: #needleCompMethod</body>-->

DONE <!--<body package="Homeostat" selector="needleUnit">needleUnit
	^needleUnit</body>-->

DONE <!--<body package="Homeostat" selector="needleUnit:">needleUnit: anObject
	needleUnit := anObject</body>-->

DONE <!--<body package="Homeostat" selector="nextDeviation">nextDeviation
	^nextDeviation</body>-->

DONE <!--<body package="Homeostat" selector="nextDeviation:">nextDeviation: anObject
	nextDeviation := anObject</body>-->

DONE <!--<body package="Homeostat" selector="noise">noise
	^noise</body>-->

DONE <!--<body package="Homeostat" selector="noise:">noise: aValue 
"changes the value of the unit's internal noise. As noise must always be between 0 and 1 clip it if outside those bounds"
	

	aValue > 1
		 ifFalse: [aValue <0
			ifFalse: [noise := aValue]
			ifTrue:   [noise := 0]]
		ifTrue: [noise := 1].	

	self changed: #noise</body>-->

DONE <!--<body package="Homeostat" selector="outputRange">outputRange
	^outputRange</body>-->

DONE <!--<body package="Homeostat" selector="outputRange:">outputRange: anObject
	outputRange := anObject</body>-->

DONE <!--<body package="Homeostat" selector="potentiometer">potentiometer
	^potentiometer

</body>-->

DONE <!--<body package="Homeostat" selector="potentiometer:">potentiometer: aValue 
"changing the value of the potentiometer affects the unit's connection to itself (which is always at position 1 in the inputConnections collection)"
	potentiometer := aValue.
	(inputConnections at: 1) weight: aValue.
	self changed: #potentiometer</body>-->

DONE <!--<body package="Homeostat" selector="removeConnectionFromUnit:">removeConnectionFromUnit: aHomeoUnit 
	"removes the connection originating from  aHomeoUnit"

| collection |
collection := inputConnections copy.

collection do: [
	:each |
	each incomingUnit = aHomeoUnit ifTrue: [inputConnections  remove: each]].

self changed: #inputConnections.</body>-->

DONE <!--<body package="Homeostat" selector="status">status
	^status</body>-->

DONE <!--<body package="Homeostat" selector="status:">status: anObject
	status := anObject.
	self changed: #status</body>-->

DONE <!--<body package="Homeostat" selector="switch">switch
	^switch</body>-->

DONE <!--<body package="Homeostat" selector="switch:">switch: aNumber
	"sets the polarity of the unit's self-connection. aNumber must be either -1 or +1, otherwise method default to a positive connection (i.e. 1)
	  Notice that  changing the value of the unit's switch  affects the unit's connection to itself (which is always at 1 in the inputConnections collection)"

| accValues |
accValues := Array with: -1 with: 1.
switch :=  aNumber.

(accValues includes: aNumber)
		 ifTrue: [ (inputConnections at: 1) switch: aNumber] 
		ifFalse: [ (inputConnections at: 1) switch: 1].
self changed: #switch.</body>-->

DONE <!--<body package="Homeostat" selector="time">time
	^time</body>-->

DONE <!--<body package="Homeostat" selector="time:">time: anObject
	time := anObject</body>-->

DONE <!--<body package="Homeostat" selector="toggleDebugMode">toggleDebugMode
	"controls whether the running methods print out debug information"

	debugMode ifTrue: [debugMode := false] ifFalse: [debugMode := true]</body>-->

DONE <!--<body package="Homeostat" selector="toggleShowUniselectorAction">toggleShowUniselectorAction
	"controls whether the running methods print out when the uniselector kicks into action"

	showUniselectorAction 
		ifTrue: [showUniselectorAction := false]
		ifFalse: [showUniselectorAction := true]</body>-->

DONE <!--<body package="Homeostat" selector="uniselector">uniselector
	^uniselector</body>-->

DONE <!--<body package="Homeostat" selector="uniselector:">uniselector: anObject
	uniselector := anObject
	self changed: #uniselector</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActivated">uniselectorActivated
	^uniselectorActivated</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActivated:">uniselectorActivated: anObject
	uniselectorActivated := anObject</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActive">uniselectorActive
	^uniselectorActive</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActive:">uniselectorActive: aBoolean
	uniselectorActive := aBoolean.
	self changed: #uniselectorActive</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorChangeType:">uniselectorChangeType: uniselectorType

"switches the uniselector type of the unit"
 |uniselectorClass|

((HomeoUniselector includesType: 'HomeoUniselector', uniselectorType) or: [(HomeoUniselector includesType: uniselectorType)]) 
    ifTrue:   [uniselectorClass := Smalltalk at: uniselectorType ifAbsent: [uniselectorClass := Smalltalk at: 'HomeoUniselector', uniselectorType]].
    
uniselectorClass isNil
	ifFalse:[ uniselector := uniselectorClass new.
			 self uniselectorTime: 0.
			  self changed: #uniselector].</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorTime">uniselectorTime
	^uniselectorTime</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorTime:">uniselectorTime: anObject
	uniselectorTime := anObject.
	self changed: #uniselectorTime</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorTimeInterval">uniselectorTimeInterval
	^uniselectorTimeInterval</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorTimeInterval:">uniselectorTimeInterval: anObject
	uniselectorTimeInterval := anObject.
	self changed: #uniselectorTiming
	</body>-->

DONE  <!--<body package="Homeostat" selector="viscosity">viscosity 
	^viscosity</body>-->

DONE <!--<body package="Homeostat" selector="viscosity:">viscosity: anObject 
	viscosity := anObject.
	self changed: #viscosity</body>-->
</methods>

DONE Private-running<methods>
<class-id>HomeoUnit</class-id> <category>private-running</category>

DONE <!--<body package="Homeostat" selector="clearFutureValues">clearFutureValues
	"sets to 0 the internal values used for computing future states. "


self nextDeviation: 0.
self inputTorque: 0.
self currentOutput: 0</body>-->

DONE <!--<body package="Homeostat" selector="clipDeviation:">clipDeviation: aValue 
	"clips the unit's criticalDeviation value if it exceeds its maximum or minimum. Preserve the sign of  aValue."



	(self isNeedleWithinLimits: aValue)
			 ifTrue: [^aValue] 
			ifFalse: [^(maxDeviation * aValue sign)]</body>-->

DONE <!--<body package="Homeostat" selector="computeNextDeviation">computeNextDeviation
	"Computes the output current at time t+1 on the basis of the current input and the various parameters
	  this basic function mimicks Asbhy's original device by the following procedure:

	1. Try to move the needle to a new position (on the basis of  the input values computed by computeTorque) 
	     (the details of this operation are in method HomeoUnit >> newNeedlePosition: aValue and in HomeoUnit>>computeTorque
	 2. clip value if it is outside maxRange
	 3. put new value in criticalDeviation

	One possibility would have been  to use a minimal function like the one used by A Eldridge in her simulation (see Eldridge 2000, p.20): 
	nextOutput := (input(j) * weight(j) * ) + noise           (with j ranging over  all units connected to the current unit)

	This approach simplifies considerably the simulation, but has the disadvantage of  reducing the role of the unit to nil. In fact, all the work  (in Eldridge's simulation)  is done by the system, which reads, for every tick of time, the outputs from the various connected units, computes new outputs, and updates the units. In other words, this approach reduces the homeostat's units to simple data structures (which is literally what they are in her C program), deprived of any possiblity of 'action', i.e. of any behavior. Our approach here will be different, by allowing a partial separation between homeostat, units, and connections. It follows that the computation of the unit's next value is internal to unit itself, even if it considers  values (obtained from inputConnections) that may have been deposited from the outside. 
	This approach allows the possibilty that different units may have different behaviors, etc. and it also allows for the possibility of having the units being operated upon by means other than the input  coming from other homeoUnits. For instance, input coming directly from the environment, like the direct manipulation of the needles. It also forces the simulation to provide a closer resemblance of Ashby's original electro-mechanical device. Furthermore, Eldridge's simple approach can be easily recovered by reducing the computation of the unit's next output to the sum of values stored in inputConnections, and by setting the range of the needles' deviation (maxDeviation) to 1. In short: Eldridge's model as reimplemented here would have the following method: 
HomeoUnit>>computeNextOuput 
nextOutput := inputsCollection inject: 0 into: [ :tempSum :conn | tempSum + conn output]

Our method is close to hers and basically reduces to this behavior when all the parameters specific to the unit are ininfluent. That is, when: noise = 0, viscosity = 0, and  there is no direct outside influence. Nonetheless, encapsulating the computation inside the unit allows for a much more flexible system that can be easily extended to encompass more sophisticated behavior."
	
	"first update the current value of critical deviation with the unit's internal noise"
	self updateDeviationWithNoise.
	" then update the deviation"
	nextDeviation  := self newNeedlePosition: self computeTorque.</body>-->

DONE <!--<body package="Homeostat" selector="computeOutput">computeOutput
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
			[out > 0 
				ifTrue: [self currentOutput: (outputRange at: 'high')]
				ifFalse: [self currentOutput: (outputRange at: 'low')]]</body>-->

DONE <!--<body package="Homeostat" selector="computeTorque">computeTorque
	
" In order to closely simulate Asbhy's implementation, computeTorque would have to compute the torque affecting the needle by solving a set of differential equations whose coefficients represents the weighted values of the input connections. This is the approach followed by Capehart (1967) in his simulaton of the Homeostat in Fortran. See the comment to the method newNeedlePosition for a discussion.
Here we simply compute the sum of the weighted input values extracted from  the inputsCollection on all the connections that are active"
| activeConnections |

activeConnections := inputConnections select: [:each | (each isActive) and: [ each incomingUnit isActive]].


inputTorque := activeConnections inject: 0 into: [ :tempSum :conn | 
								tempSum + (conn  output)].
"Testing"
debugMode ifTrue: [ Transcript show: 'current torque at time: ';  show: time printString; show: ' for unit: '; show: self name; show: ' is ' ; show: inputTorque printString; cr.].

self changed: #inputTorque.

^inputTorque</body>-->

DONE <!--<body package="Homeostat" selector="essentialVariableIsCritical">essentialVariableIsCritical

"Checks if the next output is critical, i.e. too close to the limit of the  acceptable range, stored in maxDeviation."

| allowedRange |


allowedRange := maxDeviation * 0.9.

^ (nextDeviation between: (allowedRange negated) and: allowedRange) not</body>-->

DONE <!--<body package="Homeostat" selector="isNeedleWithinLimits:">isNeedleWithinLimits: aValue
	"Checks whether the proposed value exceeds the unit's range (both + and -)"

	^aValue between:  (maxDeviation negated) and: maxDeviation.</body>-->

DONE <!--<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
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
	^criticalDeviation + newVelocity	" In an Aristotelian model, new displacement is old displacement plus velocity: x = x0 + vt, with t obviously = 1 in our case."</body>-->

DONE <!--<body package="Homeostat" selector="newNeedlePosition:">newNeedlePosition: aTorqueValue 
	"computes the new needle position on the basis of aTorqueValue, which represents the torque applied to the unit's needle. This method is marquedly different from Ashby's implementation, even if it captures its intent. A longer discussion is appended  below."

	needleCompMethod = 'linear' 
		ifTrue: [^self newLinearNeedlePosition: aTorqueValue]
		ifFalse: [ (needleCompMethod = 'proportional')
					ifTrue: [^self newProportionalNeedlePosition: aTorqueValue]
					ifFalse: [^self newRandomNeedlePosition]]       "defaults to a random computation method if the method is not specified"

        "In Asbhy's original implementation, each incoming connection corresponded to a coil 
        around the unit's magnet. The sum of the input currents flowing through the coils produced  
        a torque on the magnet, which, in turn, moved the needle in the trough.
        In order to closely simulate Asbhy's implementation, newNeedlePosition would have 
        to compute the torque affecting the needle by solving a set of differential equations 
        whose coefficients represent the weighted values of the input connections. This is 
        the approach followed by Capehart (1967) in his simulaton of the Homeostat in Fortran.
        
        However, it seems pointless to use differential equations to model a physical mechanism 
        which was originally devised to model a physiological system. After all, as Capehart 
        himself acknowledges, the Homeostat is a kind of analogue computer set up to compute 
        the fundamental features of the system it models.. We might as well use a different 
        kind of computer, assuming we are able to capture the essential features as accurately. 
        In this respect, we follow Ashby's suggestion that 'the torque on the magnet 
        [ i.e. the needle] is approximately proportional to the algebraic sum of the currents 
        in A, B, and C' (Ashby 1960:102, sec 8/2), where the coils A, B, C, (and D, i.e. 
        the unit itself) carry a current equal to the weighted input. Thus, this method 
        produces a value that is proportional to the inputValue.
        
        However,  it might be argued (for instance by a dynamic system theorist) that 
        a thoroughly digital simulation of the Homeostat like this one loses what is 
        most essential to it: the continuity of real-valued variables operating in 
        real time. Anyone accepting this objection may partially meet it by:
        
        1. subclassing HomeoUnit, 
        2. adding a method that produces differential equation describing the Torque
        3. and replacing the two methods computeTorque and newNeedlePosition: aTorqueValue 
        with numeric computations of the solutions of the diff equations.
        
        See Ashby, Design for a Brain, chps. 19-22 for a mathematical treatment of the 
        Homeostat and Capehart 1967 for suggestions on a possible implementation 
        (which requires a Runge-Kutta diff solution routine or equivalent and 
        Hutwitz convergence test on the coefficient matrix
        
        Our method(s) assumes:
        
        1. that the torque is simply the sum of the input connections, hence a value 
        included in +/-  (inputConnections size) (since the max value of any unit's output 
        and hence  of any input,  is 1 and the minimum  -1)
        
        2. the torque represents the force that displaces the needle from its current position. 
        The value of this displacement is obviously directly proportional to the force. 
        However, the constant of proportionality is important: if the displacement is 
        simply equal to the torque, which, in turn, is equal to the sum of inputs, 
        then the ***potential displacement*** grows linearly with the connected units. 
        If, instead, the displacement is equal to the ratio between the maximum torque 
        and the maximum deviation, then the ***potential displacement*** is independent 
        from the number of connected units and will depend more directly on the values of 
        the incoming units rather than their number. It is obvious that the behavior of a 
        collection of units, i.e. a homeostat, will be different in either case. Ashby's 
        probably followed the former model, as evidenced by his (widely reported) comments 
        about the direct relation between instability and number of units (see also 
        Capehart 1967 for comments to the same effect). 
        It must be admitted, however, that a careful manipulation of the weights of the 
        connection may reduce the difference between the two methods: one would have to 
        uniformly reduce the weights whenever a new conenction is added to transform the 
        first ('Ashby's') approach into the second.
        
        In order to allow experimentation with either approach, we include both methods: 
        HomeoUnit().newLinearNeedlePosition and HomeoUnit().newProportionalNeedlePosition
        The choice between the two is determined by the value of the instance variable 
        needleCompMethod. Default (stored in the class variable) is linear.
        
        The viscosity is between 0 and 1, with 0 being the maximum (needle unable to move) 
        and 1 being the minimum (no effect on movement)"</body>-->
        
DONE <!--<body package="Homeostat" selector="newProportionalNeedlePosition:">newProportionalNeedlePosition: aValue 
        	"see method newNeedlePosition for an extended comment on how to compute the displacement of the needle"

	| torque |
	torque := aValue / (maxDeviation *2).
	^criticalDeviation + (torque * viscosity)</body>-->

DONE <!--<body package="Homeostat" selector="newRandomNeedlePosition">newRandomNeedlePosition
	"computes a random value for the needle position within the accepted range "

	^ (UniformDistribution from: (self minDeviation) to: (self maxDeviation)) random.</body>-->

DONE <!--<body package="Homeostat" selector="operateUniselector">operateUniselector
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
				cr].]</body>-->

DONE <!--<body package="Homeostat" selector="physicalVelocity">physicalVelocity
	"convert the velocity of the unit into a value expressed in physical units (m/s) according to the physical equivalence parameters"


^currentVelocity * (physicalParameters at: 'lengthEquivalence') / (physicalParameters at: 'timeEquivalence')</body>-->

DONE <!--<body package="Homeostat" selector="produceNewName">produceNewName
	"produces a name made up of  'Unit'  plus an integer representing the current number  of existing units plus 1"


^ 'Unit', (self class allInstances size + 1) printString.
</body>-->

DONE <!--<body package="Homeostat" selector="updateDeviationWithNoise">updateDeviationWithNoise
	"apply the unit's internal noise to the critical deviation and update accordingly.  Computation of noise uses the utility HomeoNoise class"	
| newNoise |

	newNoise := HomeoNoise newWithCurrent: criticalDeviation andNoise: noise.
	newNoise distorting.	"since the noise is a distortion randomly select either a positive or negative value for noise"
	newNoise normal.	"compute a value for noise by choosing a normally distributed random value centered around 0."
	newNoise proportional.	"consider noise as the ration of the current affected by noise"
	criticalDeviation := criticalDeviation + newNoise getNoise.	"apply the noise to the critical deviation value"</body>-->

DONE <!--<body package="Homeostat" selector="updateTime">updateTime

""

"Do nothing. In the current model, time is updated by the homeostat, the homeounit are basically computing machine with no knowledge of time"

^self</body>-->

DONE <!--<body package="Homeostat" selector="updateUniselectorTime">updateUniselectorTime

"updates the tick counter fore the uniselector"

uniselectorTime := uniselectorTime + 1.</body>-->
</methods>

DONE Private-saving<methods>
<class-id>HomeoUnit</class-id> <category>private-saving</category>

USELESS <!--<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename

"bosses itself out on a file opened on aFilename. It will erase the old content of aFilename."

| boss |
boss := BinaryObjectStorage onNew: aFilename writeStream.
[boss nextPut: self]
	ensure: [boss close].</body>-->

DONE <!--<body package="Homeostat" selector="setName:viscosity:maxDeviation:criticalDeviation:noise:potentiometer:switch:outputRange:inputConnections:uniselector:uniselectorTimeInterval:uniselectorActive:needleCompMethod:active:">setName:  unitName viscosity: unitViscosity maxDeviation: unitMaxDeviation criticalDeviation: unitCriticalDeviation noise: unitNoise potentiometer: unitPotentiometer switch: unitSwitch outputRange: unitOutputRange inputConnections: unitInputConnections uniselector: unitUniselector uniselectorTimeInterval: unitUniselectorTimeInterval uniselectorActive: unitUniselectorActive needleCompMethod: unitNeedleCompMethod active: unitActive

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

			</body>-->
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

<initialize>
<class-id>HomeoUnit</class-id>
</initialize>

</st-source>
