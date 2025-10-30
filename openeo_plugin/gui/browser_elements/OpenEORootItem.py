# -*- coding: utf-8 -*-
import sip
import os

from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem
from qgis.core import QgsDataItem

from .OpenEOConnectionItem import OpenEOConnectionItem
from ..connect_dialog import ConnectDialog
from . import ConnectionModel

class OpenEORootItem(QgsDataCollectionItem):
    """
    Implementation of QgsDataCollectionItem. The root of the plugin within the browser view
    Direct parent to:
     - OpenEOConnectionItem
    """
    def __init__(self, plugin, name=None, parent=None):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param name: The name of the OpenEORootItem. This will be displayed in the 
            Browser.
        :type name: str

        :param parent: the parent DataItem. Root is not expected to have one.
        :type parent: QgsDataItem
        """
        name = plugin.PLUGIN_NAME if not name else name
        provider_key = plugin.PLUGIN_ENTRY_NAME
        QgsDataCollectionItem.__init__(self, parent, name, provider_key)
        self.plugin = plugin
        #self.setIcon(QIcon(icon_filepath("edr.png")))
        self.saved_connections = [] #TODO: add this to QgsSettings for more persistence later
        #TODO: also make sure to change all the add/removeConnection code accordingly
        self.items = []

    def createChildren(self):
        del self.items[:]
        settings = QgsSettings()
        items = []
        for idx, connection in enumerate(self.saved_connections):  
            item = OpenEOConnectionItem(
                plugin=self.plugin, 
                name=connection.name, 
                url=connection.url, 
                parent=self,
                connection_idx=idx)
            item.setState(QgsDataItem.Populated)
            item.refresh()
            sip.transferto(item, self)
            items.append(item)
            self.items.append(item)
        return items
    
    def refreshItems(self):
        self.depopulate()
        self.createChildren()

    def addConnection(self):
        self.dlg = ConnectDialog(iface=self.plugin.iface, openeo=self)
        self.dlg.logo.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), '../../images/icon_large.png')))
        self.dlg.logo.setFixedSize(139, 89)
        self.dlg.show()
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
    
    def removeConnection(self, connection_idx):
        #TODO: this will need to be changed when QgsSettings is implemented
        self.saved_connections.pop(connection_idx)
        self.refreshItems()
        
    def connect(self):
        conn_info = self.dlg.connect()
        connection = conn_info["connection"]

        if not connection:
            return

        conn_url = connection._orig_url
        conn_name = conn_info["name"]

        connection = ConnectionModel(conn_name, conn_url)
        self.saved_connections.append(connection)
        self.dlg.close()
        self.refreshItems()
        return
    
    def actions(self, parent):
        dirname = os.path.join(os.path.dirname(__file__), "../../images")
        
        action_new_connection = QAction(QIcon(os.path.join(dirname, "icon_small.png")), "new connection", parent)
        action_new_connection.triggered.connect(self.addConnection)
        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refreshItems)
        actions = [action_new_connection, action_refresh]
        return actions