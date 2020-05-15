# -*- coding: utf-8 -*-

import os
import json
from os.path import expanduser

from qgis.PyQt import uic

from qgis.utils import iface
from PyQt5 import QtWidgets, QtCore

from collections import OrderedDict
from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, \
    QApplication, QAction, QMainWindow, QFileDialog
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtCore import QDate, Qt, QSize, QSettings
from .utils.logging import info, warning
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'process_adapt_dialog.ui'))

PROCESSES_SPATIAL = ["load_collection", "filter_bbox"]


class ProcessAdaptDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None, iface=None, job=None, process=None):
        """Constructor method
        """
        super(ProcessAdaptDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        QApplication.setStyle("cleanlooks")
        self.setupUi(self)

        self.iface = iface
        self.job = job
        self.process = process

        if job.description:
            self.descriptionText.setText(job.description)
        if job.title:
            self.titleText.setText(job.title)

        self.process_graph_to_table()

    def init_process_graph_table(self):
        self.processTableWidget.clear()
        self.processTableWidget.setColumnCount(4)
        self.processTableWidget.setHorizontalHeaderLabels(['Id', 'Process', 'Predecessor', 'Edit'])
        header = self.processTableWidget.horizontalHeader()
        self.processTableWidget.setSortingEnabled(True)
        self.processTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)

    def set_process_widget(self, p_id, process, row):

        # Id
        qitem1 = QTableWidgetItem(str(p_id))
        qitem1.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processTableWidget.setItem(row, 0, qitem1)

        # Process
        qitem2 = QTableWidgetItem(process["process_id"])
        qitem2.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processTableWidget.setItem(row, 1, qitem2)

        # Predecessor
        qitem3 = QTableWidgetItem("")
        if "data" in process["arguments"]:
            if "from_node" in process["arguments"]["data"]:
                qitem3 = QTableWidgetItem(process["arguments"]["data"]["from_node"])
        qitem3.setFlags(QtCore.Qt.ItemIsEnabled)
        self.processTableWidget.setItem(row, 2, qitem3)

        # Edit
        self.editBtn = QPushButton(self.processTableWidget)
        self.editBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'edit_icon.png')))
        self.editBtn.setIconSize(QSize(25, 25))
        self.processTableWidget.setCellWidget(row, 3, self.editBtn)
        self.editBtn.clicked.connect(lambda *args, row=row: self.edit_process(row))

    def process_selected(self):
        """
        Gets called if a new process is selected at the process combobox.
        It loads all agruments with their type and an example (if exist) into the value
        """
        self.processTableWidget.clear()
        pr = self.backend.get_process(str(self.processBox.currentText()))

        if not pr:
            return

        # info(self.iface, "New Process {}".format(process['parameters']))
        self.processTableWidget.setRowCount(len(pr.parameters))
        self.processTableWidget.setColumnCount(3)
        self.processTableWidget.setHorizontalHeaderLabels(['Parameter', 'Type', 'Example'])
        header = self.processTableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        counter = 0
        for param in pr.parameters:
            # if key != "data" and key != "imagery":
            qitem = QTableWidgetItem(param.name)
            qitem.setFlags(QtCore.Qt.ItemIsEnabled)

            if param.required:
                boldFont = QtGui.QFont()
                boldFont.setBold(True)
                qitem.setFont(boldFont)

            self.processTableWidget.setItem(counter, 0, qitem)

            type = QTableWidgetItem(str(param.type))
            type.setFlags(QtCore.Qt.ItemIsEnabled)
            self.processTableWidget.setItem(counter, 1, type)

            if param.example:
                # type = QTableWidgetItem(str(val['schema']['type']))
                # type.setFlags(QtCore.Qt.ItemIsEnabled)
                # self.processTableWidget.setItem(counter, 2, type)
                example = QTableWidgetItem(str(param.example))
                example.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(counter, 2, example)
            else:
                example = QTableWidgetItem("")
                example.setFlags(QtCore.Qt.ItemIsEnabled)
                self.processTableWidget.setItem(counter, 2, example)

            counter += 1