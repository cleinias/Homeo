'''
Created on Apr 30, 2013

@author: stefano
'''

from PyQt5.QtCore import QThread

class SimulationThread(QThread):
    
    def __init__(self):
        super(SimulationThread,self).__init__()
        self.exiting = False
 
    def __del__(self):
        self.exiting = True
        try:
            self.exit()
        except RuntimeError:
            pass
    
    def run(self):
        self.exec_()
        
