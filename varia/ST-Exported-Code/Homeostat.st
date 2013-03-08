<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:50 am</time-stamp>


<class>
<name>Homeostat</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>time homeoUnits microTime dataCollector collectsData isRunning slowingFactor </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>Homeostat class</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="new">new

^ super new initialize
</body>
</methods>

<methods>
<class-id>Homeostat class</class-id> <category>private-saving</category>

<body package="Homeostat" selector="homeoUnits:microTime:dataCollector:collectsData:">homeoUnits: homeostatHomeoUnits microTime: homeostatMicroTime dataCollector: homeostatDataCollector collectsData: homeostatCollectsData
	"used by the Boss mechanism to store a homeostat on a boss file"

^self new
	setHomeoUnits: homeostatHomeoUnits
	microTime: homeostatMicroTime
	dataCollector: homeostatDataCollector
	collectsData: homeostatCollectsData</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<comment>
<class-id>Homeostat</class-id>
<body>Homeostat manages the complete homeostat by taking care of the communication between the units and between the Units and the Uniselector. It stores a collection of units, and some state variables representing the general state of the Homeostat at any point in time. "Starting" (an instance of) this class is equivalent to turning the switch on  the electro-mechanical machine built by Ashby. Notice that this is typically done by the application class HomeoSimulation, which offers facilities for adding units, adding connections, selecting parameters pertaining to the homeostat (weights, etcetera) and pertaining to the simulation (number of iterations, print out and/or display of data, etcetera). Homeostat collaborates with DataCollector (an instance of which it holds) to record its states for any instant of time it goes through. However, it does not contain any facility for visualizing the data themselves.  If operated manually, an instance of Homeostat requires manually setting up the various parameters and does not offer any output.

Instance Variables:
	homeoUnits			&lt;Collection&gt;		the collection of homeoUnits making up the homeostat
	microTime			&lt;aNumber&gt;		the temporal scale regulating the communication among units (typically identical to the unit time)
	time					&lt;aNumber&gt;		the current time index (i.e., t)
	dataCollector 		&lt;aDataCollector&gt; the object recording the states of the homeostat
	collectsData 		&lt;aBoolean&gt;		whether or not the homeostat collects data about its run
	slowingFactor:		&lt;milliseconds&gt;     it slows down the simulation by inserting a slowingFactor wait after each cycle.
		
</body>
</comment>

<methods>
<class-id>Homeostat</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Sets the time to 0, and microTime to 0 as well, reflecting the default conditions of a Homeostat. Sets also some physical equivalence parameters"

	time := 0.
	microTime := 0.
	homeoUnits := OrderedCollection new.
	dataCollector := HomeoDataCollector new.
	collectsData := true. "default is to collect data. Can be turned off via accessor."
	slowingFactor := 10.


	 
	^self</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>testing</category>

<body package="Homeostat" selector="hasUnit:">hasUnit: aHomeoUnit

"check whether the Homeostat includes aHomeoUnit"

^homeoUnits includes: aHomeoUnit</body>

<body package="Homeostat" selector="homeoUnitsArePresent">homeoUnitsArePresent
	"Checks that the minimun number of units are present. This is set to one, but the method is here so it can be overriden in subclasses and/or changed in the future."

	^homeoUnits size &gt; 0.</body>

<body package="Homeostat" selector="homeoUnitsAreReady">homeoUnitsAreReady

"checks that all units are ready"

^ homeoUnits inject: true into:  [:aBoolResult :unit | aBoolResult	and: [unit isReadyToGo]].</body>

<body package="Homeostat" selector="isConnectedFrom:to:">isConnectedFrom: aHomeoUnit to: anotherUnit 


	((homeoUnits includes: aHomeoUnit) and: [homeoUnits includes: anotherUnit]) 
		ifTrue: [^anotherUnit isConnectedTo: aHomeoUnit]</body>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo
	"Checks that the homeostat has all the needed elements to start the simulation:
 - at least 1 homeoUnit
 - the homeoUnits are not missing any essential parameter
 - (Other conditions that are not fully clear yet to be added later)
"

	^self homeoUnitsArePresent and: [self homeoUnitsAreReady]</body>

<body package="Homeostat" selector="sameAs:">sameAs: aHomeostat
	"checks whether two homeostats are equivalent"


| result |

result := true.
"receiver is a homeostat"

( aHomeostat class = Homeostat)
	ifFalse: [^false].

"Same number of units"

(self homeoUnits size = aHomeostat homeoUnits size)
	ifFalse: [^false].

"equivalent units"

self homeoUnits 
	with: (aHomeostat homeoUnits)
		do: 
		[ :firstUnit :secondUnit |
		result := result and: [firstUnit sameAs: secondUnit]].


^result</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>running</category>

<body package="Homeostat" selector="fullReset">fullReset
"Resets the values of the units and  their connections to random values. resets time to 0."

self timeReset.
self randomizeValuesforAllUnits.
</body>

<body package="Homeostat" selector="runFor:">runFor: ticks
	"start the simulation by setting the units 'in motion' and runs for a certain number of ticks. This involves cycling though the units and asking them to update themselves, then collecting data for each unit
 	First checks that it has enough data to start"


