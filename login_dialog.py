# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from qgis.PyQt.QtGui import QIcon, QPixmap
from .openeo_connector_dialog import OpenEODialog
from .models.backend import Backend
from .models.connect import Connection
from .models.openeohub import get_hub_backends

from .utils.logging import info, warning
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'login_dialog.ui'))


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None, iface=None):
        """Constructor method
        """
        super(LoginDialog, self).__init__(parent)
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
        try:
            backends = get_hub_backends()

            self.backendEdit.addItems(backends)  # or Backends
        except:
            warning(self.iface, "The plugin was not able to connect to openEO Hub. Are you connected to the internet?")

        self.loginButton.clicked.connect(self.login)
        self.dlg = None

    def connect(self):
        """
        Connect to the backend via the given credentials. It will connect via BasicAuthentication and Bearertoken.
        If there are no credentials, it connects to the backend without authentication.
        This method also loads all collections and processes from the backend.
        """
        url = self.backendEdit.currentText()
        pwd = self.passwordEdit.text()
        user = self.usernameEdit.text()
        if user == "":
            user = None
        if pwd == "":
            pwd = None

        backend = Backend(url=url)

        if not backend:
            warning(self.iface, "Connection failed, the backend might not be available at the moment!")
            return None

        auth = backend.login(username=user, password=pwd)

        if not auth:
            warning(self.iface, "Authentication failed!")
            return None

        return backend

    def login(self):

        backend = self.connect()

        if not backend:
            return

        self.dlg = OpenEODialog(iface=self.iface, backend=backend)
        self.dlg.infoBtn2.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'info_icon.png')))
        self.dlg.refreshButton.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'reload_icon.png')))
        self.dlg.deleteButton.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'delete_job.png')))
        self.dlg.deleteFinalButton.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'deleteFinalBtn.png')))
        self.dlg.refreshButton_service.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'reload_icon.png')))
        self.dlg.deleteButton_service.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'delete_job.png')))
        self.dlg.deleteFinalButton_service.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'deleteFinalBtn.png')))
        self.dlg.operationManualBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'user_manual_icon.png')))
        self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg.show()
        self.close()
