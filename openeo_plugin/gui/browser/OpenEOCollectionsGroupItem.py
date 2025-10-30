# -*- coding: utf-8 -*-
import sip

from qgis.core import QgsDataCollectionItem

from .OpenEOCollectionItem import OpenEOCollectionItem


class OpenEOCollectionsGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all collections offered by the corresponding
    openEO provider
    Direct parent to:
     - OpenEOCollectionItem
    """
    def __init__(self, plugin, parent):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(self, parent, "Collections", plugin.PLUGIN_ENTRY_NAME)
        self.plugin = plugin

    def getCollections(self):
        #some sort of pagination might be beneficial
        collections = self.getConnection().list_collections()
        return collections

    def createChildren(self):
        items = []
        collections = self.getCollections()
        for collection in collections:
            item = OpenEOCollectionItem(
                parent=self, 
                collection=collection,
                plugin=self.plugin
            )
            sip.transferto(item, self)
            items.append(item)
        return items
    
    def getConnection(self):
        return self.parent().getConnection()
    
    def actions(self, parent):
        return []