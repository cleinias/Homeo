#!/usr/bin/python2
'''
Created on Jan 2, 2015

A small GUI utilities that allows the visualization of
trajectory files and, if present, basic GA simulation data 
from the related DEAP logbook
@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Helpers.TrajectoryGrapher import graphTrajectory
from Helpers.StatsAnalyzer import plotFitnessesFromLogBook, genomeAndFitnessList, indivsDecodedFromLogbook, showGenealogyTree
import sys
import os
from glob import glob
from sys import stderr
import pickle


class TrajectoryViewer(QWidget):
    '''
    A Qt GUI that allows the visualization of Trajectory files
    chosen from a file list
    '''


    def __init__(self, dirPath='/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData', parent=None, appRef=None):
        '''
        Constructor
        '''
        super(TrajectoryViewer,self).__init__(parent)
        self.appRef = appRef
        self._dirpath = dirPath
        self.buidGui()
        self.setDirpath(dirPath)
        self._currentLogbookName = self.setCurrentLogbookName()
        self.setCurrentLogbook()
        self.currentDir.setText(self._dirpath)
        self.currentLogbookLE.setText(self._currentLogbookName)
        self.connectSlot()
        
        
    def buidGui(self):
        '''
        Build the general GUI for the trajectory viewer
        '''       
        self.setWindowTitle("Trajectory and GA Statistics Viewer")
        self.setMinimumSize(700, 400)

        'layouts'
        self.overallLayout = QHBoxLayout()
        self.listLayout = QVBoxLayout()
        self.buttonsLayout = QVBoxLayout()
        self.trajLayout = QHBoxLayout()
        self.logLayout = QHBoxLayout()
        self.currentDirLayout = QHBoxLayout()
        self.trajectoriesLayout = QHBoxLayout()
        

        'widgets'
        self.VisualizePB = QPushButton("Visualize")
        self.changeDirPB = QPushButton("Change Dir")             
        self.currentTrajEntry = QLineEdit(self)
        self.currentLogbookLE = QLineEdit(self)
        self.currentDirLabel = QLabel("Current dir:          ")
        self.currentDir = QLineEdit(self)
        self.trajListLabel = QLabel("Trajectories:        ")
        self.TrajList = QListWidget(self)
        self.refreshPB = QPushButton("Refresh")
        self.hallOfFamePB = QPushButton("Hall of Fame")
        self.avgFitnessPB = QPushButton("Average Fitness")
        self.GAInfoPB = QPushButton("General info")
        self.genealogyPB = QPushButton("Genealogy")
        self.trajLabel = QLabel("Curr. Trajectory:   ")
        self.logLabel = QLabel("Curr. Logbook:     ")
        self.quitPB = QPushButton("Quit")
        self.hofWidget = QTableWidget()
        
        'build layouts'
        self.trajLayout.addWidget(self.trajLabel)
        self.trajLayout.addWidget(self.currentTrajEntry)
        self.logLayout.addWidget(self.logLabel)
        self.logLayout.addWidget(self.currentLogbookLE)
        self.currentDirLayout.addWidget(self.currentDirLabel)
        self.currentDirLayout.addWidget(self.currentDir)
        self.trajectoriesLayout.addWidget(self.trajListLabel)
        self.trajectoriesLayout.addWidget(self.TrajList)


        self.buttonsLayout.addWidget(self.changeDirPB)
        self.buttonsLayout.addWidget(self.GAInfoPB)
        self.buttonsLayout.addWidget(self.VisualizePB)        
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.refreshPB)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.hallOfFamePB)
        self.buttonsLayout.addWidget(self.avgFitnessPB)
        self.buttonsLayout.addWidget(self.genealogyPB)
        self.buttonsLayout.addStretch()        
        self.buttonsLayout.addWidget(self.quitPB)


        self.listLayout.addLayout(self.currentDirLayout)
        self.listLayout.addLayout(self.logLayout)
        self.listLayout.addLayout(self.trajLayout)
        self.listLayout.addLayout(self.trajectoriesLayout)

        self.overallLayout.addLayout(self.listLayout)
        self.overallLayout.addLayout(self.buttonsLayout)

        self.setLayout(self.overallLayout)
            
    def connectSlot(self):
        self.VisualizePB.clicked.connect(self.visualize)
        self.TrajList.itemClicked.connect(self.onTrajectoryClicked)
        self.TrajList.itemDoubleClicked.connect(self.onTrajectoryDoubleClicked)
        self.changeDirPB.clicked.connect(self.getNewDir)
        self.avgFitnessPB.clicked.connect(self.visualizeAvgFitnessGraph)
        self.refreshPB.clicked.connect(self._populate)
        self.hallOfFamePB.clicked.connect(self.visualizeHOF)
        self.genealogyPB.clicked.connect(self.visualizeGen)
        self.hofWidget.cellDoubleClicked.connect(self.onCellDoubleClicked)
        self.hofWidget.cellPressed.connect(self.onCellPressed)
        self.quitPB.clicked.connect(self.appRef.exit)
        self.GAInfoPB.clicked.connect(self.visualizeGAInfo)
    
    def onTrajectoryDoubleClicked(self, curr):
        self.onTrajectoryClicked(curr)
        self.visualize()
    
    def onTrajectoryClicked(self,curr):
        self.currentTrajEntry.setText(curr.text())
        
    def onCellPressed(self,row,column):
        """Allow only selection of whole rows"""
        self.hofWidget.selectRow(row)
        
    def onCellDoubleClicked(self,row,column):
        """ Select the file corresponding to the double-clicked row and visualize 
            the corresponding trajectory"""
        "TO DO"
        pass
    
    def visualize(self):
        if len(self.currentTrajEntry.text()) == 0:
            return
        else:
            try:
                graphTrajectory(os.path.join(self._dirpath, str(self.currentTrajEntry.text())))
            except:
                "visualize warning box"
                msgBox = QMessageBox();
                msgBox.setText("Invalid trajectory file");
                msgBox.exec_();
    
    def visualizeGen(self):
        "visualize the individuals' genealogy"
        #showGenealogyTree(history)
        self.notImplementedYet()
        
    def notImplementedYet(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("NOT IMPLEMENTED!")
        msgBox.setText("Sorry, this function is not implemented yet");
        msgBox.exec_()
 
    def getNewDir(self):
        dir = QFileDialog.getExistingDirectory(parent = self, directory = self._dirpath)
        self.setDirpath(str(dir))
        self.refreshLogbook()
        self.currentLogbookLE.setText(self._currentLogbookName)        
        
    def quit(self):
        self.appRef.exit()
            
    def supportedTrajExtensions(self):
        return  ['traj', 'txt']
    
    def supportedLogBookExtensions(self):
        return ['lgb']
     
    def _trajectories(self):
        # Find the matching files for each valid
        # extension and add them to the trajectories list.
        trajectories = []
        for extension in self.supportedTrajExtensions():
            pattern = os.path.join(self._dirpath, '*.%s' % extension)
            trajectories.extend(os.path.basename(x) for x in glob(pattern))        
        return trajectories

    def _populate(self):
        """ Fill the trajectory list with trajectories from the
            current directory in self._dirpath. """
     
        # In case we're repopulating, clear the list
        self.TrajList.clear()
     
        # Create a list item for each trajectory file,
        # setting the text appropriately
        for trajectory in self._trajectories():
            item = QListWidgetItem(self.TrajList)
            item.setText(trajectory)
        self.TrajList.sortItems(order=Qt.DescendingOrder)
    
    def setDirpath(self, dirpath):        
        ''' Set the current trajectory directory and refresh the list. '''
        self._dirpath = dirpath
        self._populate()
        self.currentDir.setText(self._dirpath)
        
    def setCurrentLogbookName(self):
        """Return the first logbook in current dir, i.e, the  
           first filename with extension .lgb"""
        logFilenames = []
        for extension in self.supportedLogBookExtensions():
            pattern = os.path.join(self._dirpath, '*.%s' % extension)
            logFilenames.extend(os.path.basename(x) for x in glob(pattern))
        try:
            return logFilenames[0]
        except IndexError:
            return 'NO LOGBOOKS PRESENT'
    
    def setCurrentLogbook(self):
        """Unpickle the logbook whose filename is in self._currentLogbookName
           and store it in an iVar"""
        if not self._currentLogbookName == "NO LOGBOOKS PRESENT":
            try:
                logbookFile = open(os.path.join(self._dirpath, self._currentLogbookName),'r')
                self._currentLogbook=pickle.load(logbookFile)
                logbookFile.close()                                                    
            except IOError:
                msgBox = QMessageBox()
                msgBox.setText("No logbooks present");
                msgBox.exec_()
        else:
            self._currentLogbook = None            
    
    def refreshLogbook(self):
        self._currentLogbookName = self.setCurrentLogbookName()
        self.setCurrentLogbook()
                  
    
    def visualizeHOF(self):
        """Print the hall of fame of 10 best individuals extracted 
           from the logbook in a separate window".
           Use a QTableWidget with a list containing
        a list of headers at [0] and a list of rows at [1]"""
        
        self.hofWidget.clear()
        self.hofWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        hof = genomeAndFitnessList(indivsDecodedFromLogbook(self._currentLogbook), num = 10)
        self.hofWidget.setRowCount(len(hof[1]))
        self.hofWidget.setColumnCount(len(hof[0]))

        self.hofWidget = QTableWidget(len(hof[1]),len(hof[0]))
        self.hofWidget.setHorizontalHeaderLabels(hof[0])
        self.hofWidget.setWindowTitle("Hall of Fame: 10 best results")
        for column in xrange(len(hof[0])):
            for row in xrange(len(hof[1])):
                try:
                    item = QTableWidgetItem(str(round(hof[1][row][column],3)))
                except TypeError:
                    item = QTableWidgetItem(str(hof[1][row][column]))                    
                item.setFlags(Qt.ItemIsSelectable |  Qt.ItemIsEnabled)
                self.hofWidget.setItem(row,column,item)
        self.hofWidget.setSortingEnabled(True)
        self.hofWidget.sortByColumn(0,Qt.AscendingOrder)
        self.hofWidget.show()
    
    def visualizeAvgFitnessGraph(self):
        """Show a Matplotlib chart of fitnesses if data are present"""
        
        if self._currentLogbook is not None:
            logbook = self._currentLogbook
            plotFitnessesFromLogBook(logbook)
        else:
            msgBox = QMessageBox()
            msgBox.setText("No logbook data to visualize");
            msgBox.exec_();
    
    def visualizeGAInfo(self):
        "Show general info about the GA simulation as extracted from the relevant entry in the logbook "
        self.notImplementedYet()
    
    def closeEvent(self, *args, **kwargs):
        self.appRef.exit()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TrajectoryViewer(appRef=app)
    viewer.show()
    app.exec_()
