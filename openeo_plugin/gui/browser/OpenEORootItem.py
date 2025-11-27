# -*- coding: utf-8 -*-
import sip
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem

from . import OpenEOConnectionItem
from ..connect_dialog import ConnectDialog
from ...utils.settings import SettingsPath
from ...models.ConnectionModel import ConnectionModel

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

        #get saved connections from QgsSettings
        settings = QgsSettings()
        models = map(ConnectionModel.fromDict, settings.value(SettingsPath.SAVED_CONNECTIONS.value))
        self.saved_connections = list(models) # map needs to be turned into a list

    def createChildren(self):
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
        settings = QgsSettings()
        self.dlg = ConnectDialog(iface=self.plugin.iface)
        self.dlg.show()
        result = self.dlg.exec()

        if result:
            model = self.dlg.getModel()
            connection = self.dlg.getConnection()
            self.saved_connections.append(model)
            
            # save the model persistently
            reprs = settings.value(SettingsPath.SAVED_CONNECTIONS.value)
            reprs.append(model.toDict())
            settings.setValue(SettingsPath.SAVED_CONNECTIONS.value, reprs)

            item = self.createConnectionItem(model, connection=connection)
            self.addChildItem(item, refresh=True)

    
    def removeConnection(self, data_item):
        self.saved_connections.remove(data_item.model)
        
        # update the saved connection models
        settings = QgsSettings()
        reprs = map(lambda c : c.toDict(), self.saved_connections)
        settings.setValue(SettingsPath.SAVED_CONNECTIONS.value, list(reprs))

        self.deleteChildItem(data_item)

    
    def actions(self, parent):
        action_new_connection = QAction(QIcon(), "New openEO Connection", parent)
        action_new_connection.triggered.connect(self.addConnection)

        return [action_new_connection]