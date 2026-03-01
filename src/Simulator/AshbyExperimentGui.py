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
        'DftB 8/3--8/4, Fig. 8/4/1'),
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
        'DftB 14/6, Figs. 14/6/1--2'),
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
<p><b>Reference:</b> DftB 8/3&ndash;8/4, Fig. 8/4/1</p>
<p><b>Ashby's protocol:</b> The Homeostat is set up with 4 fully connected
units, all under uniselector (step-function) control. It is started from
random initial parameters and allowed to run freely. The system demonstrates
ultrastability by finding a stable field through its own trial-and-error
process.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and observe the strip charts.</li>
<li>No user intervention is needed.</li>
</ol>
<p><b>What to observe:</b> The units' critical deviations will initially
fluctuate widely. Uniselector firings (shown in the narrow strip below
each unit's trace) indicate parameter changes. Eventually, all units
should settle within their bounds, demonstrating that the system has
found a stable configuration.</p>
<p><b>Expected outcome:</b> Stability is achieved after a number of
uniselector firings. The time to stability depends on the random starting
configuration.</p>''',

    2: '''<h3>Exp 2: Self-Reorganization (3-Unit Circle)</h3>
<p><b>Reference:</b> DftB 8/5, Fig. 8/5/1</p>
<p><b>Ashby's protocol:</b> Three units are connected in a ring:
Motor &rarr; Sensor &rarr; Env &rarr; Motor. The Env&rarr;Motor connection
is fixed negative. The Motor&rarr;Sensor connection is under uniselector
control. The Sensor&rarr;Env connection is hand-controlled. The system
first stabilizes with the current Sensor&rarr;Env polarity. Then the
experimenter reverses this connection, forcing the system to re-adapt.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system stabilize (watch the strip charts
settle into a steady state).</li>
<li>When stable, press <b>"Reverse Sensor&rarr;Env polarity"</b>.</li>
<li>Observe the system destabilize and then re-adapt through uniselector
action on the Motor&rarr;Sensor connection.</li>
</ol>
<p><b>Expected outcome:</b> After reversal, the system destabilizes briefly,
then the uniselector on Motor&rarr;Sensor finds a compensating value,
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
<p><b>Ashby's protocol:</b> Two units are connected. One connection
(the "commutator H") is periodically reversed by the experimenter,
simulating two alternating environments. The system must find parameter
values that are stable for <i>both</i> polarities of H.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system stabilize.</li>
<li>Press <b>"Toggle commutator H"</b> to reverse the polarity of the
Unit_1&rarr;Unit_2 connection.</li>
<li>Observe the system's response. Let it re-stabilize.</li>
<li>Toggle again. Repeat several times.</li>
</ol>
<p><b>What to observe:</b> After several alternations, the system
should find parameter values that keep it stable regardless of H's
polarity. Successive re-stabilizations should become faster as the
system converges on a universally stable configuration.</p>''',

    5: '''<h3>Exp 5: Constraint (Glass Fibre)</h3>
<p><b>Reference:</b> DftB 8/11, Fig. 8/11/1</p>
<p><b>Ashby's protocol:</b> Three fully connected units, but units 1
and 2 are "joined by a glass fibre" &mdash; a rigid constraint forcing
them to move together. The system stabilizes under this constraint.
Then the constraint is removed, and the system, adapted to the
constrained topology, becomes unstable.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b>. Notice that units 1 and 2 track each other
perfectly (same critical deviation).</li>
<li>Let the system stabilize under the constraint.</li>
<li>Press <b>"Release constraint"</b>.</li>
<li>Observe that the system destabilizes and must re-adapt.</li>
</ol>
<p><b>Expected outcome:</b> The parameters found under constraint are
not necessarily stable when units 1 and 2 can move independently.
This demonstrates that adaptation depends on the system's topology.</p>''',

    6: '''<h3>Exp 6: Habituation</h3>
<p><b>Reference:</b> DftB 14/6, Figs. 14/6/1&ndash;2</p>
<p><b>Ashby's protocol:</b> Two units are joined. A fixed displacement
("stimulus D") is repeatedly applied to unit 1. The response of unit 2
is measured after each stimulus. Over successive stimuli, the response
amplitude should decrease &mdash; a simple form of habituation.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and let the system stabilize.</li>
<li>Press <b>"Deliver stimulus D"</b> and observe unit 2's response
in the strip chart.</li>
<li>Wait for the system to settle, then deliver another stimulus.</li>
<li>Repeat several times.</li>
</ol>
<p><b>What to observe:</b> Each successive stimulus should produce
a smaller deflection in unit 2's strip chart. The stimulus counter
tracks how many stimuli have been delivered.</p>
<p><b>Expected outcome:</b> Unit 2's response amplitude decreases
over trials, demonstrating that the system "habituates" to the
repeated perturbation.</p>''',

    7: '''<h3>Exp 7: Multistable System</h3>
<p><b>Reference:</b> DftB 16/8, Fig. 16/8/1</p>
<p><b>Ashby's protocol:</b> Three units with conditional connectivity.
When unit 1 is "above the line" (positive deviation), it interacts
with unit 2; when "below" (negative), with unit 3. Connections 2&harr;3
are disabled. The system must find parameters stable for <i>both</i>
subsystem configurations.</p>
<p><b>What to do:</b></p>
<ol>
<li>Press <b>Start</b> and observe.</li>
<li>Connectivity toggling is automatic (handled per tick).</li>
</ol>
<p><b>What to observe:</b> Watch unit 1's trace in the strip chart.
When it is positive, units 1 and 2 interact; when negative, units 1
and 3 interact. You can verify in the detail dialog that connections
toggle on and off. The system must find parameters that work for
both configurations.</p>
<p><b>Expected outcome:</b> The system eventually finds a stable
multistable configuration. This may take longer than single-mode
stability because the uniselector must satisfy two sets of constraints
simultaneously.</p>''',
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
            pickle_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), 'SimulationsData', 'AshbyExperiments')
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
            expLayout.addWidget(QLabel('No user action needed.\n'
                                       'The system self-organizes automatically.'))

        elif self._exp_num == 2:
            self._reverseBtn = QPushButton('Reverse Sensor->Env polarity')
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
            self._releaseBtn = QPushButton('Release constraint')
            self._releaseBtn.clicked.connect(self._releaseExp5Constraint)
            expLayout.addWidget(self._releaseBtn)
            self._constraintStatusLabel = QLabel('Constraint: ACTIVE')
            self._constraintStatusLabel.setStyleSheet('color: blue; font-weight: bold;')
            expLayout.addWidget(self._constraintStatusLabel)
            # Install constraint callback
            constraint_cb, self._constraint_flag = make_constraint_callback(
                leader_idx=0, follower_idx=1, active=True)
            self._simulation.tick_callbacks.append(constraint_cb)

        elif self._exp_num == 6:
            self._stimulusBtn = QPushButton('Deliver stimulus D')
            self._stimulusBtn.clicked.connect(self._deliverExp6Stimulus)
            self._stimulusLabel = QLabel('Stimuli delivered: 0')
            expLayout.addWidget(self._stimulusBtn)
            expLayout.addWidget(self._stimulusLabel)

        elif self._exp_num == 7:
            expLayout.addWidget(QLabel('Connectivity toggling is automatic.\n'
                                       'Watch connections change in the detail dialog.'))
            # Install multistable callback
            ms_cb = make_multistable_callback()
            self._simulation.tick_callbacks.append(ms_cb)

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
        '''Exp 2: Reverse the Sensor->Env connection polarity.'''
        hom = self._simulation.homeostat
        env = hom.homeoUnits[2]   # Env
        sensor = hom.homeoUnits[1]  # Sensor
        for conn in env.inputConnections:
            if conn.incomingUnit is sensor:
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

    def _releaseExp5Constraint(self):
        '''Exp 5: Release the constraint joining units 1 and 2.'''
        if self._constraint_flag is not None:
            self._constraint_flag[0] = False
        self._releaseBtn.setEnabled(False)
        self._releaseBtn.setText('Constraint released')
        self._constraintStatusLabel.setText('Constraint: RELEASED')
        self._constraintStatusLabel.setStyleSheet('color: gray; font-weight: bold;')

    def _deliverExp6Stimulus(self):
        '''Exp 6: Deliver stimulus D to unit 1.'''
        inject_stimulus(self._simulation.homeostat, 0, 5.0)
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

