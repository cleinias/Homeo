<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on March 8, 2013 at 9:05:37 am</time-stamp>


<class>
<name>HomeoNoiseTest</name>
<environment>Smalltalk</environment>
<super>XProgramming.SUnit.TestCase</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>unit noise </inst-vars>
<class-inst-vars></class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoNoiseTest class</class-id> <category>instance creation</category>

<body package="Homeostat" selector="new">new
	"Answer a newly created and initialized instance."

	^super new initialize</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoNoiseTest</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="initialize">initialize
	"Initialize a newly created instance. This method must answer the receiver."

	" *** Replace this comment with the appropriate initialization code *** "
	^self</body>

<body package="Homeostat" selector="setUp">setUp
	"sets up the test with a Homeostat unit and a noise object"

unit := HomeoUnit new.
noise := HomeoNoise new.</body>
</methods>

<methods>
<class-id>HomeoNoiseTest</class-id> <category>running</category>

<body package="Homeostat" selector="testDegradingConstantLinearNoise">testDegradingConstantLinearNoise


|  values tests |

values := SortedCollection new.
unit setRandomValues.
tests := 100.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.

noise constant; degrading; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].

self assert: (values size) = tests.
self assert: (values first sign) = (unit criticalDeviation sign * -1).
self assert:	((values first abs) = (unit noise)).
self assert:	((values last abs) = (unit noise)).</body>

<body package="Homeostat" selector="testDegradingConstantProportionalNoise">testDegradingConstantProportionalNoise


|  values  tests|

tests := 100.
values := SortedCollection new.
unit setRandomValues.

noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.

noise constant; degrading; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.
self assert: (values first  sign) = (unit criticalDeviation sign * -1).
self assert:	((values first abs) = ((unit noise)*unit criticalDeviation abs)).
self assert:	((values last abs) = ((unit noise)*unit criticalDeviation abs)).</body>

<body package="Homeostat" selector="testDegradingNormalLinearNoise">testDegradingNormalLinearNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	2 * (unit noise) * tolerance.
	2* (unit noise) * (1 - tolerance).


	noise
		normal;
		degrading;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


"Check if noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: (((noiseValue sign) = (unit criticalDeviation sign * -1)) or: [noiseValue = 0])].


values first &gt;= 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].


"Check mean"
self assert: ((mean &gt;= (unit noise * (1 - tolerance))) and: [mean &lt;= (unit noise * (1+ tolerance))]).


