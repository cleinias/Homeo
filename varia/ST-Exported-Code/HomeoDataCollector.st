<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:13 am</time-stamp>


<class>
<name>HomeoDataCollector</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>states </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

DONE <!--<comment>
<class-id>HomeoDataCollector</class-id>
<body>DataCollector collects the data for the Homestat simulation. It can output them on a variety of media (file, screen, etc) and formats, write them to file or read them from file. DataCollector DOES NOT collect the data about the homeostat itself---i.e. the engine that has produced the data. The homeostat class knows how to save itself and, conversely, how to read its data and parameters from a  saved instance.

Instance Variables:
	states	<aDictionary>		a collection recording a description of the states of all units, indexed by time t. It is a Dictionary indexed by time t, with each elements containing a collection of HomeoDataUnits indexed by unit's name. It cannot be an Array because the index cannot be restrained to positive numbers (1--n). Indeed, the simulation usually starts at 0, but it could reasonably start in the past. 

</body>
</comment>-->

DONE Initialize-release<methods>
<class-id>HomeoDataCollector</class-id> <category>initialize-release</category>

USELESS <!--<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	super initialize.
	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>-->
</methods>

DONE Saving <methods>
<class-id>HomeoDataCollector</class-id> <category>saving</category>

DONE <!--<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename

"save itself on a new boss file opened on aFilename. It will erase the old content of aFilename"
| boss |
boss := BinaryObjectStorage onNew: aFilename writeStream.
boss nextPut: self.
boss close.</body>-->

DONE <!--<body package="Homeostat" selector="saveDeviationOn:forUnit:">saveDeviationOn: aStream forUnit: aUnit

"Saves the output of the simulation on a stream (typically associated to a file by the calling app) as a series of lines, one per time tick, each comprising the critical deviation  value for aUnit.
Need to strip the type information (the trailing 'd') from the text representation of a double produced by printString "

| str |

states do: [
	:timeItem |
	timeItem do: [
		:dataUnit |
		(dataUnit = aUnit)
			ifTrue: 
				[str := ReadStream on: (dataUnit  output printString).
				aStream nextPutAll: (str upTo: $d)].
				aStream nextPut: Graphics.TextConstants.CR]]</body>-->

DONE <!--<body package="Homeostat" selector="saveEssentialsOn:separator:">saveEssentialsOn: aStream separator: aCharacter

"Saves the output of the simulation on a stream (typically associated to a file by the calling app) as a series of lines, one per time tick, each comprising a row of output values separated by aCharacter.
Need to strip the type information (the trailing 'd') from the text representation of a double produced by printString "

| str |
states do: [
	:timeItem |
	timeItem do: [
		:dataUnit |
		str := ReadStream on: (dataUnit  output printString).
		aStream nextPutAll: (str upTo: $d); 
				 nextPut: aCharacter.].
	aStream nextPut: Graphics.TextConstants.CR.
	]</body>-->
</methods>

DONE Accesssing<methods>
<class-id>HomeoDataCollector</class-id> <category>accessing</category>

DONE <!--<body package="Homeostat" selector="at:addDataUnitFor:">at: timeIndex addDataUnitFor: aHomeoUnit

"adds a dataunit for aHomeoUnit representing the latter state at time timeIndex"

states isNil ifTrue: [states := Dictionary new].

(states includesKey:  timeIndex) ifFalse: [states at: timeIndex put: Dictionary new].

(states at: timeIndex) at: (aHomeoUnit name) put: (HomeoDataUnit newUnitFor: aHomeoUnit).</body>-->

DONE <!--<body package="Homeostat" selector="states">states
	^states</body>-->

DONE <!--<body package="Homeostat" selector="states:">states: anObject
	states := anObject</body>-->
</methods>

DONE Printing <methods>
<class-id>HomeoDataCollector</class-id> <category>printing</category>

DONE <!--<body package="Homeostat" selector="printCompleteDataForUnit:On:">printCompleteDataForUnit: aHomeoUnit On: aStream

