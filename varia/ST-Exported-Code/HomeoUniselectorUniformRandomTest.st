<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:18 am</time-stamp>


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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorUniformRandomTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorUniformRandomTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp

uniselector := HomeoUniselectorUniformRandom new.</body>
</methods>

<methods>
<class-id>HomeoUniselectorUniformRandomTest</class-id> <category>running</category>

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

<body package="Homeostat" selector="testValueWithinIntervalBounds">testValueWithinIntervalBounds

| sortedValues tests|

tests:= 1000.

sortedValues := SortedCollection new.

tests timesRepeat:  [sortedValues add:  uniselector produceNewValue.].

self assert: (sortedValues last &lt;= uniselector upperBound).
self assert: (sortedValues first &gt;= uniselector lowerBound).</body>
</methods>

</st-source>
