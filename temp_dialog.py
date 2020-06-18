# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TempDialog

 This class is responsible for choosing temporal extent for a openEO job.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import os

from qgis.PyQt import uic

from .utils.logging import warning

from PyQt5 import QtWidgets

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'temp_dialog.ui'))


class TempDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for choosing temporal extent for a openEO job.
    """
    def __init__(self, parent=None, iface=None, extent=None, col_max=None, col_min=None):
        """
        Constructor method: Initializing the button behaviours and the Table entries.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        :param extent: dict: Current extent of the job.
        """
        super(TempDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.iface = iface
        self.called = False
        self.called2 = False
        self.processes = None

        # 2014-10-03T00:00:00Z

        self.col_max = col_max
        self.col_min = col_min

        self.setupUi(self)

        if extent:
            self.extent = extent
        else:
            end_date = QDate.currentDate()
            start_date = QDate.currentDate()
            if col_max:
                end_date = col_max
            if col_min:
                start_date = col_min
            self.extent = [start_date, end_date]

        self.date_selection(self.extent)

        self.init_calendars()

        self.buttonBox.accepted.connect(self.accept_dialog)

        self.start_date_extension = None
        self.end_date_extension = None

    def accept_dialog(self):
        """
        Dialog is finished and the chosen temporal extent gets sent to the parent (main) adaption dialog.
        """
        if self.EndDateEdit.date() < self.StartDateEdit.date():
            warning(self.iface, "End date is placed before the start date!")
        self.parent().receive_temporal_extent(extent=[self.show_start(), self.show_end()])

    def date_selection(self, dates):
        """
        Initializes the date selection by setting the current dates.
        :param dates: list: List of two date strings, first the start date and second the
                            end date of the temporal extent.
        """
        if dates:
            start_date = dates[0]
            end_date = dates[1]

            if isinstance(start_date, str):
                if "T" in start_date:
                    start_date = dates[0].split("T")[0]
                    self.start_date_extension = "T"+dates[0].split("T")[1]
                else:
                    self.start_date_extension = ""
                self.StartDateEdit.setDate(QDate.fromString(start_date, "yyyy-MM-dd"))
            else:
                self.start_date_extension = ""
                self.StartDateEdit.setDate(start_date)

            if isinstance(end_date, str):
                if "T" in end_date:
                    end_date = dates[1].split("T")[0]
                    self.end_date_extension = "T"+dates[1].split("T")[1]
                else:
                    self.end_date_extension = ""
                self.EndDateEdit.setDate(QDate.fromString(end_date, "yyyy-MM-dd"))
            else:
                self.end_date_extension = ""
                self.EndDateEdit.setDate(end_date)

    def init_calendars(self):
        """
        Initializes the calendar
        """
        if self.col_max:
            self.endCalendarWidget.setMaximumDate(self.col_max)
            self.EndDateEdit.setMaximumDate(self.col_max)
            self.startCalendarWidget.setMaximumDate(self.col_max)
            self.StartDateEdit.setMaximumDate(self.col_max)
        else:
            self.endCalendarWidget.setMaximumDate(QDate.currentDate())
            self.EndDateEdit.setMaximumDate(QDate.currentDate())
            self.startCalendarWidget.setMaximumDate(QDate.currentDate())
            self.StartDateEdit.setMaximumDate(QDate.currentDate())

        if self.col_min:
            self.startCalendarWidget.setMinimumDate(self.col_min)
            self.StartDateEdit.setMinimumDate(self.col_min)
            self.endCalendarWidget.setMinimumDate(self.col_min)
            self.EndDateEdit.setMinimumDate(self.col_min)

        self.startCalendarWidget.setSelectedDate(self.StartDateEdit.date())
        self.endCalendarWidget.setSelectedDate(self.EndDateEdit.date())

        self.startCalendarWidget.clicked[QDate].connect(self.pick_start)
        self.endCalendarWidget.clicked[QDate].connect(self.pick_end)
        self.StartDateEdit.dateChanged.connect(self.update_cal_start)
        self.EndDateEdit.dateChanged.connect(self.update_cal_end)

    def update_cal_start(self):
        """
        Updates calendar by start date widget.
        """
        start = self.StartDateEdit.date()
        self.startCalendarWidget.setSelectedDate(start)

    def update_cal_end(self):
        """
        Updates calendar by end date widget.
        """
        end = self.EndDateEdit.date()
        self.endCalendarWidget.setSelectedDate(end)

    def pick_start(self):
        """
        Starts picking the date
        """
        fe = self.endCalendarWidget.selectedDate()
        fs = self.startCalendarWidget.selectedDate()
        if fs > fe:
            warning(self.iface, "Start date needs to be before the end date!")
            fs = fe
            self.startCalendarWidget.setSelectedDate(fs)

        self.StartDateEdit.setDate(fs)

    def pick_end(self):
        """
        Ends picking the date
        """
        fe = self.endCalendarWidget.selectedDate()
        fs = self.startCalendarWidget.selectedDate()
        if fe < fs:
            warning(self.iface, "End date needs to be after the start date!")
            fe = fs
            self.endCalendarWidget.setSelectedDate(fe)

        self.EndDateEdit.setDate(fe)

    def show_start(self):
        """
        Returns the start date correctly formatted.
        """
        if self.StartDateEdit.dateChanged:
            start = self.StartDateEdit.date()
            if not self.start_date_extension:
                self.start_date_extension = ""
            return start.toString("yyyy-MM-dd")+self.start_date_extension

    def show_end(self):
        """
        Returns the end date correctly formatted.
        """
        if self.EndDateEdit.dateChanged:
            end = self.EndDateEdit.date()
            if not self.end_date_extension:
                self.end_date_extension = ""
            return end.toString("yyyy-MM-dd")+self.end_date_extension
