# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets

import qgis.PyQt.QtCore as QtCore
from PyQt5.QtCore import QDate, Qt, QSize, QSettings
from PyQt5.QtWidgets import QVBoxLayout, QApplication, QWidget, QPushButton, QListWidget, QListWidgetItem, QDialog

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'band_dialog.ui'))


class BandDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None, minimum_date=None, maximum_date=None, max_date=None):
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

        self.multipleBandBtn.clicked.connect(self.multiple_bands)
        self.allBandBtn.clicked.connect(self.save_band_choice1)
        self.label_16.hide()
        self.processgraphBands.hide()
        self.multipleBandBtn.hide()
        self.allBandBtn.hide()

        self.allBandBtn.setEnabled(True)
        self.multipleBandBtn.setEnabled(True)
        self.processgraphBands.setEnabled(True)
        self.label_16.setEnabled(True)
        self.label_11.setEnabled(True)  # Add Bands

        self.all_bands = []

        self.init_bands()

        self.buttonBox.accepted.connect(self.accept_dialog)

    def init_bands(self):
        data_collection = self.parent().connection.list_collections()
        for key, _ in self.parent().example_job.items():
            if self.parent().example_job[key]['process_id'] == "load_collection":
                if self.called2 == False:
                    self.parent().collectionBox_individual_job.addItem(self.parent().example_job[key]['arguments']['id'])
                    self.called2 = True

        selected_process = str(self.parent().collectionBox_individual_job.currentText())

        for col in data_collection:
            if str(col['id']) == selected_process:
                data = self.parent().connection.get('/collections/{}'.format(col['id']), auth=False)
                if data.status_code == 200:
                    band_info = data.json()
                    bands = band_info['properties']['cube:dimensions']['bands']['values']

                    self.all_bands = []
                    for each_band in bands:
                        self.all_bands.append(each_band)

                        if len(self.all_bands) == 1:
                            self.label_16.setText(str(self.all_bands[0]))
                            self.label_16.show()
                            self.processgraphBands.hide()
                            self.multipleBandBtn.hide()
                            self.allBandBtn.hide()
                        else:
                            self.label_16.hide()
                            self.multipleBandBtn.show()
                            self.allBandBtn.show()
                            self.processgraphBands.setText(str(self.all_bands).replace("'", '"'))
                            self.processgraphBands.show()

    def accept_dialog(self):
        self.parent().insert_Change_bands(self.processgraphBands.toPlainText())

    def multiple_bands(self):
        """
        Produces a checkable QListWidget
        :return: Of all bands, only the selected bands are returned.
        """
        self.allBandBtn.setStyleSheet("background-color: white")
        self.multipleBandBtn.setStyleSheet("background-color: white")
        if self.multipleBandBtn.clicked:
            self.multipleBandBtn.setStyleSheet("background-color: lightgray")

        self.processgraphBands.clear()
        self.band_window = QDialog(parent=self)
        self.hbox4 = QVBoxLayout()
        self.bandBox = QListWidget()

        for band in self.all_bands:
            # Set Checkbox before band
            self.item = QListWidgetItem(self.bandBox)
            self.item.setFlags(self.item.flags() | QtCore.Qt.ItemIsUserCheckable)
            self.item.setCheckState(Qt.Unchecked)
            self.item.setText(str(band))

        self.bandBox.sortItems()
        self.bandBox.setMinimumWidth(150)
        self.bandBox.setMinimumHeight(200)
        self.band_window.setWindowTitle('Select Multiple Bands')
        self.takeBandsButton = QPushButton('Save Choice of Bands')

        self.hbox4.addWidget(self.bandBox)
        self.hbox4.addWidget(self.takeBandsButton)
        self.band_window.setLayout(self.hbox4)
        #self.band_window.setGeometry(400, 400, 600, 450)

        self.takeBandsButton.setMinimumWidth(100)
        self.takeBandsButton.setMinimumWidth(50)
        self.takeBandsButton.clicked.connect(self.save_band_choice2)
        #self.takeBandsButton.setGeometry(420, 25, 150, 31)
        self.band_window.show()


    def save_band_choice1(self):
        self.allBandBtn.setStyleSheet("background-color: lightgray")
        self.multipleBandBtn.setStyleSheet("background-color: white")
        self.processgraphBands.setText(str(self.all_bands).replace("'", '"'))

    def save_band_choice2(self):
        checked_items = []
        for index in range(self.bandBox.count()):
            if self.bandBox.item(index).checkState() == Qt.Checked:
                checked_items.append(self.bandBox.item(index).text())
                self.processgraphBands.setText(str(checked_items).replace("'", '"'))
                if self.takeBandsButton.clicked:
                    self.band_window.close()
        self.allBandBtn.setStyleSheet("background-color: white")
        self.multipleBandBtn.setStyleSheet("background-color: lightgray")
