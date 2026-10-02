'''
Created on Dec 16, 2014

@author: stefano

The GUI for GA simulations of Homeo experiments.  The engine itself --
HomeoGASimulation and the worker functions -- is in Simulator/HomeoGenAlg.py and
is re-exported here, so existing imports from this module keep working.
'''

from deap import base
from deap import creator
from deap import tools
from deap.tools.mutation import mutFlipBit
# from dill import dump
# import dill as pickle
from pickle import dump
from Simulator.HomeoQtSimulation import HomeoQtSimulation
import Simulator.HomeoExperiments
from Helpers.SimulationThread import SimulationThread
from Helpers.GenomeDecoder import genomeDecoder, genomePrettyPrinter
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import numpy as np
# import csv
import datetime
from operator import attrgetter
try:
    from scoop import futures
except ImportError:
    futures = None  # scoop only works when launched via its runner
import multiprocessing


try:
    from playdoh import map as pd_map
except ImportError:
    pd_map = None  # playdoh is Python 2 only; its usage is commented out

#import RobotSimulator.WebotsTCPClient
from RobotSimulator.WebotsTCPClient import WebotsTCPClient
# from socket import error as SocketError
import os
from math import sqrt, ceil as math_ceil
import math
from time import time, strftime, localtime, sleep
from tabulate import tabulate
from Helpers.ExceptionAndDebugClasses import TCPConnectionError, HomeoDebug, hDebug
from Helpers.StatsAnalyzer import extractGenomeOfIndID
from Simulator.SimulatorBackend import SimulatorBackendHOMEO,SimulatorBackendVREP,SimulatorBackendWEBOTS
from threading import Lock
from glob import glob



# The GA engine, re-exported so that existing imports from this module keep working.
from Simulator.HomeoGenAlg import (HomeoGASimulation, selTournamentRemove,
                                   _init_worker, _evaluate_genome_worker)


class QTextEditStream(QObject):
    """Thread-safe stream that redirects write() calls to a QTextEdit via a Qt signal.

    Assign an instance to sys.stdout while the GA worker thread runs;
    the cross-thread signal/slot connection ensures QTextEdit updates
    happen on the GUI thread."""

    textWritten = pyqtSignal(str)

    def write(self, text):
        if text:
            self.textWritten.emit(str(text))

    def flush(self):
        pass


