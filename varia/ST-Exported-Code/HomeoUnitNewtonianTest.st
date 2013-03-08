<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:41 am</time-stamp>


<class>
<name>HomeoUnitNewtonianTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
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
<class-id>HomeoUnitNewtonianTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUnitNewtonianTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Edit the following to properly initialize instance variables ***"
	unit := nil.
	homeostat := nil.
	" *** And replace this comment with additional initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
	"Initialize the HomeoUnit class and sets up a default HomeoUnit for testing"

"initialize the HomeoUnit class to clear all old names (held in the Names shared variable)"
HomeoUnit initialize.

unit := HomeoUnitNewtonian new.</body>
</methods>

<methods>
<class-id>HomeoUnitNewtonianTest</class-id> <category>running</category>

<body package="Homeostat" selector="testComputeNextDeviationLinear">testComputeNextDeviationLinear
	

| oldDev oldVelocity torque |

unit criticalDeviation: 0.
1000 timesRepeat: 
		[torque := (UniformDistribution from: -1 to: 1) random.
		unit needleUnit mass: (UniformDistribution from:  1 to: 10000) random.
		oldDev := unit criticalDeviation.
		oldVelocity := unit currentVelocity.
		unit criticalDeviation: (unit newLinearNeedlePosition: torque).
		self assert: ((unit criticalDeviation) = (oldDev  + oldVelocity + (1/2 * (torque/ unit needleUnit mass))))].      "Check the computation is correct according to Newtonian dynamics"</body>

