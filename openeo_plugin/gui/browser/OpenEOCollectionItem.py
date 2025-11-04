from qgis.core import Qgis
from qgis.core import QgsLayerItem
from qgis.core import QgsDataCollectionItem
from qgis.core import QgsDataItem

from urllib.parse import urlencode, unquote, quote


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

        webMapLink = self.parent().getWebMapLinks(collection)[0]
        # different map service formats
        if webMapLink["rel"] == "xyz":
            uri = f"type=xyz&url={webMapLink["href"]}/"+quote("{z}/{y}/{x}") 
            # example
            # uri= "type=xyz&url=https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/"+quote("{z}/{y}/{x}")

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