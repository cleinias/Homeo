<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:45 am</time-stamp>


<class>
<name>HomeoUnitAristotelian</name>
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
<class-id>HomeoUnitAristotelian</class-id> <category>initialize-release</category>

DONE <!--<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>-->
</methods>

<methods>
<class-id>HomeoUnitAristotelian</class-id> <category>private-running</category>

DONE <!--<body package="Homeostat" selector="dragOn:">dragOn: aForce
	"computes the frictional forces acting on the Aristotelian unit. Only considers the viscosity of the medium in the trough the needle moves through, disregarding other possible frictional forces"
| viscRatio |
"converts the actual viscosity to a ratio"

viscRatio := viscosity / (DefaultParameters at: 'maxViscosity').
^( aForce * viscRatio ) negated.</body>-->

DONE <!--<body package="Homeostat" selector="newLinearNeedlePosition:">newLinearNeedlePosition: aTorqueValue 
	"see method newNeedlePosition for an extended comment on how to compute the displacement of the needle. Briefly, here we just sum aTorqueValue to the current deviation. "

| totalForce  newVelocity |

totalForce := aTorqueValue + (self dragOn:  aTorqueValue) .					" computes the net force acting on the needle by adding the (negative) force produduced by the drag and/ or frictional forces)"

newVelocity := (totalForce / needleUnit mass).							  "In an Aristotelian model, the change in displacement (= the velocity) is equal to the force affecting the unit divided by the  mass: F = mv or v = F/m"
"Testing"
debugMode ifTrue: [Transcript show: ' new position at time: ';  show: (time + 1) printString; show: ' for unit: '; show: self name; show: ' will be ' ; show: (criticalDeviation + (aTorqueValue * viscosity) ) printString; cr;cr.].

	^criticalDeviation + newVelocity                                                               " In an Aristotelian model, new displacement is old displacement plus velocity: x = x0 + vt, with t obviously = 1."</body>-->
</methods>

</st-source>
