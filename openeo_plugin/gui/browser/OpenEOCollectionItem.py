from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis
from qgis.core import QgsLayerItem
from qgis.core import QgsDataCollectionItem
from qgis.core import QgsDataItem

from urllib.parse import urlencode, unquote, quote
from owslib.wmts import WebMapTileService


class OpenEOCollectionItem(QgsDataCollectionItem):
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
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )
        self.collection = collection
        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def getConnection(self):
        return self.parent().getConnection()
    
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
        uri = None

        webMapLink = parent.getWebMapLinks(collection)[0]
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

            
            
            uri = f"crs=EPSG:3857&styles=default&tilePixelRatio=0&format=image/png&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={webMapLink["href"]}"


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

    def getConnection(self):
        return self.parent().getConnection()
    
    def getMime(self):
        # mimeUri is deprecated.
        print(self.mimeUri())
    
    def actions(self, parent):
        action_mime = QAction(QIcon(), "get mime uri", parent)
        action_mime.triggered.connect(self.getMime)
        actions = [action_mime]
        return actions



