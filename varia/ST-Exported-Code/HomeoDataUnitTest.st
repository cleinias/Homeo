<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:27 am</time-stamp>


<class>
<name>HomeoDataUnitTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>dataUnit unit1 </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoDataUnitTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoDataUnitTest</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="testNewStateFor">testNewStateFor

| newDataUnit |

newDataUnit := HomeoDataUnit newUnitFor: unit1.
dataUnit := newDataUnit.
self assert: dataUnit name = unit1 name.
	self assert: dataUnit maxDeviation = unit1 maxDeviation.
	unit1 inputConnections do: 
			[:conn | 
			| connArray |
			connArray := dataUnit connectedTo at: conn incomingUnit name.
			self assert: (connArray at: 1) = conn weight.
			self assert: (connArray at: 2) = conn switch.
			self assert: (connArray at: 3) = conn state.
			self assert: (connArray at: 4) = conn noise].
	self assert: dataUnit output = unit1 currentOutput.
	self assert: dataUnit uniselectorState = unit1 uniselectorActive</body>-->

DONE <!--<body package="Homeostat" selector="testPrintDataOnStream">testPrintDataOnStream

| aStream aString|
aString := String new.
aStream := ReadWriteStream on: aString.
dataUnit readStateFrom: unit1.
dataUnit printDataOn:	aStream.

"shortcut  to quickly  check the stream instead of parsing it and seeing whether it represent the unit. Will need to change this"
Transcript show: aString.

aStream close.

self assert: false.</body>-->

DONE <!--<body package="Homeostat" selector="testPrintEssentialVariableOn">testPrintEssentialVariableOn

| aStream aString|
aString := String new.
aStream := ReadWriteStream on: aString.
dataUnit readStateFrom: unit1.
dataUnit printEssentialVariableOn:	aStream.

"shortcut  to quickly  check the stream instead of parsing it and seeing whteher it represent the unit. Will need to change this"


Transcript show: aString.

aStream close.


self assert: false.</body>-->

DONE <!--<body package="Homeostat" selector="testReadDataFromUnit">testReadDataFromUnit

	dataUnit readStateFrom: unit1.
	self assert: dataUnit name = unit1 name.
	self assert: dataUnit maxDeviation = unit1 maxDeviation.
	unit1 inputConnections do: 
			[:conn | 
			| connArray |
			connArray := dataUnit connectedTo at: conn incomingUnit name.
			self assert: (connArray at: 1) = conn weight.
			self assert: (connArray at: 2) = conn switch.
			self assert: (connArray at: 3) = conn state.
			self assert: (connArray at: 4) = conn noise].
	self assert: dataUnit output = unit1 currentOutput.
	self assert: dataUnit uniselectorState = unit1 uniselectorActive</body>-->

DONE <!--<body package="Homeostat" selector="testSameValuesAs">testSameValuesAs


self assert: false.</body>-->
</methods>

<methods>
<class-id>HomeoDataUnitTest</class-id> <category>initialize-release</category>

USELESS<!--<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>-->

<body package="Homeostat" selector="setUp">setUp
DONE <!--dataUnit := HomeoDataUnit new.
unit1 := HomeoUnit new.</body>-->
</methods>

</st-source>
