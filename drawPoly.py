"""
/***************************************************************************
 DrawPolygon

 This class is responsible for drawing a polygon on the map and returning the coordinates of it.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeySequence, QColor


class DrawPolygon(QgsMapTool):
    """
    This class is responsible for drawing a polygon on the map and returning the coordinates of it.
    """
    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, parent):
        """
        Initialize the draw polygon class
        :param iface: Interface to be displayed
        :param parent: Parent dialog, which initialized the class (should be JobAdaptDialog)
        """
        canvas = iface
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.parent = parent
        self.status = 0
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(QColor(254, 178, 76, 63))

    def keyPressEvent(self, e):
        """
        Called if a keyboard key got pressed
        :param e: Event
        """
        if e.matches(QKeySequence.Undo):
            if self.rb.numberOfVertices() > 1:
                self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        """
        Called if a mouse button got pressed on the map canvas.
        :param e: Event
        """
        if e.button() == Qt.LeftButton:
            if self.status == 0:
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
                self.status = 1
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rb.numberOfVertices() > 2:
                self.status = 0
                self.selectionDone.emit()
                geometry = self.rb.asGeometry()
                self.parent.draw_poly(geometry)
            else:
                self.reset()

    def canvasMoveEvent(self, e):
        """
        Called if a mouse button got pressed on the map canvas.
        :param e: Event
        """
        if self.rb.numberOfVertices() > 0 and self.status == 1:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        self.move.emit()

    def reset(self):
        """
        Reseting the polygon
        """
        self.status = 0
        self.rb.reset(True)

    def deactivate(self):
        """
        Deactivate the polygon
        """
        self.rb.reset(True)
        QgsMapTool.deactivate(self)
