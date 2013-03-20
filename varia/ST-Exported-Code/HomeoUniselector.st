<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:04:16 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselector class</class-id> <category>instance creation</category>

USELESS<!--<body package="Homeostat" selector="new">new
	"comment stating purpose of message"

^ super new initialize</body>-->
</methods>

<methods>
<class-id>HomeoUniselector class</class-id> <category>testing class hierarchy</category>

DONE <!--<body package="Homeostat" selector="includesType:">includesType: aString

"answers true if aString represents the HomeoUniselector class or one of its subclasses"

|uniselectorClasses|

uniselectorClasses := Set new.

(HomeoUniselector withAllSubclasses) do: [:class | uniselectorClasses add: class name asString].

^uniselectorClasses includes: aString</body>-->
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<comment>
<class-id>HomeoUniselector</class-id>
DONE <!--<body>Uniselector is the abstract class for different kinds of mechanisms producing random values for the connection between two units. UniselectorAshby replicate as much as possible the original stepping mechanism described by Ashby. UniselectorRandom provides a simpler mechanism that simply produces a random value in the admitted interval. Other mechanism can be added by subclassing Uniselector and providing an alternative method produceNewValue.
 
Instance Variables:

	lowerBound           the lower bound of the weight, default is 0
	upperBound          the uperbound of the weight, default is 1
	beeps                    aBoolean that control whether the uniselector beeps when activated.
</body>-->
</comment>

<methods>
<class-id>HomeoUniselector</class-id> <category>selection-functions</category>

DONE <!--<body package="Homeostat" selector="ashbyRandom">ashbyRandom

"produces 1 of a possible 25 different values for the weight by selecting at random a 25th of the interval defined by lowerBound and upperBound "

| intervalSegment randValue sign|

intervalSegment := (upperBound - lowerBound) / 25.
randValue := ((Random new) nextBetween: 0 and: 25) rounded.
sign := ((Random new) nextBetween: -1 and: 1) rounded.

^ randValue*intervalSegment * sign.</body>-->

<body package="Homeostat" selector="simpleRandom">simpleRandom</body>
</methods>

<methods>
<class-id>HomeoUniselector</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="advance">advance

"control how to advance to the next position of the uniselector. Each subclass implements different mechanisms"
self subclassResponsibility</body>-->

DONE <!--<body package="Homeostat" selector="beeps">beeps
	^beeps</body>-->

DONE <!--<body package="Homeostat" selector="lowerBound">lowerBound
	^lowerBound</body>-->

DONE <!--<body package="Homeostat" selector="lowerBound:">lowerBound: anObject
	lowerBound := anObject</body>-->

DONE <!--<body package="Homeostat" selector="toggleBeeping">toggleBeeping
	"toggle sound"

beeps isNil
	ifFalse: [beeps:= beeps not]
	ifTrue:  [beeps := true].
self changed: #uniselectorSound</body>-->

DONE <!--<body package="Homeostat" selector="upperBound">upperBound
	^upperBound</body>-->

DONE <!--<body package="Homeostat" selector="upperBound:">upperBound: anObject
	upperBound := anObject</body>-->
</methods>

<methods>
<class-id>HomeoUniselector</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

self setDefaults.</body>-->

DONE <!--<body package="Homeostat" selector="setDefaults">setDefaults

"sets the defaults for the uniselector weights. Can be (and usually is) overidden by subclasses"

lowerBound := 0.
upperBound := 1.

beeps:= false.</body>-->
</methods>

</st-source>
