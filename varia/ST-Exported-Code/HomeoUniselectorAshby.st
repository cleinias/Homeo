<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:04:29 am</time-stamp>


<class>
<name>HomeoUniselectorAshby</name>
<environment>Smalltalk</environment>
<super>HomeoUniselector</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unitIndex ashbyKind interval steps index matrix unitsControlled </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<comment>
<class-id>HomeoUniselectorAshby</class-id>
DONE <!--<body>HomeoUniselectorAshby2 is a different implementation of Ashby's (sparsely decribed!) algorithm.  It simulates a stepping switch (or Uniselector) that advances one step every time it is activated. At every step the uniselector produces weight values for the HomeoUnits connections. The simulation is implemented  with a m x n matrix (the ivar matrix) where m are the steps of the uniselector, and n are the number of connected units. In Ashby's classical homeostat m= 25, n = 3.  The values in the matrix are produced according to three different algorithms, each a different intepretation of Ashby's original idea. the string deciding which production method to use is held in ashbyKind.

Instance Variables:
	unitsControlled <anInteger>	   The maximum number of units this uniselector controls. Default values is 10. It will be incremented in 10-units increment if needed
	unitIndex       <anInteger>        The index keeping track of which unit's connection we are currently producing a value (a weight) for.
	ashbyKind       <aString>          The string determining which initialization (and re-initialization) method to use.
	unitIndex
	interval
	steps		<anInteger>	   The number of possible steps in the Uniselector (default is 12, as per Ashby's implementation)
	index		<anInteger>	   The index keeping track of which row of weight we should output next
	matrix		<aMatrix>	   A matrix of size (unitsControlled x steps) holding all the possible weights-->

</body>
</comment>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="advance">advance

"advance the uniselector to the next position."
(index = (matrix numberOfRows)) ifTrue: [index := 1 ]
				                 ifFalse: [index := index + 1].
unitIndex := 0.</body>-->

DONE <!--<body package="Homeostat" selector="ashbyKind">ashbyKind
	^ashbyKind</body>-->

DONE <!--<body package="Homeostat" selector="equallySpaced">equallySpaced
	"set initialization procedure to equally spaced values )see method produceEquallySapcedValues for details"

ashbyKind := 'EquallySpacedValues'</body>-->

DONE <!--<body package="Homeostat" selector="independentlyRandomized">independentlyRandomized
	"set initialization procedure to independentely randomized  values (see method produceIndependentlyRandomizedValues for details)"

ashbyKind := 'IndependentlyRandomizedValues'</body>-->

DONE<!--<body package="Homeostat" selector="lowerBound:">lowerBound: aNumber

"Do nothing, lowerBound is always 0."

^self.</body>-->

DONE<!--<body package="Homeostat" selector="produceNewValue">produceNewValue

"returns the weight for the next connection and advances the unitIndex"
unitIndex + 1 > unitsControlled
			 ifFalse: [beeps
					  ifTrue: [Screen default ringBell].
					  unitIndex := unitIndex + 1.
					 ^matrix rowAt: index columnAt: unitIndex]
			 ifTrue: [Error raiseSignal: 'Too many units for the uniselector to control'].</body>-->

DONE <!--<body package="Homeostat" selector="randomized">randomized
	"set initialization procedure to  randomized  values (see method produceRandomizedValues for details)"

ashbyKind := 'RandomizedValues'</body>-->

<body package="Homeostat" selector="sequence">sequence
	^matrix</body>

<body package="Homeostat" selector="sequence:">sequence: anObject
	matrix := anObject</body>

DONE <!--<body package="Homeostat" selector="steps">steps
	^steps</body>-->

DONE<!--<body package="Homeostat" selector="steps:">steps: aPositiveNumber

"Must always be an integer > 0" 

aPositiveNumber > 0 ifTrue: [steps := aPositiveNumber asInteger]</body>-->

DONE <!--<body package="Homeostat" selector="unitsControlled">unitsControlled
	^unitsControlled</body>-->

DONE <!--<body package="Homeostat" selector="unitsControlled:">unitsControlled: aNumber

"The uniselector is initialized to control 10 maximum connections and it initializes its transition matrix (sequence) accordingly. When the required number of max connections increases, it goes up in 10 units step increments and produces a new transition matrix."

aNumber > unitsControlled 
		ifTrue: [unitsControlled := unitsControlled + 10].
self produceSequence.</body>-->

DONE <!--<body package="Homeostat" selector="upperBound:">upperBound: aNumber

"Do nothing, upperBound is always 1"

^self.</body>-->
</methods>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
		" initializes the interval and the steps to default values. The lowerBound and upperBound are always 0 and 1, as per Ashby's implementation, because they represent the fraction of the input to reach the unit (sse Design for a Brain sec 8/2, p. 102 (1960 ed.)"
   
	lowerBound := 0.
	upperBound:= 1.
	self setDefaults.
	index := 1.
	steps := 12.
	unitsControlled := 10.
	unitIndex := 0.
	ashbyKind := 'RandomizedValues'.
	self produceSequence</body>-->
</methods>

DONE <methods>
<class-id>HomeoUniselectorAshby</class-id> <category>private</category>

DONE <!--<body package="Homeostat" selector="produceEquallySpacedValues">produceEquallySpacedValues

"produces a m x n Matrix, where m = number of equally spaced values (default = 25), n = maximum number of units controlled by the Uniselector."

| spacedValues tempSeq |

tempSeq := Array new: unitsControlled.
spacedValues := OrderedCollection new.
spacedValues add: 0.
1 to: steps do: [:i | spacedValues add: i * interval.
			       spacedValues add: i * interval * -1].	
1 to: unitsControlled 
		do: [:i  |  tempSeq at: 1 put:  (spacedValues copy shuffled) asArray].

matrix := (Matrix rows: tempSeq) transpose.</body>-->

DONE <!--<body package="Homeostat" selector="produceIndependentRandomizedValues">produceIndependentRandomizedValues

"produces a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25), n = maximum number of units controlled by the Uniselector. Notice that in this implementation, all connections have ***different***  random values. This DOES NOT seem to capture the original homeostat, where random values were implemented in hardware and could not be changed. Initializing the uniselector with produceRandomized Sequence, on the other hand, produces a matrix in which all rows (connections) share the same  random values"

| rows row |

rows :=  Array new: ((steps *2 ) + 1).
1 to: ((steps * 2) + 1) 
	do: [:r |
		row:= Array new: unitsControlled.
		1 to: unitsControlled 
			do: [ :c | 
				 row at: c put: ((UniformDistribution from: -1 to: 1) random)].
		rows at: r put: row].
	       
matrix := (Matrix rows: rows).</body>-->

DONE<!--<body package="Homeostat" selector="produceRandomizedValues">produceRandomizedValues

"produces a m x n Matrix, where m = number of  uniformly distributed random values  (default = 25), n = maximum number of units controlled by the Uniselector. Notice that in this implementation, all connections share the same space of 25 random values, although they go through them in a different sequence. This seems to capture (one of the interpretations) of the original homeostat, where random values were implemented in hardware and could not be changed. Initializing the uniselector with produceIndependentRandomized Sequence, on the othe4r hand, produces a matrix in which all rows have (a highly likelihood of being) completely different values"

| randomValues tempSeq |

tempSeq := Array new: unitsControlled.
randomValues:= OrderedCollection new.
1 to: ((steps *2 ) + 1)  do: [:i | randomValues add: (UniformDistribution from: -1 to: 1) random].	
1 to: unitsControlled 
		do: [:i  |  tempSeq at: i put:  (randomValues shuffled) asArray].

matrix := (Matrix rows: tempSeq) transpose.</body>-->

DONE <!--<body package="Homeostat" selector="produceSequence">produceSequence

"produces the matrix containing the values for the uniselector switch according to the kind of Ashby uniselector specified in ashbyKind"

self perform: ('produce',ashbyKind) asSymbol.</body>-->
</methods>

<methods>
<class-id>HomeoUniselectorAshby</class-id> <category>testing</category>

DONE <!--<body package="Homeostat" selector="sameAs:">sameAs: aUniselector 
	

		self class = aUniselector class 
			ifFalse: [^false] 
			ifTrue: [
				^(ashbyKind = aUniselector ashbyKind) 					                  "uniselectors have same ashby kind"
					and: [(self sequence  - aUniselector sequence) isZero]].			"and Transition matrices are the same"</body>-->

DONE <!--<body package="Homeostat" selector="sameKindAs:">sameKindAs: aUniselector 
	

		self class = aUniselector class 
			ifFalse: [^false] 
			ifTrue: [
				^ashbyKind = aUniselector ashbyKind   ]</body>-->
</methods>

</st-source>
