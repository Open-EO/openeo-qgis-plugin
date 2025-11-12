# -*- coding: utf-8 -*-
import sip

from qgis.core import QgsDataCollectionItem

from . import OpenEOServiceItem

class OpenEOServicesGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all Services offered by the corresponding
    openEO provider to the logged in account. Requires Authentication.
    Direct parent to:
    """
    def __init__(self, plugin, parent):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(self, parent, "Web Services", plugin.PLUGIN_ENTRY_NAME)
        self.plugin = plugin

        self.populate() #removes expand icon

    def createChildren(self):
        if not self.isAuthenticated():
            return []
        items = []
        services = self.getServices()
        for service in services:
            item = OpenEOServiceItem(
                parent = self,
                service = service,
                plugin =  self.plugin,
            )
            sip.transferto(item, self)
            items.append(item)
        return items

    def getConnection(self):
        return self.parent().getConnection()
    
    def isAuthenticated(self):
        return self.parent().isAuthenticated()
    
    def handleDoubleClick(self):
        if not self.isAuthenticated():
            self.parent().authenticate()

        return super().handleDoubleClick()
    
    def getWebMapLinks(self, service):
        """
        helper-function that determines whether or not a service of this 
        connection contains a web-map-link 
        """
        webMapLinks = []
        print(service)
        #TODO: more cases. how are wmts handled?
        match service["type"]:
            case "wmts":
                webMapLinks.append(service)
            case "xyz":
                webMapLinks.append(service)
            # case "3d-tiles":
            #     webMapLinks.append(service)
            # case "wms":
            #     webMapLinks.append(service)
            # case "pmtiles":
            #     webMapLinks.append(service)
            # case "tilejson":
            #     webMapLinks.append(service)
        return webMapLinks
    
    def getServices(self):
        services = self.getConnection().list_services()
        return services