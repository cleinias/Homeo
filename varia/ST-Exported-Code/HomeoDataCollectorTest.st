<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:17 am</time-stamp>


<class>
<name>HomeoDataCollectorTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>dataCollector homeostat </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoDataCollectorTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoDataCollectorTest</class-id> <category>running</category>

DONE <!--<body package="Homeostat" selector="testAddStateForUnit">testAddStateForUnit
	" DataCollector adds a DataUnit for a  HomeoUnit for time t"

	| unit1 unit2 unit3 |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.

	unit1 time: 0.
	unit2 time: 0.
	unit3 time: 0.
	dataCollector at: 0 addDataUnitFor: unit1.
	dataCollector at: 0 addDataUnitFor: unit2.
	dataCollector at: 0 addDataUnitFor: unit3.

	unit1 time: 1.
	unit2 time: 1.
	unit3 time: 1.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.

	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

	unit1 time: -1.
	unit2 time: -1.
	unit3 time: -1.
	dataCollector at: -1 addDataUnitFor: unit1.
	dataCollector at: -1 addDataUnitFor: unit2.
	dataCollector at: -1 addDataUnitFor: unit3.

"self halt."
	"Checks that the dictionary contains DataUnits for all the units]"
	dataCollector states do: 
			[:dataDic | 
			dataDic isNil 
				ifFalse: 
					[self assert: (dataDic includesKey: unit1 name).
					self assert: (dataDic includesKey: unit2 name).
					self assert: (dataDic includesKey: unit3 name).
					self assert: (((dataDic at: unit1 name ) name)= unit1 name).				
]].</body>-->

DONE <!--<body package="Homeostat" selector="testBossOut">testBossOut
"saves the complete run to  a Boss file for later rereading and analysis "


"produce some data"
	| unit1 unit2 unit3 file newDataCollector boss|

	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.


file := Filename named: 'pippo.sts'.
dataCollector bossOutOn: file. 



boss :=  BinaryObjectStorage onOldNoScan: (Filename named: 'pippo.sts') readStream.
newDataCollector := boss next.
boss close.

self assert: (dataCollector states size = newDataCollector states size).

"checks that  the saved dataCollector has, for each time tick, a dicitonary indexed by the same unit names as the original dataCollector"
dataCollector states values asArray with: (newDataCollector states values  asArray) 
		do:[
			:firstDic :secDic |
			firstDic keys asSortedCollection asArray with: ( secDic keys asSortedCollection asArray)
					do: [
						:origName :savedName |
					  	self assert: (origName = savedName)]]</body>-->

<body package="Homeostat" selector="testConvertCriticalDevForUnit">testConvertCriticalDevForUnit



"produce some data"
	| unit1 unit2 unit3   coll|
	coll := OrderedCollection new.
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.


coll := dataCollector criticalDevAsCollectionForUnit: unit1.

"quick hack"

Transcript clear. coll do: [:elem | Transcript show: elem printString; cr].

self assert: false.</body>

DONE <!--<body package="Homeostat" selector="testExtractCriticalDevAsCollectionForUnit">testExtractCriticalDevAsCollectionForUnit
	"produce some data"

	"initializing and setting up the homeostat run  and the data collections"

	|  extractedData originalData testResultCollection |

	testResultCollection := OrderedCollection new.
	homeostat runFor: 1000.


	"extracting data and comparing to the original" 
	homeostat homeoUnits do: 
			[:unit | 
			extractedData := homeostat dataCollector criticalDevAsCollectionForUnit: unit.
			originalData := homeostat dataCollector states collect: [:tick | (tick at: unit name) criticalDeviation].
			self assert: extractedData size = originalData size.
			1 to: originalData size
				do: 
					[:index | 
					testResultCollection add: ( (extractedData at: index) = (extractedData at: index)) not].    "collecting all instances in which the data differ"
			self assert: (testResultCollection includes: true) not]</body>-->

<body package="Homeostat" selector="testPrintCriticalDeviationDataforGGobiOnFile">testPrintCriticalDeviationDataforGGobiOnFile
	"produce some data"

	"initializing and setting up the homeostat run the ouput file and the data collections"

	| datafile aStream lines dataReadBack columns originalData testResults unitNames epsilon|

	epsilon := 0.0000001.           "we take numbers as equal if their difference is less than epsilon"
	(homeostat homeoUnits at: 1) name.
	datafile := 'testing-datafile.txt' asFilename.
	aStream := datafile writeStream.
	lines := OrderedCollection new.
	columns := OrderedCollection new.
	dataReadBack := OrderedCollection new.
	testResults := OrderedCollection new.

	"running the homeostat and saving the data"
	homeostat runFor: 50000.
	homeostat dataCollector printPlottingDataForGgobiOn: aStream.

	"reading back the data and comparing to original data"
	aStream := datafile readStream.
	[aStream atEnd] whileFalse: [lines add: (aStream upTo: Character cr)].
	aStream close.
	aStream := ReadStream on: (lines at: 1).
	[aStream atEnd] whileFalse: 
			[| colTitle |
			colTitle := aStream upTo: $,.
			columns add: colTitle].
	aStream close.
	columns  do: 
			[ :elem| dataReadBack add: OrderedCollection new.].

	lines do: 
			[:line | 
			| index |
			index := 1.
			aStream := line readStream.
			[aStream atEnd] whileFalse: 
					[(dataReadBack at: index) add: (aStream upTo: $,).
					index := index + 1]].

