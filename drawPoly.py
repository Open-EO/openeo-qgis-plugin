from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapCanvas
from qgis.utils import *
from qgis.core import QgsWkbTypes
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeySequence


class DrawPolygon(QgsMapTool):
    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, couleur):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.status = 0
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(couleur)
        return None

    def keyPressEvent(self, e):
        if e.matches(QKeySequence.Undo):
            if self.rb.numberOfVertices() > 1:
                self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.status == 0:
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
                self.status = 1
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rb.numberOfVertices() > 2:
                self.status = 0
                self.selectionDone.emit()
            else:
                self.reset()
        return None

    def canvasMoveEvent(self, e):
        if self.rb.numberOfVertices() > 0 and self.status == 1:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        self.move.emit()
        return None

    def reset(self):
        self.status = 0
        self.rb.reset(True)

    def deactivate(self):
        self.rb.reset(True)
        QgsMapTool.deactivate(self)