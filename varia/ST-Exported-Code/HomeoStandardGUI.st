<?xml version="1.0"?>

<st-source>
<time-stamp>From VisualWorks® NonCommercial, 7.4 of December 5, 2005 on April 8, 2013 at 10:34:07 am</time-stamp>


<class>
<name>HomeostatStandardGUI</name>
<environment>Smalltalk</environment>
<super>UI.ApplicationModel</super>
<private>false</private>
<indexed-type>none</indexed-type>
<inst-vars>homeostat dataAreSaved datafile maxRuns slowingFactor currentRun uniselectorActiveChoices simulProcess dataChart controlPanelBuilder debugMode showUniselectorActionMode graphicView </inst-vars>
<class-inst-vars>maxRuns </class-inst-vars>
<imports></imports>
<category>Homeostat</category>
<attributes>
<package>Homeostat</package>
</attributes>
</class>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<methods>
<class-id>HomeostatStandardGUI class</class-id> <category>interface specs</category>

<body package="Homeostat" selector="homeoControlSpec">homeoControlSpec
	"Tools.UIPainter new openOnClass: self andSelector: #homeoControlSpec"

	<resource: #canvas>
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#properties: #(#{UI.PropertyListDictionary} #sizeAutoSave true #positionAutoSave true #sizeType #lastSavedSize #openType #advanced #positionType #lastSavedPosition ) 
			#label: 'Homeostat control panel' 
			#min: #(#{Core.Point} 515 200 ) 
			#max: #(#{Core.Point} 515 200 ) 
			#bounds: #(#{Graphics.Rectangle} 640 128 1155 328 ) 
			#flags: 8 ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 9 4 ) 
					#name: #Label1 
					#label: 'Homeostat:' 
					#style: #systemDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 9 24 204 41 ) 
					#name: #datafileInputField 
					#model: #datafile 
					#style: #systemDefault 
					#isReadOnly: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 137 100 158 ) 
					#name: #ActionButton1 
					#model: #saveHomeostatOnFile 
					#label: 'Save' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 110 100 131 ) 
					#name: #ActionButton2 
					#model: #readHomeostat 
					#label: 'Load' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 137 206 158 ) 
					#name: #ActionButton3 
					#model: #simulationGraph 
					#label: 'Graph' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 6 ) 
					#name: #Label2 
					#label: 'Max runs' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 6 368 23 ) 
					#name: #maxRunsInputField 
					#model: #maxRuns 
					#type: #number 
					#formatString: '#,##0' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 165 100 186 ) 
					#name: #ActionButton4 
					#model: #homeostatInspect 
					#label: 'Inspect' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 27 ) 
					#name: #Label3 
					#label: 'Current time' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 30 368 47 ) 
					#name: #currentRunInputField 
					#model: #currentRun2 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 30 497 51 ) 
					#name: #ActionButton5 
					#model: #resetTime 
					#label: 'Reset time' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 6 38 ) 
					#name: #Label4 
					#label: 'No. of units' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 82 39 112 60 ) 
					#name: #InputField4 
					#flags: 0 
					#model: #homeoUnits 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 51 ) 
					#name: #Label5 
					#label: 'Slowing factor' 
					#style: #pixelDefault ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 315 54 368 71 ) 
					#name: #slowingFactorInputField 
					#model: #slowingFactor 
					#type: #number ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 6 497 27 ) 
					#name: #ActionButton6 
					#model: #resetUnitValues 
					#label: 'Reset unit values' 
					#style: #default 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 232 165 305 185 ) 
					#name: #ActionButton7 
					#model: #stopProcess 
					#label: 'Stop' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 329 165 402 185 ) 
					#name: #ActionButton8 
					#model: #startNewProcess 
					#label: 'Go' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 426 165 499 185 ) 
					#name: #ActionButton9 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #black ) 
						#setBackgroundColor: #(#{Graphics.ColorValue} 1024 4607 8191 ) ) 
					#model: #stepSimulation 
					#label: 'Step' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 70 ) 
					#name: #Label6 
					#label: '(millisec.)' ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 213 4 217 184 ) 
					#name: #Divider1 
					#orientation: #vertical ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 54 497 75 ) 
					#name: #DebugModeActionButton 
					#model: #toggleDebugMode 
					#label: 'Debug Mode' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 382 80 497 107 ) 
					#name: #showUniselectorActionButton 
					#model: #toggleShowUniselectorAction 
					#label: 'Show Unis. Action' 
					#defaultable: true ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 375 176 391 ) 
					#name: #ComboBox1 
					#model: #Unit2ConnectStatusUnit24 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 357 176 373 ) 
					#name: #ComboBox2 
					#model: #Unit2ConnectStatusUnit23 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 338 176 354 ) 
					#name: #ComboBox3 
					#model: #Unit2ConnectStatusUnit22 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 319 176 335 ) 
					#name: #ComboBox4 
					#model: #Unit2ConnectStatusUnit21 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 109 206 130 ) 
					#name: #ActionButton11 
					#model: #savePlotDataOnFile 
					#label: 'Save plot data' 
					#defaultable: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 6 57 ) 
					#name: #Label7 
					#label: 'Homeostat actions' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 130 57 ) 
					#name: #Label8 
					#label: 'Data actions' ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 115 82 206 103 ) 
					#name: #ActionButton10 
					#model: #saveAllDataOnFile 
					#label: 'Save all data' 
					#defaultable: true ) 
				#(#{UI.ActionButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 9 81 100 102 ) 
					#name: #NewHomeostatActionButton 
					#model: #newHomeostat 
					#label: 'New' 
					#defaultable: true ) ) ) )</body>

