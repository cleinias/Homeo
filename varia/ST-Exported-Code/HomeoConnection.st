<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:01 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoConnection class</class-id> <category>instance creation</category>

DONE <!--<body package="Homeostat" selector="incomingUnit:receivingUnit:weight:switch:noise:state:active:">incomingUnit: aUnit receivingUnit: anotherUnit weight: aWeight switch: aSwitch noise: aNoise state: aState active: anActive


^self new 
	setIncomingUnit:  aUnit 
      
	weight: aWeight 
	switch: aSwitch 
	noise: aNoise 
	state: aState 
	active: anActive.</body>-->

DONE <!--<body package="Homeostat" selector="incomingUnit:weight:switch:noise:state:active:">incomingUnit: aUnit weight: aWeight switch: aSwitch noise: aNoise state: aState active: anActive


^self new 
	setIncomingUnit:  aUnit 
	weight: aWeight 
	switch: aSwitch 
	noise: aNoise 
	state: aState 
	active: anActive.</body>-->

DONE <!--<body package="Homeostat" selector="new">new
	"creates a new connection with  initialized values"

	^ super new initialize.
	</body>-->

DONE <!--<body package="Homeostat" selector="newFrom:to:">newFrom: aHomeoUnit to: anotherUnit
	"creates a new connection with  the incoming and outgoing units "

	| conn |
	conn := super new initialize.
	conn outgoingUnit: aHomeoUnit.
	conn incomingUnit: anotherUnit.
	^conn.</body>-->
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


DONE <!--<comment>
<class-id>HomeoConnection</class-id>
<body>HomeoConnection represents a connection between two HomeoUnits and holds the incoming unit (the unit the signal is coming from), the receiving unit (the unit the signal goes to---typically the unit that is holding the connection),  the weight of the connection, and the polarity of the connection.

Instance Variables:
	incomingUnit	<HomeoUnit&gt;	the HomeoUnit the signal is coming from
	receivingUnit        <HomeoUnit&gt;        the HomeoUnit the signal is going to (typically the unit holding on to this HomeoCnnection)
	switch			<Object&gt;		polarity of the connection ( +1 or -1)
	weight			<Object&gt;		weight of the connection : between 0 and 1
	noise:			<Object&gt;		possible noise on the connection (between 0--no noise - to 1, so noisy to break the connection)
      state                 <aString&gt;                   determines whether the connection is governed by weight and switch or by the uniselector. The value can only be "manual" or "uniselector"
	status 			<aString&gt;		whether the connection is active or not. Values can be 'Yes' or 'No'
	active                <aBoolean&gt;   whether or not the connection is active
</body>
</comment>-->

<methods>
<class-id>HomeoConnection</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize

self randomizeConnectionValues</body>-->

DONE <!--<body package="Homeostat" selector="randomizeConnectionValues">randomizeConnectionValues
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
</methods>-->

<methods>
<class-id>HomeoConnection</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="activate">activate

active:= true.
self changed: #active.</body>-->

DONE <!--<body package="Homeostat" selector="active">active
	^active</body>-->

DONE <!--<body package="Homeostat" selector="active:">active: anObject
	active := anObject</body>-->

DONE <!--<body package="Homeostat" selector="disactivate">disactivate

active:= false.
self changed: #active.</body>-->

DONE <!--<body package="Homeostat" selector="incomingUnit">incomingUnit
	^incomingUnit</body>-->

DONE <!--<body package="Homeostat" selector="incomingUnit:">incomingUnit: aHomeoUnit
	"Adds the incoming unit to the connection"

	incomingUnit := aHomeoUnit.
	self changed: #incomingUnit.</body>-->

DONE <!--<body package="Homeostat" selector="newWeight:">newWeight: aWeight

	"updates weight and switch on the basis-1 >=  aWeight <= 1"

weight:= aWeight abs.
switch := aWeight sign.

self changed: #switch.
self changed: #weight.</body>
-->
<!--<body package="Homeostat" selector="noise">noise
	^noise</body>-->

<<!--body package="Homeostat" selector="noise:">noise: anObject

noise := anObject.
self changed: #noise</body>-->

DONE <!--<body package="Homeostat" selector="outgoingUnit">outgoingUnit
	^receivingUnit</body>-->

