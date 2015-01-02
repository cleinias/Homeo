'''
Created on Jan 2, 2015

A small GUI utilities that allows the visualization of
trajectory files   
@author: stefano
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from Helpers.TrajectoryGrapher import graphTrajectory
import sys
from PyQt4.Qt import QMessageBox
import os
from glob import glob
from sys import stderr


class TrajectoryViewer(QWidget):
    '''
    A Qt GUI that allows the visualization of Trajectory files
    chosen from a file list
    '''


    def __init__(self, dirPath='/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData', parent=None):
        '''
        Constructor
        '''
        super(TrajectoryViewer,self).__init__(parent)
        self._dirpath = dirPath
        self.buidGui()
        self.setDirpath(dirPath)
        self.currentDir.setText(self._dirpath)
        self.connectSlot()
        
        
    def buidGui(self):
        '''
        Build the general GUI for the trajectory viewer
        '''       
        self.setWindowTitle("Trajectory Viewer")
        self.setMinimumSize(700, 400)

        'layouts'
        self.overallLayout = QHBoxLayout()
        self.listLayout = QVBoxLayout()
        self.buttonsLayout = QVBoxLayout()

        'widgets'
        self.VisualizePB = QPushButton("Visualize")
        self.changeDirPB = QPushButton("Change Dir")             
        self.currentTrajEntry = QLineEdit(self)
        self.currentDir = QLineEdit(self)
        self.TrajList = QListWidget(self)
        #self.listLayout.addWidget(self.QuitButton)
        self.listLayout.addWidget(self.currentDir)
        self.listLayout.addWidget(self.TrajList)
        self.listLayout.addWidget(self.currentTrajEntry)
        
        'build layouts'
        self.buttonsLayout.addWidget(self.changeDirPB)
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.VisualizePB)

        self.overallLayout.addLayout(self.listLayout)
        self.overallLayout.addLayout(self.buttonsLayout)
        self.setLayout(self.overallLayout)
            
    def connectSlot(self):
        self.VisualizePB.clicked.connect(self.visualize)
        self.TrajList.itemClicked.connect(self.onTrajectoryClicked)
        self.TrajList.itemDoubleClicked.connect(self.onTrajectoryDoubleClicked)
        self.changeDirPB.clicked.connect(self.getNewDir)
        #self.QuitButton.clicked.connect(self.quit())
    
    def onTrajectoryDoubleClicked(self, curr):
        self.onTrajectoryClicked(curr)
        self.visualize()
    
    def onTrajectoryClicked(self,curr):
        self.currentTrajEntry.setText(curr.text())
    
    def visualize(self):
        if len(self.currentTrajEntry.text()) == 0:
            return
        else:
            try:
                print "Trying to visualize: ", os.path.join(self._dirpath, str(self.currentTrajEntry.text()))
                graphTrajectory(os.path.join(self._dirpath, str(self.currentTrajEntry.text())))
            except:
                "visualize warning box"
                msgBox = QMessageBox();
                msgBox.setText("Invalid trajectory file");
                msgBox.exec_();
    
    def getNewDir(self):
        dir = QFileDialog.getExistingDirectory(parent = self, directory = self._dirpath)
        self.setDirpath(str(dir))
        
    def quit(self):
        app.quit()
            
    def supportedTrajExtensions(self):
        return  ['txt', 'traj']
     
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
    
    def setDirpath(self, dirpath):        
        ''' Set the current trajectory directory and refresh the list. '''
        self._dirpath = dirpath
        self._populate()
        self.currentDir.setText(self._dirpath)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = TrajectoryViewer()
    viewer.show()
    app.exec_()