| delay |
delay := Delay forMilliseconds: slowingFactor.

	self isReadyToGo 
		ifTrue: 
			[time isNil ifTrue: [time := 0].
			"TESTING
			Transcript show: 'INITIAL DATA AT TIME: '; 
					   show: time printString; 
					    show: 'and tick: '; show: ticks printString; cr.
	
	        	homeoUnits do: [:unit |           
					Transcript show: unit name printString;  show: '   '; 
				                           show: unit currentOutput printString; show: '    ';
							   show: 'dev: ';
							   show: unit criticalDeviation printString;  cr].
			END TESTING"
			[time &lt; (ticks)] whileTrue: [
				homeoUnits do: 
						[:unit | 
						collectsData ifTrue: [dataCollector at: time addDataUnitFor: unit.
						unit time: time.
						unit isActive ifTrue: [unit selfUpdate].
						]].
				self time: (self time + 1).
				delay wait ]]
		ifFalse: [Transcript show: 'Warning: Homeostat is not ready to start'].
	"TESTING
		Transcript show: 'FINAL DATA AT TIME: '; show: time  printString; show: 'and tick: '; show: ticks printString; cr.
		homeoUnits do: [:unit | Transcript show: unit name printString;  show: '   '; 
									    show: unit currentOutput printString; show: '    ';
									    show: 'dev: ';
									    show: unit criticalDeviation printString;  cr].
	END TESTING"</body>

<body package="Homeostat" selector="runOnce">runOnce

"advance the simulation by one tick"
| upTo |

upTo := time + 1.
self runFor: upTo.</body>

<body package="Homeostat" selector="start">start
	"start the simulation by setting the units 'in motion'. This involves cycling though the units and asking them to update themselves, then collecting data for each unit
 	First checks that it has enough data to start
	Notice that once started the Homeostat goes on forever. The only way to stop it is to send it the message stop."

	self isReadyToGo 
		ifTrue: 
			[time isNil ifTrue: [time := 0].
			isRunning := true.
			[isRunning] whileTrue: [
				homeoUnits do: 
						[:unit | 
						unit time: time.
						unit selfUpdate.
						collectsData ifTrue: [dataCollector at: time addDataUnitFor: unit].
						self time: (self time + 1)]]]
		ifFalse: [Transcript show: 'Warning: Homeostat is not ready to start']</body>

<body package="Homeostat" selector="stop">stop

"stop the homeostat's running by changing the value of the isRunning ivar to false. This procedure is equivalent, and indeed wants to simulate, turning the switch off on the physical equivalent of the homeostat"

isRunning := false.</body>

<body package="Homeostat" selector="timeReset">timeReset
"resets time to 0. Does not change the external values of the units or their connections, but do change their internal, computational values: input, nextdeviation, etcetera"

	self time: 0.
	homeoUnits do: [ :unit |
				unit clearFutureValues]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>adding</category>

<body package="Homeostat" selector="addConnectionWithRandomValuesFrom:to:">addConnectionWithRandomValuesFrom: unit1 to: unit2 
	"checks that the units exist, and adds a connection with random values by asking the receving unit to do the job"

	((homeoUnits includes: unit1) and: [homeoUnits includes: unit2]) 
		ifTrue: [unit2 addConnectionWithRandomValues: unit1]</body>

<body package="Homeostat" selector="addFullyConnectedUnit:">addFullyConnectedUnit: aHomeoUnit 
	"adds aHomeoUnit to the homeostat and creates connections between the new units and all other HomeoUnits already present. This latter task is actually delegated to the units themselves. Notice that the connection are uni-directional, and we need to add connections twice: from the new unit to the existing ones and from the exiting one to the new unit."

	homeoUnits do: 
			[:each | 
			each addConnectionWithRandomValues: aHomeoUnit.
			aHomeoUnit addConnectionWithRandomValues: each.
			each maxConnectedUnits: (homeoUnits size) + 1].		   "let the old units know that there may be a new connected unit."		
	aHomeoUnit maxConnectedUnits: homeoUnits size.                       "let the new unit know how many other units there may be."
	self addUnit: aHomeoUnit.
	self changed: #numberOfUnits</body>

