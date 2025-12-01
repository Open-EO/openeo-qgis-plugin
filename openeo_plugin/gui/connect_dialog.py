# -*- coding: utf-8 -*-
import os
import openeo
import requests

from qgis.PyQt import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QApplication

#from .ui.connect_dialog import Ui_ConnectDialog as FORM_CLASS
from ..models.ConnectionModel import ConnectionModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/connect_dialog.ui'))

class ConnectDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing the provider-connection window and to let the user connect to an openEO backend.
    """
    def __init__(self, parent, iface=None):
        """
        Constructor method: Initializing the button behaviours and the backend combobox.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        """
        super(ConnectDialog, self).__init__()

        self.HUB_URL = "https://hub.openeo.org"

        QApplication.setStyle("cleanlooks")
        self.iface = iface
        self.plugin = parent.plugin
        self.setupUi(self)
        self.connection = None
        self.model = None

        self.connect_button.clicked.connect(self.verify)
        self.url_edit.returnPressed.connect(self.verify)
        self.conn_name_edit.returnPressed.connect(self.verify)

        # Handle openEO Hub integration
        self.backends = []
        try:
            self.backends = self.getHubBackends()
            for item in self.backends:
                self.server_selector.addItem(item["name"])
        except Exception as e:
            print(e)
            self.plugin.logging.warning(self.iface, "The plugin was not able to connect to openEO Hub. "
                                "Are you connected to the internet?")
        
        self.server_selector.setCurrentIndex(-1) # don't select anything by default
        self.server_selector.currentIndexChanged.connect(self.serverSelectorUpdated)

    def getModel(self):
        return self.model
    
    def getConnection(self):
        return self.connection

    def verify(self):
        """
        Connect to the backend at the given URL. This will return a backend object of the
        connection to create a browser entry with.
        """
        url = self.url_edit.text()
        name = self.conn_name_edit.text()

        if not url:
            self.plugin.logging.warning("Please provide a URL to connect to.")
            return

        self.connect_button.setDisabled(True)
        btn_text = self.connect_button.text()
        self.connect_button.setText("Testing Connection...")
        QApplication.processEvents()

        self.connection = None
        self.model = None
        try:
            self.connection = openeo.connect(url)
        except Exception as e:
            print(e)
            self.plugin.logging.warning("Connection could not be established. Please check the URL and your internet connection.")

            self.connect_button.setDisabled(False)
            self.connect_button.setText(btn_text)

        if self.connection:
            if not name:
                capabilities = self.connection.capabilities()
                # Fallback to default naming if no title is provided
                name = capabilities.get("title") or url
            self.model = ConnectionModel(name, url)
            self.accept()  # Close the dialog on success

    
    def serverSelectorUpdated(self, index):
        if index < 0:
            return
        selected_backend = self.backends[index]
        new_name = selected_backend["name"]
        new_url = selected_backend["url"]
        self.conn_name_edit.setText(new_name)
        self.url_edit.setText(new_url)
        return
    
    def getHubBackends(self):
        try:
            backendUrl = requests.get('{}/api/backends'.format(self.HUB_URL), timeout=5)
        except:
            hubBackends = {}

        if backendUrl.status_code == 200:
            hubBackends = backendUrl.json()
        else:
            return []

        backends = []
        for name, url in hubBackends.items():
            backend = {"name": name, "url": url}
            backends.append(backend)

        return backends
