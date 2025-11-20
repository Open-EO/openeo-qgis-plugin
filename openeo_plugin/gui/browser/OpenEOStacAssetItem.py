
from qgis.core import QgsDataItem
from qgis.core import Qgis
from qgis.core import QgsIconUtils

class OpenEOStacAssetItem(QgsDataItem):
    def __init__(self, assetDict, parent, plugin):
        """Constructor.
        :param assetDict: a dict representing a STAC asset according to stac specifications
        :type assetDict: dict
        
        :param parent: the parent DataItem. expected to be an OpenEOJobItem.
        :type parent: OpenEOJobItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param job: dict containing relevant infos about the batch job that is created.
        :type url: dict
        """
        #TODO: might be worth using a QgsStacAsset to ensure type safetys
        print(assetDict)
        QgsDataItem.__init__(
            self,
            type = Qgis.BrowserItemType.Custom,
            parent = parent,
            name = assetDict.get("title", "asset"),
            path = None,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

        self.asset = assetDict
        self.plugin = plugin

        self.setIcon(QgsIconUtils.iconRaster())
        self.populate()

    def hasDragEnabled(self):
        return True
    
    def layerName(self):
        return self.name()
    
    def supportedFormats(self):
        return [] #TODO: determine more closely from capabilities
    
    def supportedCrs(self):
        return ["EPSG:3857"] #TODO: determine more closely from capabilities