<body package="Homeostat" selector="homeostatSpec">homeostatSpec
	"Tools.UIPainter new openOnClass: self andSelector: #homeostatSpec"

	<resource: #canvas>
	^#(#{UI.FullSpec} 
		#window: 
		#(#{UI.WindowSpec} 
			#properties: #(#{UI.PropertyListDictionary} #sizeType #specifiedSize #positionType #screenCenter #openType #advanced ) 
			#label: 'Homeostat Standard' 
			#min: #(#{Core.Point} 20 20 ) 
			#max: #(#{Core.Point} 0 0 ) 
			#bounds: #(#{Graphics.Rectangle} 1608 352 2258 1142 ) ) 
		#component: 
		#(#{UI.SpecCollection} 
			#collection: #(
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} -158 -219 ) 
					#name: #Label 
					#label: 'State' ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 46 598 198 ) 
					#name: #Unit1DeviationSlider 
					#model: #Unit1SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 96 565 113 ) 
					#name: #Unit1CriticalDeviationField 
					#model: #Unit1Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 82 107 99 ) 
					#name: #Unit1OuputInputID 
					#model: #Unit1Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 80 ) 
					#name: #Unit1OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 25 110 50 ) 
					#name: #Unit1NameInput 
					#model: #unit1Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 80 ) 
					#name: #Unit1DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 47 571 63 ) 
					#name: #UnitHighRangeInput 
					#flags: 0 
					#model: #unit1HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 184 571 200 ) 
					#name: #UnitLowRangeInput 
					#flags: 0 
					#model: #unit1LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 129 112 145 ) 
					#name: #Unit1ConnectUnit11InputID 
					#model: #Unit1ConnectUnit11 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 147 112 163 ) 
					#name: #Unit1ConnectUnit12InputID 
					#model: #Unit1ConnectUnit12 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 166 112 182 ) 
					#name: #Unit1ConnectUnit13InputID 
					#model: #Unit1ConnectUnit13 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 184 112 200 ) 
					#name: #Unit1ConnectUnit14InputID 
					#model: #Unit1ConnectUnit14 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 113 ) 
					#name: #Unit1ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 112 ) 
					#name: #Unit1ConnectionsLabel 
					#label: 'Name' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 131 272 145 ) 
					#name: #Unit1WeightSpin11ID 
					#model: #Unit1WeightSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 168 272 182 ) 
					#name: #Unit1WeightSpin12ID 
					#model: #Unit1WeightSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 186 272 200 ) 
					#name: #Unit1WeightSpin14ID 
					#model: #Unit1WeightSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 149 272 163 ) 
					#name: #Unit1WeightSpin12ID 
					#model: #Unit1WeightSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 113 ) 
					#name: #Unit1ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 114 ) 
					#name: #Unit1ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 132 430 146 ) 
					#name: #Unit1NoiseSpin11ID 
					#model: #Unit1NoiseSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 150 430 164 ) 
					#name: #Unit1NoiseSpin12 
					#model: #Unit1NoiseSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 169 430 183 ) 
					#name: #Unit1NoiseSpin13ID 
					#model: #Unit1NoiseSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 187 430 201 ) 
					#name: #Unit1NoiseSpin14ID 
					#model: #Unit1NoiseSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 114 ) 
					#name: #Unit1ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 114 ) 
					#name: #Unit1ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 132 350 146 ) 
					#name: #Unit1SwitchtSpin11ID 
					#model: #Unit1SwitchSpin11 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 150 350 164 ) 
					#name: #Unit1SwitchtSpin12ID 
					#model: #Unit1SwitchSpin12 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 169 350 183 ) 
					#name: #Unit1SwitchtSpin13ID 
					#model: #Unit1SwitchSpin13 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 187 350 201 ) 
					#name: #Unit1SwitchtSpin14ID 
					#model: #Unit1SwitchSpin14 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 186 538 201 ) 
					#name: #Unit1UniselectorActiveCombo14 
					#model: #Unit1UniselectorActive14 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 168 538 183 ) 
					#name: #Unit1UniselectorActiveCombo13 
					#model: #Unit1UniselectorActive13 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 149 538 164 ) 
					#name: #Unit1UniselectorActiveCombo12 
					#model: #Unit1UniselectorActive12 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 131 538 146 ) 
					#name: #Unit1UniselectorComboActive11 
					#model: #Unit1UniselectorActive11 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 0 207 619 211 ) 
					#name: #Divider2 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} -2 399 617 403 ) 
					#name: #Divider3 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 2 591 621 595 ) 
					#name: #Divider4 ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 216 109 241 ) 
					#name: #Unit2NameInput 
					#model: #unit2Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 271 ) 
					#name: #Unit2OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 271 107 288 ) 
					#name: #Unit2OutputInputID 
					#model: #Unit2Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 238 571 254 ) 
					#name: #unit2HighRangeInput 
					#flags: 0 
					#model: #unit2HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 240 598 392 ) 
					#name: #Unit2DeviationSlider 
					#model: #Unit2SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 271 ) 
					#name: #Unit2DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 287 565 304 ) 
					#name: #Unit2CriticalDeviationField 
					#model: #Unit2Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 305 ) 
					#name: #Unit2ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 322 538 337 ) 
					#name: #Unit2UniselectorComboActive21 
					#model: #Unit2UniselectorActive21 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 340 538 355 ) 
					#name: #Unit2UniselectorComboActive12 
					#model: #Unit2UniselectorActive22 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 359 538 374 ) 
					#name: #Unit2UniselectorComboActive23 
					#model: #Unit2UniselectorActive23 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 377 538 392 ) 
					#name: #Unit2UniselectorComboActive24 
					#model: #Unit2UniselectorActive24 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 305 ) 
					#name: #Unit2ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 323 430 337 ) 
					#name: #Unit2NoiseSpin21ID 
					#model: #Unit2NoiseSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 341 430 355 ) 
					#name: #Unit2NoiseSpin22ID 
					#model: #Unit2NoiseSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 360 430 374 ) 
					#name: #Unit2NoiseSpin23ID 
					#model: #Unit2NoiseSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 378 430 392 ) 
					#name: #Unit2NoiseSpin24ID 
					#model: #Unit2NoiseSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 305 ) 
					#name: #Unit2ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 323 350 337 ) 
					#name: #Unit2SwitchSpin21ID 
					#model: #Unit2SwitchSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 341 350 355 ) 
					#name: #Unit2SwitchSpin22ID 
					#model: #Unit2SwitchSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 360 350 374 ) 
					#name: #Unit2SwitchSpin23ID 
					#model: #Unit2SwitchSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 378 350 392 ) 
					#name: #Unit2SwitchSpin24ID 
					#model: #Unit2SwitchSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 304 ) 
					#name: #Unit2ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 322 272 336 ) 
					#name: #Unit2WeightSpin21ID 
					#model: #Unit2WeightSpin21 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 340 272 354 ) 
					#name: #Unit2WeightSpin22ID 
					#model: #Unit2WeightSpin22 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 359 272 373 ) 
					#name: #Unit2WeightSpin23ID 
					#model: #Unit2WeightSpin23 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 377 272 391 ) 
					#name: #Unit2WeightSpin24ID 
					#model: #Unit2WeightSpin24 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 304 ) 
					#name: #Unit2ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 303 ) 
					#name: #Unit2ConnectionsLabel 
					#label: 'Name' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 319 112 335 ) 
					#name: #Unit2ConnectUnit11InputID 
					#model: #Unit2ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 338 112 354 ) 
					#name: #Unit2ConnectUnit12InputID 
					#model: #Unit2ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 357 112 373 ) 
					#name: #Unit2ConnectUnit13InputID 
					#model: #Unit2ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 14 375 112 391 ) 
					#name: #Unit2ConnectUnit14InputID 
					#model: #Unit2ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 539 375 573 391 ) 
					#name: #unit2LowRangeInput 
					#flags: 0 
					#model: #unit2LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 407 110 432 ) 
					#name: #unit3NameInput 
					#model: #unit3Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 462 ) 
					#name: #Unit3OutputLabel 
					#label: 'Output' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 464 107 481 ) 
					#name: #Unit3OutputInputID 
					#model: #Unit3Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 537 429 571 445 ) 
					#name: #unit3HighRangeInput 
					#flags: 0 
					#model: #unit3HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 573 431 598 583 ) 
					#name: #Unit3DeviationSlider 
					#model: #Unit3SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 516 462 ) 
					#name: #Unit3DeviationLabel 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 523 478 565 495 ) 
					#name: #Unit3CriticalDeviationField 
					#model: #Unit3Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 539 566 573 582 ) 
					#name: #unit3LowRangeInput 
					#flags: 0 
					#model: #unit3LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 496 ) 
					#name: #Unit2ConnectUniselectorLabel 
					#label: 'Uniselector is:' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 513 538 528 ) 
					#name: #Unit3UniselectorComboActive31 
					#model: #Unit3UniselectorActive31 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 531 538 546 ) 
					#name: #Unit3UniselectorComboActive32 
					#model: #Unit3UniselectorActive32 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 550 538 565 ) 
					#name: #Unit3UniselectorComboActive33 
					#model: #Unit3UniselectorActive33 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 443 568 538 583 ) 
					#name: #Unit3UniselectorComboActive34 
					#model: #Unit3UniselectorActive34 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 373 496 ) 
					#name: #Unit2ConnectionNoiseLabel 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 514 430 528 ) 
					#name: #Unit3NoiseSpin31ID 
					#model: #Unit3NoiseSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 532 430 546 ) 
					#name: #Unit3NoiseSpin32ID 
					#model: #Unit3NoiseSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 569 430 583 ) 
					#name: #Unit3NoiseSpin34ID 
					#model: #Unit3NoiseSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 569 350 583 ) 
					#name: #Unit3SwitchSpin34ID 
					#model: #Unit3SwitchSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 551 350 565 ) 
					#name: #Unit3SwitchSpin33ID 
					#model: #Unit3SwitchSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 532 350 546 ) 
					#name: #Unit3SwitchSpin32ID 
					#model: #Unit3SwitchSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 282 514 350 528 ) 
					#name: #Unit3SwitchSpin31ID 
					#model: #Unit3SwitchSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 568 272 582 ) 
					#name: #Unit3WeightSpin34ID 
					#model: #Unit3WeightSpin34 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 550 272 564 ) 
					#name: #Unit3WeightSpin33ID 
					#model: #Unit3WeightSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 531 272 545 ) 
					#name: #Unit3WeightSpin31ID 
					#model: #Unit3WeightSpin32 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 181 513 272 527 ) 
					#name: #Unit3WeightSpin31ID 
					#model: #Unit3WeightSpin31 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 208 495 ) 
					#name: #Unit3ConnectWeightLabel 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 295 496 ) 
					#name: #Unit3ConnectionSwitchLabel 
					#label: 'Switch' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 116 495 ) 
					#name: #Unit3ConnectedLabel 
					#label: 'Connected?' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 566 113 582 ) 
					#name: #Unit3ConnectUnit14InputID 
					#model: #Unit3ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 548 113 564 ) 
					#name: #Unit3ConnectUnit13InputID 
					#model: #Unit3ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 529 113 545 ) 
					#name: #Unit3ConnectUnit12InputID 
					#model: #Unit3ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 511 113 527 ) 
					#name: #Unit3ConnectUnit11InputID 
					#model: #Unit3ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 38 494 ) 
					#name: #Label15 
					#label: 'Name' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 356 550 430 564 ) 
					#name: #Unit3NoiseSpin33ID 
					#model: #Unit3NoiseSpin33 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 13 599 108 624 ) 
					#name: #unit4NameInput 
					#model: #unit4Name 
					#helpText: 'Name of the Homeostat unit' 
					#style: #'Arbor-12-Squeeze' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 66 657 108 674 ) 
					#name: #Unit4OutputInputID 
					#model: #Unit4Output 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 655 ) 
					#name: #Label1 
					#label: 'Output' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 517 655 ) 
					#name: #Label9 
					#label: 'Deviation' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 524 671 566 688 ) 
					#name: #Unit4CriticalDeviationField 
					#model: #Unit4Deviation 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 538 622 572 638 ) 
					#name: #unit4HighRangeInput 
					#flags: 0 
					#model: #unit4HighRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 540 759 574 775 ) 
					#name: #unit4LowRangeInput 
					#flags: 0 
					#model: #unit4LowRange 
					#alignment: #right 
					#style: #small 
					#type: #number ) 
				#(#{UI.SliderSpec} 
					#layout: #(#{Graphics.Rectangle} 574 624 599 776 ) 
					#name: #Unit4DeviationSlider 
					#model: #Unit4SliderDeviation 
					#orientation: #vertical ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 761 539 776 ) 
					#name: #Unit4UniselectorComboActive44 
					#model: #Unit4UniselectorActive44 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 743 539 758 ) 
					#name: #Unit4UniselectorComboActive43 
					#model: #Unit4UniselectorActive43 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 724 539 739 ) 
					#name: #Unit4UniselectorComboActive42 
					#model: #Unit4UniselectorActive42 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 444 706 539 721 ) 
					#name: #Unit4UniselectorComboActive41 
					#model: #Unit4UniselectorActive41 
					#helpText: '''Uniselector is always manual on unit''s self-connection''' 
					#type: #string 
					#comboList: #uniselectorActiveChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 444 689 ) 
					#name: #Label10 
					#label: 'Uniselector is:' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 762 431 776 ) 
					#name: #SpinButton1 
					#model: #Unit4NoiseSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 743 431 757 ) 
					#name: #SpinButton2 
					#model: #Unit4NoiseSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 725 431 739 ) 
					#name: #SpinButton3 
					#model: #Unit4NoiseSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 357 707 431 721 ) 
					#name: #SpinButton4 
					#model: #Unit4NoiseSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: -1 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 374 689 ) 
					#name: #Label11 
					#label: 'Noise' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 762 351 776 ) 
					#name: #Unit4SwitchSpin44ID 
					#model: #Unit4SwitchSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 744 351 758 ) 
					#name: #Unit4SwitchSpin43ID 
					#model: #Unit4SwitchSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 725 351 739 ) 
					#name: #Unit4SwitchSpin42ID 
					#model: #Unit4SwitchSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 283 707 351 721 ) 
					#name: #Unit4SwitchSpin41ID 
					#model: #Unit4SwitchSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0' 
					#low: -1 
					#high: 1 
					#interval: 2 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 296 689 ) 
					#name: #Label12 
					#label: 'Switch' ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 761 273 775 ) 
					#name: #Unit4WeightSpin44ID 
					#model: #Unit4WeightSpin44 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.01 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 743 273 757 ) 
					#name: #Unit4WeightSpin43ID 
					#model: #Unit4WeightSpin43 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 724 273 738 ) 
					#name: #Unit4WeightSpin42ID 
					#model: #Unit4WeightSpin42 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.SpinButtonSpec} 
					#layout: #(#{Graphics.Rectangle} 182 706 273 720 ) 
					#name: #Unit4WeightSpin41ID 
					#model: #Unit4WeightSpin41 
					#alignment: #right 
					#style: #small 
					#type: #number 
					#formatString: '0.00' 
					#low: 0 
					#high: 1 
					#interval: 0.1 
					#isWrapAround: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 209 688 ) 
					#name: #Label13 
					#label: 'Weight' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 117 688 ) 
					#name: #Label14 
					#label: 'Connected?' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 759 113 775 ) 
					#name: #Unit3ConnectUnit12InputID 
					#model: #Unit4ConnectUnit14Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 741 113 757 ) 
					#name: #Unit4ConnectUnit12InputID 
					#model: #Unit4ConnectUnit13Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 722 113 738 ) 
					#name: #Unit4ConnectUnit12InputID 
					#model: #Unit4ConnectUnit12Input 
					#style: #pixelSmall 
					#isReadOnly: false ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 15 704 113 720 ) 
					#name: #Unit4ConnectUnit11InputID 
					#model: #Unit4ConnectUnit11Input 
					#style: #pixelSmall 
					#isReadOnly: true ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 39 687 ) 
					#name: #Label16 
					#label: 'Name' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 287 ) 
					#name: #Unit2InputLabel 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 288 107 305 ) 
					#name: #Unit2InputInputField 
					#model: #Unit2Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 14 97 ) 
					#name: #Label17 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 99 107 116 ) 
					#name: #Unit1InputInputField 
					#model: #Unit1Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 478 ) 
					#name: #Label18 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 65 481 107 498 ) 
					#name: #Unit3InputInputField 
					#model: #Unit3Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 15 671 ) 
					#name: #Label19 
					#label: 'Input' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 66 673 108 690 ) 
					#name: #Unit4InputInputField 
					#model: #Unit4Input 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 161 43 ) 
					#name: #Unit1PotentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 153 60 207 75 ) 
					#name: #Unit1PotentiometerInput 
					#model: #Unit1Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 153 77 207 92 ) 
					#name: #Unit1ViscosityInput 
					#model: #Unit1Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 77 272 92 ) 
					#name: #Unit1Switch 
					#model: #Unit1Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 60 272 75 ) 
					#name: #Unit1NoiseInput 
					#model: #Unit1Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 230 44 ) 
					#name: #Uni1NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 311 51 ) 
					#name: #Unit1UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 294 68 432 89 ) 
					#name: #Unit1UniselectorChoiceComboBox 
					#model: #Unit1UniselectorType 
					#alignment: #right 
					#isReadOnly: false 
					#type: #string 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 158 89 ) 
					#name: #Unit1ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 228 89 ) 
					#name: #Unit1SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 442 51 ) 
					#name: #Unit1UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 442 70 ) 
					#name: #Unit1UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit1UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 471 51 ) 
					#name: #Unit1UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 469 70 512 86 ) 
					#name: #Unit1UniselectorTimingInput 
					#model: #Unit1UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 158 235 ) 
					#name: #Unit2PotentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 151 251 205 266 ) 
					#name: #Unit2PotentiometerInput 
					#model: #Unit2Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 151 268 205 283 ) 
					#name: #Unit2ViscosityInput 
					#model: #Unit2Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 156 280 ) 
					#name: #Unit2ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 228 235 ) 
					#name: #Unit2NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 251 270 266 ) 
					#name: #Unit2NoiseInput 
					#model: #Unit2Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 268 270 283 ) 
					#name: #Unit2SwitchInput 
					#model: #Unit2Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 226 280 ) 
					#name: #Unit2SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 309 242 ) 
					#name: #Unit2UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 292 259 430 280 ) 
					#name: #Unit2UniselectorChoiceComboBox 
					#model: #Unit2UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 440 242 ) 
					#name: #Unit2UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 440 261 ) 
					#name: #Unit2UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit2UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 469 242 ) 
					#name: #Unit2UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 467 261 510 277 ) 
					#name: #Unit2UniselectorTimingInput 
					#model: #Unit2UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 157 618 ) 
					#name: #Label2 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 149 635 203 650 ) 
					#name: #Unit4PotentiometerInput 
					#model: #Unit4Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 149 652 203 667 ) 
					#name: #Unit4ViscosityInput 
					#model: #Unit4Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 154 664 ) 
					#name: #Label3 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 226 619 ) 
					#name: #Label5 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 635 268 650 ) 
					#name: #Unit4NoiseInput 
					#model: #Unit4Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 652 268 667 ) 
					#name: #Unit4SwitchInput 
					#model: #Unit4Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 224 664 ) 
					#name: #Label4 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 307 626 ) 
					#name: #Label6 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 290 643 428 664 ) 
					#name: #Unit4UniselectorChoiceComboBox 
					#model: #Unit4UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 438 626 ) 
					#name: #Label7 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 438 645 ) 
					#name: #Unit4UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit4UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 467 626 ) 
					#name: #Label8 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 465 645 508 661 ) 
					#name: #Unit4UniselectorTimingInput 
					#model: #Unit4UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 162 425 ) 
					#name: #Unit3PontentLabel 
					#label: 'Potent.' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 154 442 208 457 ) 
					#name: #Unit3PotentiometerInput 
					#model: #Unit3Potentiometer 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 154 459 208 474 ) 
					#name: #Unit3ViscosityInput 
					#model: #Unit3Viscosity 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 159 471 ) 
					#name: #Unit3ViscosityLabel 
					#label: 'Viscosity' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 231 426 ) 
					#name: #Unit3NoiseLabel 
					#label: 'Noise' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 219 442 273 457 ) 
					#name: #Unit3NoiseInput 
					#model: #Unit3Noise 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 219 459 273 474 ) 
					#name: #Unit3SwitchInput 
					#model: #Unit3Switch 
					#alignment: #right 
					#isReadOnly: true 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 229 471 ) 
					#name: #Unit3SwitchLabel 
					#label: 'Switch' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 312 433 ) 
					#name: #Unit3UniselectorTypeLabel 
					#label: 'Unisel. type' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 295 450 433 471 ) 
					#name: #Unit3UniselectorChoiceComboBox 
					#model: #Unit3UniselectorType 
					#alignment: #right 
					#comboList: #UniselectorChoices ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 443 433 ) 
					#name: #Unit3UniselectorIsOnLabel 
					#label: 'On' ) 
				#(#{UI.CheckBoxSpec} 
					#properties: #(#{UI.PropertyListDictionary} #labelFromApplication false ) 
					#layout: #(#{Core.Point} 443 452 ) 
					#name: #Unit3UniselectorOnCheckBoxID 
					#colors: 
					#(#{UI.LookPreferences} 
						#setForegroundColor: #(#{Graphics.ColorValue} #red ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #red ) ) 
					#model: #Unit3UniselectorOn ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 472 433 ) 
					#name: #Unit3UniselectorTimingLabel 
					#label: 'Timing' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 470 452 513 468 ) 
					#name: #Unit3UniselectorTimingInput 
					#model: #Unit3UniselectorTiming 
					#alignment: #right 
					#type: #number 
					#formatString: '0' ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 129 176 145 ) 
					#name: #unit1ConnStatus11ComboBox 
					#model: #Unit1ConnectStatusUnit11 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 14 625 108 644 ) 
					#name: #unit4ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit4Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 15 434 109 453 ) 
					#name: #unit3ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit3Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 14 243 108 262 ) 
					#name: #unit2ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit2Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 16 53 110 72 ) 
					#name: #unit1ActiveComboBox 
					#isOpaque: true 
					#colors: 
					#(#{UI.LookPreferences} 
						#setBackgroundColor: #(#{Graphics.ColorValue} #white ) 
						#setSelectionBackgroundColor: #(#{Graphics.ColorValue} #salmon ) ) 
					#model: #unit1Active 
					#type: #string 
					#comboList: #unitActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 184 176 200 ) 
					#name: #unit1ConnStatus14ComboBox 
					#model: #Unit1ConnectStatusUnit14 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 166 176 182 ) 
					#name: #unit1ConnStatus13ComboBox 
					#model: #Unit1ConnectStatusUnit13 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 148 176 164 ) 
					#name: #unit1ConnStatus12ComboBox 
					#model: #Unit1ConnectStatusUnit12 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 319 176 335 ) 
					#name: #unit2ConnStatus21ComboBox 
					#model: #Unit2ConnectStatusUnit21 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 338 176 354 ) 
					#name: #unit2ConnStatus22ComboBox 
					#model: #Unit2ConnectStatusUnit22 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 357 176 373 ) 
					#name: #unit2ConnStatus23ComboBox 
					#model: #Unit2ConnectStatusUnit23 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 375 176 391 ) 
					#name: #unit2ConnStatus24ComboBox 
					#model: #Unit2ConnectStatusUnit24 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 566 176 582 ) 
					#name: #unit3ConnStatus34ComboBox 
					#model: #Unit3ConnectStatusUnit34 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 548 176 564 ) 
					#name: #unit3ConnStatus33ComboBox 
					#model: #Unit3ConnectStatusUnit33 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 529 176 545 ) 
					#name: #unit3ConnStatus32ComboBox 
					#model: #Unit3ConnectStatusUnit32 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 511 176 527 ) 
					#name: #unit3ConnStatus31ComboBox 
					#model: #Unit3ConnectStatusUnit31 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 759 176 775 ) 
					#name: #unit4ConnStatus44ComboBox 
					#model: #Unit4ConnectStatusUnit44 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 741 176 757 ) 
					#name: #unit4ConnStatus43ComboBox 
					#model: #Unit4ConnectStatusUnit43 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 722 176 738 ) 
					#name: #unit4ConnStatus42ComboBox 
					#model: #Unit4ConnectStatusUnit42 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.ComboBoxSpec} 
					#layout: #(#{Graphics.Rectangle} 117 704 176 720 ) 
					#name: #unit4ConnStatus41ComboBox 
					#model: #Unit4ConnectStatusUnit41 
					#comboList: #ConnectionActiveChoices ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 120 605 124 ) 
					#name: #Divider1 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 587 314 602 318 ) 
					#name: #Divider5 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 505 603 509 ) 
					#name: #Divider6 ) 
				#(#{UI.DividerSpec} 
					#layout: #(#{Graphics.Rectangle} 588 698 605 702 ) 
					#name: #Divider7 ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 218 30 272 45 ) 
					#name: #Unit1MassInput 
					#model: #Unit1Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 29 ) 
					#name: #Label20 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 224 ) 
					#name: #Label21 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 172 411 ) 
					#name: #Label22 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.LabelSpec} 
					#layout: #(#{Core.Point} 170 604 ) 
					#name: #Label23 
					#label: 'Mass' 
					#style: #pixelSmall ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 216 223 270 238 ) 
					#name: #Unit2MassInput 
					#model: #Unit2Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 220 411 274 426 ) 
					#name: #Unit3MassInput 
					#model: #Unit3Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.InputFieldSpec} 
					#layout: #(#{Graphics.Rectangle} 214 606 268 621 ) 
					#name: #Unit4MassInput 
					#model: #Unit4Mass 
					#alignment: #right 
					#type: #number 
					#formatString: '0.00' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 442 93 ) 
					#name: #Unit1UniselectorSoundOnCheckBoxID 
					#model: #Unit1UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 440 284 ) 
					#name: #Unit2UniselectorSoundOnCheckBoxID 
					#model: #Unit2UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 443 474 ) 
					#name: #Unit3UniselectorSoundOnCheckBoxID 
					#model: #Unit3UniselectorSoundOn 
					#label: 'Sound' ) 
				#(#{UI.CheckBoxSpec} 
					#layout: #(#{Core.Point} 438 667 ) 
					#name: #Unit4UniselectorSoundOnCheckBoxID 
					#model: #Unit4UniselectorSoundOn 
					#label: 'Sound' ) ) ) )</body>

