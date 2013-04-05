<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:38 am</time-stamp>


<class>
<name>HomeoUnitNewtonian</name>
<environment>Smalltalk</environment>
<super>HomeoUnit</super>
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
<class-id>HomeoUnitNewtonian</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
	
	super initialize.
	self needleUnit mass: 1000.                  "default mass for Newtonian units to avoid the needle shooting up or down"</body>
</methods>-->

<methods>
<class-id>HomeoUnitNewtonian</class-id> <category>private-running</category>

DONE <!--<body package="Homeostat" selector="clearFutureValues">clearFutureValues
	"sets to 0 the internal values used for computing future states. "


self nextDeviation: 0.
self inputTorque: 0.
self currentOutput: 0.
self currentVelocity: 0.</body>-->

DONE <!--<body package="Homeostat" selector="drag">drag
	"output the drag force acting on the unit as a result of the viscosity in the trough and the velocity of the needle."

^ self stokesLawDrag.              </body>-->

DONE <!--<body package="Homeostat" selector="dragDummy">dragDummy
	"Used for testing purposes"

^ 0</body>-->

DONE <!--<body package="Homeostat" selector="dragEquationDrag">dragEquationDrag

	"Compute the drag on the needle according to the drag equation for high Reynolds numbers: 
	D = 1/2  C A rho  v^2.
	Outputs a number representing the drag expressed as force measured in Newtons"


	^ 1/2  * density * needleUnit dragCoefficient * (self physicalVelocity squared) * (needleUnit surfaceArea) .</body>-->

DONE <!--<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
	"  Computes the new position of the needle taking into consideration (a simplified version of) the forces acting on the needle. "

	"self halt."

	| totalForce acceleration displacement |
	totalForce := aTorqueValue + self drag.		"add to the  force acting on the needle the drag force produced by the fluid in the trough the  needle is moving through. 
													In the original Homeostat,  other factors related to the  physical characteristics of the device, affect the net force affecting the needle,  
													including the potential through the trough, the friction at the vane, etc. 
												    These factors are ignored here"

	acceleration := totalForce / needleUnit mass.	"As per  Newton's second law"
	displacement := currentVelocity + (1 / 2 * acceleration) asDouble.	" x - x0 = v0t + 1/2 a t, with t obviously =  1"
	
	"Testing"
"	debugMode 
		ifTrue: 
			[Transcript
				show: ' time: ';
				show: (time + 1) printString;
				show: '  unit: ';
				show: self name;
				show: '     curr, pos:';
				show: (criticalDeviation asFixedPoint: 3) printString;
				show: '     new, pos:';
				show: (criticalDeviation + newVelocity asFixedPoint: 3) printString;
				show: '   curr. vel.: ';
				show: (currentVelocity asFixedPoint: 3) printString;
				show: '           new vel.: ';
				show: (newVelocity asFixedPoint: 3) printString;
				show: '    acc.:   ';
				show: (acceleration asFixedPoint: 3) printString;
				show: ' torque: ', (aTorqueValue asFixedPoint: 3)  printString;
				cr;
				cr]."
debugMode 
	ifTrue: [ 
		 (((criticalDeviation + displacement) > maxDeviation) or: [(criticalDeviation + displacement) < maxDeviation negated])
			ifTrue: 
				[Transcript show:
				'NEW CRITICAL DEVIATION WOULD BE OVER LIMITS AT: ', ((criticalDeviation + displacement) asFixedPoint: 3) printString; cr]].
	^criticalDeviation + displacement</body>-->

<body package="Homeostat" selector="newNeedlePosition:">newNeedlePosition: aTorqueValue 
	"computes the new needle position on the basis of aTorqueValue, which represents the torque applied to the unit's needle. "
	
	needleCompMethod = 'linear' 
		ifTrue: [^self newLinearNeedlePosition: aTorqueValue]
		ifFalse: [^self newRandomNeedlePosition]       "defaults to a random computation method if the method is not specified"</body>

<body package="Homeostat" selector="physicalForce:">physicalForce: torqueValue
	"converts the torque coming into a unit into a force expressed in real physical units n (i.e. Newtons)"


^ torqueValue * (physicalParameters at: 'massEquivalent') * (physicalParameters at: 'lengthEquivalent') / ((physicalParameters at: 'timeEquivalent') squared)</body>

<body package="Homeostat" selector="reynoldsNumber">reynoldsNumber
	"computes the Reynolds number of the physical flow (the needle in the trough), according to the formula:
	Re = 2 a rho v / eta"

| viscosityInSiUnits |


viscosityInSiUnits := viscosity / 1000. "convert viscosity from centiPoise to Pascal/second"

^ 2 * needleUnit surfaceArea * density * self physicalVelocity / viscosityInSiUnits.</body>

<body package="Homeostat" selector="selfUpdate">selfUpdate
	"This is the master loop for the unit. It goes through the following sequence:
	1. compute new needle's deviation (nextDeviation (includes reading inputs))
	2. updates the current output on the basis of the deviation.
	3. check whether it's time to check the essential value and if so do it and  update the counter (uniselectorTime) [this might change the weight of the connections]
	4. Compute the new velocity on the basis of the displacement
	5. Move the needle to new position and compute new output
	"


| newDeviation|

	"1. compute where the needle should move to"

	self computeNextDeviation.

	"2. update times"
	self updateTime.
	self updateUniselectorTime.

	"3. check whether it's time to check the uniselector/detection mechanism and if so do it. 
	       Register that the uniselector is active in an instance variable"
	(uniselectorTime >= uniselectorTimeInterval and: [uniselectorActive]) 
		ifTrue: [self essentialVariableIsCritical ifTrue: [self operateUniselector.
												   uniselectorActivated := 1]]
		ifFalse: [uniselectorActivated:= 0].	      


	"4. Compute new current velocity according to classic Newtonian formula: x-x0 = 1/2t (v-v0)  where:
		x0 = criticalDeviation
		x = newDeviation
		v0 = currentVelocity
		Solving for v we get: v = 2(x-x0) -v0"
	
  	newDeviation := (self clipDeviation: nextDeviation).
"	currentVelocity := newDeviation-criticalDeviation."             "old version"
	currentVelocity := 2* (newDeviation -criticalDeviation) - currentVelocity.

	"5. updates the needle's position (critical deviation) with clipping, if necessary, and updates the output"
	
	self criticalDeviation: newDeviation.
	self computeOutput.
	nextDeviation := 0</body>

<body package="Homeostat" selector="stokesLawDrag">stokesLawDrag

	"Compute the physical drag on the needle according to Stokes equation: D = 6 pi r eta v.
	Output is negated, since Drag's sign is always  opposite  to velocity.
	Instead of the radius of the sphere (as in Stokes' law), it uses the surface area of the needle."

^ ( 6 * Double pi * ((needleUnit surfaceArea * Double pi ) sqrt) * viscosity * currentVelocity) negated.</body>
</methods>

</st-source>