<body package="Homeostat" selector="addUnit:">addUnit: aHomeoUnit 
	"adds a new unit to the homeostat"

	homeoUnits isNil ifTrue: [homeoUnits := OrderedCollection new].
	(homeoUnits includes: aHomeoUnit) 
		ifFalse: 
			[homeoUnits add: aHomeoUnit.
			self changed: #numberOfUnits]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>accessing</category>

<body package="Homeostat" selector="collectsData">collectsData
	^collectsData</body>

<body package="Homeostat" selector="collectsData:">collectsData: anObject
	collectsData := anObject</body>

<body package="Homeostat" selector="dataCollector">dataCollector
	^dataCollector</body>

<body package="Homeostat" selector="dataCollector:">dataCollector: anObject
	dataCollector := anObject</body>

<body package="Homeostat" selector="homeoUnits">homeoUnits
	^homeoUnits</body>

<body package="Homeostat" selector="homeoUnits:">homeoUnits: anObject
	homeoUnits := anObject</body>

<body package="Homeostat" selector="isRunning">isRunning
	^isRunning</body>

<body package="Homeostat" selector="isRunning:">isRunning: anObject
	isRunning := anObject</body>

<body package="Homeostat" selector="microTime">microTime
	^microTime</body>

<body package="Homeostat" selector="microTime:">microTime: anObject
	microTime := anObject</body>

<body package="Homeostat" selector="numberOfUnits">numberOfUnits

^ homeoUnits size</body>

<body package="Homeostat" selector="slowingFactor">slowingFactor
	^slowingFactor</body>

<body package="Homeostat" selector="slowingFactor:">slowingFactor: anObject
	slowingFactor := anObject.
	self changed: #slowingFactor.</body>

<body package="Homeostat" selector="time">time
	^time</body>

<body package="Homeostat" selector="time:">time: anObject
	time := anObject.
	self changed: #time</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>removing</category>

<body package="Homeostat" selector="removeConnectionFrom:to:">removeConnectionFrom: unit1 to: unit2 
	"removes a connections between two units by asking the receiving unit (unit2) to remove the inmputConnection coming from unit1"

	((homeoUnits includes: unit1) and: [homeoUnits includes: unit2]) 
		ifTrue: 
			[(self isConnectedFrom: unit1 to: unit2) 
				ifTrue: [unit2 removeConnectionFromUnit: unit1]]</body>

<body package="Homeostat" selector="removeUnit:">removeUnit: aHomeoUnit 
	"remove a unit from the homeostat. Must also remove all the connections originating from the unit"

	(homeoUnits includes: aHomeoUnit) 
		ifTrue: 
			[homeoUnits remove: aHomeoUnit.
			homeoUnits do: [:each | each removeConnectionFromUnit: aHomeoUnit].
			self changed: #numberOfUnits]
		ifFalse: [Transcript show: 'Warning: trying to remove the unit ', (aHomeoUnit name), ', which is not part of  the Homeostat';cr]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>units managing</category>

<body package="Homeostat" selector="randomizeValuesFor:">randomizeValuesFor: aHomeoUnit 
	"resets the values of a unit to random values"

	(homeoUnits includes: aHomeoUnit) 
		ifFalse: [^self]
		ifTrue: [(homeoUnits detect: [:unit | unit = aHomeoUnit]) setRandomValues]</body>

<body package="Homeostat" selector="randomizeValuesforAllUnits">randomizeValuesforAllUnits
"resets all units to random values"

homeoUnits do: [:each | 
				self randomizeValuesFor: each. 
				each randomizeAllConnectionValues].</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>saving</category>

<body package="Homeostat" selector="bossOutOn:">bossOutOn: aFilename 
	"bosses itself out on a file opened on aFilename. It will erase the old content of aFilename."

	| boss homeoCopy |
	homeoCopy := self copyWithoutDependents.
	boss := BinaryObjectStorage onNew: aFilename writeStream.
	[boss nextPut: homeoCopy] ensure: [boss close]</body>

<body package="Homeostat" selector="copyWithoutDependents">copyWithoutDependents
	"returns a copy of the homeostat with no dependents in the homeostat, homeoUnits, or homeoConnections"

	| trueCopy homeoCopy |
	trueCopy := self generalCopy.
	homeoCopy := trueCopy copy breakDependents.
	homeoCopy homeoUnits do: 
			[:unit | 
			unit inputConnections do: 
					[:conn | 
"					|  connCachedDeps incomingUnitCachedDeps |
					connCachedDeps := conn dependents.
					incomingUnitCachedDeps := conn incomingUnit dependents.
"					conn incomingUnit breakDependents.
					conn breakDependents].
			unit breakDependents].
	^homeoCopy</body>

<body package="Homeostat" selector="flushData">flushData

"clears all data from aDataCollector"

self initializeDataCollection.
</body>

<body package="Homeostat" selector="initializeDataCollection">initializeDataCollection

"trashes the dataCollector, effectively flushing all collected data"

dataCollector := HomeoDataCollector new.</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>private-saving</category>

<body package="Homeostat" selector="setHomeoUnits:microTime:dataCollector:collectsData:">setHomeoUnits: homeostatHomeoUnits microTime: homeostatMicroTime dataCollector: homeostatDataCollector collectsData: homeostatCollectsData
	"used by the Boss mechanism to store a homeostat on a boss file"

homeoUnits := homeostatHomeoUnits. 
microTime:= homeostatMicroTime.
dataCollector := homeostatDataCollector.
collectsData := homeostatCollectsData.</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>private-updating</category>

<body package="Homeostat" selector="allChanged">allChanged
	"informs all dependentss that each aspect may have changed"

	self changed: #slowingFactor.
	self changed: #time.
	self changed: #numberOfUnits.
	homeoUnits 
		do:[
			:unit |
			unit allChanged]</body>
</methods>

<methods>
<class-id>Homeostat</class-id> <category>printing</category>

<body package="Homeostat" selector="printOn:">printOn: aStream
	"personalized view of the homeostat. Default begavior so far."


super printOn: aStream.
</body>
</methods>

</st-source>
