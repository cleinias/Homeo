<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:04:45 am</time-stamp>


<class>
<name>HomeoNeedleUnit</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>mass surfaceArea dragCoefficient </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<shared-variable>
<name>DefaultParameters</name>
<environment>HomeoNeedleUnit</environment>
<private>false</private>
<constant>false</constant>
<category>initialize-release</category>
<attributes>
<package>Homeostat</package>
</attributes>
</shared-variable>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoNeedleUnit class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="initialize">initialize
	"Sets DefaultParameters, the class variable holding the  default values of all the various parameters of future needle units.
	 All 'physical' values are expressed in internal units.  Conversion to real physical units, if necessary,  done by Physical parameters dictionary in HomeoUnit
	   HomeoUnit initialize "
	
	DefaultParameters := Dictionary new.
	DefaultParameters 	at: 'mass' 				      put: 1 asDouble;  "mass expressed in internal units."
							at: 'surfaceArea' 			put: (1/ Double pi) asDouble ; "in  internal units. This is the area equivalent to a circle whose radius is 1 unit. "
							at: 'dragCoefficient' 		put:  1 asDouble.  "dimensionless, of course. Used to compute drag according to general drag law (for high velocities)"</body>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<comment>
<class-id>HomeoNeedleUnit</class-id>
<body>HomeoNeedleUnit holds parameters and methods describing the needle unit component of a homeostat unit

Instance Variables:
	dragCoefficient 	&lt;Object&gt;	The drag coefficient of the needle (dimensionless)
	mass			      &lt;Object&gt;	The mass of the needle in internal units. The conversion to physical units, if necessary, is done by HomeoUnits via its PhysicalParameters dictionary
	surfaceArea		&lt;Object&gt;	The surface area of the needle, in direction of travel through  fluid in the trough.  surfaceArea is expressed in  in internal units.The conversion to physical units, if necessary, is done by HomeoUnits via its PhysicalParameters dictionary.

</body>
</comment>

<methods>
<class-id>HomeoNeedleUnit</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
"Initialize the HomeoNeedleUnit with the default parameters found in the Class variable DefaultParameters."


	"reads default parameters"

	mass := DefaultParameters at: 'mass'.
	surfaceArea := DefaultParameters at: 'surfaceArea'. 	
	dragCoefficient := DefaultParameters at: 'dragCoefficient'.</body>
</methods>

<methods>
<class-id>HomeoNeedleUnit</class-id> <category>accessing</category>

<body package="Homeostat" selector="dragCoefficient">dragCoefficient
	^dragCoefficient</body>

<body package="Homeostat" selector="dragCoefficient:">dragCoefficient: anObject
	dragCoefficient := anObject</body>

<body package="Homeostat" selector="mass">mass
	^mass</body>

<body package="Homeostat" selector="mass:">mass: anObject
	mass := anObject</body>

<body package="Homeostat" selector="surfaceArea">surfaceArea
	^surfaceArea</body>

<body package="Homeostat" selector="surfaceArea:">surfaceArea: anObject
	surfaceArea := anObject</body>
</methods>

<initialize>
<class-id>HomeoNeedleUnit</class-id>
</initialize>

</st-source>
