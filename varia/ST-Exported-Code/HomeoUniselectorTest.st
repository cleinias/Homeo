<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:06:03 am</time-stamp>


<class>
<name>HomeoUniselectorTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>uniselector </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoUniselectorTest</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="testHomeoUniselectorClassType">testHomeoUniselectorClassType

|currentClasses bogusClasses|

currentClasses := OrderedCollection new.
bogusClasses := OrderedCollection new.
HomeoUniselector withAllSubclasses do: [:class | currentClasses add: class name asString].
bogusClasses add: 'pippo'; add: 'HomeoUnit'; add: 'Object'.


bogusClasses do: [:string | self deny: (HomeoUniselector includesType: string)].
currentClasses do: [:string| self assert: (HomeoUniselector includesType: string)].</body>-->

DONE <!--<body package="Homeostat" selector="testIntervalBounds">testIntervalBounds


 self assert: ((uniselector upperBound) - (uniselector lowerBound)) >= 0.</body>
</methods>-->

<methods>
<class-id>HomeoUniselectorTest</class-id> <category>initialize-release</category>

USELESS<!--<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>-->

DONE <!--<body package="Homeostat" selector="setUp">setUp
uniselector := HomeoUniselector new.</body>-->
</methods>

</st-source>
