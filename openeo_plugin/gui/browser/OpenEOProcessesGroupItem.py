# -*- coding: utf-8 -*-
import sip

from qgis.core import QgsDataCollectionItem

class OpenEOProcessesGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all Processes offered by the corresponding
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
        QgsDataCollectionItem.__init__(self, parent, "Processes", plugin.PLUGIN_ENTRY_NAME)
        self.plugin = plugin

    def getConnection(self):
        return self.parent().getConnection()