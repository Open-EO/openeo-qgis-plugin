# -*- coding: utf-8 -*-
import os
import sip
import openeo

from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis
from qgis.core import QgsSettings
from qgis.core import QgsDataProvider
from qgis.core import QgsDataItemProvider
from qgis.core import QgsDataItem
from qgis.core import QgsLayerItem
from qgis.core import QgsDataCollectionItem

from .connect_dialog import ConnectDialog

class OpenEOItemProvider(QgsDataItemProvider):
    """
    QgsDataItemProvider class implementation that is necessary to provide data-items to
    the QGIS browser (the tree-structured menu on the left to the map screen by default)
    """
    def __init__(self, plugin):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        """
        QgsDataItemProvider.__init__(self)
        self.root_item = None
        self.plugin = plugin

    def name(self):
        return "OpenEO"

    def capabilities(self):
        return QgsDataProvider.Net #dont understand that yet
    
    def createDataItem(self, path, parentItem):
        if not parentItem:
            ri = OpenEORootItem(plugin=self.plugin)
            sip.transferto(ri, None)
            self.root_item = ri
            return ri
        else:
            return None
        
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
        self.dlg.logo.setPixmap(QPixmap(os.path.join(os.path.dirname(__file__), '../images/icon_large.png')))
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
        dirname = os.path.join(os.path.dirname(__file__), "../images")
        
        action_new_connection = QAction(QIcon(os.path.join(dirname, "icon_small.png")), "new connection", parent)
        action_new_connection.triggered.connect(self.addConnection)
        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refreshItems)
        actions = [action_new_connection, action_refresh]
        return actions
    
class OpenEOConnectionItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that contains a connection to an OpenEO provider.
    Direct parent to:
     - OpenEOCollecionsGroupItem
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
        collections = OpenEOCollecionsGroupItem(self.plugin, self)
        collections.setState(QgsDataItem.Populated)
        sip.transferto(collections, self)
        collections.refresh()
        items.append(collections)

        return items
    
    def deleteConnection(self):
        self.parent().removeConnection(self.connection_idx)
    
    def actions(self, parent):
        action_delete = QAction(QIcon(), "delete connection...", parent)
        action_delete.triggered.connect(self.deleteConnection)
        actions = [action_delete]
        return actions
    
class OpenEOCollecionsGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all collections offered by the corresponding
    openEO provider
    Direct parent to:
     - OpenEOCollectionItem
    """
    def __init__(self, plugin, parent_connection):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(self, parent_connection, "Collections", plugin.PLUGIN_ENTRY_NAME)
        self.plugin = plugin
        self.saved_collections = self.getCollections()
        self.collection_items = []
        self.createChildren()

    def getCollections(self):
        #some sort of pagination might be beneficial
        collections = self.parent().connection.list_collections()
        return collections

    def createChildren(self):
        del self.collection_items[:]
        items = []
        for collection in self.saved_collections:
            item = OpenEOCollectionItem(
                parent=self, 
                collection_object=collection,
                plugin = self.plugin)
            item.setState(QgsDataItem.Populated)
            item.refresh()
            sip.transferto(item, self)
            items.append(item)
            self.collection_items.append(item)
        return items
    
    def actions(self, parent):
        return []

#TODO: the type this inherits is still to be debated.
class OpenEOCollectionItem(QgsLayerItem):
    def __init__(self, parent, collection_object, plugin):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollecionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param collection_object: dict containing relevant infos about the collection.
        :type url: dict
        """
        self.collection = collection_object
        QgsLayerItem.__init__(
            self,
            parent = parent,
            name = self.collection["title"],
            path = None,
            uri = None,
            layerType = Qgis.BrowserLayerType.NoType,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

class ConnectionModel():
    def __init__(self, name, url):
        self.name = name
        self.url = url