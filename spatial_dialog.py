# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SpatialDialog

 This class is responsible for choosing spatial extent for a openEO job.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""

import os
import json
from os.path import expanduser

from qgis.PyQt import uic

from qgis.utils import iface
from PyQt5 import QtWidgets

from collections import OrderedDict
from PyQt5.QtWidgets import QApplication, QMainWindow
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QFileDialog
from qgis.core import QgsVectorLayer

from PyQt5.QtGui import QIcon
from .drawRect import DrawRectangle
from .drawPoly import DrawPolygon

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'spatial_dialog.ui'))


class SpatialDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for choosing spatial extent for a openEO job.
    """
    def __init__(self, parent=None, interface=None, extent=None):
        """
        Constructor method: Initializing the button behaviours and the Table entries.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        :param extent: dict: Current extent of the job.
        """
        super(SpatialDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.iface = interface
        self.called = False
        self.called2 = False
        self.processes = None

        self.setupUi(self)

        extent_box_item = OrderedDict(
            {"Set Extent to Current Map Canvas Extent": self.set_canvas, "Draw Rectangle": self.draw_rect,
             "Draw Polygon": self.draw_poly, "Use Active Layer Extent": self.use_active_layer,
             "Insert Shapefile": self.insert_shape})
        self.extentBox.addItems(list(extent_box_item.keys()))

        self.extentBox.activated.connect(self.load_extent)
        self.extentBox.setEnabled(True)

        # Set initial button visibility correctly
        self.drawBtn.clicked.connect(self.draw)
        self.drawBtn.setVisible(False)
        self.drawBtn.setEnabled(True)
        self.getBtn.clicked.connect(self.display_before_load)
        self.getBtn.setVisible(True)
        self.getBtn.setEnabled(True)

        self.extent = extent
        if extent:
            self.processgraphSpatialExtent.setText(str(extent))

        self.reloadBtn.clicked.connect(self.refresh_layers)
        self.reloadBtn.setVisible(False)
        self.reloadBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/reload_icon.png')))

        self.layersBox.setVisible(False)

        self.buttonBox.accepted.connect(self.accept_dialog)

        self.east = None
        self.west = None
        self.north = None
        self.south = None
        self.drawRectangle = None
        self.drawPolygon = None

    def accept_dialog(self):
        """
        Dialog is finished and the chosen spatial extent gets sent to the parent (main) adaption dialog.
        """
        self.parent().receive_spatial_extent(extent=self.processgraphSpatialExtent.toPlainText())

    def refresh_layers(self):
        """
        Refreshing the current QGIS layer.
        """
        self.layersBox.clear()
        layers = iface.mapCanvas().layers()
        for layer in layers:
            self.layersBox.addItem(layer.name())

    def init_extent(self, init_value):
        """
        Initializes the spatial extent textbox.
        :param init_value: dict: initial spatial extent value.
        """
        self.processgraphSpatialExtent.setText(str(init_value))

    def load_extent(self):
        """
        Starts retrieving the extent depending on the selection of the user,
        there might be additional input needed (e.g. drawing a rectangle)
        """
        if str(self.extentBox.currentText()) == "Set Extent to Current Map Canvas Extent":
            self.drawBtn.setVisible(False)
            self.getBtn.setVisible(True)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
            self.getBtn.setText("Get Extent")
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            self.drawBtn.setVisible(True)
            self.getBtn.setVisible(False)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
        elif str(self.extentBox.currentText()) == "Draw Rectangle":
            self.drawBtn.setVisible(True)
            self.getBtn.setVisible(False)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
        elif str(self.extentBox.currentText()) == "Use Active Layer Extent":
            self.drawBtn.setVisible(False)
            self.getBtn.setVisible(True)
            self.layersBox.setVisible(True)
            self.reloadBtn.setVisible(True)
            self.getBtn.setText("Get Extent")
            self.layersBox.clear()
            layers = iface.mapCanvas().layers()
            for layer in layers:
                self.layersBox.addItem(layer.name())
        elif str(self.extentBox.currentText()) == "Insert Shapefile":
            self.drawBtn.setVisible(False)
            self.getBtn.setVisible(True)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
            self.getBtn.setText("Browse File")

    def display_before_load(self):
        """
        Puts the extent to the text field depending from the selection of the retrieval type.
        """
        if str(self.extentBox.currentText()) == "Set Extent to Current Map Canvas Extent":
            self.set_canvas()
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            self.iface.messageBar().pushMessage("Get Extent Option is not enabled for you choice of extent", duration=5)
        elif str(self.extentBox.currentText()) == "Draw Rectangle":
            self.iface.messageBar().pushMessage("Get Extent Option is not enabled for you choice of extent", duration=5)
        elif str(self.extentBox.currentText()) == "Use Active Layer Extent":
            self.use_active_layer()
        elif str(self.extentBox.currentText()) == "Insert Shapefile":
            self.insert_shape()

    def set_canvas(self):
        """
        Reads the coordinates of the drawings into the spatial extent variable.
        """
        iface.actionPan().trigger()
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()
            extent = iface.mapCanvas().extent()
            self.east = round(extent.xMaximum(), 2)
            self.north = round(extent.yMaximum(), 2)
            self.west = round(extent.xMinimum(), 2)
            self.south = round(extent.yMinimum(), 2)
            spatial_extent = {"west": self.west, "east": self.east, "north": self.north,
                              "south": self.south, "crs": crs}

            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
        elif not iface.activeLayer():
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def draw(self):
        """
        Starts the drawiong process e.g. if the user needs to interact with the map.
        """
        if str(self.extentBox.currentText()) == "Draw Rectangle":
            if iface.activeLayer():
                QMainWindow.hide(self)
                self.parent().hide()
                self.drawRectangle = DrawRectangle(iface.mapCanvas(), self)
                iface.mapCanvas().setMapTool(self.drawRectangle)
            else:
                iface.actionPan().trigger()
                self.parent().show()
                QMainWindow.show(self)
                self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            if iface.activeLayer():
                self.drawBtn.setVisible(True)
                QMainWindow.hide(self)
                self.parent().hide()
                self.drawPolygon = DrawPolygon(iface.mapCanvas(), self)
                iface.mapCanvas().setMapTool(self.drawPolygon)
            else:
                iface.actionPan().trigger()
                self.parent().show()
                QMainWindow.show(self)
                self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def draw_rect(self, x1, y1, x2, y2):
        """
        After drawing a rectangle it sets the coordinates for the spatial extent.
        :param x1: x coordinate of first point
        :param x2: x coordinate of second point
        :param y1: y coordinate of first point
        :param y2: y coordinate of second point
        """
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()

            spatial_extent = {}
            if x1 <= x2:
                spatial_extent["west"] = round(x1, 3)
                spatial_extent["east"] = round(x2, 3)
            elif x2 <= x1:
                spatial_extent["west"] = round(x2, 3)
                spatial_extent["east"] = round(x1, 3)
            else:
                return "Error: Draw a new rectangle"

            if y1 <= y2:
                spatial_extent["north"] = round(y2, 3)
                spatial_extent["south"] = round(y1, 3)
            elif y2 <= y1:
                spatial_extent["north"] = round(y1, 3)
                spatial_extent["south"] = round(y2, 3)
            else:
                return "Error: Draw a new rectangle"

            spatial_extent["crs"] = crs
            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
            self.parent().show()
            QMainWindow.show(self)
        elif not iface.activeLayer():
            iface.actionPan().trigger()
            self.parent().show()
            QMainWindow.show(self)
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def draw_poly(self, geometry):
        """
        After drawing a polygon it sets the coordinates for the spatial extent.
        :param geometry: Polygon geometry from QQGIS
        """
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()
            polygons_bounding_tuples = geometry
            polygons_bounding_json_string = polygons_bounding_tuples[0].asJson(
                1)  # this returns only the 4 desired points, rounded
            polygons_bounding_json = json.loads(polygons_bounding_json_string)
            values = []

            for points in polygons_bounding_json['coordinates']:
                values.append(points)

            point1 = values[0][0]  # longitude first position, latitude second position
            point1_long = point1[0]
            point1_lat = point1[1]
            point2 = values[0][1]
            point2_long = point2[0]
            point2_lat = point2[1]
            point3 = values[0][2]
            point3_long = point3[0]
            point3_lat = point3[1]
            point4 = values[0][3]
            point4_long = point4[0]
            point4_lat = point4[1]

            self.processgraphSpatialExtent.setText(str(values))

            long = []
            lat = []

            long.append([point1_long, point2_long, point3_long, point4_long])

            long_min = min(long[0])
            long_max = max(long[0])
            lat.append([point1_lat, point2_lat, point3_lat, point4_lat])
            lat_min = min(lat[0])
            lat_max = max(lat[0])

            spatial_extent = {"west": long_min, "east": long_max, "north": lat_max,
                              "south": lat_min, "crs": crs}

            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
            self.parent().show()
            QMainWindow.show(self)

        elif not iface.activeLayer():
            iface.actionPan().trigger()
            self.parent().show()
            QMainWindow.show(self)
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

        else:
            iface.actionPan().trigger()
            self.parent().show()
            QMainWindow.show(self)
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def use_active_layer(self):
        """
        Loads coordinates extent of the active layer.
        """
        iface.actionPan().trigger()
        layers = iface.mapCanvas().layers()
        chosen_layer = str(self.layersBox.currentText())
        for layer in layers:
            if str(layer.name()) == chosen_layer:
                crs = layer.crs().authid()
                ex_layer = layer.extent()
                east = round(ex_layer.xMaximum(), 1)
                north = round(ex_layer.yMaximum(), 1)
                west = round(ex_layer.xMinimum(), 1)
                south = round(ex_layer.yMinimum(), 1)
                spatial_extent = {"west": west, "east": east, "north": north,
                                  "south": south, "crs": crs}
                str_format = str(spatial_extent).replace("'", '"')
                self.processgraphSpatialExtent.setText(str_format)

        if not iface.activeLayer():
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def insert_shape(self):
        """
        Loads coordinates from an shapefile, starting a browsing prompt.
        """
        iface.actionPan().trigger()
        # get generic home directory
        home = expanduser("~")
        filter_type = "SHP Shape Files (*.shp);; All Files (*.*)"
        # get location of file
        root = QFileDialog.getOpenFileName(self, "Select a file", home, filter_type)

        vlayer = QgsVectorLayer(root[0])
        crs = vlayer.crs().authid()
        if vlayer.isValid():
            extent = vlayer.extent()
            east = round(extent.xMaximum(), 1)
            north = round(extent.yMaximum(), 1)
            west = round(extent.xMinimum(), 1)
            south = round(extent.yMinimum(), 1)
            spatial_extent = {"west": west, "east": east, "north": north,
                              "south": south, "crs": crs}
            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
        else:
            return "Layer failed to load!"
