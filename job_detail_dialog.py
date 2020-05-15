# -*- coding: utf-8 -*-

import os
import json
from os.path import expanduser

from qgis.PyQt import uic
from PyQt5.QtCore import Qt
from qgis.utils import iface
from PyQt5 import QtWidgets, QtCore

from collections import OrderedDict
from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTableWidgetItem, QPushButton, \
    QApplication, QAction, QMainWindow, QFileDialog
from qgis.core import QgsTextFormat, QgsVectorLayer, QgsRasterLayer, QgsProject

from PyQt5.QtGui import QIcon, QFont
from .drawRect import DrawRectangle
from .drawPoly import DrawPolygon

from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate
from .job_adapt_dialog import JobAdaptDialog
from .utils.logging import info, warning

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'job_detail_dialog.ui'))


class JobDetailDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None, iface=None, job=None, backend=None):
        """Constructor method
        """
        super(JobDetailDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        QApplication.setStyle("cleanlooks")

        self.iface = iface
        self.setupUi(self)

        self.backend = backend
        self.job = job
        # warning(self.iface, str(job))
        self.init_table()
        self.fill_table()

        self.cancelButton.clicked.connect(self.close)
        self.adaptButton.clicked.connect(self.adapt_job)

    def adapt_job(self):
        self.dlg = JobAdaptDialog(iface=self.iface, job=self.job, backend=self.backend)
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()

    def limit_north(self):
        return self.parent().limit_north()

    def limit_west(self):
        return self.parent().limit_west()

    def limit_south(self):
        return self.parent().limit_south()

    def limit_east(self):
        return self.parent().limit_east()

    def init_table(self):
        self.jobInfoTableWidget.clear()
        self.jobInfoTableWidget.setColumnCount(2)
        self.jobInfoTableWidget.setHorizontalHeaderLabels(['Property', 'Value'])
        header = self.jobInfoTableWidget.horizontalHeader()
        self.jobInfoTableWidget.setSortingEnabled(True)
        self.jobInfoTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)

    def set_value_widget(self, value, row):
        qitem = QTableWidgetItem(str(value))
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.jobInfoTableWidget.setItem(row, 1, qitem)

    def set_property_widget(self, prop, row):
        qitem = QTableWidgetItem(str(prop))
        font = QFont()
        font.setBold(True)
        qitem.setFont(font)
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.jobInfoTableWidget.setItem(row, 0, qitem)

    def fill_table(self):

        property_list = []
        if self.job.id:
            property_list.append(("Id", self.job.id))

        if self.job.title:
            property_list.append(("Title", self.job.title))

        if self.job.description:
            property_list.append(("Description", self.job.description))

        if self.job.process:
            property_list.append(("Process", str(self.job.process)))

        if self.job.status:
            property_list.append(("Status", self.job.status))

        if self.job.progress:
            property_list.append(("Progress", self.job.progress))

        if self.job.created:
            property_list.append(("Created", self.job.created))

        if self.job.updated:
            property_list.append(("Updated", self.job.updated))

        if self.job.plan:
            property_list.append(("Plan", self.job.plan))

        if self.job.costs:
            property_list.append(("Costs", self.job.costs))

        if self.job.budget:
            property_list.append(("Budget", self.job.budget))

        self.jobInfoTableWidget.setRowCount(len(property_list))
        row = 0
        for prop in property_list:
            self.set_property_widget(prop[0], row)
            self.set_value_widget(prop[1], row)
            row += 1

        self.jobInfoTableWidget.resizeColumnsToContents()