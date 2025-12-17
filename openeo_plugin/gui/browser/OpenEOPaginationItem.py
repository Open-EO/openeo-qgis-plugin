# -*- coding: utf-8 -*-
from qgis.core import QgsDataItem
from qgis.core import Qgis


class OpenEOPaginationItem(QgsDataItem):
    """
    QgsDataItem that indicates the availability of more elements within a
    paginated endpoint. Clicking it will add more items.
    """

    def __init__(self, plugin, parent, loadedItems=None):
        """Constructor.

        :param plugin: Reference to the qgis plugin object.
        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataCollectionItem
        """
        QgsDataItem.__init__(
            self,
            type=Qgis.BrowserItemType.Error,
            parent=parent,
            name="... Double Click to Load more Items",
            path=None,
            providerKey=plugin.PLUGIN_ENTRY_NAME,
        )
        self.loadedItems = loadedItems
        self.populate()

    def setLoadedItems(self, int):
        self.loadedItems = int

    def sortKey(self):
        return self.loadedItems

    def handleDoubleClick(self):
        self.parent().loadNextItems()
        return True
