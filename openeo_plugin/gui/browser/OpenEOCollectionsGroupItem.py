# -*- coding: utf-8 -*-
import sip

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsDataCollectionItem
from qgis.core import QgsApplication

from .util import getSeparator
from .OpenEOCollectionItem import OpenEOCollectionItem


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
        QgsDataCollectionItem.__init__(
            self, parent, "Collections", plugin.PLUGIN_ENTRY_NAME
        )
        self.plugin = plugin
        self.showTitles = True
        self.setIcon(QgsApplication.getThemeIcon("mIconFolder.svg"))

    def getCollections(self):
        try:
            collections = self.getConnection().list_collections()
            return collections
        except Exception as e:
            self.plugin.logging.error(
                "Can't load list of collections.", error=e
            )
        return []

    def refresh(self):
        self.depopulate()
        super().refresh()

    def createChildren(self):
        items = []
        collections = self.getCollections()
        for collection in collections:
            # determine whether collectionItem or LayerItem
            item = OpenEOCollectionItem(
                parent=self,
                collection=collection,
                plugin=self.plugin,
            )
            sip.transferto(item, self)
            items.append(item)
        return items

    def getConnection(self):
        return self.parent().getConnection()

    def actions(self, parent):
        actions = []

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        actions.append(getSeparator(parent))

        action_name = QAction(
            QgsApplication.getThemeIcon(
                "algorithms/mAlgorithmCheckGeometry.svg"
            )
            if self.showTitles
            else QIcon(),
            "Show titles",
            parent,
        )
        action_name.triggered.connect(self.toggleShowTitles)
        actions.append(action_name)

        return actions

    def toggleShowTitles(self):
        self.showTitles = not self.showTitles
        self.refresh()
