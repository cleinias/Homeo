<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:34 am</time-stamp>


<class>
<name>HomeoNoise</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>current noise mode distribution ratio randomGen </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<shared-variable>
<name>NoiseCalculator</name>
<environment>HomeoNoise</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<initializer></initializer>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>

<initialize>
<variable-id>HomeoNoise.NoiseCalculator</variable-id>
</initialize>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoNoise class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."


	NoiseCalculator isNil ifTrue: [
		NoiseCalculator := super new initialize].

	^NoiseCalculator			
</body>

<body package="Homeostat" selector="newWithCurrent:andNoise:">newWithCurrent: aNumber andNoise: anotherNumber
	"Answer a newly created and initialized instance."


	NoiseCalculator isNil ifTrue: [
		NoiseCalculator := super new initialize].
		
		NoiseCalculator current: aNumber.
		NoiseCalculator noise: anotherNumber.

	^NoiseCalculator

</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


DONE <!--<comment>
<class-id>HomeoNoise</class-id>
<body><!--HomeoNoise is a utility class that provides different algorithms to deal with the computation of how noise affects the transmission of current between units 
and the flicker noise  that may affect the units' internal values. 

Instance variables:

current       <aNumber>    The value of the current affected by the noise
noise         <aNumber>     The value of the noise affecting the transmission of the current. This value is typically between 0 (no noise) and 1 (channel so noisy to block communication)
mode          <aString>       Mode of the noise. Possible values: 'distorting' 'degrading', indicates how the noise affects the currentWhether the noise is a		
distribution  <aString>		Probability distribution of the actual noise with respect to the noise value. Possible values: 'constant', 'uniform', 'normal'
ratio 		 <aString>        Ratio of the noise to the affected current. Possible values: 'linear' 'proportional'

It is a singleton class,  its unique instance being held in class variable NoiseCalculator. The only class creation method is newWithCurrent: andNoise: which simply updates the values of 
the instance variables if the unique instance exists already.

The noise-computing algorithm is selected by changing the valies of the three iVars mode, distribution, and ration, and then calling the method getNoise. This method constructs a selector string from the values of the ivar and calls the corresponding method. -->

</body>
</comment>-->

DONE <!--<methods>
<class-id>HomeoNoise</class-id> <category>initialize-release</category>-->

DONE <!--<body package="Homeostat" selector="initialize">initialize
	"Initialize the NoiceCalculator to a current of 1 and noise of 0, representing a full current and no noise. These values are typically overriden by class creation methods."


	current := 1.
	noise := 0.

"default values for noise parameters"
	mode := 'Distorting'.
	distribution := 'Normal'.
	ratio := 'Proportional'.

"add the random number generator"

randomGen := Random new.
	^self</body>-->
<!--</methods>-->

<methods>
<class-id>HomeoNoise</class-id> <category>constant noise algorithms</category>

<body package="Homeostat" selector="constDegradLinearNoise">constDegradLinearNoise
	"Returns a value representing a constant degrading noise affecting linearly  the current .
	 Assumes noise is a value between 0 and 1"

 | sign |

sign := current sign.

sign = 0 ifTrue: [sign := 1].   "make sure we don't lose the current when noise is 0"

^((current abs) - noise) * sign</body>

<body package="Homeostat" selector="constDegradPropNoise">constDegradPropNoise
	"Returns a value representing a constant degrading noise affecting the current proportionally. Assumes noise is a value between 0 and 1, i. e. the percentage of current lost to noise"

	| sign |

	sign := current sign.
	sign = 0 ifTrue: [sign := 1].   "make sure we don't lose the current when noise is 0"


	^(current abs - (noise * current abs)) * sign</body>

<body package="Homeostat" selector="constDistortLinearNoise">constDistortLinearNoise
	"Returns a value representing a constant distorting noise affecting linearly  the current . Assumes the noise is a number between 0 and 1"

|sign noiseSign|

noiseSign := (Random new nextBetween: -1 and: 1) sign.
sign := current sign.

^((current abs) - (noise * noiseSign)) *sign 

</body>

