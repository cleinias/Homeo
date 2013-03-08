<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:41 am</time-stamp>


<class>
<name>HomeoSimulation</name>
<environment>Smalltalk</environment>
<super>Core.Object</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>maxRuns homeostat datafile </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoSimulation class</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="new">new

^ super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<comment>
<class-id>HomeoSimulation</class-id>
<body>HomeoSimulation is the class that manages a complete run of the Homeostat. It takes care of the administrative task: setting up the initial conditions, starting and stopping the simulation. It also knows how to read initial conditions from a file (for repeated experiments). The real work of simulating the Homeostat is done by the Homeostat class---an instance of which is held by the simulation---and its components.

Instance Variables:
	homeostat		&lt;aHomeostat&gt;		description of homeostat
	maxRuns		&lt;anInteger&gt;		description of maxRuns
	dataFile           &lt;aString&gt;              the string corresponding to the filename the simulation data should be saved on. 


</body>
</comment>

<methods>
<class-id>HomeoSimulation</class-id> <category>testing</category>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo

"checks that the homeostat is ready to go and that the maxRuns and datafile are present"

^ (homeostat isReadyToGo and: [maxRuns notNil]) and: [datafile asFilename isWritable]</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"initializes the instance with a new homestat and a default number of runs."

	homeostat := Homeostat new.
	maxRuns:= 1000.
	datafile := self createDefaultDatafile.
	^self</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>running</category>

<body package="Homeostat" selector="runForever">runForever

"start the homeostat and runs it indefinitely. The homeostat can be stopped by sending #stop to the simulation"

homeostat start</body>

<body package="Homeostat" selector="start">start
"runs the homeostat for the number of runs specified in maxRuns"

homeostat runFor: maxRuns.</body>

<body package="Homeostat" selector="stop">stop 

homeostat stop</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>adding</category>

<body package="Homeostat" selector="addFullyConnectedUnit:">addFullyConnectedUnit: aHomeoUnit

homeostat addFullyConnectedUnit: aHomeoUnit.
self changed: #units</body>

<body package="Homeostat" selector="addUnit:">addUnit: aHomeoUnit

homeostat addUnit: aHomeoUnit
</body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>accessing</category>

<body package="Homeostat" selector="datafile">datafile
	^datafile</body>

<body package="Homeostat" selector="datafile:">datafile: anObject
	datafile := anObject</body>

<body package="Homeostat" selector="homeostat">homeostat
	^homeostat</body>

<body package="Homeostat" selector="homeostat:">homeostat: anObject
	homeostat := anObject</body>

<body package="Homeostat" selector="maxRuns">maxRuns
	^maxRuns</body>

<body package="Homeostat" selector="maxRuns:">maxRuns: anObject
	maxRuns := anObject</body>

<body package="Homeostat" selector="units">units

^homeostat homeoUnits size </body>
</methods>

<methods>
<class-id>HomeoSimulation</class-id> <category>saving</category>

<body package="Homeostat" selector="createDefaultDatafile">createDefaultDatafile

"creates a default strings corresponding to the datafile. Checks that no file with same name exists in current directory"
|name dateString number completeName now|

now := Timestamp now.
dateString:=  now month printString, '-', now day printString, '-',now year printString.
name := 'HomeoSimulationData'.

number := 1.
completeName := name,'-',dateString,'-',number printString.

[completeName asFilename definitelyExists]
	whileTrue: [number := number+1.
				completeName := name,'-',dateString,'-',number].

^completeName</body>

<body package="Homeostat" selector="saveCompleteRunOnFile">saveCompleteRunOnFile
	"asks the datacollector of the homestat to save all data on datafile"

	| stream |
	stream := WriteStream on: datafile asFilename.
	homeostat dataCollector printCompleteDataOn: stream.
	stream close</body>

<body package="Homeostat" selector="saveEssentialDataOnFile">saveEssentialDataOnFile
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := WriteStream on: datafile asFilename.
	homeostat dataCollector printEssentialDataOn: stream.
	stream close</body>

<body package="Homeostat" selector="saveEssentialDataOnFileWithSeparator:">saveEssentialDataOnFileWithSeparator: aCharacter
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := datafile asFilename writeStream.
	

	homeostat dataCollector saveEssentialsOn:  stream separator: aCharacter.
	stream close</body>
</methods>

</st-source>
