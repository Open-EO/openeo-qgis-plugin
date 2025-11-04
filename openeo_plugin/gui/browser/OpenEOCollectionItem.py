from qgis.core import QgsDataCollectionItem
from qgis.core import QgsDataItem

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
        QgsDataCollectionItem.__init__(
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

