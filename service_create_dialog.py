# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JobAdaptDialog

 This class is responsible for adapting existing openEO jobs.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import os
import json
from copy import deepcopy
import ast
from qgis.PyQt import uic

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox, QDialog, QHBoxLayout, QTextEdit
from qgis.PyQt.QtWidgets import QTableWidgetItem, QPushButton, QApplication

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QDate
from .utils.logging import warning, error

from .spatial_dialog import SpatialDialog
from .temp_dialog import TempDialog
from .band_dialog import BandDialog
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'service_create_dialog.ui'))


class ServiceCreateDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for adapting existing openEO jobs.
    """
    def __init__(self, parent=None, iface=None, backend=None):
        """
        Constructor method: Initializing the button behaviours and the Table entries.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        :param job: models.Job: Job that should be adapted
        :param backend: Backend: Currently connected backend.
        :param subgraph: dict: Usually None, but if the JobAdaptDialog is called for a subgraph
                               (e.g. when using a reducer), it contains the process graph to be edited.
        :param row: Int: row of the process graph table widget related to the process to edit.
        :param main_dia: JobAdaptDialog: Contains the parent JobAdaptDialog object, if a subgraph is given.
        """
        super(ServiceCreateDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")
        self.setupUi(self)

        self.iface = iface
        self.backend = backend

        self.cur_job = None

        self.jobs = backend.get_jobs()

        self.processgraph_buffer = {}

        # Raw graph
        self.rawgraphBtn.clicked.connect(self.raw_graph)
        self.sendButton.clicked.connect(self.send_service)

        self.jobs_to_table()

        self.cancelButton.clicked.connect(self.close)

        self.typesComboBox.addItem("Select a Type")
        self.service_types = self.backend.get_service_types()
        for key, val in self.service_types.items():
            self.typesComboBox.addItem(key)

        self.rawgraph_window = None

    def raw_graph(self):
        """
        Shows the raw process graph window, to copy paste graphs.
        """
        if not self.processgraph_buffer:
            warning(self.iface, "No Job selected !")
            return

        self.rawgraph_window = QDialog(parent=self)
        hbox = QHBoxLayout()
        self.raw_pg_box = QTextEdit()
        self.raw_pg_box.setText(json.dumps({"process_graph": self.processgraph_buffer}, indent=4))
        self.raw_pg_box.setReadOnly(False)
        hbox.addWidget(self.raw_pg_box)

        # close_btn = QPushButton('Close')
        # hbox.addWidget(close_btn)
        # close_btn.clicked.connect(self.rawgraph_window.close)

        self.rawgraph_window.setMinimumHeight(600)
        self.rawgraph_window.setMinimumWidth(400)
        self.rawgraph_window.setLayout(hbox)
        self.rawgraph_window.setWindowTitle('Service Information')
        self.rawgraph_window.show()

    def get_job_by_id(self, job_id):
        for job in self.jobs:
            if job.id == job_id:
                return job

        return None

    def send_service(self):
        """
        Sends the currently defined process graph as a new service to the backend.
        """
        s_type = self.typesComboBox.currentText()

        if s_type == "Select a Type":
            error(self.iface, "Type must be selected!")
            return

        if not self.processgraph_buffer:
            error(self.iface, "No job selected!")
            return

        # warning(self.iface, str(self.processgraph_buffer))

        service_status = self.backend.service_create(process=self.processgraph_buffer, s_type=s_type,
                                                 title=self.titleText.text(), description=self.descriptionText.text())
        if service_status:
            error(self.iface, "Service creation failed: {}".format(str(self.backend.error_msg_from_resp(service_status))))
        else:
            self.close()

    def mark_row(self, row):
        """
        Marks a row / process on the process graph table visually.
        :param row: int: Row number of the process on the process graph table.
        """
        for pr_row in range(self.jobsTableWidget.rowCount()):
            for pr_col in range(self.jobsTableWidget.columnCount()):
                if self.jobsTableWidget.item(pr_row, pr_col):
                    if pr_row == row:
                        self.jobsTableWidget.item(pr_row, pr_col).setBackground(Qt.lightGray)
                    else:
                        self.jobsTableWidget.item(pr_row, pr_col).setBackground(Qt.white)

    def init_jobs_table(self):
        """
        Initializes the process graph table by setting the column settings and headers.
        """
        self.jobsTableWidget.clear()
        self.jobsTableWidget.setColumnCount(3)
        self.jobsTableWidget.setHorizontalHeaderLabels(['Title', 'Created', 'Selection'])
        header = self.jobsTableWidget.horizontalHeader()
        self.jobsTableWidget.setSortingEnabled(True)
        self.jobsTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        self.jobsTableWidget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

    def select_job(self, job_id, row):

        self.mark_row(row)

        job = self.backend.detailed_job(job_id)

        if job:
            self.processgraph_buffer = job.process.process_graph
        else:
            self.processgraph_buffer = {}

    def jobs_to_table(self):
        """
        Loads the current jobs to the jobs table.
        """
        self.init_jobs_table()

        suc_jobs = []

        for job in self.jobs:
            if job.status == "finished":
                suc_jobs.append(job)

        self.jobsTableWidget.setRowCount(len(suc_jobs))

        row = 0
        for job in suc_jobs:
            if job.status == "error":
                continue

            if not job.title:
                qitem = QTableWidgetItem("Untitled Job!")
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 0, qitem)
            else:
                qitem = QTableWidgetItem(job.title)
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 0, qitem)

            if job.created:
                qitem = QTableWidgetItem(job.created.strftime("%Y-%m-%d_%H-%M-%S"))
                qitem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.jobsTableWidget.setItem(row, 1, qitem)

            sel_btn = QPushButton(self.jobsTableWidget)
            sel_btn.setText("Select")
            self.jobsTableWidget.setCellWidget(row, 2, sel_btn)
            sel_btn.clicked.connect(lambda *args, job_id=job.id, sel_row=row: self.select_job(job_id, sel_row))
            row += 1

        self.jobsTableWidget.setSortingEnabled(True)
        self.jobsTableWidget.resizeColumnsToContents()
