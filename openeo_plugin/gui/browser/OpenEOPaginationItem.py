# -*- coding: utf-8 -*-
import sys

from qgis.core import QgsDataItem
from qgis.core import Qgis


class OpenEOPaginationItem(QgsDataItem):
    """
    QgsDataItem that indicates the availability of more elements within a
    paginated endpoint. Clicking it will add more items.
    """

    def __init__(self, parent, loadedItems=None):
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
            providerKey=parent.plugin.PLUGIN_ENTRY_NAME,
        )
        self.loadedItems = loadedItems
        self.populate()

    def sortKey(self):
        sortBy = self.parent().sortChildrenBy
        if sortBy == "title":
            return "\U0010ffff\U0010ffff\U0010ffff\U0010ffff"  # unicode high-Value
        elif sortBy == "newest":
            return sys.maxsize
        else:  # default or oldest
            return sys.maxsize

    def handleDoubleClick(self):
        self.parent().loadNextItems()
        return True
