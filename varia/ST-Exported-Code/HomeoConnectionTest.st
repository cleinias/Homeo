<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:06 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoConnectionTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoConnectionTest</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="testAddConnection">testAddConnection

self assert: ((connection incomingUnit) = unit1).</body>-->

DONE <!--<body package="Homeostat" selector="testDefaults">testDefaults
	"comment stating purpose of message"

	self assert: ((connection weight) between: 0 and: 1).
	self assert: ((connection noise) between: 0 and: 0.1).
	self assert: ((connection switch) notNil).</body>-->

DONE <!--<body package="Homeostat" selector="testSameAs">testSameAs

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

self deny: (connection sameAs: connection2).</body>-->

DONE <!--<body package="Homeostat" selector="testState">testState

"test default state of the connection  units" 
self assert: ((connection state) = 'uniselector'). 

"switching from manual to uniselector and back"

connection switchToUniselector.
self assert: ((connection state) = 'uniselector').

connection switchToManual.
self assert: ((connection state) = 'manual').</body>-->

DONE <!--<body package="Homeostat" selector="testValueOfState">testValueOfState
	""

self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

connection state: 'manual'.
self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

connection state: 'uniselector'.
self assert: (((connection state) = 'manual') or: [(connection state) = 'uniselector']).

self should: [connection state:  'wrongValue']  raise: Error.</body>-->

DONE <!--<body package="Homeostat" selector="testWeight">testWeight


	| outputWeighed  inputUnit errorTolerance noiseLevel|
	noiseLevel := 0.1.
	errorTolerance := 0.00001.
	outputWeighed := connection output.
	inputUnit := connection incomingUnit.
	connection noise: 0.                               "eliminate noise"
	self assert: (outputWeighed -
				 (inputUnit currentOutput * connection weight * connection switch - connection noise) < errorTolerance).

	"accounting for noise"
	connection noise: noiseLevel.                               "set noise"
	
	"the differnece between the weighed connection output and the unit's value is at most equal to noise (plus the tolerance"
	self assert: ((outputWeighed -
				 (inputUnit currentOutput * connection weight * connection switch - connection noise)) abs < (noiseLevel + errorTolerance)).</body>-->
</methods>

<methods>
<class-id>HomeoConnectionTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

DONE <!--<body package="Homeostat" selector="setUp">setUp
	"comment stating purpose of message"

	unit1 := HomeoUnit new.
	unit1 selfUpdate.              "allows the unit to have some values in its slots"
	connection := HomeoConnection new.
	connection incomingUnit: unit1.</body>-->
</methods>

</st-source>
