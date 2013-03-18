<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:43 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoSimulationTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoSimulationTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp

simulation := HomeoSimulation new.</body>

<body package="Homeostat" selector="tearDown">tearDown
	"ensure that homeostat is always new and initialized between successive runs, including of the same test.;"
simulation := HomeoSimulation new.</body>
</methods>

<methods>
<class-id>HomeoSimulationTest</class-id> <category>running</category>

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
	self assert: ((simulation homeostat homeoUnits at: 1) inputConnections size = 2).	 
	self assert: ((unit1 inputConnections size) = 2)</body>

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

<body package="Homeostat" selector="testAddUnit">testAddUnit

| unitsAdded| 
unitsAdded := 5.
simulation addUnit: HomeoUnit new.
self assert: (simulation homeostat homeoUnits size = 1).
unitsAdded timesRepeat:  [simulation addUnit: HomeoUnit new].
self assert: (simulation homeostat homeoUnits size = (1 + unitsAdded)).</body>

<body package="Homeostat" selector="testDataFile">testDataFile
"either the datafile exists and it is writable or it does not exist yet."

self assert: ((simulation datafile asFilename definitelyExists and: [simulation datafile asFilename definitelyExists  isWritable])
			or: [ simulation datafile asFilename definitelyExists not])</body>

<body package="Homeostat" selector="testDataFileIsPresent">testDataFileIsPresent

self assert: (simulation datafile notNil)</body>

<body package="Homeostat" selector="testReadConditionsFromFile">testReadConditionsFromFile

self assert: false.</body>

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

<body package="Homeostat" selector="testSaveToFile">testSaveToFile

self assert: false.</body>

<body package="Homeostat" selector="testStart">testStart

|simulationCycles|

4 timesRepeat: [simulation homeostat addFullyConnectedUnit: HomeoUnit new].
simulationCycles := 30.
simulation maxRuns: simulationCycles .

simulation start.  "runs for the default number of cycles"

self assert: (simulationCycles = simulation homeostat time).</body>

<body package="Homeostat" selector="testStop">testStop


|simulationCycles|

4 timesRepeat: [simulation homeostat addFullyConnectedUnit: HomeoUnit new].
simulationCycles := 1000.
simulation maxRuns: simulationCycles .

simulation start.
(Delay forMilliseconds: 100) wait.  "wait one second"
simulation stop.


self assert: ((simulationCycles = simulation homeostat time) not).</body>
</methods>

</st-source>
