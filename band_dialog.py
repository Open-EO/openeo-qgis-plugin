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

PROCESSES_BANDS = ["load_collection", "filter_bands"]

class BandDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None, pg_graph=None):
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

        self.pg_graph = pg_graph

        self.comboProcessBox.currentTextChanged.connect(self.update_selection)

        self.init_processes()

        self.all_bands = []

        self.init_bands()

        self.update_selection()

        self.buttonBox.accepted.connect(self.accept_dialog)

    def init_bands(self, process_id=None, cur_bands=None):
        data_collection = self.parent().connection.list_collections()

        if process_id:
            selected_collection = self.parent().get_pg_collection(process_id=process_id)
        else:
            selected_collection = self.parent().get_pg_collection()

        if cur_bands:
            self.processgraphBands.setText(str(cur_bands))
            self.processgraphBands.show()

        for col in data_collection:
            if str(col['id']) == selected_collection:
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
                            if cur_bands:
                                self.processgraphBands.setText(str(cur_bands))
                            else:
                                self.processgraphBands.setText(str(self.all_bands).replace("'", '"'))
                            self.processgraphBands.show()

    def update_selection(self):
        example_job = self.pg_graph
        if self.comboProcessBox.currentText():
            process_selection = self.comboProcessBox.currentText().split(" - ")
            if process_selection[0] in ["load_collection", "filter_bands"]:
                if "bands" in example_job[process_selection[1]]["arguments"]:
                    bands = example_job[process_selection[1]]["arguments"]["bands"]
                    self.init_bands(process_id=process_selection[1], cur_bands=bands)

    def accept_dialog(self):
        process_selection = self.comboProcessBox.currentText().split(" - ")[1]
        self.parent().change_example_bands(self.processgraphBands.toPlainText(), process_id=process_selection)

    def init_processes(self):
        example_job = self.pg_graph
        for key, _ in example_job.items():
            if example_job[key]["process_id"] in PROCESSES_BANDS:
                self.comboProcessBox.addItem("{} - {}".format(example_job[key]["process_id"], key))

    def multiple_bands(self):
        """
        Produces a checkable QListWidget
        :return: Of all bands, only the selected bands are returned.
        """
        self.allBandBtn.setStyleSheet("background-color: white")
        self.multipleBandBtn.setStyleSheet("background-color: white")
        if self.multipleBandBtn.clicked:
            self.multipleBandBtn.setStyleSheet("background-color: lightgray")

        #self.processgraphBands.clear()
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
        self.processgraphBands.clear()
        for index in range(self.bandBox.count()):
            if self.bandBox.item(index).checkState() == Qt.Checked:
                checked_items.append(self.bandBox.item(index).text())
                self.processgraphBands.setText(str(checked_items).replace("'", '"'))
                if self.takeBandsButton.clicked:
                    self.band_window.close()
        self.allBandBtn.setStyleSheet("background-color: white")
        self.multipleBandBtn.setStyleSheet("background-color: lightgray")