<body package="Homeostat" selector="windowSpec">windowSpec
	"Tools.UIPainter new openOnClass: self andSelector: #windowSpec"


"NEED TO WRITE THE WINDOW ALLOWING SELECTION OF DIFFERENT KINDS OF SIMULATION"</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI class</class-id> <category>interface opening</category>

<body package="Homeostat" selector="new">new

"open a new homeostat"

| app |

app := super new initialize.
"app openBothWindows."
app openThreeWindows.</body>
</methods>

<!-- -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -   -->


<comment>
<class-id>HomeostatStandardGUI</class-id>
<body>HomeostatStandardGUI holds all the data necessary to run a simulation of a standard 4-unit Ashby homeostat. In addition, it allows complete interactive access to the units' parameters and some facilities for saving and charting the simulation's data.
The simulation emulates real time operation of the homeostat by running through a series of discrete time steps. The delay between these discrete steps is set by default at 1 millisecond, to allow a smooth redrawing of the visual interface, but it may be changed by the user

The simulation itself is run in a  separate process (held in simulProcess) at a lower priority level than the interface. 

Instance Variables:
	currentRun					<Object>		current time step. 
	dataAreSaved				<Boolean>		flag to mark whether the simulation's data have been saved to disk (Boss out)
	dataChart					<JunChartLine>	the Jun object responsible for charting the data
	datafile					<Symbol>		the filename to save the simulation's data to
	homeostat					<Homeostat>		the homeostat that is being simulated
	maxRuns						<ValueModel>	the number of time steps we are running the simulation for.
	simulProcess				<Process>	    the process holding the simulation run
	slowingFactor				<ValueHolder>	How long (in millisecond) we are waiting between two time steps.
	uniselectorActiveChoices	<Object>		description of uniselectorActiveChoices
	debugMode  					<Boolean>		controls whether info about the units are written out to screen (slows down simulation considerably)
	showUniselectorActionMode 	<Boolean>		controls whether info about the uniselector action is written out to screen (slows down simulation considerably)
