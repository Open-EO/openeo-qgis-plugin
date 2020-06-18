# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BandDialog

 This dialog handles the adaption of a band parameter. Therefore, reads the available bands from the backend and
 lets the user choose on them. On submission it returns the values back to the AdaptDialog parent.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets

import qgis.PyQt.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QListWidgetItem

########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'band_dialog.ui'))


class BandDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This dialog class has the purpose to adaption of a band parameter. Therefore, reads the available bands
    from the backend and lets the user choose on them. On submission it returns the values back
    to the AdaptDialog parent.
    """
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
        """
        Initializes the band list in the dialog, by adding the ands to the WidgetList object and sorting them.
        It also activates the checkboxes of the currently selected bands.
        """
        self.bandsListWidget.clear()

        for band in self.all_bands:
            # Set Checkbox before band
            item = QListWidgetItem(self.bandsListWidget)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            if band in self.bands:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setText(str(band))

        self.bandsListWidget.sortItems()

    def accept_dialog(self):
        """
        Gets called when the user selected the bands and applies the selection. Calls a method from the JobAdaptDialog
        parent to pass the selection information.
        """
        band_list = []
        for index in range(self.bandsListWidget.count()):
            if self.bandsListWidget.item(index).checkState() == Qt.Checked:
                band_list.append(self.bandsListWidget.item(index).text())
        self.parent().receive_bands(band_list)
