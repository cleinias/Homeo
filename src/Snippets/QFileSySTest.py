import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class Myview(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        myRootPath ='/home/stefano/Documents/Projects/Homeostat/Simulator/Python-port/Homeo/SimulationsData'
        QtWidgets.QMainWindow.__init__(self)
        model = QtWidgets.QFileSystemModel()
        model.setRootPath('myRootPath')
        view = QtWidgets.QTreeView()
        view.setModel(model)
        self.setCentralWidget(view)
        view.setRootIndex(model.index(myRootPath))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myview = Myview()
    myview.show()
    sys.exit(app.exec_())