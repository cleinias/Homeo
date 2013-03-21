<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:15 am</time-stamp>


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
DONE <!--<body>HomeoUniselectorUniformRandom is a Uniselector that does NOT follow Ashby's model. It provides a random value uniformly distributed in the interval [lowerbound, upperBound], 
which is symmetric around 0, i.e. lowerbound = upperBound negated.
The default values for the interval are [-1, +1], but other values can be chosen. However, the accessors of lowerBound and upperBound enforce the constraint by refusing positive (resp. negative) values 
for lowerBound (resp. upperBound) and changing upperBound (resp. lowerBound) to the negated value of lowerBound (resp. upperBound). </body>-->
</comment>

<methods>
<class-id>HomeoUniselectorUniformRandom</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="advance">advance
"does nothing because this uniselector has no concept of an index---it produces a new uniformly distributed  random value every time it  is called "
^self</body>-->

DONE <!--<body package="Homeostat" selector="lowerBound:">lowerBound: aNumber
	"The lowerBound of the interval the uniselector value is chosen from. The interval must be symmetric around 0"

aNumber <= 0 ifTrue: [lowerBound := aNumber.
					      upperBound := lowerBound negated]
				ifFalse: [Transcript show: 'Uniselector received a wrong (positive) value for its lowerBound. Value was ignored.'; cr.].</body>
-->
DONE <!--<body package="Homeostat" selector="produceNewValue">produceNewValue
"produce a new random value uniformly distributed in the interval [lowerBoud, upperBound]"


beeps ifTrue: [Screen default ringBell].
^ (UniformDistribution from: lowerBound to: upperBound) random.</body>-->

<!--<body package="Homeostat" selector="upperBound:">upperBound: aNumber
	"The upperBound of the interval the uniselector value is chosen from. The interval must be symmetric around 0"

aNumber >= 0 ifTrue: [upperBound := aNumber.
					      lowerBound := upperBound negated]
				ifFalse: [Transcript show: 'Uniselector received a wrong (negative) value for its lowerBound. Value was ignored.'; cr].</body>
<-->/methods>

<methods>
<class-id>HomeoUniselectorUniformRandom</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

DONE <!--<body package="Homeostat" selector="setDefaults">setDefaults

"sets the defaults for the uniselector weights. Can be ovveridden by subclasses"

lowerBound := -1.
upperBound := 1.

beeps:= false.</body>-->
</methods>

</st-source>
