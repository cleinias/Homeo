'''
Interactive GUI for Ashby's 7 original Homeostat experiments from
*Design for a Brain* (2nd ed., 1960).

Subclass of HomeoSimulationControllerGui that adds:
- Experiment selector dialog
- Experiment-specific action buttons
- Per-tick callback installation (trainer, constraint, connectivity)
- Protocol instruction window
- Stability indicator

@author: stefano (with Claude)
'''

import os

from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextBrowser, QFrame, QGroupBox,
    QApplication, QWidget, QCheckBox, QDialogButtonBox
)
from PyQt5.QtGui import QFont

from Simulator.HomeoGeneralGUI import HomeoSimulationControllerGui
from Simulator.AshbyOriginalExperiments import (
    make_trainer_callback,
    make_constraint_callback,
    exp1_reversal_event,
    exp1_displacement_event,
    EXP6_DISPLACEMENT,
    make_multistable_callback,
    StabilityTracker,
    inject_stimulus,
)


# Module-level reference to the active GUI window, kept alive
# across experiment switches to prevent garbage collection.
_active_gui = None


# ---------------------------------------------------------------
#  Experiment metadata
# ---------------------------------------------------------------

EXPERIMENT_INFO = {
    1: ('Exp 1: Basic Ultrastability',
        'initializeAshbyExp1BasicUltrastability',
        'DftB 8/4, Fig. 8/4/1'),
    2: ('Exp 2: Self-Reorganization (3-Unit Circle)',
        'initializeAshbyExp2SelfReorganization',
        'DftB 8/5, Fig. 8/5/1'),
    3: ('Exp 3: Training by Punishment',
        'initializeAshbyExp3Training',
        'DftB 8/9, Fig. 8/9/1'),
    4: ('Exp 4: Alternating Environments',
        'initializeAshbyExp4AlternatingEnvironments',
        'DftB 8/10, Fig. 8/10/1'),
    5: ('Exp 5: Constraint (Glass Fibre)',
        'initializeAshbyExp5Constraint',
        'DftB 8/11, Fig. 8/11/1'),
    6: ('Exp 6: Habituation',
        'initializeAshbyExp6Habituation',
        'DftB 14/6, Fig. 14/6/1'),
    7: ('Exp 7: Multistable System',
        'initializeAshbyExp7Multistable',
        'DftB 16/8, Fig. 16/8/1'),
    0: ('New experiment (blank Homeostat)',
        None,
        'Default 4-unit fully connected'),
    -1: ('Load saved homeostat...',
         None,
         'Load a previously saved .pickled file'),
}


# ---------------------------------------------------------------
#  Protocol text for each experiment
# ---------------------------------------------------------------