</body>
</comment>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>initialize-release</category>

<body package="Homeostat" selector="activateConnectionCheckBoxes">activateConnectionCheckBoxes
	"construct the event triggers for all the checkboxes that activate or disactivate a connection.
As there are 4 connection for each of the 4 units, and each can be either active or inactive, we have to construct 32 event trigger handlers 
and set the default values for each to true (i.e. connection is active)

Notice that this method assumes a classic Ashby homeostat in its starting configuration: 4 units completely connected."

	"activate connection handlers"

	1 to: 4 do: 
			[:i | 
			1 to: 4 do: 
					[:k | 
					| widgetID |
					widgetID := ('Unit' , i printString , 'ConnectedCheckBox' , i printString, k printString , 'ID') asSymbol.
					self 
						widget: widgetID
						when: #checked
						send: #activate
						to: ((homeostat homeoUnits at: i) inputConnections at: k).
					self 
						widget: widgetID
						when: #unchecked
						send: #disactivate
						to: ((homeostat homeoUnits at: i) inputConnections at: k).
					(self widgetAt: widgetID) model: (ValueHolder with: true)]]</body>

<body package="Homeostat" selector="activateUnitActiveCheckboxes">activateUnitActiveCheckboxes
	"construct the event triggers for all the checkboxes that activate or disactivate a unit.
As there are 4 units in a classic Ashby Homeostat  and each can be either active or inactive, we have to construct 8 event trigger handlers, and assign default values of true (active) to each unit

Notice that this method assumes a classic Ashby homeostat in its starting configuration: 4 units completely connected."

	1 to: 4
		do: 
			[:i | 
			| widgetID |
			widgetID := ('Unit' , i printString , 'OperationalCheckBoxID') asSymbol.
			self 
				widget: widgetID
				when: #checked
				send: #activate
				to: (homeostat homeoUnits at: i).
			self 
				widget: widgetID
				when: #unchecked
				send: #disactivate
				to: (homeostat homeoUnits at: i).
			(self widgetAt: widgetID) model: (ValueHolder with: true)]</body>

<body package="Homeostat" selector="initialize">initialize
	homeostat := Homeostat new.
	graphicView := Mondrian.ViewRenderer new.
	maxRuns := 1000 asValue.
	self initializeAshbySimulation.
        self initializeGraphicView.

	dataAreSaved := true.
	datafile := 'newHomeostat.hst' asValue.
	datafile onChangeSend: #changedDatafile to: self.
	slowingFactor := 10 asValue.
	debugMode := false.
	showUniselectorActionMode := false.</body>

<body package="Homeostat" selector="initializeAshbySimulation">initializeAshbySimulation
"Adds four fully connected units with random values to the simulator (as per Ashby basic design)"
 
4 timesRepeat: [ | unit | unit := HomeoUnitNewtonian new setRandomValues. homeostat addFullyConnectedUnit: unit].</body>

<body package="Homeostat" selector="initializeGraphicView">initializeGraphicView

| activeUnits |

"builds the Mondrian-based graphic editor"


"choose active units"
activeUnits := homeostat homeoUnits select: [ :unit | unit isActive].