DONE <!--<body package="Homeostat" selector="outgoingUnit:">outgoingUnit: aHomeoUnit
	"Adds the receiving unit to the connection"

	outgoingUnit := aHomeoUnit.
	self changed: #outgoingUnit.</body>-->

DONE <!--<body package="Homeostat" selector="output">output
	"outputs the value of the connection times the weight, possibly switched,  and it includes  the noise. The latter is computed with the help of the HomeoNoise utility class. Several different algorithms are available, see the instance methods of HomeoNoise for details. "

| newNoise  |

newNoise := (HomeoNoise newWithCurrent: (incomingUnit currentOutput)  andNoise: noise).

newNoise normal.          "select noise as normally (Gaussian)  distributed around the value for the unit's connection noise"
newNoise distorting.    "select  noise as distorting the current"
newNoise proportional. "consider the noise on the communication line as a ration of the current being transmitted"

^ (incomingUnit currentOutput * switch * weight) + newNoise getNoise.</body>-->

DONE <!--<body package="Homeostat" selector="state">state
	^state</body>-->

DONE <!--<body package="Homeostat" selector="state:">state: aString
		
	"raise an exception if the input value is neither 'manual' or 'uniselector'"

(aString = 'manual' or: [aString = 'uniselector'] ) ifTrue: [state := aString] ifFalse: [Error raiseSignal: 'Only accepted values are: "uniselector" or "manual" '].
self changed: #state</body>-->

DONE <!--<body package="Homeostat" selector="status">status
	^status</body>-->

DONE <!--<body package="Homeostat" selector="status:">status: anObject
	status := anObject</body>-->

DONE  <!--<body package="Homeostat" selector="switch">switch
^ switch</body>-->

DONE  <!--<body package="Homeostat" selector="switch:">switch: anObject
	switch := anObject</body>-->

DONE <!--<body package="Homeostat" selector="switchToManual">switchToManual
	"changes the state of the connection to manual"

	state := 'manual'.
	self changed: #state</body>-->

DONE  <!--<body package="Homeostat" selector="switchToUniselector">switchToUniselector
	"changes the state of the connection to uniselector"

	state := 'uniselector'.
	self changed: #state</body>-->

DONE <!--<body package="Homeostat" selector="weight">weight
	^weight</body>-->

DONE <!--<body package="Homeostat" selector="weight:">weight: anObject
	
"this should not be used. The correct method is newWeight: a value, which takes care of absolute value and polarity (switch)"
weight := anObject.
self changed: #weight</body>-->
</methods>

<methods>
<class-id>HomeoConnection</class-id> <category>testing</category>

DONE <!--<body package="Homeostat" selector="isActive">isActive

^status = 'Yes'</body>-->

DONE <!--<body package="Homeostat" selector="sameAs:">sameAs: aConnection 
	"tests if two connections are the same, which means:

	- same parameters, 

	- same incoming Unit  (first level parameters only)

	Notice that since incoming units have, in turn, input connections, we cannot pursue the testing that deep because we may enter into a loop. We only check the first level parameters"

	^weight = aConnection weight and: 
			[switch = aConnection switch and: 
					[noise = aConnection noise and: 
							[state = aConnection state and: 
									[status = aConnection status 
										and: [incomingUnit sameFirstLevelParamsAs: aConnection incomingUnit]]]]]</body>-->
</methods>

<methods>
<class-id>HomeoConnection</class-id> <category>private-saving</category>

<body package="Homeostat" selector="setIncomingUnit:setOutgoingUnit:weight:switch:noise:state:active:">setIncomingUnit:  aUnit setOutgoingUnit: anotherUnit weight: aWeight switch: aSwitch noise: aNoise  state: aState active: anActive

"used by Boss for saving purposes (to recreate an instance of the class as MessageSend)"


incomingUnit :=  aUnit.
outgoingUnit := anotherUnit.
 weight := aWeight.
 switch := aSwitch.
 noise := aNoise.
 state := aState.
 active := anActive.</body>

<body package="Homeostat" selector="setIncomingUnit:weight:switch:noise:state:active:">setIncomingUnit:  aUnit weight: aWeight switch: aSwitch noise: aNoise  state: aState active: anActive

"used by Boss for saving purposes (to recreate an instance of the class as MessageSend)"


incomingUnit :=  aUnit.
 weight := aWeight.
 switch := aSwitch.
 noise := aNoise.
 state := aState.
 active := anActive.</body>
</methods>

</st-source>
