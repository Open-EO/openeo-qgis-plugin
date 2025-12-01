# -*- coding: utf-8 -*-
import sip
import openeo

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsDataCollectionItem
from qgis.core import QgsApplication

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

        self.setIcon(QgsApplication.getThemeIcon("mIconFolder.svg"))

    def refresh(self):
        self.depopulate()
        super().refresh()

    def createChildren(self):
        items = []
        services = self.getServices()
        for service in services:
            item = OpenEOServiceItem(
                parent = self,
                service = service,
                plugin = self.plugin,
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
    
    def getServices(self):
        try:
            services = self.getConnection().list_services()
            return services
        except openeo.rest.OpenEoApiError:
            return [] #this happens when authentication is missing
        except Exception as e:
            self.plugin.logging.logError(e)
            self.plugin.logging.error("Fetching services failed. See log for details")
        return []
    
    def actions(self, parent):
        action_refresh = QAction(QgsApplication.getThemeIcon("mActionRefresh.svg"), "Refresh", parent)
        action_refresh.triggered.connect(self.refresh)
        return [action_refresh]