# -*- coding: utf-8 -*-
import sip
import openeo

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsDataItem
from qgis.core import QgsDataCollectionItem

from .OpenEOCollectionsGroupItem import OpenEOCollectionsGroupItem

class OpenEOConnectionItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that contains a connection to an OpenEO provider.
    Direct parent to:
     - OpenEOCollectionsGroupItem
     - OpenEo_batchjob_group_item
     - OpenEo_services_group_item 
    """
    def __init__(self, plugin, name, url, parent, connection_idx):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param name: The name of the OpenEORootItem. This will be displayed in the 
            Browser.
        :type name: str

        :param url: The url where the openEO endpoint of the connection is located.
        :type url: str

        :param parent: the parent DataItem. expected to be an OpenEORootItem.
        :type parent: QgsDataItem

        :param connection_idx: index of the connection in the parents' list of connection.
            relevant for deletion of connections.
        :type connection_idx: int
        """
        self.connection = openeo.connect(url)
        capabilities = self.connection.capabilities()
        if not name:
            self.name = capabilities.get("title")
        else:
            self.name = name
        self.plugin = plugin
        self.url = url
        self.connection_idx = connection_idx
        QgsDataCollectionItem.__init__(self, parent, self.name, plugin.PLUGIN_ENTRY_NAME)
        self.createChildren()

    def createChildren(self):
        #TODO: children for collections, batch-jobs, services
        items = []
        
        # create Collections group
        collections = OpenEOCollectionsGroupItem(self.plugin, self)
        collections.setState(QgsDataItem.Populated)
        sip.transferto(collections, self)
        collections.refresh()
        items.append(collections)

        return items
    
    def remove(self):
        self.parent().removeConnection(self.connection_idx)

    def getConnection(self):
        return self.connection
    
    def actions(self, parent):
        action_delete = QAction(QIcon(), "delete connection...", parent)
        action_delete.triggered.connect(self.remove)
        actions = [action_delete]
        return actions