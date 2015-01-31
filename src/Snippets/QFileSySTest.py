import sys
from PyQt4 import QtGui,QtCore

class Myview(QtGui.QMainWindow):
    def __init__(self,parent=None):
        myRootPath ='/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData'
        QtGui.QMainWindow.__init__(self)
        model = QtGui.QFileSystemModel()
        model.setRootPath('myRootPath')
        view = QtGui.QTreeView()
        view.setModel(model)
        self.setCentralWidget(view)
        view.setRootIndex(model.index(myRootPath))


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myview = Myview()
    myview.show()
    sys.exit(app.exec_())