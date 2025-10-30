# -*- coding: utf-8 -*-
import sip

from qgis.core import QgsDataItem
from qgis.core import QgsDataCollectionItem

from .OpenEOCollectionItem import OpenEOCollectionItem


class OpenEOCollectionsGroupItem(QgsDataCollectionItem):
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
    
    def getConnection(self):
        return self.parent().getConnection()
    
    def actions(self, parent):
        return []