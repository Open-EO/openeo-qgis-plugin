# -*- coding: utf-8 -*-
import sip
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem

from .OpenEOConnectionItem import OpenEOConnectionItem
from ..connect_dialog import ConnectDialog

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
        self.setIcon(QIcon(self.getImagePath("icon_small.png")))
        self.saved_connections = [] #TODO: add this to QgsSettings for more persistence later
        #TODO: also make sure to change all the add/removeConnection code accordingly

        self.populate() # todo: not sure why this is needed

    def createChildren(self):
        settings = QgsSettings()
        items = []
        for connection in self.saved_connections:
            item = self.createConnectionItem(connection)
            items.append(item)
        return items

    def createConnectionItem(self, model, connection=None):
        item = OpenEOConnectionItem(
            plugin=self.plugin, 
            model=model,
            parent=self,
            connection=connection
        )
        sip.transferto(item, self)
        return item
    
    def getImagePath(self, name):
        dirname = os.path.join(os.path.dirname(__file__), "../../images")
        return os.path.join(dirname, name)

    def addConnection(self):
        self.dlg = ConnectDialog(iface=self.plugin.iface)
        self.dlg.show()
        result = self.dlg.exec()

        if result:
            model = self.dlg.getModel()
            connection = self.dlg.getConnection()
            self.saved_connections.append(model)
            item = self.createConnectionItem(model, connection=connection)
            self.addChildItem(item, refresh=True)

    
    def removeConnection(self, data_item):
        #TODO: this will need to be changed when QgsSettings is implemented
        self.saved_connections.remove(data_item.model)
        self.deleteChildItem(data_item)

    
    def actions(self, parent):
        action_new_connection = QAction(QIcon(), "New openEO Connection", parent)
        action_new_connection.triggered.connect(self.addConnection)

        return [action_new_connection]