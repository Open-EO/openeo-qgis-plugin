from urllib.parse import quote
from ...utils.wmts import WebMapTileService
from ...utils.logging import warning

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import Qgis, QgsLayerItem, QgsDataItem, QgsMimeDataUtils, QgsMapLayerFactory

class OpenEOCollectionLayerItem(QgsLayerItem):
    def __init__(self, parent, collection, plugin):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param collection: dict containing relevant infos about the collection.
        :type url: dict
        """

        QgsLayerItem.__init__(
            self,
            parent = parent,
            name = collection.get("title") or collection.get("id"),
            path = None,
            uri = "",
            layerType = Qgis.BrowserLayerType.Raster,
            providerKey = "wms"
        )
        self.collection = collection
        self.plugin = plugin
        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def createUri(self, link):
        title = link.get("title") or ""
        rel = link.get("rel") or ""

        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(self.mapLayerType())
        uri.providerKey = self.providerKey()
        uri.name = self.layerName()
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"
        uri.supportedFormats = self.supportedFormats() # todo: do we need to set this more specifically?
        uri.supportedCrs = self.supportedCrs() # todo: set more specific supportedCrs below

        # different map service formats
        if rel == "xyz":
            uri.uri = f"type=xyz&url={link["href"]}/"+quote("{z}/{y}/{x}")
            return uri
        elif rel == "wmts":
            wmtsUrl = link["href"]+"?service=wmts&request=getCapabilities"
            wmts = WebMapTileService(wmtsUrl)
            targetCRS = "EPSG::3857"
            
            tileMatrixSet = None
            for tms_id, tms in list(wmts.tilematrixsets.items()):
                if targetCRS in tms.crs: 
                    tileMatrixSet = tms_id
                    break
            layerID = None
            layerID = list(wmts.contents)[0]
            styleID = wmts.contents[layerID].styles

            #TODO: determine more URI parameters programmatically
            uri.uri = f"crs=EPSG:3857&styles=default&tilePixelRatio=0&format=image/png&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={link["href"]}"
            return uri
        else:
            return None

    def getConnection(self):
        return self.parent().getConnection()

    def mimeUris(self):
        mimeUris = []

        webMapLinks = self.parent().getWebMapLinks(self.collection)
        if len(webMapLinks) == 0:
            warning(self.plugin.iface, "Could not detect a layer from the given source.")
            return mimeUris

        QApplication.setOverrideCursor(Qt.BusyCursor)

        #TODO: what if operation takes way too long?
        for link in webMapLinks:
            try:
                mimeUri = self.createUri(link)
                mimeUris.append(mimeUri)
            except Exception as e:
                print(e)
                warning(
                    self.plugin.iface,
                    f"Loading the map service {webMapLinks['href']} failed."
                )
        
        QApplication.restoreOverrideCursor()

        return mimeUris
         
    
    #try just returning the new uri through mimeuri
    
    def actions(self, parent):
        return []