PROTOCOL_TEXT = {
    1: '''<h3>Exp 1: Basic Ultrastability</h3>
<p><b>Reference:</b> DftB 8/4, Fig. 8/4/1</p>
<p><b>Ashby's protocol:</b> Two units interact, 1 &harr; 2, Ashby's analogue
of the operations of Marina and Sperry, who crossed nerves or muscles in
animals. 1&rarr;2 is hand-controlled; 2&rarr;1 is under the control of
unit 1's uniselector. The system starts stable: an upward displacement of 2
moves 1 up. The experimenter then reverses 1&rarr;2 (R1), making the system
unstable; unit 1's uniselector changes 2&rarr;1 until stability returns.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system settle.</li>
<li>Press <b>"Displace unit 2 (D)"</b>: 1 follows 2.</li>
<li>Press <b>"Reverse 1&rarr;2 (R)"</b>. Wait for the runaway, the
uniselector changes and the return to rest (a few thousand ticks).</li>
<li>Displace unit 2 again: 1 now moves the opposite way.</li>
<li>Reverse 1&rarr;2 again and repeat.</li>
</ol>
<p><b>Expected outcome:</b> after each reversal the uniselector of unit 1
finds a value of 2&rarr;1 of the opposite sign: "This reversal compensated
for the reversal of 1&rarr;2". Ashby's run needed one uniselector change
after R1 and three after R2.</p>''',

    2: '''<h3>Exp 2: Self-Reorganization (3-Unit Circle)</h3>
<p><b>Reference:</b> DftB 8/5, Fig. 8/5/1</p>
<p><b>Ashby's protocol:</b> Three units are connected in a ring:
1 &rarr; 2 &rarr; 3 &rarr; 1. The 3&rarr;1 connection
is fixed negative. The 1&rarr;2 connection is under the control of
unit 2's uniselector. The 2&rarr;3 connection is hand-controlled. The system
first stabilizes with the current 2&rarr;3 polarity. Then the
experimenter reverses this connection, forcing the system to re-adapt.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system stabilize (watch the strip charts
settle into a steady state).</li>
<li>When stable, press <b>"Reverse 2&rarr;3 polarity"</b>.</li>
<li>Observe the system destabilize and then re-adapt through uniselector
action on the 1&rarr;2 connection.</li>
</ol>
<p><b>Expected outcome:</b> After reversal, the system destabilizes briefly,
then unit 2's uniselector finds a compensating value for 1&rarr;2,
restoring stability. This demonstrates self-reorganization.</p>''',

    3: '''<h3>Exp 3: Training by Punishment</h3>
<p><b>Reference:</b> DftB 8/9, Fig. 8/9/1</p>
<p><b>Ashby's protocol:</b> Three units form a triangle. An external
"trainer" watches the direction of movement of units 1 and 2. If they
move in the same direction (which is "wrong"), the trainer punishes
by forcing unit 3 to its extreme, destabilizing the system and forcing
the uniselector to try new values.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and observe.</li>
<li>The trainer acts automatically. The punishment counter in the action
panel shows how many times punishment has been delivered.</li>
</ol>
<p><b>What to observe:</b> Early on, punishments are frequent (units
often move in the same direction). Over time, the uniselector finds
parameters where units 1 and 2 reliably move in opposite directions,
and punishments cease.</p>
<p><b>Expected outcome:</b> The system learns the "correct" behavior
(opposite movement) through punishment-driven reorganization.</p>''',

    4: '''<h3>Exp 4: Alternating Environments</h3>
<p><b>Reference:</b> DftB 8/10, Fig. 8/10/1</p>
<p><b>Ashby's protocol:</b> The Homeostat is "partly under uniselector-,
and partly under hand-, control". Two units: 1&rarr;2 is a hand-controlled
commutator H; 2&rarr;1 is under the control of unit 1's uniselector. From
time to time the experimenter reverses H, each value "sustained long enough
so that the change does not interrupt the process of trial and error".</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system settle (it starts stable).</li>
<li>Press <b>"Toggle commutator H"</b>.</li>
<li>Wait until the system has settled again: a runaway, uniselector
changes and the return to rest can take several thousand ticks.</li>
<li>Toggle again. Repeat several times.</li>
</ol>
<p><b>What to observe:</b> "a field that is terminal for only one of the
parameter-values will be lost when the parameter next changes; but the
first field terminal for both will be retained." Once such a field is
found, further reversals of H cause no uniselector changes.</p>''',

    5: '''<h3>Exp 5: Constraint (Glass Fibre)</h3>
<p><b>Reference:</b> DftB 8/11, Fig. 8/11/1</p>
<p><b>Ashby's protocol:</b> Three units are joined and "at first stable".
At J the experimenter joins the magnets of 1 and 2 with a light glass fibre,
so that they move together; "in this case" the constraint makes the system
unstable, and the uniselectors find a new stable field. At R the fibre is
lifted away, and the system becomes unstable: the new field "took notice of"
the constraint and used it.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system settle.</li>
<li>Press <b>"Join fibre (J)"</b>: units 1 and 2 now move together.</li>
<li>Wait for the runaway, the uniselector changes and the return to rest
(several thousand ticks).</li>
<li>Press <b>"Release fibre (R)"</b>.</li>
</ol>
<p><b>Expected outcome:</b> the field found with the fibre is stable only
with it; after R the system runs away again.</p>''',

    6: '''<h3>Exp 6: Habituation</h3>
<p><b>Reference:</b> DftB 14/6, Fig. 14/6/1</p>
<p><b>Ashby's protocol:</b> "Two units were joined 1 &rarr; 2. The effect
of 1 on 2 was determined by 2's uniselector, which changed position if 2
exceeded its critical states. The operator then repeatedly disturbed 2 by
moving 1, at D." There is no 2&rarr;1.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system settle.</li>
<li>Press <b>"Deliver stimulus D"</b>: unit 1 is displaced by a fixed
angle, and unit 2 responds.</li>
<li>Wait until both units are back at rest (a few thousand ticks), then
deliver another stimulus. Repeat ten times or so.</li>
</ol>
<p><b>What to observe:</b> while D drives unit 2 past its critical level,
its uniselector changes 1&rarr;2. The first value for which D no longer
does is "retained permanently", and from then on 2's response to D stays
small. Ashby's run needed four changes. If the first value already gives a
small response, there is nothing to habituate.</p>
<p>Fig. 14/6/2 (1 &harr; 2, both on uniselectors) can be run headless:
<tt>run_ashby_original_experiments.py --exp 6 --fig 2</tt>.</p>''',

    7: '''<h3>Exp 7: Multistable System</h3>
<p><b>Reference:</b> DftB 16/8, Fig. 16/8/1</p>
<p><b>Ashby's protocol:</b> Three units, 2 &harr; 1 &harr; 3, with no
link between 2 and 3. Bars across the potentiometer dishes of 2 and 3 let
them move only downwards from the centre. 1 acts on 2 negatively and on 3
positively, by hand; 2&rarr;1 and 3&rarr;1 are under the control of unit 1's
uniselector. When 1 is above the centre it pushes 2 down, and 1 and 2
interact while 3 rests at its bar; below the centre, 1 and 3 interact.
Every step of the uniselector changes both 2&rarr;1 and 3&rarr;1, so a step
that makes one pair stable can make the other unstable.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and watch unit 1's uniselector (no action needed).</li>
<li>When it has stopped changing, test the result by displacing unit 1
up and down (unit 1's slider).</li>
</ol>
<p><b>Expected outcome:</b> the uniselector stops only at values that make
both pairs stable; then "1 can interact repeatedly with both 2 and 3 without
loss of stability". Ashby's run took four changes.</p>''',
}


