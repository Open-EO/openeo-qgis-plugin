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
from osgeo import ogr
from os.path import expanduser
from collections import OrderedDict

from qgis.PyQt import uic, QtGui, QtWidgets
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, QApplication, QAction, QMainWindow
import qgis.PyQt.QtCore as QtCore
from qgis.gui import *
from qgis.core import *
#from qgis.core import QgsVectorLayer, QgsProject
from qgis.utils import * # imports iface
from PyQt5.QtCore import *

## from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView,QWebEnginePage as QWebPage

from PyQt5 import QtCore, Qt
from PyQt5.QtGui import *
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from tkinter import filedialog

from PyQt5.QtCore import QUrl
from .models.result import Result
from .models.connect import Connection
from .models.processgraph import Processgraph
from .utils.logging import info, warning
from .DrawRect import *
from .MapToolPoint import PointTool


########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'openeo_connector_dialog_base.ui'))

class OpenEODialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Constructor."""

        super(OpenEODialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.iface = iface
        self.connection = Connection()
        self.processgraph = Processgraph()
        self.processes = None

        self.setupUi(self)
        self.connectButton.clicked.connect(self.connect)
        self.addButton.clicked.connect(self.add_process)
        self.processBox.currentTextChanged.connect(self.process_selected)
        # self.collectionBox.currentTextChanged.connect(self.collection_selected)
        self.refreshButton.clicked.connect(self.refresh_jobs)
        self.clearButton.clicked.connect(self.collection_selected)
        self.sendButton.clicked.connect(self.send_job)
        self.loadButton.clicked.connect(self.load_collection)

        ### Draw desired extent
        extentBoxItems = OrderedDict({"Set Extent to Current Map Canvas Extent": self.set_canvas, "Draw Rectangle": self.drawRect,
                                      "Draw Polygon": self.drawPoly, "Insert Shapefile": self.insertShape}) # Set Label to improve
        self.extentBox.addItems(list(extentBoxItems.keys()))

        ### Change to incorporate the WebEditor:
        self.moveButton.clicked.connect(self.web_view)
        self.moveButton_QGIS.clicked.connect(self.web_view_QGIS)

        self.processgraphEdit.textChanged.connect(self.update_processgraph)

        # Jobs Tab
        self.init_jobs()

    def set_canvas(self):
        crs = iface.activeLayer().crs().authid()
        extent = iface.mapCanvas().extent()  # Problem is: Object of type 'MapCanvas' is not JSON serializable
        e = extent.xMaximum()
        er = round(e, 1)
        n = extent.yMaximum()
        nr = round(n, 1)
        w = extent.xMinimum()
        wr = round(w, 1)
        s = extent.yMinimum()
        sr = round(s, 1)
        spatial_extent = {}
        spatial_extent["west"] = wr
        spatial_extent["east"] = er
        spatial_extent["north"] = nr
        spatial_extent["south"] = sr
        spatial_extent["crs"] = crs
        return str(spatial_extent)    # Improvement: Change ' in json to "

    def drawRect(self):
        crs = iface.activeLayer().crs().authid()
        self.canvas = QgsMapCanvas()

        ## MapToolPoint
        #x = PointTool(iface.mapCanvas())
        #iface.mapCanvas().setMapTool(x)

        ## DrawRect
        #self.x1 = 0.0
        #self.y1 = 0.0
        #self.x2 = 0.0
        #self.y2 = 0.0
        #self.x3 = 0.0
        #self.y3 = 0.0
        #self.x4 = 0.0
        #self.y4 = 0.0

        y = RectangleAreaTool(iface.mapCanvas())
        iface.mapCanvas().setMapTool(y)

        y.canvasPressEvent()

        #w = canvas_clicked.xMinimum()
        #wr = round(w, 1)
        #e = canvas_clicked.xMaximum()
        #er = round(e, 1)
        #n = canvas_clicked.yMaximum()
        #nr = round(n, 1)
        #s = canvas_clicked.yMinimum()
        #sr = round(s, 1)

        spatial_extent = {}
        #spatial_extent["west"] = self.x1
        #spatial_extent["east"] = self.x2
        #spatial_extent["north"] = self.y2
        #spatial_extent["south"] = self.y1
        spatial_extent["crs"] = crs
        return str(spatial_extent)  # Improvement: Change ' in json to "


    def drawPoly(self):
        crs = iface.activeLayer().crs().authid()

        return str(crs)

    def insertShape(self):
        # get generic home directory
        home = expanduser("~")
        # get location of file
        root = filedialog.askopenfilename(initialdir = home, title="Select A File" , filetypes = (("Shapefiles", "*.shp"), ("All Files", "*.*")))
        vlayer = QgsVectorLayer(root, "*.shp", "ogr")
        crs = vlayer.crs().authid()
        if vlayer.isValid():
            elayer = vlayer.extent()
            w = elayer.xMinimum()
            wr = round(w, 1)
            e = elayer.xMaximum()
            er = round(e, 1)
            n = elayer.yMaximum()
            nr = round(n, 1)
            s = elayer.yMinimum()
            sr = round(s, 1)

            spatial_extent = {}
            spatial_extent["west"] = wr
            spatial_extent["east"] = er
            spatial_extent["north"] = nr
            spatial_extent["south"] = sr
            spatial_extent["crs"] = crs
            return str(spatial_extent)  # Improvement: Change ' in json to "
        else:
            return "Layer failed to load!"


    def add_extent(self):
        if str(self.extentBox.currentText()) == "Set Extent to Current Map Canvas Extent":
            return self.set_canvas()
        elif str(self.extentBox.currentText()) == "Draw Rectangle":
            return self.drawRect()
        elif str(self.extentBox.currentText()) == "Draw Polygon":
            return self.drawPoly()
        elif str(self.extentBox.currentText()) == "Insert Shapefile":
            return self.insertShape()
        else:
            return 999

    def web_view(self):
        return 1
        #view = QWebEngineHttpRequest(self) # QWebEngineView is the new version, but can not be loaded into QGIS
        #view.load(QUrl("https://open-eo.github.io/openeo-web-editor/demo/"))
        #view.show()

        #print(help('PyQt5'))

        # add:
        ## send login data (backend, user, pwd, collection & process) - does the demo version work then?
        ## another def request_ProcessGraph: get back generated process graph in web editor
        ## Create Job at Backend then via QGIS Plugin

    def web_view_QGIS(self):
        web = QWebView(self)
        web.load(QUrl("https://mliang8.github.io/SoilWaterCube/")) # works
        #web.load(QUrl("https://mliang8.github.io/SoilWaterCube/")) # works
        #web.load(QUrl("https://open-eo.github.io/openeo-web-editor/demo/")) # Error: Sorry, the openEO Web Editor requires a modern browsers.
        # Please update your browser or use Google Chrome or Mozilla Firefox as alternative.
        web.show()

        # add:
        ## send login data (backend, user, pwd, collection & process) - does the demo version work then?
        ## another def request_ProcessGraph: get back generated process graph in web editor
        ## Create Job at Backend then via QGIS Plugin

    def connect(self):
        """
        Connect to the backend via the given credentials. It will connect via BasicAuthentication and Bearertoken.
        If there are no credentials, it connects to the backend without authentication.
        This method also loads all collections and processes from the backend.
        """
        pwd = self.passwordEdit.text()
        user = self.usernameEdit.text()
        url = self.backendEdit.text()

        if user == "":
            user = None
        if pwd == "":
            pwd = None

        auth = self.connection.connect(url   , username=user, password=pwd)

        if not auth:
            warning(self.iface, "Authentication failed!")
            return

        collection_result = self.connection.list_collections()
        process_result = self.connection.list_processes()
        self.processes = process_result

        self.collectionBox.clear()
        self.processBox.clear()
        self.extentBox.clear()

        # Load Collections from Backend
        for col in collection_result:
            if "id" in col:
                self.collectionBox.addItem(col['id'])

        # Load Processes of Backend
        for pr in process_result:
            if "id" in pr:
                self.processBox.addItem(pr['id'])

        # Give Extent to Backend
        #for ex in add_extent:
        #    if "id" in ex:
        #        self.extentBox.addItem(ex['id'])

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

    def init_jobs(self):
        """
        Initializes the jobs table
        """
        self.jobsTableWidget.clear()
        self.jobsTableWidget.setColumnCount(6)
        self.jobsTableWidget.setHorizontalHeaderLabels(['Job Id', 'Description/Error', 'Submission Date', 'Status',
                                                        'Execute', 'Display'])
        header = self.jobsTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)

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

            execBtn = QPushButton(self.jobsTableWidget)
            execBtn.setText('Execute')

            if "status" in val:
                qitem = QTableWidgetItem(val["status"])
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 3, qitem)

                if val["status"] == "finished":
                    dispBtn = QPushButton(self.jobsTableWidget)
                    dispBtn.setText('Display')
                    self.jobsTableWidget.setCellWidget(row, 5, dispBtn)
                    dispBtn.clicked.connect(lambda *args, row=row: self.job_display(row))

            self.jobsTableWidget.setCellWidget(row, 4, execBtn)
            execBtn.clicked.connect(lambda *args, row=row: self.job_execute(row))

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
            info(self.iface, "Downloaded to {}".format(download_dir))   # def web_view(self):
            result = Result(path=download_dir)
            result.display()

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

    def load_collection(self):
        """
        Loads the collection form the GUI and starts a new process graph in doing so.
        """
        col = str(self.collectionBox.currentText())
        ex = self.add_extent() # shall not display current text but values!

        ### west=None
        ### east=None
        ### south=None
        ### north=None
        ### crs=None

        ### if self.westEdit.text() != "":
        ###    west = float(self.westEdit.text())
        ###if self.eastEdit.text() != "":
        ###    east = float(self.eastEdit.text())
        ###if self.southEdit.text() != "":
        ###    south = float(self.southEdit.text())
        ###if self.northEdit.text() != "":
        ###    north = float(self.northEdit.text())
        ###if self.crsEdit.text() != "":
        ###    crs = int(self.crsEdit.text())

        ### start = self.startDateEdit.date().toPyDate()
        ### end = self.endDateEdit.date().toPyDate()

        arguments = {
            "id": col,
            "spatial_extent": ex
        }

            ### "temporal_extent": [str(start), str(end)],
            ### "spatial_extent": {}

        ### if west:
        ###    arguments["spatial_extent"]["west"] = west
        ### if east:
        ###    arguments["spatial_extent"]["east"] = east
        ### if south:
        ###    arguments["spatial_extent"]["south"] = south
        ### if north:
        ###    arguments["spatial_extent"]["north"] = north
        ### if crs:
        ###    arguments["spatial_extent"]["crs"] = crs

        # info(self.iface, "Load Collection {}".format(str(arguments)))

        self.processgraph.load_collection(arguments)
        # Refresh process graph in GUI
        self.reload_processgraph_view()

    def collection_selected(self):
        """
        Gets called if a new collection is selected, resets the process graph with an initial one and the collection id.
        --Deprecated--
        """
        self.processgraph.set_collection(str(self.collectionBox.currentText()))
        self.reload_processgraph_view()

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
        #widget = self.processgraphWidget
        #self.load_dict_into_widget(widget, self.processgraph.graph)
        self.processgraphEdit.setText(json.dumps(self.processgraph.graph, indent=2, sort_keys=True))
        #widget.show()

    def update_processgraph(self):
        """
            Reloads the process graph from the raw process graph text field
        """
        graph = self.processgraphEdit.toPlainText()
        self.processgraph.graph = json.loads(graph)
        self.processgraph.builder.processes = json.loads(graph)

        #widget = self.processgraphWidget
        #self.load_dict_into_widget(widget, self.processgraph.graph)
        #widget.show()

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
                        #info(self.iface, "New Process {}".format(process['parameters']))
                        self.processTableWidget.setRowCount(len(process['parameters']))
                        self.processTableWidget.setColumnCount(3)
                        self.processTableWidget.setHorizontalHeaderLabels(['Parameter', 'Type', 'Value'])
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
                                    example = QTableWidgetItem(str(val['schema']['examples'][0]))
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