unitNames := (homeostat homeoUnits collect: [:unit | unit name]).
dataReadBack removeAllSuchThat: [:dataColumn |  (unitNames includes: (dataColumn at: 1)) not].


originalData := OrderedCollection new.

homeostat homeoUnits do: [:unit | | data | 
						   data  :=  (homeostat dataCollector criticalDevAsCollectionForUnit: unit). 						
						   data addFirst: unit name.
						    originalData add: data]. 


dataReadBack doWithIndex: [:dataColumnReadBack :index |
				   originalData do: [ :origDataColumn |
								((dataColumnReadBack at: 1) = (origDataColumn at: 1)) 
									 ifTrue: [ (origDataColumn allButFirst: 1) with: (dataColumnReadBack allButFirst: 1) 
											do:  [:orig :readBack | 
													(((orig asNumber) - ((readBack, 'd') asNumber)) &lt; epsilon)
													 ifFalse: [testResults add: (Array with: orig 
																				  with: readBack 
																				  with: (((orig asNumber) - ((readBack, 'd') asNumber))) 
																			    	  with: index)]]]]].

self assert: (testResults size = 0).</body>

DONE <!--<body package="Homeostat" selector="testPrintOutCompleteData">testPrintOutCompleteData

"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printCompleteDataOn: aStream.

"quick hack"
Transcript clear; show: aString.

self assert: false.</body>-->

<body package="Homeostat" selector="testPrintOutCompleteDataForUnit">testPrintOutCompleteDataForUnit

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printCompleteDataForUnit: unit1 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printCompleteDataForUnit: unit2 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printCompleteDataForUnit: unit3 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.

"quick hack"
Transcript clear; show: aString.


self assert: false.
aStream close.</body>

<body package="Homeostat" selector="testPrintOutEssentialData">testPrintOutEssentialData

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printEssentialDataOn: aStream.

"quick hack"
Transcript clear; show: aString.

self assert: false.</body>

<body package="Homeostat" selector="testPrintOutEssentialDataForUnit">testPrintOutEssentialDataForUnit

"write out the essential data for the simulation"


"produce some data"
	| unit1 unit2 unit3 aStream aString  |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.

aString := String new.
aStream := WriteStream on: aString.

dataCollector printEssentialDataForUnit: unit1 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printEssentialDataForUnit: unit2 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.
dataCollector printEssentialDataForUnit: unit3 On: aStream.
aStream nextPut: Graphics.TextConstants.CR.

"quick hack"
Transcript clear; show: aString.

self assert: false.

aStream close.</body>

<body package="Homeostat" selector="testSaveCriticalDeviationDataforOneUnitOnFile">testSaveCriticalDeviationDataforOneUnitOnFile

"produce some data"
	|  datafile firstUnitName aStream dataReadBack  |

"initializing and setting up the homeostat run the ouput file and the data collections" 
	
	firstUnitName := (homeostat homeoUnits at: 1) name.
	datafile := 'testing-datafile.txt' asFilename.
	aStream := datafile writeStream.
	dataReadBack := OrderedCollection new.


	homeostat runFor: 100.
	homeostat dataCollector printCompleteDataOn: aStream.

self assert: false.</body>

<body package="Homeostat" selector="testSaveDeviationForUnit">testSaveDeviationForUnit
	"write out the essential data for the simulation, i.e. the output values"

	"produce some data"

	| unit1 unit2 unit3 aStream file |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.
	file := Filename named: 'pippo.txt'.
	aStream := file writeStream.
	dataCollector saveDeviationOn: aStream forUnit: unit1.
	aStream close.
	"here we need to read back the data saved out, do some parsing, and random checking to test consistency."

	"STILL TO DO!"

self assert: false.</body>

<body package="Homeostat" selector="testSaveEssentialsAsSV">testSaveEssentialsAsSV
	"write out the essential data for the simulation, i.e. the output values"

	"produce some data"

	| unit1 unit2 unit3 aStream file |
	unit1 := HomeoUnit new.
	unit2 := HomeoUnit new.
	unit3 := HomeoUnit new.
	dataCollector at: 1 addDataUnitFor: unit1.
	dataCollector at: 1 addDataUnitFor: unit2.
	dataCollector at: 1 addDataUnitFor: unit3.
	unit1 time: 2.
	unit2 time: 2.
	unit3 time: 2.
	dataCollector at: 2 addDataUnitFor: unit1.
	dataCollector at: 2 addDataUnitFor: unit2.
	dataCollector at: 2 addDataUnitFor: unit3.
	file := Filename named: 'pippo.txt'.
	aStream := file writeStream.
	dataCollector saveEssentialsOn: aStream
		separator: $,.
	aStream close.
	"here we need to read back the data saved out, do some parsing, and random checking to test consistency."

	"STILL TO DO!"

self assert: false.</body>
</methods>

<methods>
<class-id>HomeoDataCollectorTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

DONE <!--<body package="Homeostat" selector="setUp">setUp

dataCollector := HomeoDataCollector new.

"setup a standard Ashby 4 units homeostat to be used in various tests"
	
	homeostat := Homeostat new.
	4 timesRepeat: 
			[| unit |
			unit := HomeoUnit new setRandomValues.
			homeostat addFullyConnectedUnit: unit].
	homeostat slowingFactor: 0.</body>-->
</methods>

</st-source>
