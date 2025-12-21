import requests

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsApplication

from .util import getSeparator, showInBrowser
from ...utils.TileMapServiceMimeUtils import (
    TileMapServiceMimeUtils as TMSMimeUtils,
    WMTSLink,
)


class OpenEOCollectionItem(QgsDataItem):
    def __init__(self, parent, collection):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param collection: dict containing relevant infos about the collection.
        :type url: dict
        """
        QgsDataItem.__init__(
            self,
            type=Qgis.BrowserItemType.Custom,
            name=None,
            parent=parent,
            path=None,
            providerKey=parent.plugin.PLUGIN_ENTRY_NAME,
        )

        self.collection = collection
        self.plugin = parent.plugin
        self.uris = []

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

        self._init()

    def _init(self):
        self.setName(self.name())

        self.links = self.getWebMapLinks()

        self.setIcon(
            QgsIconUtils.iconRaster()
            if self.hasPreview()
            else QgsApplication.getThemeIcon("mIconTiledScene.svg")
        )

    def getWebMapLinks(self):
        """
        helper-function that determines whether or not a collection of this
        connection contains a web-map-link
        """
        webMapLinks = []
        links = self.collection["links"]
        for link in links:
            match link["rel"]:
                case "wmts":
                    webMapLinks.append(link)
                case "xyz":
                    webMapLinks.append(link)

        return webMapLinks

    def hasPreview(self):
        return len(self.links) > 0

    def hasDragEnabled(self):
        return self.hasPreview()

    def name(self):
        if self.parent().showTitles:
            return self.collection.get("title") or self.collection.get("id")
        else:
            return self.collection.get("id")

    def layerName(self):
        return self.name()

    def supportedFormats(self):
        return []

    def supportedCrs(self):
        return []

    def getConnection(self):
        return self.parent().getConnection()

    def createUris(self, linkDict):
        uris = []
        link = WMTSLink.from_dict(linkDict)
        if link.rel == "xyz":
            uris.append(TMSMimeUtils.createXYZ(link, self.layerName()))
        elif link.rel == "wmts":
            uris.extend(TMSMimeUtils.createWMTS(link, self.layerName()))

        return uris

    def mimeUris(self):
        if not self.hasPreview() or len(self.uris) > 0:
            return self.uris

        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        for link in self.links:
            try:
                uris = self.createUris(link)
                self.uris.extend(uris)
            except Exception as e:
                self.plugin.logging.error(
                    f"Can't visualize the mapping service {link['href']} for collection {self.collection['id']}.",
                    error=e,
                )

        QApplication.restoreOverrideCursor()

        return self.uris

    def addToProject(self):
        if not self.hasPreview():
            return

        uris = self.mimeUris()
        uri = uris[0]
        self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    def get_url(self, key):
        links = self.collection["links"]
        for link in links:
            if link["rel"] == key:
                return link["href"]

        return self.getConnection().build_url(
            f"/collections/{self.collection['id']}"
        )

    def viewProperties(self):
        collection_link = self.get_url("self")
        collection = requests.get(collection_link).json()
        showInBrowser("collectionProperties", {"collection": collection})

    def actions(self, parent):
        actions = []

        if self.hasPreview():
            action_add_to_project = QAction(
                QgsApplication.getThemeIcon("mActionAddLayer.svg"),
                "Add Layer to Project",
                parent,
            )
            action_add_to_project.triggered.connect(self.addToProject)
            actions.append(action_add_to_project)

            actions.append(getSeparator(parent))

        action_properties = QAction(
            QgsApplication.getThemeIcon("propertyicons/metadata.svg"),
            "Details",
            parent,
        )
        action_properties.triggered.connect(self.viewProperties)
        actions.append(action_properties)

        return actions
