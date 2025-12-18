# -*- coding: utf-8 -*-

from qgis.core import QgsDataProvider
from qgis.core import QgsDataItemProvider

from .OpenEORootItem import OpenEORootItem


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
        return QgsDataProvider.Net  # dont understand that yet

    def createDataItem(self, path, parentItem):
        if not parentItem:
            self.root_item = OpenEORootItem(plugin=self.plugin)
            return self.root_item
        else:
            return None