# ---------------------------------------------------------------
#  Experiment selector dialog
# ---------------------------------------------------------------

class ExperimentSelectorDialog(QDialog):
    '''Dialog to choose one of Ashby's 7 experiments.'''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Ashby Experiment")
        self.setMinimumSize(420, 320)
        self.selected_exp = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose an experiment to replicate:"))

        self.listWidget = QListWidget()
        # Ashby experiments first (1-7)
        for num in sorted(k for k in EXPERIMENT_INFO if k >= 1):
            title, _, ref = EXPERIMENT_INFO[num]
            item = QListWidgetItem('%s  (%s)' % (title, ref))
            item.setData(Qt.UserRole, num)
            self.listWidget.addItem(item)
        # Separator + non-Ashby options (0, -1)
        sep = QListWidgetItem('---')
        sep.setFlags(Qt.NoItemFlags)
        self.listWidget.addItem(sep)
        for num in (0, -1):
            title, _, ref = EXPERIMENT_INFO[num]
            item = QListWidgetItem('%s  (%s)' % (title, ref))
            item.setData(Qt.UserRole, num)
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            self.listWidget.addItem(item)
        self.listWidget.setCurrentRow(0)
        self.listWidget.itemDoubleClicked.connect(self._accept)
        layout.addWidget(self.listWidget)

        btnLayout = QHBoxLayout()
        selectBtn = QPushButton("Select")
        selectBtn.clicked.connect(self._accept)
        cancelBtn = QPushButton("Cancel")
        cancelBtn.clicked.connect(self.reject)
        btnLayout.addWidget(selectBtn)
        btnLayout.addWidget(cancelBtn)
        layout.addLayout(btnLayout)

    def _accept(self):
        item = self.listWidget.currentItem()
        if item:
            self.selected_exp = item.data(Qt.UserRole)
            self.accept()

    @staticmethod
    def getExperiment(parent=None):
        '''Show the dialog and return the selected experiment number, or None.'''
        dlg = ExperimentSelectorDialog(parent)
        if dlg.exec_() == QDialog.Accepted:
            return dlg.selected_exp
        return None


# ---------------------------------------------------------------
#  Main GUI subclass
# ---------------------------------------------------------------

