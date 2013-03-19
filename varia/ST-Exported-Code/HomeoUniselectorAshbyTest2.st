<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 18, 2013 at 4:28:45 pm</time-stamp>


<class>
<name>HomeoUniselectorAshbyTest2</name>
<environment>Smalltalk</environment>
<super>HomeoUniselectorAshbyTest</super>
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

<methods>
<class-id>HomeoUniselectorAshbyTest2</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="testDefaultSteps">testDefaultSteps
"test Asby's original implementation's value: it must be 12, because Ashby had 25 steps overall, and we assume 12 positive values, 0, and 12 negative values"

self assert: (uniselector steps = 12).</body>-->

DONE <!--<body package="Homeostat" selector="testEquallySpacedValuesMatrix">testEquallySpacedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector equallySpaced.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>-->

DONE <!--<body package="Homeostat" selector="testIndependentlyRandomizedValuesMatrix">testIndependentlyRandomizedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector independentlyRandomized.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>-->

DONE <!--<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds
"always 0 and 1"

100 timesRepeat: [ uniselector lowerBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector lowerBound = 0).
					uniselector upperBound: (UniformDistribution from: -10 to: 10) random.
					self assert: (uniselector upperBound = 1)].

self assert: ((uniselector upperBound =1) and: [ uniselector lowerBound = 0]).</body>-->

DONE <!--<body package="Homeostat" selector="testProduceSound">testProduceSound
"checks that  the Uniselector produces a sound when toggleBeeping is toggled."




2 timesRepeat: [uniselector produceNewValue.
				   uniselector advance].

uniselector toggleBeeping.
2 timesRepeat: [uniselector produceNewValue.
				   uniselector advance].</body>-->

DONE <!--<body package="Homeostat" selector="testRandomizedValuesMatrix">testRandomizedValuesMatrix
"checks that  the Uniselector produces a number of different sets of value equal to uniselector steps (which would  be  25 different sets of values, as in Ashby's original implementation, with the default value of steps)"


|valuesProduced expectedNumberOfValues|

uniselector randomized.
expectedNumberOfValues :=(uniselector steps * 2 ) + 1 .
valuesProduced :=  OrderedCollection new.

1000 timesRepeat: [| values | values :=  OrderedCollection new.
   					  uniselector unitsControlled  timesRepeat: [values add: uniselector produceNewValue.]. 
					  valuesProduced add: values.
					 uniselector advance].

self assert: (valuesProduced asSet size = expectedNumberOfValues).
valuesProduced do: 
			[ :values |
			 "self assert: (values asSet size = values size)."               " Values for different units cannot (necessarily)  be all
																	         different, because there are only 25 possible random values
																		    (see comments to produceRandomizedSequence for more comments" 
                   self assert: (values size = uniselector unitsControlled)].</body>-->

DONE <!--<body package="Homeostat" selector="testStep">testStep
"always positive"

self assert: (uniselector steps > 0).

100 timesRepeat: [ uniselector steps: (UniformDistribution from: -100 to: 100) random asInteger.
					self assert: (uniselector steps >  0).]</body>-->

DONE <!--<body package="Homeostat" selector="testValuesWithinBounds">testValuesWithinBounds
	"checks that  the Uniselector produces values that are always between the upper and lower bounds"

	| valuesProduced outOfBounds tests |
	outOfBounds := tests := 1000.
	valuesProduced := OrderedCollection new.
	tests timesRepeat: 
			[| values |
			values := OrderedCollection new.
			uniselector unitsControlled 
				timesRepeat: [values add: uniselector produceNewValue].
			valuesProduced add: values.
			uniselector advance].



	valuesProduced do: 
			[:valuesSet | 
			valuesSet do: 
					[:value | 
					(value >= uniselector lowerBound and: [value <= uniselector upperBound]) 
						ifFalse: [outOfBounds := 1]]].
	self assert: outOfBounds = 1</body>-->
</methods>

<methods>
<class-id>HomeoUniselectorAshbyTest2</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselectorAshby new.</body>-->
</methods>

</st-source>
