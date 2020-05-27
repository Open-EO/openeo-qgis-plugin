# -*- coding: utf-8 -*-

import os
import json
from os.path import expanduser
from copy import deepcopy
import ast
from qgis.PyQt import uic

from qgis.utils import iface
from PyQt5 import QtWidgets, QtCore, QtGui

from collections import OrderedDict
from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow, QComboBox
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, \
    QApplication, QAction, QMainWindow, QFileDialog
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtCore import QDate, Qt, QSize, QSettings
from .utils.logging import info, warning

from .spatial_dialog import SpatialDialog
from .temp_dialog import TempDialog
from .band_dialog import BandDialog
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'job_adapt_dialog.ui'))

PROCESSES_SPATIAL = ["load_collection", "filter_bbox"]


class JobAdaptDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None, iface=None, job=None, backend=None, subgraph=None, row=0, main_dia=None):
        """Constructor method
        """
        super(JobAdaptDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        QApplication.setStyle("cleanlooks")
        self.setupUi(self)

        self.iface = iface
        self.job = job
        self.backend = backend
        self.main_dia = main_dia

        self.processgraph_buffer = None

        # Init Process graph
        if self.job.process.process_graph:
            self.processgraph_buffer = deepcopy(self.job.process.process_graph)

        # IF subgraph
        self.subgraph = subgraph
        self.row = row

        if subgraph:
            self.setWindowTitle("Adapt Parameter")
            self.sendButton.setText("Adapt")
            self.sendButton.clicked.connect(self.send_pg)
            self.processgraph_buffer = json.loads(subgraph)["process_graph"]
        else:
            if job.description:
                self.descriptionText.setText(job.description)
            if job.title:
                self.titleText.setText(job.title)
            self.sendButton.clicked.connect(self.send_job)

        self.process_graph_to_table()

        self.cancelButton.clicked.connect(self.close)
        self.reset_processBtn.clicked.connect(self.reset_process)

        self.resultCheckBox.stateChanged.connect(self.update_result_node)

        self.newprocessButton.clicked.connect(self.add_new_process)

        self.processesComboBox.addItem("Select a process")
        for key, val in self.backend.get_processes().items():
            self.processesComboBox.addItem(key)

        self.processesComboBox.currentTextChanged.connect(self.process_selected)
        self.processIdText.setText("")

    def process_selected(self):
        if self.processesComboBox.currentText() == "Select a process":
            return

        counter = 1
        p_id = "{}{}".format(self.processesComboBox.currentText().lower(), str(counter))
        while p_id in self.processgraph_buffer:
            counter += 1
            p_id = "{}{}".format(self.processesComboBox.currentText().lower(), str(counter))
        self.processIdText.setText(p_id)
        self.new_process_to_table(self.processesComboBox.currentText())

    def add_new_process(self):

        p_id = self.processIdText.text()
        process_id = self.processesComboBox.currentText()
        arguments = {}

        for pr_row in range(self.processTableWidget.rowCount()):
            arguments[self.processTableWidget.item(pr_row, 0).text()] = json.loads(self.processTableWidget.item(pr_row, 2).text())

        self.processgraph_buffer[p_id] = {"arguments": arguments, "process_id": process_id}
        self.process_graph_to_table()
        self.processesComboBox.setCurrentText("Select a process")
        self.processIdText.setText("")
        self.processTableWidget.clear()

    def reset_process(self):

        if not self.cur_pid:
            return

        if self.subgraph:
            self.processgraph_buffer[self.cur_pid] = json.loads(self.subgraph)["process_graph"][self.cur_pid]
        else:
            self.processgraph_buffer[self.cur_pid] = self.job.process.process_graph[self.cur_pid]

        self.process_to_table(self.cur_pid, self.cur_row)

    def send_job(self):
        self.backend.job_create(self.processgraph_buffer, title=self.titleText.text(), desc=self.descriptionText.text())
        self.close()

    def send_pg(self):
        if isinstance(self.main_dia, JobAdaptDialog):
            self.main_dia.receive_pg(self.processgraph_buffer, row=self.row)
        self.close()

    def receive_pg(self, process_graph, row):
        qitem = QTableWidgetItem(json.dumps({"process_graph": process_graph}))
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processTableWidget.setItem(row, 2, qitem)

        arg_name = self.processTableWidget.item(row, 0).text()
        value = self.processTableWidget.item(row, 2).text()

        if arg_name and value:
            self.processgraph_buffer[self.cur_pid]["arguments"][arg_name] = json.loads(value)

    def init_process_table(self):
        self.processTableWidget.clear()
        self.processTableWidget.setColumnCount(4)
        self.processTableWidget.setHorizontalHeaderLabels(['Argument', 'Type', 'Value', 'Edit'])
        header = self.processTableWidget.horizontalHeader()
        self.processTableWidget.setSortingEnabled(True)
        self.processTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)

    def incompatible_process_to_table(self, p_id, row):

        self.cur_process = self.get_process_by_id(p_id)

        if not self.cur_process:
            return

        self.mark_pg_row(row)

        self.init_process_table()

        arguments = self.cur_process["arguments"]

        self.processTableWidget.setRowCount(len(arguments))

        par_row = 0
        for key, val in arguments.items():
            qitem = QTableWidgetItem(key)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            self.processTableWidget.setItem(par_row, 0, qitem)

            type = QTableWidgetItem("Unknown to backend")
            type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, type)

            if val:
                val_item = QTableWidgetItem(json.dumps(val))
            else:
                val_item = QTableWidgetItem("")

            self.processTableWidget.setItem(par_row, 2, val_item)
            par_row += 1

    def mark_pg_row(self, row):
        for pr_row in range(self.processgraphTableWidget.rowCount()):
            for pr_col in range(self.processgraphTableWidget.columnCount()):
                if self.processgraphTableWidget.item(pr_row, pr_col):
                    if pr_row == row:
                        self.processgraphTableWidget.item(pr_row, pr_col).setBackground(Qt.lightGray)
                    else:
                        self.processgraphTableWidget.item(pr_row, pr_col).setBackground(Qt.white)

    def set_complex_edit_element(self, param, p_id, value, row):

        if (p_id == "load_collection") and (str(param.name) == "id"):
            id_combo = QComboBox()
            all_collections = self.backend.get_collections()
            for col in all_collections:
                if "id" in col:
                    id_combo.addItem(col['id'])
            if value:
                id_combo.setCurrentText(str(value))
            self.processTableWidget.setCellWidget(row, 3, id_combo)
            id_combo.currentTextChanged.connect(lambda *args, row=row,
                                                       combo=id_combo: self.update_col_selection(combo, row))

        # Edit stuff for special values
        if ("geojson" in str(param.get_type())) or ("bounding-box" in str(param.get_type())):
            editBtn = QPushButton(self.processgraphTableWidget)
            editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
            editBtn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, editBtn)
            editBtn.clicked.connect(lambda *args, row=row: self.adapt_spatial(row))
            return editBtn
        elif "raster-cube" in str(param.get_type()):
            id_combo = QComboBox()
            id_combo.addItem("Select")
            id_combo.addItems(self.get_process_id_list(exception=p_id))
            if "from_node" in value:
                id_combo.setCurrentText(str(value["from_node"]))
            self.processTableWidget.setCellWidget(row, 3, id_combo)
            id_combo.currentTextChanged.connect(lambda *args, row=row,
                                                       combo=id_combo: self.update_cube_selection(combo, row))
        elif "temporal-interval" in str(param.get_type()):
            editBtn = QPushButton(self.processgraphTableWidget)
            editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
            editBtn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, editBtn)
            editBtn.clicked.connect(lambda *args, row=row: self.adapt_temporal(row))
        elif "process-graph" in str(param.get_type()):
            editBtn = QPushButton(self.processgraphTableWidget)
            editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
            editBtn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, editBtn)
            editBtn.clicked.connect(lambda *args, row=row: self.adapt_pg(row))

        if "bands" in str(param.name):
            editBtn = QPushButton(self.processgraphTableWidget)
            editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
            editBtn.setIconSize(QSize(25, 25))
            self.processTableWidget.setCellWidget(row, 3, editBtn)
            editBtn.clicked.connect(lambda *args, row=row: self.adapt_bands(row))

    def new_process_to_table(self, process_id):
        """
        Gets called if a new process is selected at the process graph table.
        It loads all agruments with their type and an example (if exist) into the value
        """
        self.processTableWidget.clear()
        self.cur_process = None
        self.cur_pid = None
        self.cur_row = None

        # Set label with the process name and the bold font

        pr = self.backend.get_process(process_id)

        p_id = self.processIdText.text()

        self.processLabel.setText("New Process: {}".format(p_id))
        myFont = QtGui.QFont()
        myFont.setBold(True)
        self.processLabel.setFont(myFont)

        # info(self.iface, "New Process {}".format(process['parameters']))
        self.init_process_table()
        self.processTableWidget.setRowCount(len(pr.parameters))

        par_row = 0
        for param in pr.parameters:
            # if key != "data" and key != "imagery":
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if not param.optional:
                boldFont = QFont()
                boldFont.setBold(True)
                qitem.setFont(boldFont)

            self.processTableWidget.setItem(par_row, 0, qitem)

            type = QTableWidgetItem(str(param.get_type()))
            type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, type)

            val_item = QTableWidgetItem("")

            self.processTableWidget.setItem(par_row, 2, val_item)
            self.set_complex_edit_element(param, process_id, "", par_row)

            par_row += 1


        self.resultCheckBox.setChecked(False)

        # self.processTableWidget.cellChanged.connect(lambda *args, p_id=p_id: self.set_process_by_id(p_id))
        self.processTableWidget.resizeRowsToContents()

    def process_to_table(self, p_id, row):
        """
        Gets called if a new process is selected at the process graph table.
        It loads all agruments with their type and an example (if exist) into the value
        """
        self.processTableWidget.clear()
        self.cur_process = self.get_process_by_id(p_id)
        self.cur_pid = p_id
        self.cur_row = row

        if not self.cur_process:
            return

        # Set label with the process name and the bold font

        pr = self.backend.get_process(self.cur_process["process_id"])

        if not pr:
            self.processLabel.setText("Process: {} (not compatible with the backend)".format(p_id))
            myFont = QtGui.QFont()
            myFont.setBold(True)

            self.processLabel.setFont(myFont)
            warning(self.iface, "Process '{}' not available at this backend".format(str(self.cur_process["process_id"])))
            self.incompatible_process_to_table(p_id, row)
            return

        self.processLabel.setText("Process: {}".format(p_id))
        myFont = QtGui.QFont()
        myFont.setBold(True)
        self.processLabel.setFont(myFont)

        self.mark_pg_row(row)

        # info(self.iface, "New Process {}".format(process['parameters']))
        self.init_process_table()
        self.processTableWidget.setRowCount(len(pr.parameters))

        par_row = 0
        for param in pr.parameters:
            # if key != "data" and key != "imagery":
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if not param.optional:
                boldFont = QFont()
                boldFont.setBold(True)
                qitem.setFont(boldFont)

            self.processTableWidget.setItem(par_row, 0, qitem)

            type = QTableWidgetItem(str(param.get_type()))
            type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(par_row, 1, type)

            if "arguments" in self.cur_process:
                value = self.cur_process["arguments"]
                if param.name in value:
                    value = value[param.name]
                else:
                    value = ""
            if value:
                val_item = QTableWidgetItem(json.dumps(value))
            else:
                val_item = QTableWidgetItem("")

            self.processTableWidget.setItem(par_row, 2, val_item)
            self.set_complex_edit_element(param, p_id, value, par_row)

            par_row += 1

        if "result" in self.cur_process:
            if self.cur_process["result"]:
                self.resultCheckBox.setChecked(True)
            else:
                self.resultCheckBox.setChecked(False)
        else:
            self.resultCheckBox.setChecked(False)

        self.processTableWidget.cellChanged.connect(lambda *args, p_id=p_id: self.set_process_by_id(p_id))
        self.processTableWidget.resizeRowsToContents()

    def update_result_node(self):

        if not self.cur_pid:
            return

        if self.resultCheckBox.isChecked():
            self.processgraph_buffer[self.cur_pid]["result"] = True
        else:
            if "result" in self.processgraph_buffer[self.cur_pid]:
                self.processgraph_buffer[self.cur_pid].pop("result")

    def update_cube_selection(self, combo, row):
        selection = combo.currentText()

        if selection == "Select":
            return

        qitem = QTableWidgetItem(json.dumps({'from_node': str(selection)}))
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)

        self.processTableWidget.setItem(row, 2, qitem)

    def update_col_selection(self, combo, row):
        selection = combo.currentText()
        qitem = QTableWidgetItem(selection)
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)

        self.processTableWidget.setItem(row, 2, qitem)

    def limit_north(self):
        if self.parent():
            return self.parent().limit_north()
        else:
            return None

    def limit_west(self):
        if self.parent():
            return self.parent().limit_west()
        else:
            return None

    def limit_south(self):
        if self.parent():
            return self.parent().limit_south()
        else:
            return None

    def limit_east(self):
        if self.parent():
            return self.parent().limit_east()
        else:
            return None

    def get_process_id_list(self, exception=None):
        id_list = []
        row_count = self.processgraphTableWidget.rowCount()
        for row in range(row_count):
            id_text = self.processgraphTableWidget.item(row, 0).text()
            if id_text != exception:
                id_list.append(id_text)
        return id_list

    def init_process_graph_table(self):
        self.processgraphTableWidget.clear()
        self.processgraphTableWidget.setColumnCount(4)
        self.processgraphTableWidget.setHorizontalHeaderLabels(['Id', 'Process', 'Predecessor', 'Edit'])
        header = self.processgraphTableWidget.horizontalHeader()
        self.processgraphTableWidget.setSortingEnabled(True)
        self.processgraphTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)
        self.processgraphTableWidget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        # self.processgraphTableWidget.itemSelectionChanged.connect(self.process_to_table)

    def set_process_graph_widget(self, p_id, process, row):

        # Id
        qitem1 = QTableWidgetItem(str(p_id))
        qitem1.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 0, qitem1)

        # Process
        qitem2 = QTableWidgetItem(process["process_id"])
        qitem2.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 1, qitem2)

        # Predecessor
        qitem3 = QTableWidgetItem("")
        if "data" in process["arguments"]:
            if "from_node" in process["arguments"]["data"]:
                qitem3 = QTableWidgetItem(process["arguments"]["data"]["from_node"])
        qitem3.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processgraphTableWidget.setItem(row, 2, qitem3)

        # Edit
        self.editBtn = QPushButton(self.processgraphTableWidget)
        self.editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
        self.editBtn.setIconSize(QSize(25, 25))
        self.processgraphTableWidget.setCellWidget(row, 3, self.editBtn)
        self.editBtn.clicked.connect(lambda *args, p_id=p_id, row=row: self.process_to_table(p_id, row))

    def process_graph_to_table(self):
        self.init_process_graph_table()
        self.processgraphTableWidget.setRowCount(len(self.processgraph_buffer))

        row = 0
        for id, proc in self.processgraph_buffer.items():
            self.set_process_graph_widget(id, proc, row)
            row += 1

        self.processgraphTableWidget.resizeColumnsToContents()

    def get_process_by_id(self, p_id):

        if not p_id in self.processgraph_buffer:
            return None

        return self.processgraph_buffer[p_id]

    def set_process_by_id(self, p_id):
        process = self.get_process_by_id(p_id)
        row = self.processTableWidget.currentRow()
        if process:
            arg_name = None
            value = None
            if self.processTableWidget.item(row, 0):
                arg_name = self.processTableWidget.item(row, 0).text()

            if self.processTableWidget.item(row, 2):
                value = self.processTableWidget.item(row, 2).text()

            if arg_name and value:
                self.processgraph_buffer[p_id]["arguments"][arg_name] = json.loads(value)

    def get_collection_id(self):

        process_graph = self.processgraph_buffer

        if not process_graph:
            return None

        for p_id, proc in process_graph.items():
            if proc["process_id"] == "load_collection":
                return proc["arguments"]["id"]

        return None

    def adapt_pg(self, row):
        value = self.processTableWidget.item(row, 2).text()
        self.dlg = JobAdaptDialog(iface=self.iface, job=self.job, backend=self.backend, subgraph=value, row=row, main_dia=self)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def adapt_bands(self, row):
        sel_bands = self.processTableWidget.item(row, 2).text()
        if sel_bands:
            sel_bands = ast.literal_eval(sel_bands)
        else:
            sel_bands = []

        cur_collection = self.get_collection_id()
        all_bands = self.backend.get_bands(cur_collection)

        self.band_dialog = BandDialog(iface=self.iface, parent=self,
                                      bands=sel_bands, all_bands=all_bands)

        self.band_dialog.show()
        self.band_dialog.raise_()
        self.band_dialog.activateWindow()

    def adapt_spatial(self, row):

        extent = self.processTableWidget.item(row, 2).text()

        try:
            extent = ast.literal_eval(extent)
        except:
            extent = {}

        self.spatial_dialog = SpatialDialog(iface=self.iface, parent=self, extent=extent)

        self.spatial_dialog.show()
        self.spatial_dialog.raise_()
        self.spatial_dialog.activateWindow()

    def adapt_temporal(self, row):
        extent = self.processTableWidget.item(row, 2).text()

        try:
            extent = ast.literal_eval(extent)
        except:
            extent = []
        self.temp_dialog = TempDialog(iface=self.iface, parent=self, extent=list(extent))

        self.temp_dialog.show()
        self.temp_dialog.raise_()
        self.temp_dialog.activateWindow()

    def change_example_temporal(self, extent):
        row_count = self.processTableWidget.rowCount()

        for row in range(row_count):
            type_text = self.processTableWidget.item(row, 1).text()
            if "temporal-interval" in type_text:
                qitem = QTableWidgetItem(str(extent))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(row, 2, qitem)

    def change_example_spatial(self, extent):

        row_count = self.processTableWidget.rowCount()
        for row in range(row_count):
            type_text = self.processTableWidget.item(row, 1).text()
            if ("geojson" in type_text) or ("bounding-box" in type_text):
                qitem = QTableWidgetItem(str(extent))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(row, 2, qitem)

    def change_example_bands(self, bands):
        row_count = self.processTableWidget.rowCount()
        for row in range(row_count):
            arg_text = self.processTableWidget.item(row, 0).text()
            if "bands" in arg_text:
                qitem = QTableWidgetItem(json.dumps(bands))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(row, 2, qitem)