"appends to aStream a brief representation of  aHomeoUnit data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name ifTrue: [
						aStream nextPutAll: 'time: ';
						nextPutAll: timeIndex printString;
						nextPutAll: '  '.
						value printDataOn:  aStream]].
				timeIndex := timeIndex + 1.]].</body>-->

DONE <!--<body package="Homeostat" selector="printCompleteDataOn:">printCompleteDataOn: aStream


"appends to aStream a complete representation of its data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each do: [
					:value |
					aStream nextPutAll: 'time: ';
					nextPutAll: timeIndex printString;
					nextPutAll: '  '.
					value printDataOn:  aStream].
			timeIndex := timeIndex + 1.]].</body>-->

DONE <!--<body package="Homeostat" selector="printCriticalDevForUnit:On:">printCriticalDevForUnit: aHomeoUnit On: aStream

"appends to aStream the values for Critical Deviation of aHomeoUnit "


states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name 
						ifTrue: [
							value printCriticalDeviationOn:  aStream]]]].</body>-->

DONE <!--<body package="Homeostat" selector="printEssentialDataForUnit:On:">printEssentialDataForUnit: aHomeoUnit On: aStream

"appends to aStream a brief representation of  aHomeoUnit data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each keysAndValuesDo: [
					:key :value |
					key = aHomeoUnit name ifTrue: [
						aStream nextPutAll: 'time: ';
						nextPutAll: timeIndex printString;
						nextPutAll: '  ';
						nextPutAll: (value name) , ': '.
						value printEssentialVariableOn:  aStream]].
				timeIndex := timeIndex + 1.]].</body>-->

DONE <!--<body package="Homeostat" selector="printEssentialDataOn:">printEssentialDataOn: aStream

"appends to aStream a brief representation of its data"

| timeIndex |

timeIndex := 1.
states do: [
		:each |
		 each isNil ifFalse: [
			each do: [
					:value |
					aStream nextPutAll: 'time: ';
					nextPutAll: timeIndex printString;
					nextPutAll: '  ';
					nextPutAll: (value name) , ': '.
					value printEssentialVariableOn:  aStream].
			timeIndex := timeIndex + 1.]].</body>-->

DONE <!--<body package="Homeostat" selector="printPlottingDataForGgobiOn:">printPlottingDataForGgobiOn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit 
Notice that we convert datapoints  to a fixed number of decimal and we strip the trailing s that VisualWorks appends to the literal represntation of a fixed Number "




| criticDevData unitNames  aCharacter decimals|

decimals := 8.    "The number of fixed decimals we keep. Data points are double and may have up to 15 digits, sometimes expressed in exponential notation"

aCharacter := $,.

unitNames := OrderedCollection new.
states size < 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.


"Print  the column headers"
aStream nextPutAll: 'Time,'.
unitNames do: [:name |
				 aStream nextPutAll: (name printStringNoQuotes);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printStringNoQuotes), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData doWithIndex: [ :timeSlice : index  |
			aStream nextPutAll: index printString;
					 nextPut: aCharacter.
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: (dataPoint asFixedPoint: decimals)  printString) upTo: $s); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>-->

DONE <!--<body package="Homeostat" selector="printPlottingDataForROn:">printPlottingDataForROn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting with the R softwre package. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  aCharacter |

aCharacter := $,.

unitNames := OrderedCollection new.
states size < 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr).

"Print  the column headers, preceded by the 'Time' Header"
aStream nextPutAll:  'Time';  nextPut: aCharacter.

unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData doWithIndex: [ :timeSlice : index  |
			aStream nextPutAll: index printString;
					 nextPut: aCharacter.
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>-->

DONE <!--<body package="Homeostat" selector="printPlottingDataOn:">printPlottingDataOn: aStream

"appends to aStream a multi-column  representation of its data, suitable for plotting. The format includes:

first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  |

unitNames := OrderedCollection new.
states size < 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPutAll: '# '.
unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: Character tab; 
						 nextPut: Character tab; 
						 nextPut: Character tab]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData do: [ :timeSlice |
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
											nextPut: (Character tab);
											nextPut: (Character tab);
											nextPut: (Character tab)].
			aStream nextPut: (Character cr)].