<body package="Homeostat" selector="constDistortPropNoise">constDistortPropNoise
	"Returns a value representing a constant distorting noise affecting proportionally  the current . Assumes the noise is a number between 0 and 1, i. e. the percentage of current lost to noise"

|sign noiseSign|

noiseSign := (Random new nextBetween: -1 and: 1) sign.
sign := current sign.

^((current abs) - (noise * (current abs) * noiseSign)) *sign</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>noiseAlgorithms</category>

<body package="Homeostat" selector="getCurrentLinearlyAffected">getCurrentLinearlyAffected
	"Returns a value representing a current linearly affected by the noise."



| currentSign |
	currentSign := current sign.
	currentSign = 0 ifTrue: [currentSign := 1].

^((current abs)  - noise ) * currentSign</body>

<body package="Homeostat" selector="getCurrentPropAffected">getCurrentPropAffected
	"Returns a value representing a current proportionally affected by the noise."


| currentSign |
	currentSign := current sign.
	currentSign = 0 ifTrue: [currentSign := 1].

^(current abs * (1- noise )) * currentSign</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>private-noiseAlgorithms</category>

<body package="Homeostat" selector="getNoiseDegradingConstantLinear">getNoiseDegradingConstantLinear
	"returns a degrading noise (with sign always opposite to affected current), and constant value equal to the noise parameter"





^ noise * current sign *-1</body>

<body package="Homeostat" selector="getNoiseDegradingConstantProportional">getNoiseDegradingConstantProportional
	"returns a degrading noise (with sign always opposite to affected current), and constant value equal to the ratio between the noise parameter and the affected current"





^ (noise*(current abs))  * current sign *-1</body>

<body package="Homeostat" selector="getNoiseDegradingNormalLinear">getNoiseDegradingNormalLinear
	"returns a degrading noise (sign always opposite to current) normally distributed and proportional to the  absolute magnitude of the noise parameter"

	

| noiseAbsValue noiseSign |

noiseSign := current sign negated.
noiseAbsValue := (NormalDistribution new: noise sigma: noise *1 /3) random.

"trim noise within the interval {0, 2 *noise}"
noiseAbsValue > (2 * noise) ifTrue: [ noiseAbsValue := 2* noise].
noiseAbsValue < 0 ifTrue: [noiseAbsValue := 0].
^ noiseAbsValue * noiseSign.</body>

<body package="Homeostat" selector="getNoiseDegradingNormalProportional">getNoiseDegradingNormalProportional
	"returns a degrading noise (with sign always opposite to affected current), and normally distributed value in the interval [0, 2*noiseParameter]"

| noiseAbsValue  minAbsNoise maxAbsNoise  noiseSign |

noiseSign := current sign negated.
minAbsNoise :=0.
maxAbsNoise := noise * current abs *2.

noiseAbsValue := (NormalDistribution new: maxAbsNoise / 2  sigma: maxAbsNoise / 6) random.
"trim noise within the interval {0, 2 *noise *current abs}"
noiseAbsValue > maxAbsNoise ifTrue: [ noiseAbsValue := maxAbsNoise].
noiseAbsValue <  minAbsNoise  ifTrue: [noiseAbsValue := minAbsNoise].

^ noiseAbsValue * noiseSign</body>

<body package="Homeostat" selector="getNoiseDegradingUniformLinear">getNoiseDegradingUniformLinear
	"returns a degrading noise (sign always opposite to current) uniformly distributed and proportional to the  absolute magnitude of the noise parameter"

| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise.
noiseAbsValue := (UniformDistribution new initialize: 0 to: (2 * maxNoise)) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDegradingUniformProportional">getNoiseDegradingUniformProportional
	"returns a degrading noise (with sign always opposite to affected current), and uniformly distributed value in the interval [0, (2*noiseParameter) * current ]"

| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := 2 * (noise * (current abs)).
noiseAbsValue := (UniformDistribution new initialize: 0 to:  maxNoise) random.
^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDistortingConstantLinear">getNoiseDistortingConstantLinear
	"returns a distorting noise (centered around 0),  with absolute value equal to the noise parameter"


| randomSign |

randomSign := (UniformDistribution  new initialize: -1 to: 1) random  sign .


