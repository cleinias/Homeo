<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:53 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeostatTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeostatTest</class-id> <category>running</category>

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

<body package="Homeostat" selector="testAddUnit">testAddUnit

| unit1 |
unit1 := HomeoUnit new.
"test adding a new unit"
homeostat addUnit: unit1.
self assert: (homeostat hasUnit: unit1).

"test adding an already exisitng unit"
homeostat addUnit: unit1.
self assert: ((homeostat homeoUnits size) = 1).</body>

<body package="Homeostat" selector="testBossOutHomeostat">testBossOutHomeostat
	"comment stating purpose of message"



	| boss newHomeostat  filename |
	filename := 'pippo.unit' asFilename.
	
	homeostat  bossOutOn: filename. 

	boss :=  BinaryObjectStorage onOldNoScan: filename readStream.
	newHomeostat:= boss next.
	boss close.

	self assert: (homeostat sameAs: newHomeostat ).</body>

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

<body package="Homeostat" selector="testRemoveUnit">testRemoveUnit

| unit1 | 
unit1 := HomeoUnit new.

"teat remove an existinng unit"

homeostat addUnit: unit1.
homeostat removeUnit: unit1.
self deny: (homeostat hasUnit: unit1).

"test removing a non existing unit"

self shouldnt: [homeostat removeUnit: unit1] raise: (Error).</body>

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

<body package="Homeostat" selector="testSameAs">testSameAs


| anotherHomeostat |

anotherHomeostat := homeostat copy.

self assert: (homeostat sameAs: anotherHomeostat)</body>

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

<body package="Homeostat" selector="testStop">testStop


self assert: false.</body>
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

</st-source>
