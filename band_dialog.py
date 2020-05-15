# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets, QtGui

import qgis.PyQt.QtCore as QtCore
from PyQt5.QtCore import QDate, Qt, QSize, QSettings
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QWidget, QPushButton, QListWidget, QListWidgetItem, QDialog

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'band_dialog.ui'))

PROCESSES_BANDS = ["load_collection", "filter_bands"]


class BandDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None, bands=None, all_bands=None):
        """Constructor method
        """
        super(BandDialog, self).__init__(parent)
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

        self.label_11.setEnabled(True)  # Add Bands

        self.bands = bands
        self.all_bands = all_bands

        self.init_band_list()

        self.buttonBox.accepted.connect(self.accept_dialog)

    def init_band_list(self):
        self.bandsListWidget.clear()

        for band in self.all_bands:
            # Set Checkbox before band
            self.item = QListWidgetItem(self.bandsListWidget)
            self.item.setFlags(self.item.flags() | QtCore.Qt.ItemIsUserCheckable)
            if band in self.bands:
                self.item.setCheckState(Qt.Checked)
            else:
                self.item.setCheckState(Qt.Unchecked)
            self.item.setText(str(band))

        self.bandsListWidget.sortItems()

    def accept_dialog(self):
        # process_selection = self.comboProcessBox.currentText().split(" - ")[1]
        band_list = []
        for index in range(self.bandsListWidget.count()):
            if self.bandsListWidget.item(index).checkState() == Qt.Checked:
                band_list.append(self.bandsListWidget.item(index).text())
        self.parent().change_example_bands(str(band_list))

    def save_band_choice2(self):
        checked_items = []
        self.processgraphBands.clear()
        for index in range(self.bandBox.count()):
            if self.bandBox.item(index).checkState() == Qt.Checked:
                checked_items.append(self.bandBox.item(index).text())
                self.processgraphBands.setText(str(checked_items).replace("'", '"'))
                if self.takeBandsButton.clicked:
                    self.band_window.close()
        self.allBandBtn.setStyleSheet("background-color: white")
        self.multipleBandBtn.setStyleSheet("background-color: lightgray")
