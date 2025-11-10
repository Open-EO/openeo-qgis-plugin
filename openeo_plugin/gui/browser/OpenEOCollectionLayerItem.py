from urllib.parse import quote
from ...utils.wmts import WebMapTileService
from ...utils.logging import warning

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import Qgis, QgsLayerItem, QgsDataItem, QgsMimeDataUtils, QgsMapLayerFactory

class OpenEOCollectionLayerItem(QgsDataItem):
    def __init__(self, parent, collection, plugin):
        name = collection.get("title") or collection.get("id")
        QgsDataItem.__init__(
            self,
            type = Qgis.BrowserItemType.Custom,
            parent = parent,
            name = name,
            path = None,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

        self.collection = collection
        self.plugin = plugin

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def icon(self):
        return QgsIconUtils.iconRaster()

    def hasDragEnabled(self):
        return True
    
    def layerName(self):
        return self.name()
    
    def supportedFormats(self):
        return [] #TODO: determine more closely from capabilities
    
    def supportedCrs(self):
        return ["EPSG:3857"] #TODO: determine more closely from capabilities
    
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
        
    
    def mimeUris(self):
        mimeUris = []

        webMapLinks = self.parent().getWebMapLinks(self.collection)
        print(webMapLinks)
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
                    f"Loading the map service {link['href']} failed."
                )
        
        QApplication.restoreOverrideCursor()

        return mimeUris
    
    def addToProject(self):
        for uri in self.mimeUris():
            self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    def actions(self, parent):
        action_add_to_project = QAction(QIcon(), "Add Layer to Project", parent)
        action_add_to_project.triggered.connect(self.addToProject)
        return [action_add_to_project]
        return []