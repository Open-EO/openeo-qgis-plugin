# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LoginDialog

 This class is responsible for showing the login window and to let the user log in to an openEO backend.

        author            : 2020 by Bernhard Goesswein
        email             : bernhard.goesswein@geo.tuwien.ac.at
 ***************************************************************************/
"""
import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from qgis.PyQt.QtGui import QIcon
from .openeo_connector_dialog import OpenEODialog
from .models.backend import Backend
from .models.openeohub import get_hub_backends

from .utils.logging import warning
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'login_dialog.ui'))


class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing the login window and to let the user log in to an openEO backend.
    """
    def __init__(self, parent=None, iface=None, openeo=None):
        """
        Constructor method: Initializing the button behaviours and the backend combobox.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        """
        super(LoginDialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.openeo = openeo

        self.iface = iface
        self.called = False
        self.called2 = False
        self.processes = None

        self.setupUi(self)
        self.backends = []
        try:
            self.backends = get_hub_backends()
            self.set_backend_urls()
        except:
            warning(self.iface, "The plugin was not able to connect to openEO Hub. "
                                "Are you connected to the internet?")

        self.loginButton.clicked.connect(self.login)
        self.dlg = None

        self.versionBox.stateChanged.connect(self.version_checkbox_changed)

    def set_backend_urls(self, latest_version=True):
        """
        Loads the backend urls, already retrieved in the constructor, into the combo box. If latest_version is set, it
        will show the backend names, otherwise it shows the urls of all versions.
        :param latest_version: bool: show only latest versions or all of the backends.
        """
        self.backendEdit.clear()
        if latest_version:
            for backend in self.backends:
                self.backendEdit.addItem(backend.name)
        else:
            for backend in self.backends:
                self.backendEdit.addItems(backend.get_all_urls())

    def version_checkbox_changed(self):
        """
        Adapt the backend combo box according to the version check box.
        """
        self.set_backend_urls(latest_version=self.versionBox.isChecked())

    def get_current_url(self):
        """
        Returns the currently selected url, so either the latest version of the selected backend or just
        the url in the backend url field.
        """
        if self.versionBox.isChecked():
            for bckend in self.backends:
                if bckend.name == self.backendEdit.currentText():
                    return bckend.get_latest_version()

        return self.backendEdit.currentText()

    def connect(self):
        """
        Connect to the backend via the given credentials. It will connect via BasicAuthentication and Bearertoken.
        If there are no credentials, it connects to the backend without authentication.
        This method also loads all collections and processes from the backend.
        """
        url = self.get_current_url()
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
        """
        Logs the user into the backend and starts the main openEO dialog, also closes this login dialog.
        """
        self.openeo.login()
        # backend = self.connect()
        #
        # if not backend:
        #     return
        #
        # self.dlg = OpenEODialog(interface=self.iface, backend=backend)
        # self.dlg.infoBtn2.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/info_icon.png')))
        # self.dlg.refreshButton.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/reload_icon.png')))
        # self.dlg.refreshButton_service.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'images/reload_icon.png')))
        # self.dlg.jobsManualBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__),
        #                                                        'images/user_manual_icon.png')))
        # self.dlg.servicesManualBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__),
        #                                                        'images/user_manual_icon.png')))
        # self.dlg.explorativeManualBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__),
        #                                                        'images/user_manual_icon.png')))
        # # self.dlg.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.dlg.show()
        # # self.close()
