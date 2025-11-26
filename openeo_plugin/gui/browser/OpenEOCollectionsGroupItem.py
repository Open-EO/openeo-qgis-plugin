# -*- coding: utf-8 -*-
import sip

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsDataCollectionItem
from qgis.core import QgsApplication

from . import OpenEOCollectionItem
from ...utils.logging import error

class OpenEOCollectionsGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all collections offered by the corresponding
    openEO provider
    Direct parent to:
     - OpenEOCollectionLayerItem
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
        self.setIcon(QgsApplication.getThemeIcon("mIconFolder.svg"))

    def getCollections(self):
        try:
            collections = self.getConnection().list_collections()
            return collections
        except Exception as e:
            self.plugin.logging.logError(e)
            self.plugin.logging.error("Fetching collections failed. See log for details")
        return []

    def createChildren(self):
        items = []
        collections = self.getCollections()
        for collection in collections:
            # determine whether collectionItem or LayerItem
            if len(self.getWebMapLinks(collection)) > 0:
                item = OpenEOCollectionItem(
                    parent=self, 
                    collection=collection,
                    plugin=self.plugin,
                    preview=True
                )
                sip.transferto(item, self)
                items.append(item)
            else:
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
    
    def getWebMapLinks(self, collection):
        """
        helper-function that determines whether or not a collection of this 
        connection contains a web-map-link 
        """
        webMapLinks = []
        links = collection["links"]
        for link in links:
            match link["rel"]:
                case "wmts":
                    webMapLinks.append(link)
                case "xyz":
                    webMapLinks.append(link)
                # case "3d-tiles":
                #     webMapLinks.append(link)
                # case "wms":
                #     webMapLinks.append(link)
                # case "pmtiles":
                #     webMapLinks.append(link)
                # case "tilejson":
                #     webMapLinks.append(link)

        return webMapLinks
    
    def actions(self, parent):        
        action_refresh = QAction(QgsApplication.getThemeIcon("mActionRefresh.svg"), "Refresh", parent)
        action_refresh.triggered.connect(self.refresh)
        return [action_refresh]