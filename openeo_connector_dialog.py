# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenEODialog
                                 A QGIS plugin
 Plugin to access openEO compliant backends.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-07-18
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Bernhard Goesswein
        email                : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
########################################################################################################################
########################################################################################################################

import os
import json
import requests
from os.path import expanduser
from collections import OrderedDict
import webbrowser

from qgis.PyQt import uic, QtGui, QtWidgets
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, QApplication, QAction, QMainWindow, QFileDialog
import qgis.PyQt.QtCore as QtCore
from qgis.core import QgsVectorLayer
from qgis.utils import iface

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QTextEdit
from PyQt5 import QtCore
from PyQt5.QtCore import QDate
from PyQt5 import QtGui
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QCalendarWidget

from .models.result import Result
from .models.connect import Connection
from .models.processgraph import Processgraph
from .utils.logging import info, warning
from .drawRect import DrawRectangle
from .drawPoly import DrawPolygon
from distutils.version import LooseVersion

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'openeo_connector_dialog_base.ui'))

class OpenEODialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Constructor method
        """
        super(OpenEODialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.iface = iface
        self.connection = Connection()
        self.processgraph = Processgraph()
        self.called = False

        self.processes = None

        self.setupUi(self)
        ### Backend Issue:
        backendURL = requests.get('http://hub.openeo.org/api/backends')

        backends = []

        if backendURL.status_code == 200:
            backendsALL = backendURL.json()


            if 'VITO GeoPySpark' in backendsALL:
                for item in backendsALL['VITO GeoPySpark'].values():
                    backends.append(str(item))
                del backendsALL['VITO GeoPySpark']

            for backend in backendsALL.values():
                if ".well-known" in str(backend):
                    backend_versions = requests.get(backend)

                    if backend_versions.status_code == 200:
                        backend_versions = backend_versions.json()
                        for versions in backend_versions.values():

                            for version in versions:
                                if "api_version" in version:
                                    if LooseVersion("0.4.0") <= LooseVersion(version["api_version"]):
                                        if "url" in version:
                                            backends.append(str(version["url"]))
                else:
                    backends.append(str(backend))

        self.backendEdit.addItems(backends) # or Backends

        self.connectButton.clicked.connect(self.connect)
        self.addButton.clicked.connect(self.add_process)
        # Until it works properly:
        self.addButton.hide()

        self.processBox.currentTextChanged.connect(self.process_selected)
        # self.collectionBox.currentTextChanged.connect(self.collection_selected)
        self.refreshButton.clicked.connect(self.refresh_jobs)
        self.clearButton.clicked.connect(self.clear) # Clear Button
        self.sendButton.clicked.connect(self.send_job)  # Create Job Button
        self.loadButton.clicked.connect(self.load_collection)  # Load Button shall load the complete json file
        self.deleteButton.clicked.connect(self.del_job)

        extentBoxItems = OrderedDict(
            {"Set Extent to Current Map Canvas Extent": self.set_canvas, "Draw Rectangle": self.draw_rect,
             "Draw Polygon": self.draw_poly, "Use Active Layer Extent": self.use_active_layer,
             "Insert Shapefile": self.insert_shape})
        self.extentBox.addItems(list(extentBoxItems.keys()))

        self.extentBox.activated.connect(self.load_extent)

        # Set initial button visibility correctly
        self.drawBtn.clicked.connect(self.draw)
        self.drawBtn.setVisible(False)
        self.getBtn.clicked.connect(self.display_before_load)
        self.getBtn.setVisible(True)
        self.reloadBtn.clicked.connect(self.refresh_layers)
        self.reloadBtn.setVisible(False)
        self.layersBox.setVisible(False)

        # Temporal Extent
        self.selectDate.clicked.connect(self.add_temporal)
        self.StartDateEdit.setDate(QDate.currentDate())
        self.EndDateEdit.setDate(QDate.currentDate())

        # Link to the Web Editor Demo Version:
        self.moveButton.clicked.connect(self.web_view)

        # Info Buttons about Datasets and Methods
        self.infoBtn.setStyleSheet('''   
                                 border-image: url("./info_icon.png") 10 10 0 0;
                                 border-top: 10px transparent;
                                 border-bottom: 10px transparent;
                                 border-right: 0px transparent;
                                 border-left: 0px transparent''')
        self.infoBtn.clicked.connect(self.col_info)
        self.collectionBox.setGeometry(10, 60, 381, 21)
        self.infoBtn2.setStyleSheet('''   
                                 border-image: url("./info_icon.png") 10 10 0 0;
                                 border-top: 10px transparent;
                                 border-bottom: 10px transparent;
                                 border-right: 0px transparent;
                                 border-left: 0px transparent''')
        self.infoBtn2.clicked.connect(self.pr_info)
        self.processBox.setGeometry(10, 130, 381, 21) # when add Button visible, set 381 to 291
        self.infoBtn.setVisible(False)
        self.infoBtn2.setGeometry(370, 130, 21, 21) # remove, when add Button is visible
        self.infoBtn2.setVisible(False)

        # Jobs Tab
        self.init_jobs()

    def set_canvas(self):
        iface.actionPan().trigger()
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()
            extent = iface.mapCanvas().extent()
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
            self.processgraphSpatialExtent.setText(str(spatial_extent)) # Improvement: Change ' in json to "
        elif not iface.activeLayer():
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

    def draw(self):
        if str(self.extentBox.currentText()) == "Draw Rectangle":
            QMainWindow.hide(self)
            self.drawRectangle = DrawRectangle(iface.mapCanvas(), self)
            iface.mapCanvas().setMapTool(self.drawRectangle)
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            self.drawBtn.setVisible(True)
            QMainWindow.hide(self)
            self.drawPolygon = DrawPolygon(iface.mapCanvas(), self)
            iface.mapCanvas().setMapTool(self.drawPolygon)
        else:
            self.iface.messageBar().pushMessage("Draw Extent Option is not enabled for you choice of extent", duration=5)

    def draw_rect(self, x1, y1, x2, y2):
        if iface.activeLayer():
            crs = iface.activeLayer().crs().authid()

            spatial_extent = {}
            if x1 <= x2:
                spatial_extent["west"] = round(x1, 1)
                spatial_extent["east"] = round(x2, 1)
            elif x2 <= x1:
                spatial_extent["west"] = round(x2, 1)
                spatial_extent["east"] = round(x1, 1)
            else:
                return "Error: Draw a new rectangle"

            if y1 <= y2:
                spatial_extent["north"] = round(y2, 1)
                spatial_extent["south"] = round(y1, 1)
            elif y2 <= y1:
                spatial_extent["north"] = round(y1, 1)
                spatial_extent["south"] = round(y2, 1)
            else:
                return "Error: Draw a new rectangle"
            spatial_extent["crs"] = crs
            self.processgraphSpatialExtent.setText(str(spatial_extent))
            QMainWindow.show(self)

        elif not iface.activeLayer():
            iface.actionPan().trigger()
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
            items = []

            for value in polygons_boundingBox_json.values():   # keys = ['type', 'coordinates'] , values
                values.append(value)
            for item in value:
                items.append(item)
            point1 = items[0][0]  # longitude first position, latitude second position
            point1_long = point1[0]
            point1_lat = point1[1]
            point2 = items[0][1]
            point2_long = point2[0]
            point2_lat = point2[1]
            point3 = items[0][2]
            point3_long = point3[0]
            point3_lat = point3[1]
            point4 = items[0][3]
            point4_long = point4[0]
            point4_lat = point4[1]

            long = []
            lat = []

            long.append([point1_long,point2_long, point3_long, point4_long])

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
            self.processgraphSpatialExtent.setText(str(spatial_extent))
            QMainWindow.show(self)

        elif not iface.activeLayer():
            iface.actionPan().trigger()
            QMainWindow.show(self)
            self.iface.messageBar().pushMessage("Please open a new layer to get extent from.", duration=5)

        else:
            iface.actionPan().trigger()
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
                self.processgraphSpatialExtent.setText(str(spatial_extent))

    def refresh_layers(self):
        self.layersBox.clear()
        layers = iface.mapCanvas().layers()
        for layer in layers:
            self.layersBox.addItem(layer.name())
            self.layers = layer

    def insert_shape(self):
        iface.actionPan().trigger()
        # get generic home directory
        home = expanduser("~")
        # get location of file
        root = QFileDialog.getOpenFileName(self, "Select a file", home) #, "All Files (*.*), Shape Files (*.shp)")
        #root = QFileDialog.getOpenFileName(initialdir=home, title="Select A File", filetypes=(("Shapefiles", "*.shp"), ("All Files", "*.*")))
        #QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)

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
            self.processgraphSpatialExtent.setText(str(spatial_extent))
        else:
            return "Layer failed to load!"

    def add_extent(self):
        if self.called == False:
            DisplayedExtent = self.processgraphSpatialExtent.toPlainText()
            self.called = True
            return str(DisplayedExtent)
#        else:
#            warning(self.iface, "Extent can be added only once!")

    def display_before_load(self):
        if str(self.extentBox.currentText()) == "Set Extent to Current Map Canvas Extent":
            self.set_canvas()
            #self.called = False
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            self.iface.messageBar().pushMessage("Get Extent Option is not enabled for you choice of extent", duration=5)
        elif str(self.extentBox.currentText()) == "Draw Rectangle":
            self.iface.messageBar().pushMessage("Get Extent Option is not enabled for you choice of extent", duration=5)
        elif str(self.extentBox.currentText()) == "Use Active Layer Extent":
            self.use_active_layer()
            #self.called = False
        elif str(self.extentBox.currentText()) == "Insert Shapefile":
            self.insert_shape()
            #self.called = False
        else:
            return 999

    def add_temporal(self):

        QMainWindow.show(self)
        self.dateWindow = QWidget()
        self.start_calendar = QCalendarWidget(self)
        self.end_calendar = QCalendarWidget(self)
        self.start_calendar.clicked[QDate].connect(self.pick_start)
        self.end_calendar.clicked[QDate].connect(self.pick_end)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.start_calendar)
        self.hbox.addWidget(self.end_calendar)
        self.dateWindow.setLayout(self.hbox)
        self.dateWindow.setGeometry(400, 400, 600, 350)
        self.dateWindow.setWindowTitle('Calendar')
        self.dateWindow.show()

        #self.start_calendar.setMaximumDate(QDate(2017-06-29))
        #self.end_calendar.setMinimumDate(QDate(2017-06-29))

    def pick_start(self):
        if self.selectDate.clicked:
            startDate = self.start_calendar.selectedDate().toString("yyyy-MM-dd")
            fS = QDate.fromString(startDate, "yyyy-MM-dd")
            self.StartDateEdit.setDate(fS)

    def pick_end(self):
        if self.selectDate.clicked:
            endDate = self.end_calendar.selectedDate().toString("yyyy-MM-dd")
            fE = QDate.fromString(endDate, "yyyy-MM-dd")
            self.EndDateEdit.setDate(fE)

    def show_start(self):
        if self.StartDateEdit.dateChanged:
            Start = self.StartDateEdit.date()
            sD = Start.toString("yyyy-MM-dd")
            return sD
        elif self.selectDate.clicked:
            self.pick_start()
            Start = self.StartDateEdit.date()
            sD = Start.toString("yyyy-MM-dd")
            return sD

    def show_end(self):
        if self.StartDateEdit.dateChanged:
            End = self.EndDateEdit.date()
            eD = End.toString("yyyy-MM-dd")
            return eD
        elif self.selectDate.clicked:
            self.pick_end()
            End = self.EndDateEdit.date()
            eD= End.toString("yyyy-MM-dd")
            return eD

    def bands(self):
        bands = ["None"]  # e.g. "bands": ["B08", "B04", "B02"]
        return bands

    def web_view(self):

        webbrowser.open("https://open-eo.github.io/openeo-web-editor/demo/")

        ### Old approach, which opens Webeditor Demoversion directly in QGIS
        #self.webWindow = QWidget()
        #self.web = QWebView(self)
        #self.web.load(QUrl("https://mliang8.github.io/SoilWaterCube/")) #"https://open-eo.github.io/"))  # both work
        # web.load(QUrl("https://open-eo.github.io/openeo-web-editor/demo/")) # Error: Sorry, the openEO Web Editor requires a modern browsers.
        # Please update your browser or use Google Chrome or Mozilla Firefox as alternative.
        #self.button = QPushButton('Close Web Editor', self)
        #self.button.clicked.connect(self.web_view_close)
        #self.hbox = QHBoxLayout()
        #self.hbox.addWidget(self.web)
        #self.hbox.addWidget(self.button)
        #self.webWindow.setLayout(self.hbox)
        #self.webWindow.setGeometry(550, 420, 800, 600)
        #self.webWindow.setWindowTitle('Web Editor')
        #self.webWindow.show()

    def web_view_close(self):
        self.webWindow.close()
        return

    def connect(self):
        """
        Connect to the backend via the given credentials. It will connect via BasicAuthentication and Bearertoken.
        If there are no credentials, it connects to the backend without authentication.
        This method also loads all collections and processes from the backend.
        """

        if self.backendEdit.currentText() == "None of the listed ones match":
            url = self.backendEdit2.text()
        else:
            url = self.backendEdit.currentText()

        pwd = self.passwordEdit.text()
        user = self.usernameEdit.text()
        if user == "":
            user = None
        if pwd == "":
            pwd = None

        auth = self.connection.connect(url, username=user, password=pwd)

        if not auth:
            warning(self.iface, "Authentication failed!")
            return

        collection_result = self.connection.list_collections()
        process_result = self.connection.list_processes()
        self.processes = process_result

        self.infoBtn.setVisible(True)
        self.collectionBox.setGeometry(10, 60, 351, 21)
        self.infoBtn2.setVisible(True)
        self.processBox.setGeometry(10, 130, 351, 21) # when add Button is visible - set 351 to 261

        self.collectionBox.clear()
        self.processBox.clear()

        # Load Collections from Backend
        for col in collection_result:
            if "id" in col:
                self.collectionBox.addItem(col['id'])

        # Load Processes from Backend
        for pr in process_result:
            if "id" in pr:
                self.processBox.addItem(pr['id'])

        self.refresh_jobs()

        if len(collection_result) == 0 and len(process_result) == 0:
            warning(self.iface, "Backend URL does not have collections or processes defined, or is not valid!")
            return

        # Update Status text
        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        self.statusLabel.setFont(boldFont)
        if user:
            self.statusLabel.setText("Connected to {} as {}".format(url, user))
        else:
            self.statusLabel.setText("Connected to {} without user".format(url))

    def col_info(self):
        collection_info_result = self.connection.list_collections()
        selected_col = str(self.collectionBox.currentText())
        for col_info in collection_info_result:
            if str(col_info['id']) == selected_col:
                if "description" in col_info:
                    self.infoWindow = QWidget()
                    self.hbox = QHBoxLayout()
                    self.infoBox = QTextEdit()
                    self.infoBox.setText(str(col_info['id']) + ': ' + str(col_info['description']))
                    self.infoBox.setReadOnly(True)
                    self.hbox.addWidget(self.infoBox)
                    self.infoWindow.setLayout(self.hbox)
                    self.infoWindow.setGeometry(400, 400, 600, 450)
                    self.infoWindow.setWindowTitle('Collection Information')
                    self.infoWindow.show()
                    #self.processgraphEdit.setText(str(col_info['id']) + ": " +  str(col_info['description']))

    def pr_info(self):
        process_info_result = self.connection.list_processes()
        selected_process = str(self.processBox.currentText())
        for pr_info in process_info_result:
            if str(pr_info['id']) == selected_process:
                if "description" in pr_info:
                    self.infoWindow = QWidget()
                    self.hbox = QHBoxLayout()
                    self.infoBox = QTextEdit()
                    if "returns" in pr_info:
                        self.infoBox.setText(
                            str(str(pr_info['id']) + ': ' + str(pr_info['description']) + "\n\n Returns: \n" + str(pr_info['returns']['description'])))
                    else:
                        self.infoBox.setText(
                            str(str(pr_info['id']) + ': ' + str(pr_info['description'])))
                    self.infoBox.setReadOnly(True)
                    self.hbox.addWidget(self.infoBox)
                    self.infoWindow.setLayout(self.hbox)
                    self.infoWindow.setGeometry(400, 400, 600, 350)
                    self.infoWindow.setWindowTitle('Process Information')
                    self.infoWindow.show()
                    #self.processgraphEdit.setText(str(pr_info['id']) + ": " + str(pr_info['description']))

    def job_info(self):
        self.jobInfo = QWidget()
        self.jobInfo.show()

    def init_jobs(self):
        """
        Initializes the jobs table
        """
        self.jobsTableWidget.clear()
        self.jobsTableWidget.setColumnCount(7)
        self.jobsTableWidget.setHorizontalHeaderLabels(['Job Id', 'Description/Error', 'Submission Date', 'Status',
                                                        'Execute', 'Display', 'Information'])
        header = self.jobsTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)

    def refresh_jobs(self):
        """
        Refreshes the job table, so fetches all jobs of the user from the backend and lists them in the table.
        This method also generates the "Execute" and "Display" buttons.
        """

        jobs = self.connection.user_jobs()

        self.init_jobs()
        self.jobsTableWidget.setRowCount(len(jobs))
        row = 0

        for val in jobs:

            if "id" in val:
                qitem = QTableWidgetItem(val["id"])
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 0, qitem)

            if "error" in val:
                if val["error"]:
                    if "message" in val["error"]:
                        qitem = QTableWidgetItem(val["error"]["message"])
                        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                        self.jobsTableWidget.setItem(row, 1, qitem)
            elif "description" in val:
                qitem = QTableWidgetItem(val["description"])
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 1, qitem)

            if "submitted" in val:
                qitem = QTableWidgetItem(val["submitted"])
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 2, qitem)

            execBtn = QPushButton('Execute', self.jobsTableWidget)

            if "status" in val:
                qitem = QTableWidgetItem(val["status"])
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 3, qitem)

                if val["status"] == "finished":
                    self.jobsTableWidget.item(row, 3).setBackground(QColor(75, 254, 40, 160))
                    dispBtn = QPushButton(self.jobsTableWidget)
                    dispBtn.setText('Display')
                    self.jobsTableWidget.setCellWidget(row, 5, dispBtn)
                    dispBtn.clicked.connect(lambda *args, row=row: self.job_display(row))
                    iface.actionZoomIn().trigger()

                elif val["status"] == "submitted":
                    self.jobsTableWidget.item(row, 3).setBackground(QColor(254, 178, 76, 200))

                elif val["status"] == "error":
                    self.jobsTableWidget.item(row, 3).setBackground(QColor(254, 100, 100, 200))

            self.jobsTableWidget.setCellWidget(row, 4, execBtn)
            execBtn.clicked.connect(lambda *args, row=row: self.job_execute(row))

            self.infoBtn3 = QPushButton(self.jobsTableWidget)
            self.infoBtn3.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'info_icon.png')))
            self.jobsTableWidget.setCellWidget(row, 6, self.infoBtn3)
            self.infoBtn3.clicked.connect(lambda *args, row=row: self.job_info)

            row += 1

    def job_execute(self, row):
        """
        Executes the job of the given row of the job table.
        This method is called after the "Execute" button is clicked at the job table.
        :param row: Integer number of the row the button is clicked.
        """
        job_id = self.jobsTableWidget.item(row, 0).text()
        self.connection.job_start(job_id)
        self.refresh_jobs()

    def job_display(self, row):
        """
        Displays the job of the given row of the job table on a new QGis Layer.
        This method is called after the "Display" button is clicked at the job table.
        :param row: Integer number of the row the button is clicked.
        """
        job_id = self.jobsTableWidget.item(row, 0).text()
        download_dir = self.connection.job_result_download(job_id)
        if download_dir:
            info(self.iface, "Downloaded to {}".format(download_dir))  # def web_view(self):
            result = Result(path=download_dir)
            result.display()
            iface.zoomToActiveLayer()

        self.refresh_jobs()
        # info(self.iface, "New Job {}".format(job_id))

    def send_job(self):
        """
        Sends the current process graph to the backend to create a new job.
        """
        graph = self.processgraphEdit.toPlainText()
        # info(self.iface, graph)
        response = self.connection.job_create(json.loads(graph))
        if response.status_code == 201:
            info(self.iface, "Successfully created new job, Response: {}".format(response.status_code))
        else:
            warning(self.iface, "Not able to created new job, Response: {}".format(str(response.json())))

        self.refresh_jobs()

    def del_job(self):
        self.chosenRow = self.jobsTableWidget.currentRow()
        self.jobsTableWidget.removeRow(self.chosenRow)

    def load_collection(self):
        """
        Loads the collection form the GUI and starts a new process graph in doing so.
        """
        col = str(self.collectionBox.currentText())
        ex = self.processgraphSpatialExtent.toPlainText()
        texS = self.show_start()
        texE = self.show_end()
        if texE < texS:
            self.iface.messageBar().pushMessage("Start Date must be before End Date", duration=5)
        B = self.bands()

        arguments = OrderedDict({
            "id": col,
            "spatial_extent": ex,
            "temporal_extent": [texS, texE],
            "bands": B,
        })

        self.processgraph.load_collection(arguments)
        # Refresh process graph in GUI
        self.reload_processgraph_view()

    def load_extent(self):
        if str(self.extentBox.currentText()) == "Set Extent to Current Map Canvas Extent":
            self.drawBtn.setVisible(False)
            self.getBtn.setVisible(True)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
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
            self.layersBox.clear()
            layers = iface.mapCanvas().layers()
            for layer in layers:
                self.layersBox.addItem(layer.name())
                self.layers = layer
        elif str(self.extentBox.currentText()) == "Insert Shapefile":
            self.drawBtn.setVisible(False)
            self.getBtn.setVisible(True)
            self.layersBox.setVisible(False)
            self.reloadBtn.setVisible(False)
        else:
            return 999

    def collection_selected(self):
        """
        Gets called if a new collection is selected, resets the process graph with an initial one and the collection id.
        --Deprecated--
        """
        #self.processgraph.set_collection(str(self.collectionBox.currentText()))
        #self.reload_processgraph_view()

    def clear(self):
        self.processgraphEdit.clear()

    def add_process(self):
        """
        Adds the current process (process Table) with its arguments to the process graph.
        """
        process_id = str(self.processBox.currentText())

        arguments = {}

        for row in range(0, self.processTableWidget.rowCount()):
            p_id = ""
            val = None

            if self.processTableWidget.item(row, 0):
                p_id = self.processTableWidget.item(row, 0).text()
            if self.processTableWidget.item(row, 2):
                val = self.processTableWidget.item(row, 2).text()
                if len(val) > 0:
                    try:
                        val = json.loads(val)
                    except json.JSONDecodeError:
                        pass
                else:
                    val = None
            if p_id != "":
                if val:
                    arguments[p_id] = val

        self.processgraph = self.processgraph.add_process(process_id, arguments)
        # Refresh process graph in GUI
        self.reload_processgraph_view()

    def reload_processgraph_view(self):
        """
        Reloads the process graph tree widget by loading the current processgraph into it.
        """
        # widget = self.processgraphWidget
        # self.load_dict_into_widget(widget, self.processgraph.graph)
        self.processgraphEdit.setText(json.dumps(self.processgraph.graph, indent=2, sort_keys=True))
        # widget.show()

    # def update_processgraph(self):
    #    """
    #        Reloads the process graph from the raw process graph text field
    #    """
    #    graph = self.processgraphEdit.toPlainText()
    #    self.processgraph.graph = json.loads(graph)
    #    self.processgraph.builder.processes = json.loads(graph)

    # widget = self.processgraphWidget
    # self.load_dict_into_widget(widget, self.processgraph.graph)
    # widget.show()

    def process_selected(self):
        """
        Gets called if a new process is selected at the process combobox.
        It loads all agruments with their type and an example (if exist) into the value
        """
        self.processTableWidget.clear()
        for p in self.processes:
            if "id" in p:
                if p['id'] == str(self.processBox.currentText()):
                    process = p
                    if "parameters" in process:
                        # info(self.iface, "New Process {}".format(process['parameters']))
                        self.processTableWidget.setRowCount(len(process['parameters']))
                        self.processTableWidget.setColumnCount(3)
                        self.processTableWidget.setHorizontalHeaderLabels(['Parameter', 'Type', 'Example'])
                        header = self.processTableWidget.horizontalHeader()
                        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
                        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
                        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

                        counter = 0
                        for key, val in process['parameters'].items():
                            # if key != "data" and key != "imagery":
                            qitem = QTableWidgetItem(key)
                            qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                            if "required" in val:
                                if val["required"]:
                                    boldFont = QtGui.QFont()
                                    boldFont.setBold(True)
                                    qitem.setFont(boldFont)

                            self.processTableWidget.setItem(counter, 0, qitem)
                            if "schema" in val:
                                if "type" in val["schema"]:
                                    type = QTableWidgetItem(str(val['schema']['type']))
                                    type.setFlags(QtCore.Qt.ItemIsEnabled)
                                    self.processTableWidget.setItem(counter, 1, type)
                                if "examples" in val["schema"]:
                                    #type = QTableWidgetItem(str(val['schema']['type']))
                                    #type.setFlags(QtCore.Qt.ItemIsEnabled)
                                    #self.processTableWidget.setItem(counter, 2, type)
                                    example = QTableWidgetItem(str(val['schema']['examples'][0]))
                                    example.setFlags(QtCore.Qt.ItemIsEnabled)
                                    self.processTableWidget.setItem(counter, 2, example)
                                else:
                                    example = QTableWidgetItem("")
                                    example.setFlags(QtCore.Qt.ItemIsEnabled)
                                    self.processTableWidget.setItem(counter, 2, example)
                            counter += 1
                        return
                    else:
                        info(self.iface, "New Process: Parameters not found")

    def fill_item(self, item, value):
        """
        Helper method used by load_dict_into_widget
        """
        item.setExpanded(True)
        if type(value) is dict:
            for key, val in sorted(value.items()):
                child = QTreeWidgetItem()
                child.setText(0, str(key))
                item.addChild(child)
                self.fill_item(child, val)
        elif type(value) is list:
            for val in value:
                child = QTreeWidgetItem()
                item.addChild(child)
                if type(val) is dict:
                    child.setText(0, '[dict]')
                    self.fill_item(child, val)
                elif type(val) is list:
                    child.setText(0, '[list]')
                    self.fill_item(child, val)
                else:
                    child.setText(0, str(val))
                child.setExpanded(True)
        else:
            child = QTreeWidgetItem()
            child.setText(0, str(value))
            item.addChild(child)

    def load_dict_into_widget(self, widget, value):
        """
        Helper method to convert a dictionary into TreeWidgetItems, used e.g. for the process graph TreeWidget
        """
        widget.clear()
        self.fill_item(widget.invisibleRootItem(), value)
