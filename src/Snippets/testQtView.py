import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *; from PyQt5.QtGui import *

app = QApplication(sys.argv)

grview = QGraphicsView()
scene = QGraphicsScene()
scene.addPixmap(QPixmap('pic.jpg'))
grview.setScene(scene)

grview.show()

sys.exit(app.exec_())