class HomeoGASimulGUI(QWidget):
    """GUI to GA simulation"""

    def __init__(self, parent=None):
        super(HomeoGASimulGUI, self).__init__(parent)

        self.setWindowTitle('Homeo GA simulation')
        self.setMinimumWidth(600)

        self.gaSimulation = None
        self._population = None
        self._clonableGenome = None
        self._originalStdout = sys.stdout

        self.buildGui()
        self.connectSlots()

        self._stdoutStream = QTextEditStream(self)
        self._stdoutStream.textWritten.connect(self._appendToOutput)

    def buildGui(self):
        """Build the GUI for the GA simulation"""

        self.overallLayout = QVBoxLayout()

        # --- Control buttons row ---
        self.controlLayout = QGridLayout()
        self.initializePopButton = QPushButton("Initialize Population")
        self.noIndividualsLabel = QLabel("Population size")
        self.noIndividualsSpinBox = QSpinBox()
        self.noIndividualsSpinBox.setRange(2, 5000)
        self.noIndividualsSpinBox.setValue(150)
        self.currentFitnessLabel = QLabel("Best Fitness")
        self.currentFitnessLineEdit = QLineEdit()
        self.currentFitnessLineEdit.setReadOnly(True)
        self.startPushButton = QPushButton("Start")
        self.startPushButton.setEnabled(False)
        self.stopPushButton = QPushButton("Stop")
        self.stopPushButton.setEnabled(False)
        self.quitPushButton = QPushButton("Quit")

        self.controlLayout.addWidget(self.initializePopButton, 0, 0)
        self.controlLayout.addWidget(self.noIndividualsLabel, 0, 2)
        self.controlLayout.addWidget(self.noIndividualsSpinBox, 0, 3)
        self.controlLayout.addWidget(self.currentFitnessLabel, 1, 2)
        self.controlLayout.addWidget(self.currentFitnessLineEdit, 1, 3)
        self.controlLayout.addWidget(self.startPushButton, 2, 0)
        self.controlLayout.addWidget(self.stopPushButton, 2, 2)
        self.controlLayout.addWidget(self.quitPushButton, 2, 3)

        self.overallLayout.addLayout(self.controlLayout)

        # --- GA Parameters group ---
        self.paramGroupBox = QGroupBox("GA Parameters")
        paramLayout = QFormLayout()

        self.stepsSpinBox = QSpinBox()
        self.stepsSpinBox.setRange(10, 10000000)
        self.stepsSpinBox.setValue(1000)

        self.generationsSpinBox = QSpinBox()
        self.generationsSpinBox.setRange(0, 10000)
        self.generationsSpinBox.setValue(100)

        self.noUnitsSpinBox = QSpinBox()
        self.noUnitsSpinBox.setRange(2, 20)
        self.noUnitsSpinBox.setValue(6)

        self.cxProbSpinBox = QDoubleSpinBox()
        self.cxProbSpinBox.setRange(0.0, 1.0)
        self.cxProbSpinBox.setSingleStep(0.05)
        self.cxProbSpinBox.setValue(0.5)

        self.mutProbSpinBox = QDoubleSpinBox()
        self.mutProbSpinBox.setRange(0.0, 1.0)
        self.mutProbSpinBox.setSingleStep(0.05)
        self.mutProbSpinBox.setValue(0.2)

        self.indivProbSpinBox = QDoubleSpinBox()
        self.indivProbSpinBox.setRange(0.0, 1.0)
        self.indivProbSpinBox.setSingleStep(0.01)
        self.indivProbSpinBox.setValue(0.05)

        self.tournamentSpinBox = QSpinBox()
        self.tournamentSpinBox.setRange(2, 20)
        self.tournamentSpinBox.setValue(3)

        self.workersSpinBox = QSpinBox()
        self.workersSpinBox.setRange(1, os.cpu_count() or 4)
        self.workersSpinBox.setValue(4)
        self.workersSpinBox.setToolTip("Number of parallel worker processes (HOMEO backend only)")

        self.experimentComboBox = QComboBox()
        self.experimentComboBox.addItems([
            "initializeBraiten2_2_Full_GA_phototaxis",
            "initializeBraiten2_2_Full_GA_phototaxis_continuous",
            "initializeBraiten2_2_Full_GA_continuous_weightfree",
            "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed",
            "initializeBraiten2_2_Full_GA_continuous_weightfree_fixed_dt",
            "initializeBraiten2_2_Full_GA_scototaxis",
            "initializeBraiten2_2_Full_GA",
            "initializeBraiten2_2_NoUnisel_Full_GA",
            "initializeBraiten2_2_NoUnisel_No_Noise_Full_GA",
            "initializeBraiten2_2_Full_GA_DUMMY_SENSORS_NO_UNISEL__NO_NOISE",
        ])

        self.noNoiseCheckBox = QCheckBox("No Noise")
        self.noUniselCheckBox = QCheckBox("No Uniselector")
        self.useDummyFitnessCheckBox = QCheckBox("Dummy Fitness (testing)")

        self.popTypeComboBox = QComboBox()
        self.popTypeComboBox.addItems(["Random", "Clones"])
        self.cloneFileButton = QPushButton("Select Clone Genome...")
        self.cloneFileButton.setEnabled(False)
        self.cloneFileLabel = QLabel("No genome loaded")

        paramLayout.addRow("Steps per individual:", self.stepsSpinBox)
        paramLayout.addRow("Generations:", self.generationsSpinBox)
        paramLayout.addRow("No. of units:", self.noUnitsSpinBox)
        paramLayout.addRow("Crossover prob:", self.cxProbSpinBox)
        paramLayout.addRow("Mutation prob:", self.mutProbSpinBox)
        paramLayout.addRow("Indiv. mutation prob:", self.indivProbSpinBox)
        paramLayout.addRow("Tournament size:", self.tournamentSpinBox)
        paramLayout.addRow("Workers:", self.workersSpinBox)
        paramLayout.addRow("Experiment:", self.experimentComboBox)
        paramLayout.addRow(self.noNoiseCheckBox)
        paramLayout.addRow(self.noUniselCheckBox)
        paramLayout.addRow(self.useDummyFitnessCheckBox)
        paramLayout.addRow("Population type:", self.popTypeComboBox)
        paramLayout.addRow(self.cloneFileButton, self.cloneFileLabel)
        self.paramGroupBox.setLayout(paramLayout)

        self.overallLayout.addWidget(self.paramGroupBox)

        # --- Progress ---
        self.currentGenerationLabel = QLabel("Generation: --")
        self.generationProgressBar = QProgressBar()
        self.generationProgressBar.setRange(0, 1)
        self.generationProgressBar.setValue(0)

        self.overallLayout.addWidget(self.currentGenerationLabel)
        self.overallLayout.addWidget(self.generationProgressBar)

        # --- Output pane ---
        self.outputPane = QTextEdit()
        self.outputPane.setReadOnly(True)
        self.overallLayout.addWidget(self.outputPane)

        self.setLayout(self.overallLayout)

    def connectSlots(self):
        self.initializePopButton.clicked.connect(self._initializePopulation)
        self.startPushButton.clicked.connect(self._startEvolution)
        self.stopPushButton.clicked.connect(self._stopEvolution)
        self.quitPushButton.clicked.connect(self._quit)
        self.popTypeComboBox.currentTextChanged.connect(self._onPopTypeChanged)
        self.cloneFileButton.clicked.connect(self._selectCloneGenome)

    # --- Slot implementations ---

    def _initializePopulation(self):
        """Create a HomeoGASimulation with current parameter values and generate a population."""

        popSize = self.noIndividualsSpinBox.value()
        useDummy = self.useDummyFitnessCheckBox.isChecked()
        backend = "NONE" if useDummy else "HOMEO"
        self.gaSimulation = HomeoGASimulation(
            stepsSize=self.stepsSpinBox.value(),
            popSize=popSize,
            generSize=self.generationsSpinBox.value(),
            noUnits=self.noUnitsSpinBox.value(),
            cxProb=self.cxProbSpinBox.value(),
            mutationProb=self.mutProbSpinBox.value(),
            indivProb=self.indivProbSpinBox.value(),
            tournamentSize=self.tournamentSpinBox.value(),
            exp=self.experimentComboBox.currentText(),
            noNoise=self.noNoiseCheckBox.isChecked(),
            noUnisel=self.noUniselCheckBox.isChecked(),
            clonableGenome=self._clonableGenome,
            simulatorBackend=backend,
            nWorkers=self.workersSpinBox.value(),
        )

        if self.useDummyFitnessCheckBox.isChecked():
            self.gaSimulation.toolbox.register("evaluate",
                self.gaSimulation.evaluateGenomeFitnessSUPER_DUMMY)

        popType = self.popTypeComboBox.currentText()
        if popType == "Clones" and self._clonableGenome is not None:
            self._population = self.gaSimulation.generatePopOfClones(
                cloneName=self._clonableGenome.get('indivId', 'clone'))
        else:
            self._population = self.gaSimulation.generateRandomPop()

        gens = self.generationsSpinBox.value()
        self.generationProgressBar.setRange(0, gens + 1)
        self.generationProgressBar.setValue(0)
        self.currentGenerationLabel.setText("Population initialized (%d individuals)" % popSize)
        self.currentFitnessLineEdit.clear()

        self.startPushButton.setEnabled(True)
        self.outputPane.append("Population of %d individuals initialized.\n" % popSize)

    def _startEvolution(self):
        """Run the GA evolution synchronously on the main thread.

        The HOMEO simulator backend (Box2D) is not thread-safe, so we
        run on the main thread and call processEvents() in the progress
        callback to keep the GUI responsive."""

        self._setParametersEnabled(False)
        self.startPushButton.setEnabled(False)
        self.initializePopButton.setEnabled(False)
        self.stopPushButton.setEnabled(True)

        self._redirectStdout()

        try:
            self.gaSimulation.runGaSimulation(
                self._population, progressCallback=self._onProgress)
            completedNormally = not self.gaSimulation._stopRequested
        except Exception as e:
            self._restoreStdout()
            QMessageBox.critical(self, "GA Error", str(e))
            self._setParametersEnabled(True)
            self.initializePopButton.setEnabled(True)
            self.startPushButton.setEnabled(False)
            self.stopPushButton.setEnabled(False)
            return

        self._onEvolutionFinished(completedNormally)

    def _onProgress(self, gen, record, bestFitness):
        """Progress callback invoked by runGaSimulation after each generation."""
        self._onGenerationFinished(
            gen,
            record.get('avg', 0.0),
            record.get('min', 0.0),
            record.get('max', 0.0),
            record.get('std', 0.0))
        self._onBestFitnessUpdated(bestFitness)
        QApplication.processEvents()

    def _stopEvolution(self):
        """Request a clean stop of the evolution."""
        if self.gaSimulation is not None:
            self.gaSimulation._stopRequested = True
        self.stopPushButton.setEnabled(False)
        self.outputPane.append("\n*** Stop requested. Finishing current evaluation... ***\n")

    def _quit(self):
        """Quit the GA GUI. Stop evolution first if running."""
        if self.gaSimulation is not None:
            self.gaSimulation._stopRequested = True
        self._restoreStdout()
        self.close()

    def _onPopTypeChanged(self, text):
        self.cloneFileButton.setEnabled(text == "Clones")

    def _selectCloneGenome(self):
        """Open a file dialog to select a logbook, then extract a genome from it."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Logbook File", "",
            "Logbook files (*.lgb);;All files (*.*)")
        if filename:
            indId, ok = QInputDialog.getText(self, "Individual ID",
                "Enter the ID of the individual to clone (e.g., '018-006'):")
            if ok and indId:
                genome = extractGenomeOfIndID(indId, filename)
                if genome['genome'] != "Not Found":
                    self._clonableGenome = genome
                    self.cloneFileLabel.setText("Loaded: %s" % indId)
                else:
                    QMessageBox.warning(self, "Not Found",
                        "Individual %s not found in logbook." % indId)

    # --- Signal handler slots ---

    def _onGenerationFinished(self, gen, avg, minFit, maxFit, std):
        self.generationProgressBar.setValue(gen + 1)
        self.currentGenerationLabel.setText("Generation: %d" % gen)
        self.outputPane.append(
            "Gen %d -- avg: %.4f  min: %.4f  max: %.4f  std: %.4f\n" %
            (gen, avg, minFit, maxFit, std))

    def _onBestFitnessUpdated(self, fitness):
        self.currentFitnessLineEdit.setText("%.6f" % fitness)

    def _onEvolutionFinished(self, completedNormally):
        self._restoreStdout()
        self._setParametersEnabled(True)
        self.initializePopButton.setEnabled(True)
        self.startPushButton.setEnabled(False)
        self.stopPushButton.setEnabled(False)
        if completedNormally:
            self.outputPane.append("\n=== Evolution completed successfully ===\n")
        else:
            self.outputPane.append("\n=== Evolution stopped ===\n")

    def _onError(self, message):
        self._restoreStdout()
        QMessageBox.critical(self, "GA Error", message)
        self._setParametersEnabled(True)
        self.initializePopButton.setEnabled(True)
        self.startPushButton.setEnabled(False)
        self.stopPushButton.setEnabled(False)

    # --- Helpers ---

    def _setParametersEnabled(self, enabled):
        for w in (self.noIndividualsSpinBox, self.stepsSpinBox,
                  self.generationsSpinBox, self.noUnitsSpinBox,
                  self.cxProbSpinBox, self.mutProbSpinBox,
                  self.indivProbSpinBox, self.tournamentSpinBox,
                  self.experimentComboBox, self.noNoiseCheckBox,
                  self.noUniselCheckBox, self.useDummyFitnessCheckBox,
                  self.popTypeComboBox):
            w.setEnabled(enabled)
        self.cloneFileButton.setEnabled(
            enabled and self.popTypeComboBox.currentText() == "Clones")

    def _appendToOutput(self, text):
        sb = self.outputPane.verticalScrollBar()
        atBottom = sb.value() >= sb.maximum() - 4
        self.outputPane.moveCursor(QTextCursor.End)
        self.outputPane.insertPlainText(text)
        if atBottom:
            sb.setValue(sb.maximum())
        else:
            sb.setValue(sb.value())

    def _redirectStdout(self):
        self._originalStdout = sys.stdout
        sys.stdout = self._stdoutStream

    def _restoreStdout(self):
        sys.stdout = self._originalStdout


if __name__ == '__main__':
    app = QApplication(sys.argv)
    simulGUI = HomeoGASimulGUI()
    simulGUI.show()
    sys.exit(app.exec_())