aStream close.</body>-->

DONE <!--<body package="Homeostat" selector="printPlottingDataOn:withSeparator:">printPlottingDataOn: aStream withSeparator: aCharacter

"appends to aStream a multi-column  representation of its data, suitable for plotting. aCharacter is the character separatng the column.
The format includes:
first a couple of lines of commented data detailing the particular simulation the data describe,
then a commented line with the data headers
then a sequence of lines with each  column containing the critical deviation value for a unit "




| criticDevData unitNames  |

unitNames := OrderedCollection new.
states size < 1 ifTrue: [^Dialog warn: 'There are no data to save'].
(states at: 1) do: [:dataUnit | unitNames add: (dataUnit name)].
criticDevData := self criticalDevAsCollectionOfArraysForAllUnits asArray.

"Print a header with general information at the top of the file"
aStream nextPutAll: '# Simulation data produced by HOMEO---the homeostat simulation program';
		nextPut: (Character cr);
		nextPutAll: '# Data printed on: ', (Time dateAndTimeNow) printString;
		nextPut: (Character cr);	  
		nextPutAll: '# There were exactly ', (unitNames size printString), ' units in this simulation';
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPut: (Character cr); 
		nextPutAll: '# '.
unitNames do: [:name |
				 aStream nextPutAll: (name printString);
						 nextPut: aCharacter; 
						 nextPutAll: ((name printString), '-unisel'); 
						 nextPut: aCharacter]. 
aStream nextPut: (Character cr).

"print the data"
criticDevData do: [ :timeSlice |
			timeSlice do: [:dataPoint | aStream nextPutAll: ((ReadStream on: dataPoint printString) upTo: $d); 
										 nextPut: aCharacter]. 
	         		aStream nextPut: (Character cr)].
aStream close.</body>-->
</methods>

DONE Converting <methods>
<class-id>HomeoDataCollector</class-id> <category>converting</category>

DONE <!--<body package="Homeostat" selector="criticalDevAsCollectionForUnit:">criticalDevAsCollectionForUnit: aHomeoUnit 
	"Extracts the Critical Deviaton values for aHomeoUnits and returns them as an Ordered Collection"

	| aCollection |
	aCollection := OrderedCollection new.
	states do: 
			[:each | 
			each isNil 
				ifFalse: 
					[each keysAndValuesDo: 
							[:key :value | 
							key = aHomeoUnit name ifTrue: [ aCollection add: (value criticalDeviation)]]]].
	^aCollection</body>-->

DONE <!--<body package="Homeostat" selector="criticalDevAsCollectionOfArraysForAllUnits">criticalDevAsCollectionOfArraysForAllUnits 
	"Extracts the Critical Deviaton homeoDataunits for all units  and returns them as an Ordered Collection of Arrays. Each array has all the homeoDataunits for a point in time"

	| aCollection  |
	aCollection := OrderedCollection new.
	states do: 
			[:stateAtTick | 
			stateAtTick isNil 
				ifFalse: 
					[
					  | dataPoint | 
					   dataPoint := OrderedCollection new .
					   stateAtTick do: 
							[:homeoDataunit | 
							dataPoint add: homeoDataunit criticalDeviation.
							dataPoint add: homeoDataunit uniselectorActivated].
			aCollection add: dataPoint asArray]].




	^aCollection.</body>-->

DONE <!--<body package="Homeostat" selector="uniselectorActivatedAsCollectionOfArraysForAllUnits">uniselectorActivatedAsCollectionOfArraysForAllUnits 
	"Extracts the data about the activation of the uniselector  for all units  and returns them as an Ordered Collection of Arrays. Each array has all the values for a point in time"

	| aCollection  |
	aCollection := OrderedCollection new.
	states do: 
			[:each | 
			each isNil 
				ifFalse: 
					[
					  | dataPoint | 
					   dataPoint := OrderedCollection new .
					   each do: 
							[:value | 
							dataPoint add: value uniselectorActivated].
			aCollection add: dataPoint asArray]].




	^aCollection.</body>-->
</methods>

</st-source>
