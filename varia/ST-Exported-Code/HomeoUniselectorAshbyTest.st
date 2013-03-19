<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 18, 2013 at 4:29:07 pm</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorAshbyTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorAshbyTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselectorAshbyOld new.</body>
</methods>

<methods>
<class-id>HomeoUniselectorAshbyTest</class-id> <category>running</category>

<body package="Homeostat" selector="testDefaultSteps">testDefaultSteps
"always 12 to reflect  Asby's original implementation's values of 25 (12 positive, 12 negative, plus 0)"

self assert: (uniselector steps = 12).</body>

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

<body package="Homeostat" selector="testStep">testStep
"always positive"

self assert: (uniselector steps > 0).

100 timesRepeat: [ uniselector steps: (UniformDistribution from: -100 to: 100) random asInteger.
					self assert: (uniselector steps >  0).]</body>

<body package="Homeostat" selector="testValueOfValuesProduced">testValueOfValuesProduced

"the values are always "


|valuesProduced  |

valuesProduced := Set new.

1000 timesRepeat: [valuesProduced add: uniselector produceNewValue].
self assert: (valuesProduced asSortedCollection first = -1).
self assert: (valuesProduced asSortedCollection last = 1).

valuesProduced do: [ :value |  value class = Fraction ifTrue: [
							    			 self assert: ((uniselector steps \\ value denominator)   = 0). "The denominator is the number of steps or a submuiltiple thereof"
							     			 self assert: (value numerator >= (uniselector steps negated) and: [value numerator &lt;= uniselector steps])]
													ifFalse: [self assert: ((value = 0) or: [value abs = 1])]].</body>
</methods>

</st-source>
