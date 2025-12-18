from urllib.parse import quote
import requests

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import QgsApplication

from .util import getSeparator, showInBrowser
from ...utils.wmts import WebMapTileService


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
                # case "3d-tiles":
                #     webMapLinks.append(link)
                # case "wms":
                #     webMapLinks.append(link)
                # case "pmtiles":
                #     webMapLinks.append(link)
                # case "tilejson":
                #     webMapLinks.append(link)

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

    def createBaseUri(self, link):
        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
        uri.providerKey = "wms"
        # todo: do we need to set this more specifically?
        uri.supportedFormats = []
        uri.supportedCrs = []

        uri.name = self.layerName()
        title = link.get("title") or ""
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"

        return uri

    def createXYZ(self, link):
        uri = self.createBaseUri(link)
        uri.supportedCrs = ["EPSG:3857"]
        uri.uri = f"type=xyz&url={link['href']}/" + quote("{z}/{y}/{x}")
        return uri

    def createWMTS(self, link):
        # todo: Currently only supports KVP encoding, not REST
        # todo: does not support wmts:dimensions
        wmtsUrl = link["href"] + "?service=wmts&request=getCapabilities"
        wmts = WebMapTileService(wmtsUrl)

        layers = link.get("wmts:layer")
        if layers:
            if isinstance(layers, str):
                layers = [layers]
            else:
                layers = list(layers)
        else:
            layers = list(wmts.contents)

        mediaType = link.get("type")
        style = None
        tileMatrixSet = None
        crs = None

        uris = []
        for layer in layers:
            uri = self.createBaseUri(link)

            # Get layer info from WMTS capabilities
            lyr = wmts.contents.get(layer)
            if lyr:
                if not mediaType and hasattr(lyr, "formats") and lyr.formats:
                    mediaType = lyr.formats[0]

                if hasattr(lyr, "styles") and lyr.styles:
                    style = (
                        list(lyr.styles.keys())[0]
                        if isinstance(lyr.styles, dict)
                        else lyr.styles[0]
                    )

                if hasattr(lyr, "tilematrixsets") and lyr.tilematrixsets:
                    tileMatrixSet = list(lyr.tilematrixsets)[0]
                    tms = wmts.tilematrixsets.get(tileMatrixSet)
                    if tms and hasattr(tms, "crs"):
                        crs = tms.crs

            # Fallback if no tileMatrixSet found
            if not tileMatrixSet:
                tileMatrixSet = "EPSG:3857"
            if not crs:
                crs = "EPSG:3857"
            if not mediaType:
                mediaType = "image/png"
            if not style:
                style = "default"

            uri.uri = f"crs={crs}&styles={style}&tilePixelRatio=0&format={mediaType}&layers={layer}&tileMatrixSet={tileMatrixSet}&url={link['href']}"
            uris.append(uri)

        return uris

    def createUris(self, link):
        uris = []
        rel = link.get("rel") or ""
        if rel == "xyz":
            uris.append(self.createXYZ(link))
        elif rel == "wmts":
            uris.extend(self.createWMTS(link))

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
