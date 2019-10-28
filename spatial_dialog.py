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
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'spatial_dialog.ui'))


class SpatialDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None, iface=None):
        """Constructor method
        """
        super(SpatialDialog, self).__init__(parent)
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


        #self.selectDate.clicked.connect(self.add_temporal)

        self.buttonBox.accepted.connect(self.accept_dialog)

    def accept_dialog(self):
        print("TBD")