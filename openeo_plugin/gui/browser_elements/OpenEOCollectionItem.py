from qgis.core import Qgis
from qgis.core import QgsLayerItem


#TODO: the type this inherits is still to be debated.
class OpenEOCollectionItem(QgsLayerItem):
    def __init__(self, parent, collection_object, plugin):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param collection_object: dict containing relevant infos about the collection.
        :type url: dict
        """
        self.collection = collection_object
        QgsLayerItem.__init__(
            self,
            parent = parent,
            name = self.collection["title"],
            path = None,
            uri = None,
            layerType = Qgis.BrowserLayerType.NoType,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

    def getConnection(self):
        return self.parent().getConnection()