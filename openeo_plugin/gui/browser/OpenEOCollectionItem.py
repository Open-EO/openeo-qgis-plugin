from qgis.core import Qgis
from qgis.core import QgsLayerItem
from qgis.core import QgsDataItem


#TODO: the type this inherits is still to be debated.
class OpenEOCollectionItem(QgsLayerItem):
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
            uri = None,
            layerType = Qgis.BrowserLayerType.NoType,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )
        self.collection = collection
        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def getConnection(self):
        return self.parent().getConnection()