graphicView := Mondrian.ViewRenderer new.
graphicView nodes: activeUnits using: (Mondrian.Shape new
									 add:  (Mondrian.RectangleShape width: 100 height: 50 fillColor: Mondrian.Color red);
									 add:  (Mondrian.BorderShape new);
									 add:   (Mondrian.LabelShape align: #center label: #name)).


	 
"building edges in a double loop through units and units inputConnections"
activeUnits do: [:unit |
			     unit inputConnections do: [:conn | 
				
                             graphicView edge: unit  from: #yourself to: [:foo | conn incomingUnit ] using: ((Mondrian.LineShape new) decoratedWith: (Mondrian.ArrowShape new))]].									



"Choose the view Layout"

graphicView layout: ((Mondrian.RadialTreeLayout new)).



"set the window size and label"

</body>

<body package="Homeostat" selector="open">open

"as the correct opening method  is openBothWindows, issue by the method new, this method is redefined to do nothing"

^nil</body>

<body package="Homeostat" selector="openBothWindows">openBothWindows
	"open both the control panel and a new initialized Ashby homeostat window"


controlPanelBuilder := self openInterface: #homeoControlSpec.
self  openInterface:  #homeostatSpec.</body>

<body package="Homeostat" selector="openThreeWindows">openThreeWindows
	"open  the control panel, a new initialized Ashby homeostat window, and the Mondrian graphic view"


controlPanelBuilder := self openInterface: #homeoControlSpec.
self  openInterface:  #homeostatSpec.
graphicView open.</body>

<body package="Homeostat" selector="postBuildWith:">postBuildWith: aBuilder
	"comment stating purpose of message"

"	aBuilder windowSpec label = 'Homeostat Standard' 
		ifTrue:[ 
			self activateConnectionCheckBoxes.
			self activateUnitActiveCheckboxes]
"</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>testing</category>

<body package="Homeostat" selector="isReadyToGo">isReadyToGo

"checks that the homeostat is ready to go and that the maxRuns and datafile are present"
datafile  isNil 
	ifTrue:
		 [Dialog warn: 'You have not entered a filename to save the simulation data'. 
		^false] 
	ifFalse: [
 		^(homeostat  isReadyToGo and: [maxRuns value notNil])]</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>accessing</category>

<body package="Homeostat" selector="dataAreSaved">dataAreSaved
	^dataAreSaved</body>

<body package="Homeostat" selector="dataAreSaved:">dataAreSaved: anObject
	dataAreSaved := anObject</body>

<body package="Homeostat" selector="homeostat">homeostat
	^homeostat</body>

<body package="Homeostat" selector="homeostat:">homeostat: anObject
	homeostat := anObject</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-events</category>

<body package="Homeostat" selector="changedDatafile">changedDatafile

self redisplayDatafile</body>

<body package="Homeostat" selector="changeRequest">changeRequest

"check  user does not want to save data before closing"

^super changeRequest
		ifFalse: [false]
		ifTrue:  [dataAreSaved 
			ifFalse: 
				[(Dialog confirm: 'Save simulation data?') 
					ifTrue: [self saveCompleteRunOnFile. true]
					ifFalse:[true]]
			ifTrue: [true]]</body>

<body package="Homeostat" selector="newHomeostat">newHomeostat
	"closes the current window, flushes the homeostat and puts a new one in its place."

	"close the homeostat window and open a new one on the new homeostat"

	

	self mainWindow close.
	controlPanelBuilder window close.
	
	"switch to a new homeostat and initialize variables"
	
	self initialize.
	self openBothWindows.

	"update values"
	homeostat allChanged</body>

<body package="Homeostat" selector="newHomeostat:">newHomeostat: anHomeostat 
	"swaps the current homeostat with anHomeostat, including all the components of the former,
	tells the new homeostat to updates the values in the GUI"

	"close the homeostat window and open a new one on the new homeostat"

	
	self mainWindow close.
	controlPanelBuilder window close.
	"switch to new homeostat"
	homeostat :=  anHomeostat.
	"Prepare the window and change its label  to the filename of the new homeostat"
	 self openBothWindows.
	 self builder window label: datafile value.
	"update values"
	homeostat allChanged</body>

<body package="Homeostat" selector="redisplayDatafile">redisplayDatafile
	"update the display of the filename in the Control panel window"

(controlPanelBuilder componentAt: #datafileInputField) invalidate.</body>

<body package="Homeostat" selector="redisplayFilename">redisplayFilename
	"update the display of the filename in the Control panel window"

(controlPanelBuilder componentAt: #datafileInputField) invalidate.</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>actions</category>

<body package="Homeostat" selector="exit">exit
	dataAreSaved 
		ifFalse: 
			[(Dialog confirm: 'Save simulation data?') 
				ifTrue: [self saveCompleteRunOnFile]].
	self closeRequest</body>

<body package="Homeostat" selector="homeostatInspect">homeostatInspect

	 homeostat inspect
	"homeostat inspect."</body>

<body package="Homeostat" selector="pause">pause

"Pause the simulation and allows a restart. Needs to change the label of the start widget to 'restart'"

simulRunning
	ifTrue: [ simulProcess suspend]</body>

<body package="Homeostat" selector="pauseProcess">pauseProcess
	"Pause the simulation and allows a restart. Needs to change the label of the start widget to 'restart'"

	simulProcess isNil 
		ifFalse: [(Processor isPaused: simulProcess) 
				ifFalse: [ simulProcess suspend]]</body>

<body package="Homeostat" selector="readHomeostat">readHomeostat
	"reads the initial conditions for a simulation, i.e. the homeostat, from a filename"

	| dialog filename boss bossedHomeostat |
	dialog := OpenFileDialog new.
	dialog
		windowTitle: 'Load a homeostat';
		acceptButtonLabel: 'Load';
		addFilterForAllFiles;
		addFirstFileFilter: 'Homeostat file (*.hst)' pattern: '*.hst';
		defaultExtension: '.hst';
		fileCondition: #mustBeOld.
	filename := dialog select.
	filename notNil 
				ifTrue: 
					[
					[boss := BinaryObjectStorage onOldNoScan: filename readStream.
					bossedHomeostat := boss next.
					boss close] 
							on: Exception
							do: [:ex | ^Dialog warn: 'I am sorry, the selected file is not a homeostat.'].
					bossedHomeostat class = Homeostat 
						ifFalse: [^Dialog warn: 'I am sorry, the selected file is not a homeostat']
						ifTrue: 
							[self datafile value: filename tail.
							self newHomeostat: bossedHomeostat]].
	</body>

<body package="Homeostat" selector="resetTime">resetTime
	"start a new simulation: 
		resets simulation time to zero 	
		clear the simulation data
		set dataAreSaved to true"

	homeostat timeReset.
	homeostat flushData.
	simulProcess := nil.
	dataAreSaved := true.</body>

<body package="Homeostat" selector="resetUnitValues">resetUnitValues

homeostat randomizeValuesforAllUnits.</body>

<body package="Homeostat" selector="simulationGraph">simulationGraph

	"Open a JunChartLine graph window on the simulation data of the last run (since application started or since last 'reset time' command.
	  Needs  to be improved to :
		- include the data about the  uniselector's action
		- parametrize the values of the y axis to the current min and max values of the units
		- improve the graphic look by adding a legend and  making it less cartoonish" 

	|  junDataColl |



"1. obtain data"

junDataColl := OrderedCollection new.
junDataColl add: homeostat dataCollector criticalDevAsCollectionOfArraysForAllUnits.

"2 construct chart"

dataChart := JunChartLine samples: junDataColl.
dataChart valueRangeFrom: -10  to: 10.
dataChart lineWidth: 1.
dataChart showXAxis.
dataChart showYAxisWithLabels.



"4. display chart"
dataChart  open.</body>

<body package="Homeostat" selector="simulationSave">simulationSave

"save the simulation data to file. Offer a choice between saving the complete simulation data and only a subset"

Dialog warn: 'Under construction. Not ready to to go quite yet'</body>

<body package="Homeostat" selector="start">start
	(self isReadyToGo)
		ifTrue: 
			[dataAreSaved := false.
			homeostat  runFor: maxRuns value]
		ifFalse: [Dialog warn: 'The homeostat simulation is not ready to go']</body>

<body package="Homeostat" selector="startNewProcess">startNewProcess
	"if no simulation is running starts one in  a new process and runs it. Otherwise resume suspended simulation"

	self isReadyToGo 
		ifTrue: 
			[dataAreSaved := false.
			simulProcess isNil 
				ifTrue: 
					[simulProcess := [homeostat runFor: maxRuns value] 
								forkAt: Processor userBackgroundPriority]
				ifFalse: [(Processor isPaused: simulProcess) ifTrue: [simulProcess resume]]]
		ifFalse: [Dialog warn: 'The homeostat simulation is not ready to go']</body>

<body package="Homeostat" selector="stepSimulation">stepSimulation

	homeostat runOnce</body>

<body package="Homeostat" selector="stop">stop
"stops the simulation"

homeostat stop</body>

<body package="Homeostat" selector="stopProcess">stopProcess
"stops the simulation"

simulProcess isNil
		ifFalse: [
			simulProcess terminate.
			simulProcess :=  nil]</body>

<body package="Homeostat" selector="toggleDebugMode">toggleDebugMode
	"turns debug mode on or off by changing the value of the debugMode ivar of the homeoUnits. Changes the color of the button accordingly"

	| wrapper lookPref aColor |
	homeostat homeoUnits do: [:unit | unit toggleDebugMode].
	debugMode 
		ifTrue: 
			[aColor := ColorValue black.
			debugMode := false]
		ifFalse: 
			[aColor := ColorValue red.
			debugMode := true].
	wrapper := controlPanelBuilder componentAt: #DebugModeActionButton.
	lookPref := wrapper lookPreferences foregroundColor: aColor.
	wrapper lookPreferences: lookPref</body>

<body package="Homeostat" selector="toggleShowUniselectorAction">toggleShowUniselectorAction
	"turns debug mode on or off by changing the value of the debugMode ivar of the homeoUnits. Changes the color of the button accordingly"

	| wrapper lookPref aColor |
	homeostat homeoUnits do: [:unit | unit toggleShowUniselectorAction].
	showUniselectorActionMode 
		ifTrue: 
			[aColor := ColorValue black.
			showUniselectorActionMode := false]
		ifFalse: 
			[aColor := ColorValue red.
			showUniselectorActionMode := true].
	wrapper := controlPanelBuilder componentAt: #showUniselectorActionButton.
	lookPref := wrapper lookPreferences foregroundColor: aColor.
	wrapper lookPreferences: lookPref</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>saving</category>

<body package="Homeostat" selector="saveAllDataOnFile">saveAllDataOnFile
	"asks the datacollector of the homeostat to save all data on datafile"



Dialog warn: 'Sorry, not implemented yet'</body>

<body package="Homeostat" selector="saveAllDataOnFile:">saveAllDataOnFile: aFilename
	"save on aFilename a complete  version of the simulation data, suitable"

"TO DO"</body>

<body package="Homeostat" selector="saveEssentialDataOnFile">saveEssentialDataOnFile
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := WriteStream on: (datafile, '.essential-simul-data') asFilename.
	homeostat  dataCollector printEssentialDataOn: stream.
	stream close</body>

<body package="Homeostat" selector="saveEssentialDataOnFileWithSeparator:">saveEssentialDataOnFileWithSeparator: aCharacter
	"asks the datacollector of the homestat to save only the essential data on datafile"

	| stream |
	stream := datafile asFilename writeStream.
	

	homeostat  dataCollector saveEssentialsOn:  stream separator: aCharacter.
	stream close</body>

<body package="Homeostat" selector="saveHomeostatOnFile">saveHomeostatOnFile
	"save on a file the homeostat itself, which includes all the units, their connections, etcetera. Does not save the data about the simulation's run"

	| dialog filename|
	dialog := SaveFileDialog new.
	dialog 
		windowTitle: 'Save the homeostat';
		addFirstFileFilter: 'Homeostat file (*.hst)' pattern: '*.hst';
		defaultExtension: '.hst';
		fileCondition: #new;
		defaultFilename: (datafile value) asFilename.
	
	filename := dialog select.
	self saveHomeostatOnFile: filename.
	datafile value:  filename tail.
	builder window label: filename tail.</body>

<body package="Homeostat" selector="saveHomeostatOnFile:">saveHomeostatOnFile: aFilename
	"save on aFilename the homeostat itself, which includes all the units, their connections, etcetera. Does not save the data about the simulation's run"

	aFilename isNil 
		ifTrue: 
			[^Dialog warn: 'Saving canceled']
		ifFalse: [homeostat bossOutOn: aFilename]</body>

<body package="Homeostat" selector="savePlotDataOnFile">savePlotDataOnFile
	"save on a file a stripped version of the simulation data, suitable for plotting. It onjly includes the data about the critical deviation of each unit."

	| dialog filename|
	dialog := SaveFileDialog new.
	dialog 
		windowTitle: 'Save plotting data';
		addFirstFileFilter: 'Homeostat data file (*.txt)' pattern: '*.txt';
		defaultExtension: '.data';
		fileCondition: #new;
		defaultFilename: 'simulation-data.txt' asFilename.
	filename := dialog select.
	self savePlotDataOnFile: filename.</body>

<body package="Homeostat" selector="savePlotDataOnFile:">savePlotDataOnFile: aFilename
	"save on aFilename a stripped version of the simulation data, suitable for plotting."

	| stream |
	aFilename isNil 
		ifTrue: 
			[^Dialog warn: 'Saving canceled']
		ifFalse: [stream :=   aFilename writeStream.
			       homeostat dataCollector printPlottingDataForGgobiOn: stream.
			       stream close].</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-adaptors units</category>

<body package="Homeostat" selector="adaptorForDeviationForUnit:">adaptorForDeviationForUnit: aUnitNumber

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aUnitNumber).
adaptor 
	getBlock: [ :model |
		model criticalDeviation ]
	putBlock: 
		[:model :value |
		 model criticalDeviation: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aUnitNumber)) &amp; (aspect = #criticalDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForInputFor:">adaptorForInputFor: unitNumber

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: unitNumber).
adaptor 
	getBlock: [ :model |
		model inputTorque ]
	putBlock: 
		[:model :value |
		 ]               						"cannot be changed in the GUI"						 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: unitNumber)) &amp; (aspect = #inputTorque)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForInternallNoiseOfUnitNumber:">adaptorForInternallNoiseOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the internal noise of the 4 units.
	use it , e.g., as:  ^adaptorForInternallNoiseOfUnitNumber:  3 
	to obtain an adaptor for the  internal noise of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model noise ]
	putBlock: 
		[:model :value |
		 model noise: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #noise)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForMass:">adaptorForMass: aNumber
"Private method that returns a pluggable adaptor for the  mass of the 4 units.
	use it , e.g., as:  ^adaptorForMass: 3 
	to obtain an adaptor for the  switch of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: aNumber) needleUnit).
adaptor 
	getBlock: [ :model |
		model mass ]
	putBlock: 
		[:model :value |
		 model mass: value]               								 
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (homeostat homeoUnits at: aNumber) needleUnit) &amp; (aspect = #mass)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNameOfUnitNumber:">adaptorForNameOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  names of the 4 units.
	use it , e.g., as:  ^adaptorForNameOfUnitNumber: 3 
	to obtain an adaptor for the  name of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model name ]
	putBlock: 
		[:model :value |
		 model name: value.
		 model changed: #name]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #name)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForOutputFor:">adaptorForOutputFor: unitNumber
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: unitNumber).
adaptor 
	getBlock: [ :model |
		model currentOutput ]
	putBlock: 
		[:model :value |
		 model currentOutput: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: unitNumber)) &amp; (aspect = #currentOutput)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForOutputSliderFor:">adaptorForOutputSliderFor: aNumber
"Private method that returns a pluggable adaptor for the  output of the 4 units, to be used in the slider.
	use it , e.g., as:  ^adaptorForOutputSlider: 3 
	to obtain an adaptor for the  output of the third unit"
	
| adaptor |
"
adaptor := RangeAdaptor
		on: (homeostat homeoUnits at: aNumber) currentOutput asValue
		start: ((homeostat homeoUnits at: aNumber) outputRange at: 'low')  
		stop: ((homeostat homeoUnits at: aNumber) outputRange at: 'high') 
		grid: nil.	

^adaptor


old code: 
"
adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model currentOutput ]
	putBlock: 
		[:model :value |
		 model currentOutput: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #currentOuput)].
self halt.
^adaptor</body>

<body package="Homeostat" selector="adaptorForPotentiomOfUnitNumber:">adaptorForPotentiomOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  potentiometers of the 4 units.
	use it , e.g., as:  ^adaptorForPotentiomOfUnitNumber: 3 
	to obtain an adaptor for the  potentiometer of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model potentiometer ]
	putBlock: 
		[:model :value |
		 model potentiometer: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #potentiometer)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSliderDeviationFor:">adaptorForSliderDeviationFor: aUnitNumber

| adaptor rangeStop rangeStart|

rangeStart := (homeostat homeoUnits at: aUnitNumber) maxDeviation. 
rangeStop := (homeostat homeoUnits at: aUnitNumber) minDeviation. 

adaptor := PluggableRangeAdaptor on: (homeostat homeoUnits at: aUnitNumber).
adaptor rangeStart: rangeStart.
adaptor rangeStop: rangeStop.

adaptor 
	getBlock: 
		[ :model |
		rangeStart == rangeStop
		ifTrue: [0]
		ifFalse: [((model criticalDeviation)  - rangeStart) asFloat / (rangeStop - rangeStart) ]]
	putBlock: 
		[:model :value |
		 model criticalDeviation: ((value*(rangeStop-rangeStart))+rangeStart)]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aUnitNumber)) &amp; (aspect = #criticalDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSwitch:">adaptorForSwitch: aNumber
"Private method that returns a pluggable adaptor for the  switch of the 4 units.
	use it , e.g., as:  ^adaptorForSwitch: 3 
	to obtain an adaptor for the  switch of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model switch ]
	putBlock: 
		[:model :value |
		 model switch: value]               								 
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #switch)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorIsOn:">adaptorForUniselectorIsOn: aNumber
"Private method that returns a pluggable adaptor for the  state of the Uniselector of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorIsOn: 3 
	to obtain an adaptor for the  stte of the unisellector of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | 
		model uniselectorActive ]
	putBlock: 
		[:model :value |
		 model uniselectorActive: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselectorActive)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorSoundIsOn:">adaptorForUniselectorSoundIsOn: aNumber