class AshbyExperimentGui(HomeoSimulationControllerGui):
    '''Interactive GUI for Ashby's 7 original Homeostat experiments.

    Subclasses the standard HomeoSimulationControllerGui to add
    experiment-specific controls, callbacks, and protocol display.
    '''

    def __init__(self, parent=None, exp_num=None):
        # Show selector if no experiment specified
        if exp_num is None:
            exp_num = ExperimentSelectorDialog.getExperiment()
            if exp_num is None:
                # User cancelled — default to experiment 1
                exp_num = 1

        self._exp_num = exp_num
        title, func_name, ref = EXPERIMENT_INFO[exp_num]

        # Initialize parent with the chosen experiment
        super().__init__(parent=parent, experiment=func_name)

        # 1. Default maxRuns to 10000
        self._simulation._maxRuns = 10000
        self.maxRunSpinBox.setValue(10000)

        # 2. Size aux window to tightly fit 4 units
        self._homeostat_gui.setMinimumSize(880, 920)
        self._homeostat_gui.resize(880, 920)

        # 3. Pickle homeostat and set experiment name (Ashby experiments only)
        if exp_num >= 1:
            exp_name = 'Ashby_Experiment_%d' % exp_num
            from Helpers.General_Helper_Functions import simulations_data_dir
            pickle_dir = os.path.join(simulations_data_dir(), 'AshbyExperiments')
            os.makedirs(pickle_dir, exist_ok=True)
            pickle_path = os.path.join(pickle_dir, exp_name + '.pickled')
            self._simulation.homeostat.saveTo(pickle_path)
            self._simulation.homeostatFilename = exp_name
            self._simulation._homeostatIsSaved = True

        # 3b. Load a pickled homeostat if requested
        if exp_num == -1:
            self.loadHomeostat()

        # 4. Grey out inactive units in aux window
        for i, unit in enumerate(self._simulation.homeostat.homeoUnits):
            if not unit.isActive():
                pattern = QRegularExpression('^unit%d' % (i + 1))
                for widget in self._homeostat_gui.findChildren(QWidget, pattern):
                    widget.setEnabled(False)
                    widget.setStyleSheet(
                        'background-color: #999; color: #666;')

        # State for callbacks
        self._punishment_log = []
        self._constraint_flag = None
        self._stimulus_count = 0

        # Stability tracker
        self._stability_tracker = StabilityTracker(
            self._simulation.homeostat, window=200, burn_in=200)

        # Install per-tick callbacks and build action panel
        self._setupExperimentActions()

        # Stability tracker updates data only (no GUI) — runs in simulation thread
        self._simulation.tick_callbacks.append(self._stability_tick_data)

        # GUI updates happen on the main thread via the liveDataCritDevChanged signal
        self._simulation.liveDataCritDevChanged.connect(self._updateExperimentDisplay)

        # Update window title
        self.setWindowTitle('%s  [%s]' % (title, ref))

    def _setupExperimentActions(self):
        '''Add experiment-specific widgets to the simulation dialog.'''

        # Create a group box for experiment actions
        self._expGroup = QGroupBox('Experiment Actions')
        expLayout = QVBoxLayout()

        # Experiment title label
        title, _, ref = EXPERIMENT_INFO[self._exp_num]
        titleLabel = QLabel('<b>%s</b><br><i>%s</i>' % (title, ref))
        titleLabel.setTextFormat(Qt.RichText)
        expLayout.addWidget(titleLabel)

        # Stability indicator
        self._stabilityLabel = QLabel('UNSTABLE')
        self._stabilityLabel.setStyleSheet(
            'color: red; font-weight: bold; padding: 2px;')
        expLayout.addWidget(self._stabilityLabel)

        # Protocol button (Ashby experiments only)
        if self._exp_num >= 1:
            protocolBtn = QPushButton('Show Protocol')
            protocolBtn.clicked.connect(self._showProtocol)
            expLayout.addWidget(protocolBtn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        expLayout.addWidget(sep)

        # Experiment-specific controls
        if self._exp_num <= 0:
            expLayout.addWidget(QLabel('Standard 4-unit Homeostat.\n'
                                       'Use the controls below to run.'))

        elif self._exp_num == 1:
            self._displaceBtn = QPushButton('Displace unit 2 (D)')
            self._displaceBtn.clicked.connect(
                lambda: exp1_displacement_event(self._simulation.homeostat))
            self._reverseBtn = QPushButton('Reverse 1->2 (R)')
            self._reverseBtn.clicked.connect(
                lambda: exp1_reversal_event(self._simulation.homeostat))
            expLayout.addWidget(self._displaceBtn)
            expLayout.addWidget(self._reverseBtn)

        elif self._exp_num == 2:
            self._reverseBtn = QPushButton('Reverse 2->3 polarity')
            self._reverseBtn.clicked.connect(self._reverseExp2Polarity)
            expLayout.addWidget(self._reverseBtn)

        elif self._exp_num == 3:
            self._punishLabel = QLabel('Punishments: 0')
            expLayout.addWidget(self._punishLabel)
            expLayout.addWidget(QLabel('Trainer acts automatically.'))
            # Install trainer callback (modifies homeostat state only, no GUI)
            trainer_cb, self._punishment_log = make_trainer_callback()
            self._simulation.tick_callbacks.append(trainer_cb)

        elif self._exp_num == 4:
            self._toggleBtn = QPushButton('Toggle commutator H')
            self._toggleBtn.clicked.connect(self._toggleExp4Commutator)
            self._polarityLabel = QLabel('H polarity: +1')
            expLayout.addWidget(self._toggleBtn)
            expLayout.addWidget(self._polarityLabel)

        elif self._exp_num == 5:
            self._joinBtn = QPushButton('Join fibre (J)')
            self._joinBtn.clicked.connect(self._joinExp5Constraint)
            expLayout.addWidget(self._joinBtn)
            self._releaseBtn = QPushButton('Release fibre (R)')
            self._releaseBtn.clicked.connect(self._releaseExp5Constraint)
            self._releaseBtn.setEnabled(False)
            expLayout.addWidget(self._releaseBtn)
            self._constraintStatusLabel = QLabel('Fibre: OFF')
            self._constraintStatusLabel.setStyleSheet('color: gray; font-weight: bold;')
            expLayout.addWidget(self._constraintStatusLabel)
            # Install the fibre callback, not yet joined
            constraint_cb, self._constraint_flag = make_constraint_callback()
            self._simulation.tick_callbacks.append(constraint_cb)

        elif self._exp_num == 6:
            self._stimulusBtn = QPushButton('Deliver stimulus D')
            self._stimulusBtn.clicked.connect(self._deliverExp6Stimulus)
            self._stimulusLabel = QLabel('Stimuli delivered: 0')
            expLayout.addWidget(self._stimulusBtn)
            expLayout.addWidget(self._stimulusLabel)

        elif self._exp_num == 7:
            expLayout.addWidget(QLabel('Bars stop units 2 and 3 above the centre.\n'
                                       'No user action needed.'))
            # Install the bars
            self._simulation.tick_callbacks.append(make_multistable_callback())

        # Separator before "Change Experiment" button
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        expLayout.addWidget(sep2)

        changeBtn = QPushButton('Change Experiment...')
        changeBtn.clicked.connect(self._changeExperiment)
        expLayout.addWidget(changeBtn)

        self._expGroup.setLayout(expLayout)

        # Insert the experiment panel into the main layout
        mainLayout = self.layout()
        mainLayout.insertWidget(0, self._expGroup)

    # -----------------------------------------------------------
    #  Per-tick data update (runs in simulation thread — NO GUI calls)
    # -----------------------------------------------------------

    def _stability_tick_data(self, hom, tick):
        '''Update the stability tracker data only. No widget updates here.'''
        self._stability_tracker.check(tick)

    # -----------------------------------------------------------
    #  GUI update (runs on main thread via liveDataCritDevChanged signal)
    # -----------------------------------------------------------

    def _updateExperimentDisplay(self, unitRef):
        '''Update experiment-specific GUI elements. Called on the main thread.'''
        # Stability indicator
        if self._stability_tracker.currently_stable:
            self._stabilityLabel.setText('STABLE')
            self._stabilityLabel.setStyleSheet(
                'color: green; font-weight: bold; padding: 2px;')
        else:
            self._stabilityLabel.setText('UNSTABLE')
            self._stabilityLabel.setStyleSheet(
                'color: red; font-weight: bold; padding: 2px;')

        # Experiment-specific displays
        if self._exp_num == 3:
            self._punishLabel.setText('Punishments: %d' % len(self._punishment_log))

    # -----------------------------------------------------------
    #  Protocol display
    # -----------------------------------------------------------

    def _showProtocol(self):
        '''Show the protocol instruction window for the current experiment.'''
        dlg = QDialog(self)
        dlg.setWindowTitle('Protocol: %s' % EXPERIMENT_INFO[self._exp_num][0])
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(PROTOCOL_TEXT.get(self._exp_num, '<p>No protocol available.</p>'))
        layout.addWidget(browser)
        closeBtn = QPushButton('Close')
        closeBtn.clicked.connect(dlg.accept)
        layout.addWidget(closeBtn)
        dlg.show()

    # -----------------------------------------------------------
    #  Experiment action slots
    # -----------------------------------------------------------

    def _reverseExp2Polarity(self):
        '''Exp 2: Reverse the 2->3 connection polarity.'''
        hom = self._simulation.homeostat
        unit3 = hom.homeoUnits[2]
        unit2 = hom.homeoUnits[1]
        for conn in unit3.inputConnections:
            if conn.incomingUnit is unit2:
                conn.newWeight(conn.weight * conn.switch * -1)
                break
        self._reverseBtn.setEnabled(False)
        self._reverseBtn.setText('Polarity reversed')

    def _toggleExp4Commutator(self):
        '''Exp 4: Toggle the commutator H (Unit_1->Unit_2 connection).'''
        hom = self._simulation.homeostat
        unit1 = hom.homeoUnits[0]
        unit2 = hom.homeoUnits[1]
        for conn in unit2.inputConnections:
            if conn.incomingUnit is unit1:
                conn.newWeight(conn.weight * conn.switch * -1)
                # Show current polarity
                new_sign = '+1' if conn.switch >= 0 else '-1'
                self._polarityLabel.setText('H polarity: %s' % new_sign)
                break

    def _joinExp5Constraint(self):
        '''Exp 5: Join units 1 and 2 with the fibre (J).'''
        self._constraint_flag[0] = True
        self._joinBtn.setEnabled(False)
        self._releaseBtn.setEnabled(True)
        self._constraintStatusLabel.setText('Fibre: JOINED')
        self._constraintStatusLabel.setStyleSheet('color: blue; font-weight: bold;')

    def _releaseExp5Constraint(self):
        '''Exp 5: Remove the fibre joining units 1 and 2 (R).'''
        self._constraint_flag[0] = False
        self._releaseBtn.setEnabled(False)
        self._releaseBtn.setText('Fibre released')
        self._constraintStatusLabel.setText('Fibre: RELEASED')
        self._constraintStatusLabel.setStyleSheet('color: gray; font-weight: bold;')

    def _deliverExp6Stimulus(self):
        '''Exp 6: Deliver stimulus D to unit 1.'''
        inject_stimulus(self._simulation.homeostat, 0, EXP6_DISPLACEMENT)
        self._stimulus_count += 1
        self._stimulusLabel.setText('Stimuli delivered: %d' % self._stimulus_count)

    # -----------------------------------------------------------
    #  Change experiment
    # -----------------------------------------------------------

    def _showSaveDialog(self):
        '''Show a dialog offering to save homeostat and/or data before switching.

        Returns (save_homeostat, save_data) booleans, or None if cancelled.
        '''
        dlg = QDialog(self)
        dlg.setWindowTitle('Change Experiment')
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel('Before switching experiment, would you like to save?'))

        saveHomeostatCb = QCheckBox('Save homeostat (pickled state)')
        saveDataCb = QCheckBox('Save experiment data')
        layout.addWidget(saveHomeostatCb)
        layout.addWidget(saveDataCb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Continue')
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() == QDialog.Accepted:
            return (saveHomeostatCb.isChecked(), saveDataCb.isChecked())
        return None

    def _changeExperiment(self):
        '''Switch to a different Ashby experiment.'''

        # 1. Pause if running
        was_running = self._simulation._isRunning
        if was_running:
            self.pause()

        # 2. Show save dialog
        result = self._showSaveDialog()
        if result is None:  # cancelled
            if was_running:
                self.resume()
            return

        # 3. Do saves if requested
        save_homeostat, save_data = result
        if save_homeostat:
            self.saveHomeostat()
        if save_data:
            self.saveAllData()

        # 4. Show experiment selector
        new_exp = ExperimentSelectorDialog.getExperiment(self)
        if new_exp is None:  # cancelled
            if was_running:
                self.resume()
            return

        # 5. Create new GUI and close old one.
        #    Store on the module to prevent garbage collection before
        #    the new window's event loop takes over.
        global _active_gui
        _active_gui = AshbyExperimentGui(exp_num=new_exp)
        _active_gui.setAttribute(Qt.WA_DeleteOnClose)
        _active_gui.show()
        self._homeostat_gui.close()
        self.close()

