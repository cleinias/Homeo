<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on April 8, 2013 at 10:34:17 am</time-stamp>


<class>
<name>HomeoMinimalGUI</name>
<environment>Smalltalk</environment>
<super>UI.ApplicationModel</super>
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

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeoMinimalGUI class</class-id> <category>interface specs</category>

<body package="Homeostat" selector="windowSpec">windowSpec
	"Tools.UIPainter new openOnClass: self andSelector: #windowSpec"

	&lt;resource: #canvas&gt;
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#label: 'Simulation general settings' 
			#bounds: #(#{Graphics.Rectangle} 512 384 792 544 ) ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 193 122 246 142 ) 
					#name: #OKButton 
					#label: 'Apply' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 122 122 175 142 ) 
					#name: #CancelButton 
					#label: 'Cancel' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 24 ) 
					#name: #maxRunsLabel 
					#label: 'Maximum runs' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 51 ) 
					#name: #dataFileLabel 
					#label: 'Results saved on:' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 25 79 ) 
					#name: #UnitNumberLabel 
					#label: 'Number of units: ' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 21 245 43 ) 
					#name: #maxRuns ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 48 245 70 ) 
					#name: #datafile ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 145 76 245 98 ) 
					#name: #unitsNumber ) ) ) )</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


</st-source>
