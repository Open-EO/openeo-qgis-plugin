import openeo
import requests

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QApplication

from ..utils.logging import warning
from .ui.connect_dialog import Ui_SpatialDialog as FORM_CLASS
########################################################################################################################
########################################################################################################################

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
#FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/connect_dialog.ui'))

class ConnectDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing the provider-connection window and to let the user connect to an openEO backend.
    """
    def __init__(self, parent=None, iface=None, openeo=None):
        """
        Constructor method: Initializing the button behaviours and the backend combobox.
        :param parent: parent dialog of this dialog (e.g. OpenEODialog).
        :param iface: Interface to show the dialog.
        """
        super(ConnectDialog, self).__init__(parent)

        self.HUB_URL = "https://hub.openeo.org"

        QApplication.setStyle("cleanlooks")
        self.openeo = openeo
        self.iface = iface

        self.setupUi(self)
        self.backends = []
        # TODO: query openEO hub to populate combobox
        try:
            self.backends = self.getHubBackends()
        except Exception as e:
            print(e)
            warning(self.iface, "The plugin was not able to connect to openEO Hub. "
                                "Are you connected to the internet?")
        #populate combobox
        for item in self.backends:
            self.server_selector.addItem(item["name"])

        self.server_selector.currentIndexChanged.connect(self.serverSelectorUpdated)

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

        #TODO: use of a dict might not be most elegant. perhaps connection_model can be imported
        conn_info = {
            "connection": connection,
            "name": name,
            "url": url 
        }

        return conn_info

    def serverSelectorUpdated(self, index):
        selected_backend = self.backends[index]
        new_name = selected_backend["name"]
        new_url = selected_backend["url"]
        self.conn_name_edit.setText(new_name)
        self.url_edit.setText(new_url)
        return
    
    def getHubBackends(self):
        try:
            backendURL = requests.get('{}/api/backends'.format(self.HUB_URL), timeout=5)
        except:
            backendsALL = {}

        if backendURL.status_code == 200:
            backendsALL = backendURL.json()
        else:
            return []
        # self.processgraphEdit.setText(json.dumps(self.backendsALL, indent=4))
        backends = []

        # Look for .well-known endpoint
        for name, url in backendsALL.items():
            backend = {"name": name, "url": url}
            backends.append(backend)
            #backends[index].append(HubBackend(url, name=name))

        return backends
