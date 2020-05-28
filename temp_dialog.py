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
    def __init__(self, parent=None, iface=None, extent=None):
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

        self.setupUi(self)

        self.extent = extent

        self.date_selection(extent)

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

    def init_calendars(self):
        """
        Initializes the calendar
        """
        self.endCalendarWidget.setMaximumDate(QDate.currentDate())
        self.EndDateEdit.setMaximumDate(QDate.currentDate())

        self.startCalendarWidget.setSelectedDate(self.StartDateEdit.date())
        self.endCalendarWidget.setSelectedDate(self.EndDateEdit.date())

        self.startCalendarWidget.clicked[QDate].connect(self.pick_start)
        self.endCalendarWidget.clicked[QDate].connect(self.pick_end)

    def pick_start(self):
        """
        Starts picking the date
        """
        fs = self.startCalendarWidget.selectedDate()
        self.StartDateEdit.setDate(fs)

    def pick_end(self):
        """
        Ends picking the date
        """
        fe = self.endCalendarWidget.selectedDate()
        self.EndDateEdit.setDate(fe)

    def show_start(self):
        """
        Returns the start date correctly formatted.
        """
        if self.StartDateEdit.dateChanged:
            start = self.StartDateEdit.date()
            return start.toString("yyyy-MM-dd")+self.start_date_extension

    def show_end(self):
        """
        Returns the end date correctly formatted.
        """
        if self.EndDateEdit.dateChanged:
            end = self.EndDateEdit.date()
            return end.toString("yyyy-MM-dd")+self.end_date_extension