<body package="Homeostat" selector="testComputeNextVelocityWithConnections">testComputeNextVelocityWithConnections
	| testRuns oldVelocity anotherUnit errorTolerance maxDelta counter |
	errorTolerance := 10 raisedTo: -14.
	testRuns := 1000.
	anotherUnit := HomeoUnitNewtonian new.
	unit addConnectionWithRandomValues: anotherUnit.
	(unit inputConnections at: 2) noise: 0.
	"Transcript clear."
	unit criticalDeviation: 0.
	unit noise: 0.
	"Transcript show: 'Testing velocity with 1 connection, starting with unit at: ', unit criticalDeviation printString; cr."
	100 timesRepeat: 
			[counter := 0.
			maxDelta := 0.
			1 to: testRuns
				do: 
					[:i | 
					"		Transcript show: 'Test run number: ', i printString, ' '."

					| torque velocityDelta computedVelocity |
					unit needleUnit mass: (UniformDistribution from: 1 to: 1000) random.
					oldVelocity := unit currentVelocity.
					torque := (unit inputConnections 
								select: [:each | each isActive and: [each incomingUnit isActive]]) 
									inject: 0
									into: [:tempSum :conn | tempSum + conn output].		"compute the torque as sum of the output coming from connected units"
					torque := torque + unit drag.											"consider the drag affecting the force."
					computedVelocity := oldVelocity + (torque / unit needleUnit mass).	"velocity value according to  Newtonian dynamics: v = v0 +at (where a is force / mass)"
					unit selfUpdate.
					"Do not compare calculations when the unit's needle would have gone over the maximum limit, because the actual displacement is clipped at the maximum value. 
			Since actual velocity is computed on the basis of actual displacement (as it should be), the theoretical value is bound to be off"
					(unit criticalDeviation &gt;= unit maxDeviation 
						or: [unit criticalDeviation &lt;= unit maxDeviation negated]) 
							ifTrue: [velocityDelta := 0]
							ifFalse: [velocityDelta := (unit currentVelocity - computedVelocity) abs].
					velocityDelta &lt; errorTolerance 
						ifFalse: 
							["Transcript
								show: 'Failed on: ' , velocityDelta printString , ' at run: ' 
											, i printString;
								cr."
							counter := counter + 1].
					"Transcript
						show: 'delta between theoretical velocity and computed velocity is: ' 
									, velocityDelta printString , ' and test is: ' 
									, (velocityDelta &lt; errorTolerance) printString;
						cr."
					velocityDelta &gt; maxDelta ifTrue: [maxDelta := velocityDelta].
					self assert: velocityDelta &lt; errorTolerance].
			"Transcript
				show: 'MaxDelta was: ' , maxDelta printString , ' and I failed ' 
							, counter printString , ' test over: ' 
							, testRuns printString , ' or about: ' 
							, (counter / testRuns * 100) asFloat printString , '%';
				cr"]</body>

<body package="Homeostat" selector="testComputeNextVelocityWithoutConnections">testComputeNextVelocityWithoutConnections
	

| testRuns oldVelocity  errorTolerance maxDelta counter|

errorTolerance :=10 raisedTo: -13 .
testRuns := 100.

"Transcript clear."
unit criticalDeviation: 0.
unit noise: 0.
unit currentOutput: 0.1.
"unit toggleDebugMode."
(unit inputConnections at: 1)  noise: 0.
"Transcript show: 'Testing velocity with no connections, starting with unit at: ', unit criticalDeviation printString; cr."
1000 timesRepeat:[
	counter := 0.
	maxDelta := 0.
	1 to: testRuns do: 
		[:i |
		| torque velocityDelta computedVelocity |

"		Transcript show: 'Test run number: ', i printString, ' '."
		unit needleUnit mass: (UniformDistribution from:  1 to: 1000) random.
		"unit needleUnit mass: 1."
		oldVelocity := unit currentVelocity.
		torque :=  
            (unit  inputConnections select: [:each | (each isActive) and: [ each incomingUnit isActive]])
		 inject: 0 into: [ :tempSum :conn | tempSum + (conn  output)].  "compute the torque as sum of the output coming from connected units"	
		torque := torque + unit drag.      "include drag affecting the force"
		computedVelocity := (oldVelocity + (torque / unit needleUnit mass)).  "velocity value according to  Newtonian dynamics: v = v0 +at (where a is force / mass)"
		unit selfUpdate.
		"Do not compare calculations when the unit's needle would have gone over the maximum limit, because the actual displacement is clipped at the maximum value. 
		Since actual velocity is computed on the basis of actual displacement (as it should be), the theoretical value is bound to be off"
		((unit criticalDeviation &gt;= unit maxDeviation)	or: [unit criticalDeviation &lt;= unit maxDeviation negated]) 
			ifTrue: [ velocityDelta := 0]
			ifFalse:[velocityDelta := ((unit currentVelocity) - computedVelocity) abs] .      
		velocityDelta &lt; errorTolerance  ifFalse: ["Transcript show: 'Failed on: ', velocityDelta printString, ' at run: ', i printString; cr. " counter := counter + 1.].
"		Transcript show: 'delta between theoretical velocity and computed velocity is: ', velocityDelta printString,  ' and test is: ', (velocityDelta &lt; errorTolerance) printString; cr."
		velocityDelta &gt; maxDelta ifTrue: [maxDelta := velocityDelta].
		"velocityDelta abs &gt; errorTolerance ifTrue: [ Transcript show: 'Run number: ', i printString, ' delta: ', velocityDelta printString, ' updated comp vel.: ', unit currentVelocity printString, ' theoretical vel.: ',  computedVelocity printString; cr]."
		self assert: (velocityDelta abs &lt; errorTolerance)].
	"Transcript show: 'MaxDelta was: ', maxDelta printString, ' and I failed ', counter printString, ' test over: ', testRuns printString, ' or about: ', (counter/testRuns*100) asFloat printString, '%'; cr"
]</body>

<body package="Homeostat" selector="testDragEquationDrag">testDragEquationDrag
	"The Drag equation comptutes drag force on a surface of area A as
	 Drag = Area * 1/2 * DragCoefficient * density * velocity^2
	  We actually need to convert the unit's current velocity
	   to real physical units to have a minimun of plausibility.
	  HomeoUnit&gt;&gt;physicalVelocity does that on the basis of conversion parameters
	 stored in the iVar physicalParameters"

|dragForce errorTolerance testRuns delta|

errorTolerance := 0.000000001.

testRuns := 1000.

"When the unit is started, velocity is zero, and dragForce should be zero"
unit currentVelocity: 0.
testRuns timesRepeat: [
	
	unit density: (UniformDistribution from: 1 to: 1000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	unit needleUnit dragCoefficient: (UniformDistribution from: 0.3 to: 2) random.

	dragForce := unit dragEquationDrag.
	self assert: (dragForce = 0).].

"When Velocity is not zero, Drag Force follows drag's equation.
 We briefly test with random velocities,  random densities,  random surface areas, and random coefficients"

testRuns timesRepeat: [

	unit currentVelocity: (UniformDistribution from: -10 to: 10) random.
	unit density: (UniformDistribution from: 1 to: 1000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	unit needleUnit dragCoefficient: (UniformDistribution from: 0.3 to: 2) random.

	dragForce := unit dragEquationDrag.
	delta := (dragForce - (1/2 * unit needleUnit surfaceArea * unit needleUnit dragCoefficient * unit density * unit physicalVelocity squared)) abs.
	self assert: delta &lt; errorTolerance. ]</body>

<body package="Homeostat" selector="testStokesDrag">testStokesDrag
	"Stokes's law computes drag force on a sphere of radius r  as 6* pi * radius * viscosity * velocity.
	 We use the radius of the surface area of the moving needle instead"

|dragForce  radius testRuns|
testRuns := 1000.
radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.

"When the unit is started, velocity is zero, and dragForce should be zero"
unit currentVelocity: 0.

testRuns timesRepeat: [	
	unit viscosity: (UniformDistribution from: 0.1 to: 100000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.
	dragForce := unit stokesLawDrag.
	self assert: (dragForce = 0)].

"When Velocity is not zero, Drag Force follows Stokes's law.
 We briefly test with random velocities,  random densities, and random surface areas"


testRuns timesRepeat: [
	unit currentVelocity: (UniformDistribution from: -10 to: 10) random.
	unit viscosity: (UniformDistribution from: 0.1 to: 100000) random.
	unit needleUnit surfaceArea: (UniformDistribution from: ((1/Double pi) * 0.001) to: 1000) random.
	radius := (unit needleUnit surfaceArea *( Double pi)) sqrt.
	dragForce := unit stokesLawDrag.
	self assert: ((dragForce = (6 * (Double pi) * radius * unit viscosity * unit currentVelocity) negated))].</body>
</methods>

</st-source>
