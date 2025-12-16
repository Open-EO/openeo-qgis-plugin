from urllib.parse import quote
import tempfile
import webbrowser
import pathlib
import os
import requests
import json

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import QgsApplication

from .util import getSeparator
from ...utils.wmts import WebMapTileService


class OpenEOCollectionItem(QgsDataItem):
    def __init__(self, parent, collection, plugin, preview=False):
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
            providerKey=plugin.PLUGIN_ENTRY_NAME,
        )

        self.collection = collection
        self.plugin = plugin
        self.preview = (
            preview  # whether the collection contains a wmts preview
        )

        self.uris = []

        self.setName(self.name())

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

        if self.preview:
            self.setIcon(QgsIconUtils.iconRaster())
        else:
            self.setIcon(QgsApplication.getThemeIcon("mIconTiledScene.svg"))

    def hasDragEnabled(self):
        return self.preview

    def name(self):
        if self.parent().showTitles:
            return self.collection.get("title") or self.collection.get("id")
        else:
            return self.collection.get("id")

    def layerName(self):
        return self.name()

    def supportedFormats(self):
        return []  # TODO: determine more closely from capabilities

    def supportedCrs(self):
        return ["EPSG:3857"]  # TODO: determine more closely from capabilities

    def getConnection(self):
        return self.parent().getConnection()

    def createUri(self, link):
        title = link.get("title") or ""
        rel = link.get("rel") or ""

        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
        uri.providerKey = "wms"
        uri.name = self.layerName()
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"
        uri.supportedFormats = (
            self.supportedFormats()
        )  # todo: do we need to set this more specifically?
        uri.supportedCrs = (
            self.supportedCrs()
        )  # todo: set more specific supportedCrs below

        # different map service formats
        if rel == "xyz":
            uri.uri = f"type=xyz&url={link['href']}/" + quote("{z}/{y}/{x}")
            return uri
        elif rel == "wmts":
            wmtsUrl = link["href"] + "?service=wmts&request=getCapabilities"
            wmts = WebMapTileService(wmtsUrl)
            targetCRS = "EPSG::3857"

            tileMatrixSet = None
            for tms_id, tms in list(wmts.tilematrixsets.items()):
                if targetCRS in tms.crs:
                    tileMatrixSet = tms_id
                    break
            layerID = link.get("wmts:layer", list(wmts.contents)[0])

            # Determine style and format from WMTS layer metadata
            layer = wmts[layerID]
            
            # Get default style or first available style
            style = "default"
            if layer.styles:
                for style_id, style_info in layer.styles.items():
                    if style_info.get("isDefault", False):
                        style = style_id
                        break
                else:
                    # If no default style found, use the first one
                    style = list(layer.styles.keys())[0]
            
            # Get first available format or fallback to image/png
            format = "image/png"
            if layer.formats:
                format = layer.formats[0]

            uri.uri = f"crs=EPSG:3857&styles={style}&tilePixelRatio=0&format={format}&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={link['href']}"
            return uri
        else:
            return None

    def mimeUris(self):
        if not self.preview:
            return []

        # see if uri has already been created
        # TODO: in the current state this only supports single URIs, should not be an issue for the used types.
        if len(self.uris) != 0:
            return self.uris

        mimeUris = []

        webMapLinks = self.parent().getWebMapLinks(self.collection)
        if len(webMapLinks) == 0:
            self.plugin.logging.warning(
                "The collection does not provide any web map services for preview."
            )
            return mimeUris

        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        # TODO: what if operation takes way too long?
        for link in webMapLinks:
            try:
                mimeUri = self.createUri(link)
                mimeUris.append(mimeUri)
            except Exception as e:
                self.plugin.logging.error(
                    f"Can't visualize the mapping service {link['href']} for collection {self.collection['id']}.",
                    error=e,
                )

        QApplication.restoreOverrideCursor()

        self.uris = mimeUris

        return mimeUris

    def addToProject(self):
        if not self.preview:
            return

        uris = self.mimeUris()
        uri = uris[0]
        self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    def get_url(self, key):
        collection_link = None
        links = self.collection["links"]
        for link in links:
            if link["rel"] == key:
                collection_link = link["href"]
                break
        if collection_link is None:
            collection_link = self.getConnection().build_url(
                f"/collections/{self.collection['id']}"
            )
        return collection_link

    def viewProperties(self):
        collection_link = self.get_url("key")
        collection_json = requests.get(collection_link).json()
        collection_json = json.dumps(collection_json)

        filePath = pathlib.Path(__file__).parent.resolve()
        with open(
            os.path.join(filePath, "..", "collectionProperties.html")
        ) as file:
            collectionInfoHTML = file.read()
        collectionInfoHTML = collectionInfoHTML.replace(
            "{{ json }}", collection_json
        )

        fh, path = tempfile.mkstemp(suffix=".html")
        url = "file://" + path
        with open(path, "w") as fp:
            fp.write(collectionInfoHTML)
        webbrowser.open_new(url)

    def actions(self, parent):
        actions = []

        if self.preview:
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
