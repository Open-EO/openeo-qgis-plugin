# -*- coding: utf-8 -*-

import os
import json
from os.path import expanduser

from qgis.PyQt import uic

from qgis.utils import iface
from PyQt5 import QtWidgets

from collections import OrderedDict
from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, \
    QApplication, QAction, QMainWindow, QFileDialog
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject

from PyQt5.QtGui import QIcon
from .drawRect import DrawRectangle
from .drawPoly import DrawPolygon

from .utils.logging import info, warning

from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'spatial_dialog.ui'))

PROCESSES_SPATIAL = ["load_collection", "filter_bbox"]


class SpatialDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None, iface=None, extent=None):
        """Constructor method
        """
        super(SpatialDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        QApplication.setStyle("cleanlooks")

        self.iface = iface
        self.called = False
        self.called2 = False
        self.processes = None

        self.setupUi(self)

        extentBoxItems = OrderedDict(
            {"Set Extent to Current Map Canvas Extent": self.set_canvas, "Draw Rectangle": self.draw_rect,
             "Draw Polygon": self.draw_poly, "Use Active Layer Extent": self.use_active_layer,
             "Insert Shapefile": self.insert_shape})
        self.extentBox.addItems(list(extentBoxItems.keys()))

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

        # self.comboProcessBox.currentTextChanged.connect(self.update_selection)

        # self.init_processes()

        self.reloadBtn.clicked.connect(self.refresh_layers)
        self.reloadBtn.setVisible(False)
        self.reloadBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/reload_icon.png')))

        self.layersBox.setVisible(False)

        self.buttonBox.accepted.connect(self.accept_dialog)

    def accept_dialog(self):
        # warning(self.iface, "Inside Accep DIalog with {}".format(self.processgraphSpatialExtent.toPlainText()))
        # process_selection = self.comboProcessBox.currentText().split(" - ")[1]
        self.parent().change_example_spatial(extent=self.processgraphSpatialExtent.toPlainText())

    def refresh_layers(self):
        self.layersBox.clear()
        layers = iface.mapCanvas().layers()
        for layer in layers:
            self.layersBox.addItem(layer.name())

    # def init_processes(self):
    #     example_job = self.pg_graph
    #     if example_job:
    #         for key, _ in example_job.items():
    #             if example_job[key]["process_id"] in PROCESSES_SPATIAL:
    #                 self.comboProcessBox.addItem("{} - {}".format(example_job[key]["process_id"], key))
    #
    # def update_selection(self):
    #     example_job = self.pg_graph
    #     if example_job:
    #         if self.comboProcessBox.currentText():
    #             process_selection = self.comboProcessBox.currentText().split(" - ")
    #             if process_selection[0] == "load_collection":
    #                 if "spatial_extent" in example_job[process_selection[1]]["arguments"]:
    #                     spatial = example_job[process_selection[1]]["arguments"]["spatial_extent"]
    #                     self.init_extent(spatial)
    #             elif process_selection[0] == "filter_spatial":
    #                 if "extent" in example_job[process_selection[1]]["arguments"]:
    #                     spatial = example_job[process_selection[1]]["arguments"]["extent"]
    #                     self.init_extent(spatial)

    def init_extent(self, init_value):
        self.processgraphSpatialExtent.setText(str(init_value))

    def load_extent(self):
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
        else:
            return 999

    def display_before_load(self):
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
        else:
            return 999

    def check_spatial_cover(self):
        west = self.west
        east = self.east
        north = self.north
        south = self.south
        if west < self.parent().limit_west():
            self.iface.messageBar().pushMessage("Your Choice of extent is not covered by the data provider.",
                                                duration=5)
        if east > self.parent().limit_east():
            self.iface.messageBar().pushMessage("Your Choice of extent is not covered by the data provider.",
                                                duration=5)
        if south < self.parent().limit_south():
            self.iface.messageBar().pushMessage("Your Choice of extent is not covered by the data provider.",
                                                duration=5)
        if north > self.parent().limit_north():
            self.iface.messageBar().pushMessage("Your Choice of extent is not covered by the data provider.",
                                                duration=5)

    def set_canvas(self):
        iface.actionPan().trigger()
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()
            extent = iface.mapCanvas().extent()
            self.east = round(extent.xMaximum(), 2)
            self.north = round(extent.yMaximum(), 2)
            self.west = round(extent.xMinimum(), 2)
            self.south = round(extent.yMinimum(), 2)
            spatial_extent = {}
            spatial_extent["west"] = self.west
            spatial_extent["east"] = self.east
            spatial_extent["north"] = self.north
            spatial_extent["south"] = self.south
            spatial_extent["crs"] = crs
            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
            self.check_spatial_cover()
        elif not iface.activeLayer():
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def draw(self):
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
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()
            polygons_boundingBox_tuples = geometry
            polygons_boundingBox_json_string = polygons_boundingBox_tuples[0].asJson(
                1)  # this returns only the 4 desired points, rounded
            polygons_boundingBox_json = json.loads(polygons_boundingBox_json_string)
            values = []

            for points in polygons_boundingBox_json['coordinates']:  # keys = ['type', 'coordinates'] , values
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

            spatial_extent = {}
            spatial_extent["west"] = long_min
            spatial_extent["east"] = long_max
            spatial_extent["north"] = lat_max
            spatial_extent["south"] = lat_min
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

        else:
            iface.actionPan().trigger()
            self.parent().show()
            QMainWindow.show(self)
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def use_active_layer(self):
        iface.actionPan().trigger()
        layers = iface.mapCanvas().layers()
        self.chosenLayer = str(self.layersBox.currentText())
        for layer in layers:
            if str(layer.name()) == self.chosenLayer:
                crs = layer.crs().authid()
                ex_layer = layer.extent()
                east = round(ex_layer.xMaximum(), 1)
                north = round(ex_layer.yMaximum(), 1)
                west = round(ex_layer.xMinimum(), 1)
                south = round(ex_layer.yMinimum(), 1)
                spatial_extent = {}
                spatial_extent["west"] = west
                spatial_extent["east"] = east
                spatial_extent["north"] = north
                spatial_extent["south"] = south
                spatial_extent["crs"] = crs
                str_format = str(spatial_extent).replace("'", '"')
                self.processgraphSpatialExtent.setText(str_format)

        if not iface.activeLayer():
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def insert_shape(self):
        iface.actionPan().trigger()
        # get generic home directory
        home = expanduser("~")
        filter = "SHP Shape Files (*.shp);; All Files (*.*)"
        # get location of file
        root = QFileDialog.getOpenFileName(self, "Select a file", home, filter)  # , "All Files (*.*), Shape Files (*.shp)")
        # root = QFileDialog.getOpenFileName(initialdir=home, title="Select A File", filetypes=(("Shapefiles", "*.shp"), ("All Files", "*.*")))
        # QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)

        vlayer = QgsVectorLayer(root[0])
        crs = vlayer.crs().authid()
        if vlayer.isValid():
            extent = vlayer.extent()
            east = round(extent.xMaximum(), 1)
            north = round(extent.yMaximum(), 1)
            west = round(extent.xMinimum(), 1)
            south = round(extent.yMinimum(), 1)
            spatial_extent = {}
            spatial_extent["west"] = west
            spatial_extent["east"] = east
            spatial_extent["north"] = north
            spatial_extent["south"] = south
            spatial_extent["crs"] = crs
            str_format = str(spatial_extent).replace("'", '"')
            self.processgraphSpatialExtent.setText(str_format)
        else:
            return "Layer failed to load!"