# -*- coding: utf-8 -*-

import os
import json

from qgis.PyQt import uic

from .utils.logging import info, warning

from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'temp_dialog.ui'))

PROCESSES_TEMPORAL = ["load_collection", "filter_temporal"]

class TempDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None, minimum_date=None, maximum_date=None, max_date=None, pg_graph=None):
        """Constructor method
        """
        super(TempDialog, self).__init__(parent)
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


        self.minimum_date = minimum_date
        self.maximum_date = maximum_date
        self.max_date = max_date

        self.pg_graph = pg_graph

        self.comboProcessBox.currentTextChanged.connect(self.update_selection)

        self.init_processes()

        self.update_selection()
        #self.date_selection(cur_dates)

        self.selectDate.clicked.connect(self.add_temporal)
        #self.refreshButton_service.clicked.connect(self.refresh_services)
        #self.refreshButton_service.clicked.connect(self.refresh_services)
        self.buttonBox.accepted.connect(self.accept_dialog)

    def accept_dialog(self):
        process_id = self.comboProcessBox.currentText().split(" - ")[1]
        self.parent().change_example_temporal(start_date=self.show_start(),
                                              end_date=self.show_end(), process_id=process_id)

    def update_selection(self):
        example_job = self.pg_graph
        if self.comboProcessBox.currentText():
            process_selection = self.comboProcessBox.currentText().split(" - ")
            if process_selection[0] == "load_collection":
                if "temporal_extent" in example_job[process_selection[1]]["arguments"]:
                    temporal = example_job[process_selection[1]]["arguments"]["temporal_extent"]
                    self.date_selection(temporal)
                if "temporal" in example_job[process_selection[1]]["arguments"]:
                    temporal = example_job[process_selection[1]]["arguments"]["temporal"]
                    self.date_selection(temporal)
            elif process_selection[0] == "filter_temporal":
                if "extent" in example_job[process_selection[1]]["arguments"]:
                    temporal = example_job[process_selection[1]]["arguments"]["extent"]
                    self.date_selection(temporal)

    def date_selection(self, dates):
        # 2018-10-10T00:00:00Z
        if dates:
            start_date = dates[0]
            end_date = dates[1]
            if "T" in start_date:
                start_date = dates[0].split("T")[0]
                self.start_date_extension = "T"+dates[0].split("T")[1]
            else:
                self.start_date_extension = ""

            if "T" in end_date:
                end_date = dates[1].split("T")[0]
                self.end_date_extension = "T"+dates[1].split("T")[1]
            else:
                self.end_date_extension = ""

            self.StartDateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
            self.EndDateEdit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))

    def init_processes(self):
        example_job = self.pg_graph
        for key, _ in example_job.items():
            if example_job[key]["process_id"] in PROCESSES_TEMPORAL:
                self.comboProcessBox.addItem("{} - {}".format(example_job[key]["process_id"], key))

    def add_temporal(self):
        QMainWindow.show(self)
        self.dateWindow = QWidget()

        self.start_calendar = QCalendarWidget(self)
        self.start_calendar.setMinimumDate(self.minimum_date)
        self.StartDateEdit.setMinimumDate(self.minimum_date)

        self.end_calendar = QCalendarWidget(self)
        if self.max_date == None:
            self.end_calendar.setMaximumDate(QDate.currentDate())
            self.EndDateEdit.setMaximumDate(QDate.currentDate())
        else:
            self.end_calendar.setMaximumDate(self.maximum_date)
            self.EndDateEdit.setMaximumDate(self.maximum_date)

        self.start_calendar.setSelectedDate(self.StartDateEdit.date())
        self.end_calendar.setSelectedDate(self.EndDateEdit.date())

        self.start_calendar.clicked[QDate].connect(self.pick_start)
        self.end_calendar.clicked[QDate].connect(self.pick_end)
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.start_calendar)
        self.hbox.addWidget(self.end_calendar)
        self.dateWindow.setLayout(self.hbox)
        self.dateWindow.setGeometry(400, 400, 600, 350)
        self.dateWindow.setWindowTitle('Calendar')
        self.dateWindow.show()

    def pick_start(self):
        if self.selectDate.clicked:
            fS = self.start_calendar.selectedDate()
            # fS = QDate.fromString(startDate, "yyyy-MM-dd")
            self.StartDateEdit.setDate(fS)

    def pick_end(self):
        if self.selectDate.clicked:
            fE = self.end_calendar.selectedDate()
            #fE = QDate.fromString(endDate, "yyyy-MM-dd")
            self.EndDateEdit.setDate(fE)

    def show_start(self):
        if self.StartDateEdit.dateChanged:
            Start = self.StartDateEdit.date()
            sD = Start.toString("yyyy-MM-dd")+self.start_date_extension
            return sD
        elif self.selectDate.clicked:
            self.pick_start()
            Start = self.StartDateEdit.date()
            sD = Start.toString("yyyy-MM-dd")+self.start_date_extension
            return sD

    def show_end(self):
        if self.StartDateEdit.dateChanged:
            End = self.EndDateEdit.date()
            eD = End.toString("yyyy-MM-dd")+self.end_date_extension
            return eD
        elif self.selectDate.clicked:
            self.pick_end()
            End = self.EndDateEdit.date()
            eD = End.toString("yyyy-MM-dd")+self.end_date_extension
            return eD