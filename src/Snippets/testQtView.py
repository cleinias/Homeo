import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

app = QApplication(sys.argv)

grview = QGraphicsView()
scene = QGraphicsScene()
scene.addPixmap(QPixmap('pic.jpg'))
grview.setScene(scene)

grview.show()

sys.exit(app.exec_())
