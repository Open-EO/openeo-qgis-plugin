# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JobDetailDialog

 This class is responsible for showing detailed metadata on an existing openEO job.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import os


from qgis.PyQt import uic
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore

from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QTableWidgetItem, QApplication

from PyQt5.QtGui import QFont
from .job_adapt_dialog import JobAdaptDialog

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'job_detail_dialog.ui'))


class JobDetailDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing detailed metadata on an existing openEO job.
    """
    def __init__(self, parent=None, iface=None, job=None, backend=None):
        """
        Constructor method: Initializing the button behaviours and the metadata fields.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        :param job: Job: Job that should be displayed in detail.
        :param backend: Backend: Currently connected backend.
        """
        super(JobDetailDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.iface = iface
        self.setupUi(self)

        self.backend = backend

        self.log_info = self.backend.job_log(job.id)

        self.job = job
        self.init_table()
        self.fill_table()

        self.dlg = None

        self.cancelButton.clicked.connect(self.close)
        # self.adaptButton.clicked.connect(self.adapt_job)

    # def adapt_job(self):
    #     """
    #     Starts an adaption dialog to adapt the current job.
    #     """
    #     self.dlg = JobAdaptDialog(iface=self.iface, job=self.job, backend=self.backend)
    #     self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
    #     self.dlg.show()
    #     self.close()

    def init_table(self):
        """
        Initializes the job infor table.
        """
        self.jobInfoTableWidget.clear()
        self.jobInfoTableWidget.setColumnCount(2)
        self.jobInfoTableWidget.setHorizontalHeaderLabels(['Property', 'Value'])
        header = self.jobInfoTableWidget.horizontalHeader()
        self.jobInfoTableWidget.setSortingEnabled(True)
        self.jobInfoTableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)

    def set_value_widget(self, value, row):
        """
        Sets the property value into the given row of the job table.
        :param value: str: Property value of the row.
        :param row: int: Row number to but the value in
        """
        qitem = QTableWidgetItem(str(value))
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.jobInfoTableWidget.setItem(row, 1, qitem)

    def set_property_widget(self, prop, row):
        """
        Sets the property name into the given row of the job table.
        :param prop: str: Property name of the row.
        :param row: int: Row number to but the value in
        """
        qitem = QTableWidgetItem(str(prop))
        font = QFont()
        font.setBold(True)
        qitem.setFont(font)
        qitem.setFlags(QtCore.Qt.ItemIsEnabled)
        self.jobInfoTableWidget.setItem(row, 0, qitem)

    def fill_table(self):
        """
        Fills the table with the properties and their values.
        """
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

        if self.log_info:
            property_list.append(("Log Entries:", "see below"))
            for log in self.log_info.get("logs"):
                property_list.append((log.get("code"), log.get("message")))

        self.jobInfoTableWidget.setRowCount(len(property_list))
        row = 0
        for prop in property_list:
            self.set_property_widget(prop[0], row)
            self.set_value_widget(prop[1], row)
            row += 1

        self.jobInfoTableWidget.resizeColumnsToContents()
