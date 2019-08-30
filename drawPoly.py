from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeySequence, QColor


class DrawPolygon(QgsMapTool):
    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, action):
        canvas = iface  #.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.action = action
        self.status = 0
        mFillColor = QColor(254, 178, 76, 63)
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(mFillColor)
        #return None

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
                #geometry = self.rb.asGeometry().boundingBox() # Discussion if boundingBox() or orientedMinimumBoundingBox() # this would also be an option
                geometry = self.rb.asGeometry().orientedMinimumBoundingBox() # Favourable one, as it only returns the 4 best points + cost point
                #extent_pol = extent_geometry.extent()
                #west = extent_pol.xMinimum()
                #east = extent_pol.xMaximum()
                #north = extent_pol.yMaximum()
                #south = extent_pol.yMinimum()
                self.action.draw_poly(geometry)  # (west, east, north, south)
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