# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QHBoxLayout, QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'temp_dialog.ui'))


class TempDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None, minimum_date=None, maximum_date=None, max_date=None):
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

        self.selectDate.clicked.connect(self.add_temporal)
        #self.refreshButton_service.clicked.connect(self.refresh_services)
        #self.refreshButton_service.clicked.connect(self.refresh_services)
        self.buttonBox.accepted.connect(self.accept_dialog)

    def accept_dialog(self):
        self.parent().insert_Change_temporal(start_date=self.show_start(), end_date=self.show_end())

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
            eD = End.toString("yyyy-MM-dd")
            return eD