"Check all values within {0, 2* noise} interval"
self assert: (minAbsNoise &gt;= 0 and: [maxAbsNoise &lt;= (2 * unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {1/3 noise, 5/3 * noise}, with mu= noise and sigma = 1/3 noise (which is what I need to have all values between 0 and 2* noise"

coll := values select: [:noiseValue | noiseValue abs &gt; (unit noise * 1/3) and: [noiseValue abs &lt;= (unit noise * 5/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {2/3 * noise, 4/3 noise}"

coll := values select: [:noiseValue | noiseValue abs &gt; (unit noise * 2/3) and: [noiseValue abs &lt;= (unit noise * 4/3)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDegradingNormalProportionalNoise">testDegradingNormalProportionalNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	2 * (unit noise) * tolerance.
	2* (unit noise) * (1 - tolerance).


	noise
		normal;
		degrading;
		proportional.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


"Check if noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: (((noiseValue sign) = (unit criticalDeviation sign * -1)) or: [noiseValue = 0])].


values first &gt;= 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].


"Check mean---should be noise * current abs (+/- tolerance) "
self assert: ((mean &gt;= ((unit noise * unit criticalDeviation abs) * (1 - tolerance))) and: [mean &lt;= ((unit noise * unit criticalDeviation abs) * (1+ tolerance))]).


"Check all values within {0, 2* noise*current abs} interval"
self assert: (minAbsNoise &gt;= 0 and: [maxAbsNoise &lt;= (2 * unit noise* unit criticalDeviation abs)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {1/3 noise * current abs, 5/3 * noise* current abs}, with mu= noise and sigma = 1/3 noise * current abs(which is what I need to have all values between 0 and 2* noise"

coll := values select: [:noiseValue | noiseValue abs&gt; (unit noise * 1/3* unit criticalDeviation abs) and: [noiseValue abs &lt;= (unit noise * 5/3 *unit criticalDeviation abs)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {2/3 * noise*current abs, 4/3 noise * current abs}"

coll := values select: [:noiseValue | noiseValue abs&gt; (unit noise * 2/3 *unit criticalDeviation abs) and: [noiseValue abs &lt;= (unit noise * 4/3 *unit criticalDeviation abs)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDegradingUniformLinearNoise">testDegradingUniformLinearNoise


|  values tests tolerance mean lowThreshold highThreshold minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.
lowThreshold :=  2 * (unit noise) * tolerance.
highThreshold := 2* (unit noise) * (1 - tolerance).



noise uniform; degrading; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"Check noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: ((noiseValue sign) = (unit criticalDeviation sign * -1)).].

"checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*unit noise,   (with a tolerance indicated by 'tolerance'')"
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	((minAbsNoise &gt;= 0)  and: [minAbsNoise &lt;= lowThreshold]).
self assert: ((maxAbsNoise &lt;= (2 * unit noise)) and: [ maxAbsNoise &gt;= highThreshold]). 

"checks the mean of the noise values are about equal to unit noise"
self assert:  ((mean &gt;= ((unit noise ) * (1 - tolerance)))
 
			and: [mean &lt;= ((unit noise) * (1+ tolerance ))]).</body>

<body package="Homeostat" selector="testDegradingUniformProportionalNoise">testDegradingUniformProportionalNoise


|  values tests tolerance mean lowThreshold highThreshold minAbsNoise maxAbsNoise |
tolerance := 0.05.
values:= SortedCollection new.
unit setRandomValues.

tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.
lowThreshold :=  2 * (unit noise * (unit criticalDeviation abs)) * tolerance.
highThreshold := 2* (unit noise*(unit criticalDeviation abs)) * (1 - tolerance).



noise uniform; degrading; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"Check noise's sign is always opposite to current's sign"
values do: [:noiseValue | self assert: ((noiseValue sign) = (unit criticalDeviation sign * -1)).].


"checks min and max values of noise values are within boundaries of distribution, i.e. 0 and 2*(unit noise/unit noise current abs),   (with a tolerance indicated by 'tolerance'')"
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise&gt;= 0  and: [minAbsNoise &lt;= lowThreshold]).
self assert: ((maxAbsNoise &lt;= (2 * unit noise)) and: [ maxAbsNoise &gt;= highThreshold]).

"checks the mean of the noise values are about equal to unit noise"
self assert:  ((mean &gt;= ((unit noise *(unit criticalDeviation abs )) * (1 - tolerance)) )
 
			and: [mean &lt;= ((unit noise*(unit criticalDeviation abs)) * (1+ tolerance ))]).</body>

<body package="Homeostat" selector="testDistortingConstantLinearNoise">testDistortingConstantLinearNoise
	
| values signs tests positives tolerance |
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.07.
	unit setRandomValues.
	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	noise
		constant;
		distorting;
		linear.
	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.

	"test whether the sign of the noise value is about 50% of the times positive and 50% negative. Chooses 'tolerance' as  threshold"
	positives := (signs select: [:item | item = 1]) size.
	(signs select: [:item | item = -1]) size.
	self assert: (positives / (signs size / 2) &gt;= (1 - tolerance) 
				and: [positives / (signs size / 2) &lt;= (1 + tolerance)]).

	"test the value of the noise produced"
	self assert: values first abs = unit noise.
	self assert: values last abs = unit noise</body>

<body package="Homeostat" selector="testDistortingConstantProportionalNoise">testDistortingConstantProportionalNoise
	
| values signs tests positives tolerance |
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.07.
	unit setRandomValues.
	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	noise
		constant;
		distorting;
		proportional.
	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.

	"test whether the sign of the noise value is about 50% of the times positive and 50% negative. Chooses 'tolerance' as  threshold"
	positives := (signs select: [:item | item = 1]) size.
	(signs select: [:item | item = -1]) size.
	self assert: (positives / (signs size / 2) &gt;= (1 - tolerance) 
				and: [positives / (signs size / 2) &lt;= (1 + tolerance)]).

	"test the value of the noise produced"
	self assert:	((values first abs) = ((unit noise)*unit criticalDeviation abs)).
	self assert:	((values last abs) = ((unit noise)*unit criticalDeviation abs)).</body>

<body package="Homeostat" selector="testDistortingNormalLinearlNoise">testDistortingNormalLinearlNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minAbsNoise := values first abs.
maxAbsNoise := values last abs.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {-noise, +noise} interval"
self assert: (minAbsNoise &gt;= (unit noise negated)  and: [maxAbsNoise &lt;= (unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 noise, 2/3 * noise}, with mu= 0 and sigma = 1/3 noise (which is what I need to have all values between -noise and +noise"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 2/3 negated) and: [noiseValue &lt;= (unit noise * 2/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise, 1/3 noise}"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 1/3 negated) and: [noiseValue &lt;= (unit noise * 1/3)]].
self assert: (((coll size/ tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingNormalLinearNoise">testDistortingNormalLinearNoise
| values signs tests  tolerance  mean minAbsNoise maxAbsNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		linear.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minAbsNoise := values first abs.
maxAbsNoise := values last abs.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {-noise, +noise} interval"
self assert: (minAbsNoise &gt;= (unit noise negated)  and: [maxAbsNoise &lt;= (unit noise)]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 noise, 2/3 * noise}, with mu= 0 and sigma = 1/3 noise (which is what I need to have all values between -noise and +noise"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 2/3* -1) and: [noiseValue &lt;= (unit noise * 2/3)]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise, 1/3 noise}"

coll := values select: [:noiseValue | noiseValue &gt; (unit noise * 1/3 negated) and: [noiseValue &lt;= (unit noise * 1/3)]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingNormalProportionalNoise">testDistortingNormalProportionalNoise
| values signs tests  tolerance  mean minNoise maxNoise coll|
	
	tests := 1000.
	signs := SortedCollection new.
	values := SortedCollection new.
	tolerance := 0.05.
	unit setRandomValues.
"temp test"
"unit noise: 0.1.
unit criticalDeviation:  -0.1."

"end temp test"

	noise := HomeoNoise newWithCurrent: unit criticalDeviation
				andNoise: unit noise.
	

	noise
		normal;
		distorting;
		proportional.

	1 to: tests
		do: 
			[:index | 
			| noiseValue |
			noiseValue := noise getNoise.
			values add: noiseValue.
			signs add: noiseValue sign].
	self assert: values size = tests.


minNoise := values first.
maxNoise := values last.
mean := (values inject: 0 into: [:sum :element | sum + element])   / values size.

"Check mean is around 0 (plus or minus tolerance)"
self assert: ((mean &gt;= (0 -  tolerance)) and: [mean &lt;= (0 + tolerance)]).


"Check all values within {(current * -noise), (current * noise} interval"
self assert: (minNoise &gt;= ((unit noise negated)* unit criticalDeviation abs)  and: [maxNoise &lt;= ((unit noise) * (unit criticalDeviation abs) )]).

"Check 95% of values (with tolerance) within 2 sigma, i.e. in the interval {-2/3 * noise * current, 2/3 * noise * current }, with mu= 0 and sigma = 1/3 noise * current (which is what I need to have all values between -noise * current  and +noise * current"

coll := values select: [:noiseValue | noiseValue &gt; ((unit noise * 2/3* -1) * (unit criticalDeviation abs)) and: [noiseValue &lt;= ((unit noise * 2/3) * (unit criticalDeviation abs))]].
self assert: (((coll size/tests) &gt;= (0.95 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.95)]).



"Check 68% of values (with tolerance) within 1 sigma, i.e. in the interval {-1/3 * noise * current, 1/3 noise * current}"

coll := values select: [:noiseValue | noiseValue &gt; ((unit noise * 1/3* -1) * (unit criticalDeviation abs)) and: [noiseValue &lt;=  ((unit noise * 1/3) * (unit criticalDeviation abs))]].
self assert: (((coll size/tests) &gt;= (0.68 * (1-tolerance))) and: [(coll size /tests) &lt;= ((1+ tolerance) * 0.68)]).</body>

<body package="Homeostat" selector="testDistortingUniformLinearNoise">testDistortingUniformLinearNoise


|  values tests tolerance mean minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.




noise uniform; distorting; linear.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"checks min and max values of noise values are within boundaries of distribution, i.e. [- unit noise , unit noise] "
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise &gt;= unit noise negated).
self assert: (maxAbsNoise &lt;= unit noise). 

"checks the mean of the noise values are about equal to 0"
self assert:  ((mean &gt;= (0  - tolerance)) 
			and: [mean &lt;= (0+  tolerance )]).</body>

<body package="Homeostat" selector="testDistortingUniformProportionalNoise">testDistortingUniformProportionalNoise


|  values tests tolerance mean minAbsNoise maxAbsNoise|
tolerance := 0.1.
values:= SortedCollection new.
unit setRandomValues.


tests := 1000.
noise := HomeoNoise newWithCurrent: unit criticalDeviation andNoise: unit noise.




noise uniform; distorting; proportional.

1 to: tests do: [ :index |
		values add:  noise getNoise.].
self assert: (values size) = tests.

"checks min and max values of noise values are within boundaries of distribution, i.e. [- unit noise *current abs, unit noise *current abs] "
values first &gt; 0 ifTrue:
				[ minAbsNoise := values first abs.
				  maxAbsNoise := values last abs.
				  mean := (values inject: 0 into: [:sum :element | sum + element])   / values size]
			ifFalse:
			 	[minAbsNoise := values last abs.
				 maxAbsNoise := values first abs.
				mean := (values inject: 0 into: [:sum :element | sum + element]) *-1  / values size.].
	
self assert:	(minAbsNoise &gt;= (unit noise negated * unit criticalDeviation abs)).
self assert: (maxAbsNoise &lt;= (unit noise  * unit criticalDeviation abs)). 

"checks the mean of the noise values are about equal to 0"
self assert:  ((mean &gt;= (0  - tolerance)) 
			and: [mean &lt;= (0+  tolerance )]).</body>
</methods>

</st-source>