"Private method that returns a pluggable adaptor for the  sound of the Uniselector of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorSoundIsOn: 3 
	to obtain an adaptor for the  state of the uniselector sound of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber) uniselector.
adaptor 
	getBlock: [ :model | 
		model beeps ]
	putBlock: 
		[:model :value |
		 model toggleBeeping]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber) uniselector) &amp; (aspect = #uniselectorSound)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorTimingOfUnitNumber:">adaptorForUniselectorTimingOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  uniselector timing of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorTimingOfUnitNumber: 3 
	to obtain an adaptor for the  UniselectorTiming of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model uniselectorTimeInterval  ]
	putBlock: 
		[:model :value |
		 model uniselectorTimeInterval:  value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselectorTimeInterval )].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorTypeOfUnitNumber:">adaptorForUniselectorTypeOfUnitNumber: aNumber
"Private method that returns a pluggable adaptor for the  uniselector type  of the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorTypeOfUnitNumber: 3 
	to obtain an adaptor for the  uniselector type  of the third unit"

"PUTBLOCK CHANGED ON 3/18/08"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | | string |
			    string := model uniselector class name asString.
                          (string  beginsWith: 'HomeoUniselector') 
				ifTrue: [string := string  copyFrom: ('HomeoUniselector' size) +1  to:  string  size]
				ifFalse: [ string]]
	putBlock: 
		[:model :value |
		model uniselectorChangeType: value]               				
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #uniselector)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUnitActive:">adaptorForUnitActive: aNumber
"Private method that returns a pluggable adaptor for whether the unit is active.
	use it , e.g., as:  ^adaptorForUnitActive: 3 
	to obtain an adaptor for the  activity status of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model | 
		model status]
	putBlock: 
		[:model :value |
		 model status: value ]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #status)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForViscosity:">adaptorForViscosity: aNumber
"Private method that returns a pluggable adaptor for the  viscosity of the 4 units.
	use it , e.g., as:  ^adaptorForNameOfUnitNumber: 3 
	to obtain an adaptor for the  viscosity of the third unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber).
adaptor 
	getBlock: [ :model |
		model viscosity ]
	putBlock: 
		[:model :value |
		 model viscosity: value]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #viscosity)].
^adaptor</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>private-adaptors connections</category>

<body package="Homeostat" selector="adaptorForConnectionStatusOf:forUnit:">adaptorForConnectionStatusOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  status  of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForConnectionStatusOf: 1 forUnit: 2
	to obtain an adaptor for the  connection status  of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model status ]
	putBlock: 
		[:model :value | 
		 model status: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		(model = ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber) ) &amp; aspect = #status].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNameOf:forUnit:">adaptorForNameOf: theConnectionDestiNumber forUnit: theConnectionOriginNumber
"Private method that returns a pluggable adaptor for the  names of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForNameOf: 1 forUnit: 2
	to obtain an adaptor for the  name of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model | 
		(model inputConnections at: theConnectionDestiNumber) incomingUnit name ]
	putBlock: 
		[:model :value |
		 ]               								 "cannot be changed in the GUI"
	updateBlock:
		[ :model :aspect :parameter | 
		 aspect = #name].
^adaptor</body>

<body package="Homeostat" selector="adaptorForNoiseOf:forUnit:">adaptorForNoiseOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  noise of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForNoiseOf: 1 forUnit: 2
	to obtain an adaptor for the  noise of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model noise ]
	putBlock: 
		[:model :value | 
		 model noise: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		true].
^adaptor</body>

<body package="Homeostat" selector="adaptorForRange:forUnit:">adaptorForRange: highOrLow forUnit: aNumber
"Private method that returns a pluggable adaptor for the  range of the 4 units.
	use it , e.g., as:  ^adaptorForRange: #highRange forUnit: 1 
	to obtain an adaptor for the  high range  of the first unit"
	
| adaptor |

