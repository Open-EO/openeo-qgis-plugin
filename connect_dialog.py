import os

from qgis.PyQt import uic

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from qgis.PyQt.QtGui import QIcon
from .openeo_connector_dialog import OpenEODialog
import openeo
#from .models.openeohub import get_hub_backends

from .utils.logging import warning
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'connect_dialog.ui'))

class Connect_dialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing the provider-connection window and to let the user connect to an openEO backend.
    """
    def __init__(self, parent=None, iface=None, openeo=None):
        """
        Constructor method: Initializing the button behaviours and the backend combobox.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        """
        super(Connect_dialog, self).__init__(parent)

        QApplication.setStyle("cleanlooks")

        self.openeo = openeo
        self.iface = iface

        self.setupUi(self)
        self.backends = []
        # TODO: query openEO hub to populate combobox
        #try:
        #    self.backends = get_hub_backends()
        #    self.set_backend_urls()
        #except:
        #    warning(self.iface, "The plugin was not able to connect to openEO Hub. "
        #                        "Are you connected to the internet?")

        self.connect_button.clicked.connect(self.openeo.connect)

    def connect(self):
        """
        Connect to the backend at the given URL. This will return a backend object of the
        connection to create a browser entry with.
        """
        url = self.url_edit.text()
        name = self.conn_name_edit.text()

        if not url:
            warning(self.iface, "Connection not established. Enter a valid URL")
            return None
        
        if not name:
            name = False

        connection = openeo.connect(url)

        conn_info = {
            "connection": connection,
            "name": name,
            "url": url 
        }

        return conn_info