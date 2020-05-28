"""
/***************************************************************************
 DrawRectangle

 This class is responsible for drawing a rectangle on the map and returning the coordinates of it.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsPointXY
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import pyqtSignal


class DrawRectangle(QgsMapTool):
    """
    This class is responsible for drawing a rectangle on the map and returning the coordinates of it.
    """
    rectangleCreated = pyqtSignal(float, float, float, float)

    def __init__(self, canvas, parent):
        """
        Initialize the draw rectangle class
        :param canvas: Canvas to be displayed
        :param parent: Parent dialog, which initialized the class (should be JobAdaptDialog)
        """
        QgsMapTool.__init__(self, canvas)

        self.canvas = canvas
        self.active = False
        self.parent = parent
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(QColor(254, 178, 76, 63))
        self.rubberBand.setWidth(1)
        self.startPoint = None
        self.endPoint = None
        self.isEmittingPoint = False
        self.reset()

    def reset(self):
        """
        Reseting the rectangle
        """
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)

    def canvasPressEvent(self, e):
        """
        Called if a mouse button got pressed on the map canvas, taking the starting point of the rectangle.
        :param e: Event
        """
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.show_rect(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        """
        Called if a mouse button got released on the map canvas, finishing the selection and
        returning to the parent dialog.
        :param e: Event
        """
        self.isEmittingPoint = False
        self.rubberBand.show()
        self.parent.draw_rect(self.startPoint.x(), self.startPoint.y(), self.endPoint.x(), self.endPoint.y())

    def canvasMoveEvent(self, e):
        """
        Called if a mouse moves over the map canvas, taking the end point of the rectangle.
        :param e: Event
        """
        if not self.isEmittingPoint:
            return
        self.endPoint = self.toMapCoordinates(e.pos())
        self.show_rect(self.startPoint, self.endPoint)

    def show_rect(self, start_point, end_point):
        """
        Showing the rectangle with the given start and end point.
        :param start_point: Point: Starting point of the rectangle drawing
        :param end_point: Point: End point of the rectangle drawing
        """
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        if start_point.x() == end_point.x() or start_point.y() == end_point.y():
            return
        point1 = QgsPointXY(start_point.x(), start_point.y())
        point2 = QgsPointXY(start_point.x(), end_point.y())
        point3 = QgsPointXY(end_point.x(), end_point.y())
        point4 = QgsPointXY(end_point.x(), start_point.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)    # true to update canvas
        self.rubberBand.show()

    def deactivate(self):
        """
        Deactivating the rectangle
        """
        self.rubberBand.hide()
        QgsMapTool.deactivate(self)