adaptor := PluggableAdaptor on: (homeostat homeoUnits at: aNumber) .
adaptor 
	getBlock: [ :model |
		model perform: highOrLow ]
	putBlock: 
		[:model :value |
		 model perform: (highOrLow asString, ':') asSymbol with: value.]               								 
	updateBlock:
		[ :model :aspect :parameter |
		(model = (homeostat homeoUnits at: aNumber)) &amp; (aspect = #maxDeviation)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSelfUniselectorForUnit:">adaptorForSelfUniselectorForUnit: theConnectionDestiNumber

"Private method that returns a pluggable adaptor for the  state of uniselector on the connection between the unit and itself.
 Notice that the unit's self-connection is always the first of the connections.
  As the connection is always manual, the adaptor does not allow changing the value.
   Use it , e.g., as:  ^self adaptorForSelfUniselectoForUnit:2
to obtain an adaptor for the  state of the Uniselector of the self-connection of thesecond unit"

| adaptor |

adaptor := PluggableAdaptor on:((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: 1).
adaptor 
	getBlock: [ :model |
		model state ]
	putBlock: 
		[:model :value |
		  ]               								"GUI cannot change state of the unit's self-connection"
	updateBlock:
		[ :model :aspect :parameter |
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: 1)) &amp; (aspect = #state)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForSwitchOf:forUnit:">adaptorForSwitchOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber

"Private method that returns a pluggable adaptor for the  switch of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForSwitchOf: 1 forUnit: 2
	to obtain an adaptor for the  switch of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model switch ]
	putBlock: 
		[:model :value |
		 model switch: value  ]               								
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #switch)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForUniselectorOf:forUnit:">adaptorForUniselectorOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  state of uniselector of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForUniselectorOf: 1 forUnit: 2
	to obtain an adaptor for the  state of the Uniselector of the first unit connected to the second unit"

| adaptor |

adaptor := PluggableAdaptor on:((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model state ]
	putBlock: 
		[:model :value |
		 model  state: value  ]               								
	updateBlock:
		[ :model :aspect :parameter |
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #state)].
^adaptor</body>

<body package="Homeostat" selector="adaptorForWeightOf:forUnit:">adaptorForWeightOf: theConnectionOriginNumber forUnit: theConnectionDestiNumber
"Private method that returns a pluggable adaptor for the  weight of the connected units to the 4 units.
	use it , e.g., as:  ^adaptorForWeightOf: 1 forUnit: 2
	to obtain an adaptor for the  weight of the first unit connected to the second unit"
	
| adaptor |

adaptor := PluggableAdaptor on: ((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections at: theConnectionOriginNumber).
adaptor 
	getBlock: [ :model |
		model weight ]
	putBlock: 
		[:model :value |
		 model weight: value  ]               								
	updateBlock:
		[ :model :aspect :parameter | 
		(model = (((homeostat homeoUnits at: theConnectionDestiNumber) inputConnections) at: theConnectionOriginNumber)) &amp; (aspect = #weight)].
^adaptor</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>aspects</category>

<body package="Homeostat" selector="currentRun">currentRun

| adaptor |

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ :model |
		model time ]
	putBlock: 
		[:model :value |
		 ]               								 "GUI cannot jump to specific times"
	updateBlock:									
		[ :model :aspect :parameter |
		aspect = #time].
^adaptor</body>

<body package="Homeostat" selector="currentRun2">currentRun2


|adaptor|

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ 
		:model |
		model time]
	putBlock: [									"GUI cannot skip to a specific step"
		:model :value| 
		 ]
	updateBlock: [
		:model :aspect :parameter |
		 (model = homeostat) &amp; (aspect = #time)].

^adaptor</body>

<body package="Homeostat" selector="datafile">datafile
	

	^datafile isNil
		ifTrue:
			[datafile := 'newHomeostat.hst'  asValue]
		ifFalse:
			[datafile]</body>

<body package="Homeostat" selector="homeoUnits">homeoUnits
| adaptor |

adaptor := PluggableAdaptor on: homeostat.
adaptor 
	getBlock: [ :model |
		model homeoUnits size.]
	putBlock: 
		[: model :value |]                "number of Units cannot be changed in the GUI"
	updateBlock:
		[ :model :aspect :parameter |
		(model = homeostat) &amp; (aspect = #units)].
^adaptor</body>

<body package="Homeostat" selector="maxRuns">maxRuns
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^maxRuns isNil
		ifTrue:
			[maxRuns := 0 asValue]
		ifFalse:
			[maxRuns]</body>

<body package="Homeostat" selector="slowingFactor">slowingFactor


| adaptor |

adaptor := PluggableAdaptor on: (homeostat).
adaptor 
	getBlock: [ :model |
		model slowingFactor ]
	putBlock: 
		[: model :value |
		 model slowingFactor: value]               								 
	updateBlock:									
		[ :model :aspect :parameter |
		aspect = #slowingFactor ].
^adaptor</body>

<body package="Homeostat" selector="unit1Active">unit1Active


^self adaptorForUnitActive: 1</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit11">Unit1ConnectStatusUnit11
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit12">Unit1ConnectStatusUnit12
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit13">Unit1ConnectStatusUnit13
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit1ConnectStatusUnit14">Unit1ConnectStatusUnit14
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1ConnectUnit11">Unit1ConnectUnit11
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 1.</body>

<body package="Homeostat" selector="Unit1ConnectUnit12">Unit1ConnectUnit12

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 1.</body>

<body package="Homeostat" selector="Unit1ConnectUnit13">Unit1ConnectUnit13

"connect the GUI to the name of the first connected unit of the third unit "
	

^self adaptorForNameOf: 3 forUnit: 1.</body>

<body package="Homeostat" selector="Unit1ConnectUnit14">Unit1ConnectUnit14
	
"connect the GUI to the name of the first connected unit of the fourth unit "
	

^self adaptorForNameOf: 4 forUnit: 1.</body>

<body package="Homeostat" selector="Unit1Deviation">Unit1Deviation
	^self adaptorForDeviationForUnit: 1</body>

<body package="Homeostat" selector="unit1HighRange">unit1HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 1</body>

<body package="Homeostat" selector="Unit1Input">Unit1Input

^self adaptorForInputFor: 1</body>

<body package="Homeostat" selector="unit1LowRange">unit1LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 1</body>

<body package="Homeostat" selector="Unit1Mass">Unit1Mass
	
^self adaptorForMass: 1</body>

<body package="Homeostat" selector="unit1Name">unit1Name

^self adaptorForNameOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1Noise">Unit1Noise

^self adaptorForInternallNoiseOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin11">Unit1NoiseSpin11


^self adaptorForNoiseOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin12">Unit1NoiseSpin12


^self adaptorForNoiseOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin13">Unit1NoiseSpin13


^self adaptorForNoiseOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit1NoiseSpin14">Unit1NoiseSpin14


^self adaptorForNoiseOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1Operational">Unit1Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit1Operational isNil
		ifTrue:
			[Unit1Operational := false asValue]
		ifFalse:
			[Unit1Operational]</body>

<body package="Homeostat" selector="Unit1Output">Unit1Output

^self adaptorForOutputFor: 1</body>

<body package="Homeostat" selector="Unit1Potentiometer">Unit1Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1SliderDeviation">Unit1SliderDeviation
^self adaptorForSliderDeviationFor: 1</body>

<body package="Homeostat" selector="Unit1Switch">Unit1Switch
	
^self adaptorForSwitch: 1</body>

<body package="Homeostat" selector="Unit1SwitchSpin11">Unit1SwitchSpin11
^self adaptorForSwitchOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit1SwitchSpin12">Unit1SwitchSpin12

^self adaptorForSwitchOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1SwitchSpin13">Unit1SwitchSpin13

^self adaptorForSwitchOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit1SwitchSpin14">Unit1SwitchSpin14

^self adaptorForSwitchOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive11">Unit1UniselectorActive11
 
^self adaptorForSelfUniselectorForUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive12">Unit1UniselectorActive12
 
^self adaptorForUniselectorOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive13">Unit1UniselectorActive13
 ^self adaptorForUniselectorOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorActive14">Unit1UniselectorActive14
	

 ^self adaptorForUniselectorOf:4 forUnit: 1</body>

<body package="Homeostat" selector="Unit1UniselectorOn">Unit1UniselectorOn
	

^self adaptorForUniselectorIsOn: 1</body>

<body package="Homeostat" selector="Unit1UniselectorSoundOn">Unit1UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 1</body>

<body package="Homeostat" selector="Unit1UniselectorTiming">Unit1UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1UniselectorType">Unit1UniselectorType
	

^self adaptorForUniselectorTypeOfUnitNumber: 1</body>

<body package="Homeostat" selector="Unit1Viscosity">Unit1Viscosity
	
^self adaptorForViscosity: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin11">Unit1WeightSpin11

^self adaptorForWeightOf: 1 forUnit: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin12">Unit1WeightSpin12
^self adaptorForWeightOf: 2 forUnit: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin13">Unit1WeightSpin13
^self adaptorForWeightOf: 3 forUnit: 1</body>

<body package="Homeostat" selector="Unit1WeightSpin14">Unit1WeightSpin14
^self adaptorForWeightOf: 4 forUnit: 1</body>

<body package="Homeostat" selector="unit2Active">unit2Active


^self adaptorForUnitActive: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit21">Unit2ConnectStatusUnit21
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit22">Unit2ConnectStatusUnit22
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit23">Unit2ConnectStatusUnit23
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectStatusUnit24">Unit2ConnectStatusUnit24
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2ConnectUnit11Input">Unit2ConnectUnit11Input
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 2.</body>

<body package="Homeostat" selector="Unit2ConnectUnit12Input">Unit2ConnectUnit12Input

"connect the GUI to the name of the second connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 2.</body>

<body package="Homeostat" selector="Unit2ConnectUnit13Input">Unit2ConnectUnit13Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 3 forUnit: 2.</body>

<body package="Homeostat" selector="Unit2ConnectUnit14Input">Unit2ConnectUnit14Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 4 forUnit: 2.</body>

<body package="Homeostat" selector="Unit2Deviation">Unit2Deviation

^self adaptorForDeviationForUnit: 2</body>

<body package="Homeostat" selector="unit2HighRange">unit2HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 2</body>

<body package="Homeostat" selector="Unit2Input">Unit2Input

^self adaptorForInputFor: 2</body>

<body package="Homeostat" selector="unit2LowRange">unit2LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 2</body>

<body package="Homeostat" selector="Unit2Mass">Unit2Mass
	
^self adaptorForMass: 2</body>

<body package="Homeostat" selector="unit2Name">unit2Name

^self adaptorForNameOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit2Noise">Unit2Noise

^self adaptorForInternallNoiseOfUnitNumber:  2</body>

<body package="Homeostat" selector="Unit2NoiseSpin21">Unit2NoiseSpin21


^self adaptorForNoiseOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit2NoiseSpin22">Unit2NoiseSpin22


^self adaptorForNoiseOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2NoiseSpin23">Unit2NoiseSpin23


^self adaptorForNoiseOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2NoiseSpin24">Unit2NoiseSpin24


^self adaptorForNoiseOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2Operational">Unit2Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit2Operational isNil
		ifTrue:
			[Unit2Operational := false asValue]
		ifFalse:
			[Unit2Operational]</body>

<body package="Homeostat" selector="Unit2Output">Unit2Output

^self adaptorForOutputFor: 2</body>

<body package="Homeostat" selector="Unit2Potentiometer">Unit2Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit2SliderDeviation">Unit2SliderDeviation

^self adaptorForSliderDeviationFor: 2</body>

<body package="Homeostat" selector="Unit2Switch">Unit2Switch
	
^self adaptorForSwitch: 2</body>

<body package="Homeostat" selector="Unit2SwitchSpin21">Unit2SwitchSpin21
^self adaptorForSwitchOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit2SwitchSpin22">Unit2SwitchSpin22
^self adaptorForSwitchOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2SwitchSpin23">Unit2SwitchSpin23
^self adaptorForSwitchOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2SwitchSpin24">Unit2SwitchSpin24
^self adaptorForSwitchOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2UniselectorActive21">Unit2UniselectorActive21
 
^self adaptorForSelfUniselectorForUnit: 2</body>

<body package="Homeostat" selector="Unit2UniselectorActive22">Unit2UniselectorActive22
 
^self adaptorForUniselectorOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2UniselectorActive23">Unit2UniselectorActive23
 
^self adaptorForUniselectorOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2UniselectorActive24">Unit2UniselectorActive24
 
^self adaptorForUniselectorOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="Unit2UniselectorOn">Unit2UniselectorOn
	

^self adaptorForUniselectorIsOn: 2</body>

<body package="Homeostat" selector="Unit2UniselectorSoundOn">Unit2UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 2</body>

<body package="Homeostat" selector="Unit2UniselectorTiming">Unit2UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit2UniselectorType">Unit2UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 2</body>

<body package="Homeostat" selector="Unit2Viscosity">Unit2Viscosity
	
^self adaptorForViscosity: 2</body>

<body package="Homeostat" selector="Unit2WeightSpin21">Unit2WeightSpin21

^self adaptorForWeightOf: 1 forUnit: 2</body>

<body package="Homeostat" selector="Unit2WeightSpin22">Unit2WeightSpin22

^self adaptorForWeightOf: 2 forUnit: 2</body>

<body package="Homeostat" selector="Unit2WeightSpin23">Unit2WeightSpin23

^self adaptorForWeightOf: 3 forUnit: 2</body>

<body package="Homeostat" selector="Unit2WeightSpin24">Unit2WeightSpin24

^self adaptorForWeightOf: 4 forUnit: 2</body>

<body package="Homeostat" selector="unit3Active">unit3Active


^self adaptorForUnitActive: 3</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit31">Unit3ConnectStatusUnit31
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit32">Unit3ConnectStatusUnit32
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit33">Unit3ConnectStatusUnit33
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3ConnectStatusUnit34">Unit3ConnectStatusUnit34
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3ConnectUnit11Input">Unit3ConnectUnit11Input
"connect the GUI to the name of the first connected unit of the first unit (i.e. itself)"
	

^self adaptorForNameOf: 1 forUnit: 3.</body>

<body package="Homeostat" selector="Unit3ConnectUnit12Input">Unit3ConnectUnit12Input

"connect the GUI to the name of the second connected unit of the second unit "
	

^self adaptorForNameOf: 2 forUnit: 3.</body>

<body package="Homeostat" selector="Unit3ConnectUnit13Input">Unit3ConnectUnit13Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 3 forUnit: 3.</body>

<body package="Homeostat" selector="Unit3ConnectUnit14Input">Unit3ConnectUnit14Input

"connect the GUI to the name of the first connected unit of the second unit "
	

^self adaptorForNameOf: 4 forUnit: 3.</body>

<body package="Homeostat" selector="Unit3Deviation">Unit3Deviation

^self adaptorForDeviationForUnit: 3</body>

<body package="Homeostat" selector="unit3HighRange">unit3HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 3</body>

<body package="Homeostat" selector="Unit3Input">Unit3Input

^self adaptorForInputFor: 3</body>

<body package="Homeostat" selector="unit3LowRange">unit3LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 3</body>

<body package="Homeostat" selector="Unit3Mass">Unit3Mass
	
^self adaptorForMass: 3</body>

<body package="Homeostat" selector="unit3Name">unit3Name

^self adaptorForNameOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit3Noise">Unit3Noise

^self adaptorForInternallNoiseOfUnitNumber:  3</body>

<body package="Homeostat" selector="Unit3NoiseSpin31">Unit3NoiseSpin31


^self adaptorForNoiseOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit3NoiseSpin32">Unit3NoiseSpin32


^self adaptorForNoiseOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3NoiseSpin33">Unit3NoiseSpin33


^self adaptorForNoiseOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3NoiseSpin34">Unit3NoiseSpin34


^self adaptorForNoiseOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3Operational">Unit3Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit3Operational isNil
		ifTrue:
			[Unit3Operational := false asValue]
		ifFalse:
			[Unit3Operational]</body>

<body package="Homeostat" selector="Unit3Output">Unit3Output

^self adaptorForOutputFor: 3</body>

<body package="Homeostat" selector="Unit3Potentiometer">Unit3Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit3SliderDeviation">Unit3SliderDeviation

^self adaptorForSliderDeviationFor: 3</body>

<body package="Homeostat" selector="Unit3Switch">Unit3Switch
	
^self adaptorForSwitch: 3</body>

<body package="Homeostat" selector="Unit3SwitchSpin31">Unit3SwitchSpin31
^self adaptorForSwitchOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit3SwitchSpin32">Unit3SwitchSpin32
^self adaptorForSwitchOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3SwitchSpin33">Unit3SwitchSpin33
^self adaptorForSwitchOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3SwitchSpin34">Unit3SwitchSpin34
^self adaptorForSwitchOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive31">Unit3UniselectorActive31
 
^self adaptorForSelfUniselectorForUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive32">Unit3UniselectorActive32
 
^self adaptorForUniselectorOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive33">Unit3UniselectorActive33
 
^self adaptorForUniselectorOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorActive34">Unit3UniselectorActive34
 
^self adaptorForUniselectorOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="Unit3UniselectorOn">Unit3UniselectorOn
	

^self adaptorForUniselectorIsOn: 3</body>

<body package="Homeostat" selector="Unit3UniselectorSoundOn">Unit3UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 3</body>

<body package="Homeostat" selector="Unit3UniselectorTiming">Unit3UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit3UniselectorType">Unit3UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 3</body>

<body package="Homeostat" selector="Unit3Viscosity">Unit3Viscosity
	
^self adaptorForViscosity: 3</body>

<body package="Homeostat" selector="Unit3WeightSpin31">Unit3WeightSpin31

^self adaptorForWeightOf: 1 forUnit: 3</body>

<body package="Homeostat" selector="Unit3WeightSpin32">Unit3WeightSpin32

^self adaptorForWeightOf: 2 forUnit: 3</body>

<body package="Homeostat" selector="Unit3WeightSpin33">Unit3WeightSpin33

^self adaptorForWeightOf: 3 forUnit: 3</body>

<body package="Homeostat" selector="Unit3WeightSpin34">Unit3WeightSpin34

^self adaptorForWeightOf: 4 forUnit: 3</body>

<body package="Homeostat" selector="unit4Active">unit4Active


^ self adaptorForUnitActive: 4</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit41">Unit4ConnectStatusUnit41
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit42">Unit4ConnectStatusUnit42
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit43">Unit4ConnectStatusUnit43
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4ConnectStatusUnit44">Unit4ConnectStatusUnit44
"adaptor for the status of the connection between  the first connected unit of the first unit (i.e. itself)"
	


^self adaptorForConnectionStatusOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4ConnectUnit11Input">Unit4ConnectUnit11Input
	

^self adaptorForNameOf: 1 forUnit: 4.</body>

<body package="Homeostat" selector="Unit4ConnectUnit12Input">Unit4ConnectUnit12Input
	

^self adaptorForNameOf: 2 forUnit: 4.</body>

<body package="Homeostat" selector="Unit4ConnectUnit13Input">Unit4ConnectUnit13Input


^self adaptorForNameOf: 3 forUnit: 4.</body>

<body package="Homeostat" selector="Unit4ConnectUnit14Input">Unit4ConnectUnit14Input


^self adaptorForNameOf: 4 forUnit: 4.</body>

<body package="Homeostat" selector="Unit4Deviation">Unit4Deviation

^self adaptorForDeviationForUnit: 4</body>

<body package="Homeostat" selector="unit4HighRange">unit4HighRange

^self adaptorForRange: ('maxDeviation' asSymbol) forUnit: 4</body>

<body package="Homeostat" selector="Unit4Input">Unit4Input

^self adaptorForInputFor: 4</body>

<body package="Homeostat" selector="unit4LowRange">unit4LowRange

^ self adaptorForRange: ('minDeviation' asSymbol) forUnit: 4</body>

<body package="Homeostat" selector="Unit4Mass">Unit4Mass
	
^self adaptorForMass: 4</body>

<body package="Homeostat" selector="unit4Name">unit4Name

^self adaptorForNameOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit4Noise">Unit4Noise

^self adaptorForInternallNoiseOfUnitNumber:  4</body>

<body package="Homeostat" selector="Unit4NoiseSpin41">Unit4NoiseSpin41


^self adaptorForNoiseOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit4NoiseSpin42">Unit4NoiseSpin42


^self adaptorForNoiseOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4NoiseSpin43">Unit4NoiseSpin43


^self adaptorForNoiseOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4NoiseSpin44">Unit4NoiseSpin44


^self adaptorForNoiseOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4Operational">Unit4Operational
	"This method was generated by UIDefiner.  Any edits made here
	may be lost whenever methods are automatically defined.  The
	initialization provided below may have been preempted by an
	initialize method."

	^Unit4Operational isNil
		ifTrue:
			[Unit4Operational := false asValue]
		ifFalse:
			[Unit4Operational]</body>

<body package="Homeostat" selector="Unit4Output">Unit4Output

^self adaptorForOutputFor: 4</body>

<body package="Homeostat" selector="Unit4Potentiometer">Unit4Potentiometer
	
^self adaptorForPotentiomOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit4SliderDeviation">Unit4SliderDeviation

^self adaptorForSliderDeviationFor: 4</body>

<body package="Homeostat" selector="Unit4Switch">Unit4Switch
	
^self adaptorForSwitch: 4</body>

<body package="Homeostat" selector="Unit4SwitchSpin41">Unit4SwitchSpin41
^self adaptorForSwitchOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit4SwitchSpin42">Unit4SwitchSpin42
^self adaptorForSwitchOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4SwitchSpin43">Unit4SwitchSpin43
^self adaptorForSwitchOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4SwitchSpin44">Unit4SwitchSpin44
^self adaptorForSwitchOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive41">Unit4UniselectorActive41
 
^self adaptorForSelfUniselectorForUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive42">Unit4UniselectorActive42
 
^self adaptorForUniselectorOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive43">Unit4UniselectorActive43
 
^self adaptorForUniselectorOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorActive44">Unit4UniselectorActive44
 
^self adaptorForUniselectorOf: 4 forUnit: 4</body>

<body package="Homeostat" selector="Unit4UniselectorOn">Unit4UniselectorOn
	

^self adaptorForUniselectorIsOn: 4</body>

<body package="Homeostat" selector="Unit4UniselectorSoundOn">Unit4UniselectorSoundOn
	

^self adaptorForUniselectorSoundIsOn: 4</body>

<body package="Homeostat" selector="Unit4UniselectorTiming">Unit4UniselectorTiming
	

^self adaptorForUniselectorTimingOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit4UniselectorType">Unit4UniselectorType
	^self adaptorForUniselectorTypeOfUnitNumber: 4</body>

<body package="Homeostat" selector="Unit4Viscosity">Unit4Viscosity
	
^self adaptorForViscosity: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin41">Unit4WeightSpin41

^self adaptorForWeightOf: 1 forUnit: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin42">Unit4WeightSpin42

^self adaptorForWeightOf: 2 forUnit: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin43">Unit4WeightSpin43

^self adaptorForWeightOf: 3 forUnit: 4</body>

<body package="Homeostat" selector="Unit4WeightSpin44">Unit4WeightSpin44

^self adaptorForWeightOf: 4 forUnit: 4</body>
</methods>

<methods>
<class-id>HomeostatStandardGUI</class-id> <category>combobox helper methods</category>

<body package="Homeostat" selector="activeStringToBoolean:">activeStringToBoolean: aString


aString = 'Active' 
	ifTrue: [^true].
aString = 'Non Active'
	ifTrue: [^false].
^nil

</body>

<body package="Homeostat" selector="booleanToActiveString:">booleanToActiveString: aBoolean

aBoolean ifTrue: [^'Active'] ifFalse:[^'Non Active']</body>

<body package="Homeostat" selector="booleanToString:">booleanToString: aBoolean

^aBoolean printString</body>

<body package="Homeostat" selector="booleanValuesChoices">booleanValuesChoices
	"returns a list  of boolean values"

	| list |
	list := List new.
	list add: true; 
	      add: false.
	^list asValue.

</body>

<body package="Homeostat" selector="ConnectionActiveChoices">ConnectionActiveChoices
	"returns a list  of  values for the status of the connection"

	| list |
	list := List new.
	list add: 'Yes'; 
	      add: 'No'.
	^list asValue.</body>

<body package="Homeostat" selector="stringToBoolean:">stringToBoolean: aString


aString = 'true' 
	ifTrue: [^true].
aString = 'false'
	ifTrue: [^false].
^nil




</body>

<body package="Homeostat" selector="uniselectorActiveChoices">uniselectorActiveChoices
	"returns a list with of choices for the uniselector controlling the connected units."

	| uniChoices |
	uniChoices := List new.
	uniChoices add: 'uniselector'; 
			      add: 'manual'.
	^uniChoices asValue.</body>

<body package="Homeostat" selector="UniselectorChoices">UniselectorChoices
	"returns a list with of choices for the uniselector controlling the connected units."

	| uniChoices prefix |

	prefix := 'HomeoUniselector'.
	uniChoices:= SortedCollection new.
	HomeoUniselector allSubclasses do: [:each | |stream |
									stream := each name asString.
									(stream beginsWith: prefix) 
										ifTrue: [
											uniChoices add: (stream copyFrom: (prefix size) +1  to: stream size )]
										ifFalse: [
											uniChoices add: stream]]. 

		
	^uniChoices  asList  asValue.</body>

<body package="Homeostat" selector="uniselectorTypeClassToString:">uniselectorTypeClassToString: aUniselectorTypeClass

	"Converts the Uniselector type class to a String"


"TEMP"
"Since the UniselectorChoices method returns a string already, just pass on the string."

^aUniselectorTypeClass</body>

<body package="Homeostat" selector="uniselectorTypeStringToClass:">uniselectorTypeStringToClass: aString
	"Converts the string describing the Uniselector type to the appropriate class"

|prefix className|

"aString contains the last part of the uniselector description, stripped of the initial HomeoUniselector prefix. Reconstruct the name and convert to a class."

prefix := 'HomeoUniselector'.

className := prefix, aString.

^className asSymbol</body>

<body package="Homeostat" selector="unitActiveChoices">unitActiveChoices
	"returns a list  of boolean values"

	| list |
	list := List new.
	list add: 'Active'; 
	      add: 'Non Active'.
	^list asValue.</body>
</methods>

</st-source>
