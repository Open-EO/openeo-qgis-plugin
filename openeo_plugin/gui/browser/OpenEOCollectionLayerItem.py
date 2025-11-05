from urllib.parse import quote
from owslib.wmts import WebMapTileService

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import Qgis
from qgis.core import QgsLayerItem
from qgis.core import QgsDataItem

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

        webMapLink = parent.getWebMapLinks(collection)[0]
        #uri = self.createUri(webMapLink)
        uri = "placeholder"
        QgsLayerItem.__init__(
            self,
            parent = parent,
            name = collection.get("title") or collection.get("id"),
            path = None,
            uri = uri,
            layerType = Qgis.BrowserLayerType.Raster,
            providerKey = "wms"
        )
        self.collection = collection
        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def createUri(self, webMapLink):
        uri = None
        # different map service formats
        if webMapLink["rel"] == "xyz":
            uri = f"type=xyz&url={webMapLink["href"]}/"+quote("{z}/{y}/{x}") 
            # example
            # uri= "type=xyz&url=https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/"+quote("{z}/{y}/{x}")

        if webMapLink["rel"] == "wmts":
            wmtsUrl = webMapLink["href"]+"?service=wmts&request=getCapabilities"
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
            
            uri = f"crs=EPSG:3857&styles=default&tilePixelRatio=0&format=image/png&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={webMapLink["href"]}"

        return uri

    def getConnection(self):
        return self.parent().getConnection()

    def mimeUris(self):
        #TODO: what if operation takes way too long?
        mimeUri = super().mimeUris()[0]
        
        webMapLink = self.parent().getWebMapLinks(self.collection)[0]
        try:
            # TODO: test on different systems and decide on the following
            # WaitCursor, BusyCursor, DragMoveCursor, DragCopyCursor
            #   DragCopyCursor is whats used by QGIS by default
            #   however, what we chose will also end up being used on right-click add-to-map
            QApplication.setOverrideCursor(Qt.DragCopyCursor)
            self.uri = self.createUri(webMapLink)
        except:
            QApplication.restoreOverrideCursor()
        mimeUri.uri = self.uri

        QApplication.restoreOverrideCursor()
        return [mimeUri]
         
    
    #try just returning the new uri through mimeuri
    
    def actions(self, parent):
        actions = []
        return actions


