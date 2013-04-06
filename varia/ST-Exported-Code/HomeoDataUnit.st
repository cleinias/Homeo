<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:24 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


DONE Class methods <!--<methods>
<class-id>HomeoDataUnit class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
-->
DONE <!--<body package="Homeostat" selector="newUnitFor:">newUnitFor: aHomeoUnit

"creates a new instance, reads the state from aHomeoUnit and returns it.
  This is just a convenience, but it is useful becaue it is the most common use of HomeoDataUnit"

| dataUnit |

dataUnit := super new initialize.

^dataUnit readStateFrom: aHomeoUnit.

</body>-->
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


DONE <comment>
<class-id>HomeoDataUnit</class-id>
DONE <!--<body>HomeoDataUnit holds the 'photograph' of a HomeoUnit unit at a certain time instant t. It contains a representation of all the variablle affecting the unit's functioning.
It knows how to read these values from a unit and how to print itself (in various ways) on a stream. Consistently with Ashby's, the time itself is not recorded, because we are assuming that the unit is in time always, and the data unit represents a particular splice of the unit's behavior.

Instance Variables:
	connectedTo			&lt;aDictionary&gt;	indexed by unit's name: it contains weight, switch, and state for every unit connected to.
	criticalDeviation		&lt;aNumber&gt;		the critical value of the unit at t
	maxDeviation 		&lt;anObject&gt;           the  maximum deviation of the unit
	name				&lt;aString&gt;		name of the unit
	output				&lt;aNumber&gt;		output value at t
	uniselectorState		&lt;aString&gt;		state of the unit's uniselector
	uniselectorActive         &lt;aNumber&gt;           indicates whether the uniselector is active at time t (thus potentially changing connections' weight for time t+1) 

</body>-->
</comment>

DONE Comparing<methods>
<class-id>HomeoDataUnit</class-id> <category>comparing</category>

DONE <!--<body package="Homeostat" selector="sameValuesAs:">sameValuesAs: dataUnit

"answers true if the values in the two data units are the same. It does not check the values of the connections"


^ self name = dataUnit name &amp;
self output = dataUnit output &amp;
self maxDeviation = dataUnit maxDeviation &amp;
self uniselectorState = dataUnit uniselectorState</body>-->
</methods>

DONE Initialize-release <methods>
<class-id>HomeoDataUnit</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
	connectedTo := Dictionary new.</body>-->
</methods>

DONE printing <methods>
<class-id>HomeoDataUnit</class-id> <category>printing</category>

DONE <!--<body package="Homeostat" selector="printCriticalDeviationOn:">printCriticalDeviationOn: aStream 
	"prints  just the DataUnit's criticalDeviation values on stream. Useful for graphing and compact representations."


	aStream nextPutAll: (criticalDeviation printString); cr.</body>-->

DONE <!--<body package="Homeostat" selector="printDataOn:">printDataOn: aStream 
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
	aStream nextPut: Graphics.TextConstants.CR</body>-->

DONE <!--<body package="Homeostat" selector="printEssentialVariableOn:">printEssentialVariableOn: aStream 
	"prints  just the DataUnit's output values on stream. Useful for graphing and compact representations."


	aStream nextPutAll: (output printString); cr.</body>-->

DONE <!--<body package="Homeostat" selector="printUniselectorActivatedOn:">printUniselectorActivatedOn: aStream 
	"prints  just the data about whether the DataUnit's uniselctor has been activated"


aStream nextPutAll: (uniselectorActivated printString); cr.</body>-->
</methods>

DONE Accessing <methods>
<class-id>HomeoDataUnit</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="connectedTo">connectedTo
	^connectedTo</body>-->

DONE <!--<body package="Homeostat" selector="connectedTo:">connectedTo: anObject
	connectedTo := anObject</body>-->

DONE <!--<body package="Homeostat" selector="criticalDeviation">criticalDeviation
	^criticalDeviation</body>-->

DONE <!--<body package="Homeostat" selector="criticalDeviation:">criticalDeviation: anObject
	criticalDeviation := anObject</body>-->

DONE <!--<body package="Homeostat" selector="maxDeviation">maxDeviation
	^maxDeviation</body>-->

DONE <!--<body package="Homeostat" selector="maxDeviation:">maxDeviation: anObject
	maxDeviation := anObject</body>-->

DONE <!--<body package="Homeostat" selector="name">name
	^name</body>-->

DONE <!--<body package="Homeostat" selector="name:">name: anObject
	name := anObject</body>-->

DONE <!--<body package="Homeostat" selector="output">output
	^output</body>-->

DONE <!--<body package="Homeostat" selector="output:">output: anObject
	output := anObject</body>-->

DONE <!--<body package="Homeostat" selector="readStateFrom:">readStateFrom: aHomeoUnit

"reads the fundamental variables of the unit's state from the unit itself."

name := aHomeoUnit name.
output :=aHomeoUnit currentOutput.
uniselectorState := aHomeoUnit uniselectorActive.
maxDeviation :=  aHomeoUnit maxDeviation.
criticalDeviation := aHomeoUnit criticalDeviation.
uniselectorActivated := aHomeoUnit uniselectorActivated.
aHomeoUnit inputConnections do: [ :conn | connectedTo at: (conn incomingUnit name) put: (Array with: (conn weight) with: (conn switch) with: (conn state) with: (conn noise))].</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActivated">uniselectorActivated
	^uniselectorActivated</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActivated:">uniselectorActivated: anObject
	uniselectorActivated := anObject</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorState">uniselectorState
	^uniselectorState</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorState:">uniselectorState: anObject
	uniselectorState := anObject</body>-->
</methods>

</st-source>