^ noise * current sign *randomSign.</body>

<body package="Homeostat" selector="getNoiseDistortingConstantProportional">getNoiseDistortingConstantProportional
	"returns a distorting noise (centered around 0),  equal to the ratio between the absolute magnitude of the affected current and the noise parameter"

| randomSign |

randomSign := (UniformDistribution  new initialize: -1 to: 1) random  sign .


^ (noise * (current abs)) * current sign *randomSign.</body>

<body package="Homeostat" selector="getNoiseDistortingNormalLinear">getNoiseDistortingNormalLinear
	"returns a distorting noise (centered around 0) normally distributed and proportional to the  absolute magnitude of the noise parameter"
	

| noiseValue |

noiseValue := (NormalDistribution new: 0 sigma: noise / 3) random.
"trim noise within the interval { -noise, noise}"
noiseValue > noise ifTrue: [ noiseValue := noise.].
noiseValue < (noise negated)  ifTrue: [noiseValue :=  noise negated.].

^ noiseValue</body>

<body package="Homeostat" selector="getNoiseDistortingNormalProportional">getNoiseDistortingNormalProportional
	"returns a distorting noise (centered around 0) normally distributed and porportional to the absolute magnitude of the affected current"

	

| noiseValue minNoise maxNoise|
minNoise := noise negated * current abs.
maxNoise := noise * current abs.

noiseValue := (NormalDistribution new: 0 sigma: maxNoise / 3) random.
"trim noise within the interval {0, 2 *noise}"
noiseValue > maxNoise ifTrue: [ noiseValue := maxNoise].
noiseValue < minNoise  ifTrue: [noiseValue :=  minNoise].

^ noiseValue</body>

<body package="Homeostat" selector="getNoiseDistortingUniformLinear">getNoiseDistortingUniformLinear
	"returns a distorting noise (centered around 0) uniformly  distributed in the interval [-noise, noise]."


| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise.
noiseAbsValue := (UniformDistribution new initialize: maxNoise negated to:  maxNoise) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="getNoiseDistortingUniformProportional">getNoiseDistortingUniformProportional
	"returns a distorting noise (centered around 0) uniformly  distributed in the interval [0, noise/current]."



| sign noiseAbsValue maxNoise|

sign := current sign * -1.
maxNoise := noise * current abs.
noiseAbsValue := (UniformDistribution new initialize: maxNoise negated to:  maxNoise) random.

^ noiseAbsValue * sign</body>

<body package="Homeostat" selector="testNormalDistrib">testNormalDistrib
	
	"replaces noise with a random value normally distributed around noise, and with a standard distribution of noise/3"
	 noise := (NormalDistribution new: noise sigma: noise / 3) random.</body>
</methods>

<methods>
<class-id>HomeoNoise</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="constant">constant
	
	distribution := 'Constant'</body>-->

<body package="Homeostat" selector="current">current
	^current</body>

<body package="Homeostat" selector="current:">current: anObject
	current := anObject</body>

DONE <!--<body package="Homeostat" selector="degrading">degrading
mode := 'Degrading'</body>-->

DONE <!--<body package="Homeostat" selector="distorting">distorting


mode := 'Distorting'.</body>-->

DONE <!--<body package="Homeostat" selector="getNoise">getNoise
	"select the correct noise algorithm according to the values of mode, distribution and ratio and returns the noise value."

| noiseAlg |

noiseAlg := 'getNoise', mode , distribution , ratio.
^ self perform: noiseAlg asSymbol.</body>-->

DONE <!--<body package="Homeostat" selector="linear">linear


ratio := 'Linear'</body>-->

<body package="Homeostat" selector="noise">noise
	^noise</body>

<body package="Homeostat" selector="noise:">noise: anObject
	noise := anObject</body>

<body package="Homeostat" selector="normal">normal
	distribution := 'Normal'.</body>

DONE <!--<body package="Homeostat" selector="proportional">proportional


ratio := 'Proportional'</body>-->

DONE <body package="Homeostat" selector="uniform">uniform
distribution := 'Uniform'</body>
</methods>

</st-source>
