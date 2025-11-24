from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsDataItem
from qgis.core import Qgis
from qgis.core import QgsIconUtils
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import QgsRasterLayer
#from qgis.core import QgsStacController

from ...utils.logging import warning


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
        #TODO: might be worth using a QgsStacAsset to ensure type safety
        # problem. Those are only introduced with 3.44
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
        #self.stacController = QgsStacController()
        self.uris = None #initialise
        self.uris = self.mimeUris()
        self.validLayer = None

        self.setIcon(QgsIconUtils.iconRaster())
        self.producesValidLayer()
        self.populate()

    def mimeUris(self):
        if self.uris is not None:
            return self.uris
        
        uri = QgsMimeDataUtils.Uri() 

        #TODO: support for other types needed? like jpeg?
        if (("image/tiff; application=geotiff" in self.asset.get("type", "")) or
            ("image/vnd.stac.geotiff" in self.asset.get("type", ""))):
            uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
            uri.providerKey = "gdal"
            uri.name = self.layerName()
            uri.supportedFormats = self.supportedFormats()
            uri.supportedCrs = self.supportedCrs()
            
            # create the uri string
            uriString = ""
            href = self.asset.get("href", "")
            #authcfg = self.stacController.authCfg()
            if href.startswith("http") or href.startswith("ftp"):
                uriString = f"/vsicurl/{href}"
                #if len(authcfg) > 0:
                #    uriString += f" authcfg='{authcfg}'"
            elif href.startswith("s3://"):
                uriString = f"/vsis3/{href[5:]}"
            else:
                uriString = href
            uri.uri = uriString

        # QGIS' STAC implementation also has more cases for pointclouds here.
        # I am not sure if these are needed

        return [uri]

    def hasDragEnabled(self):
        return self.producesValidLayer()
    
    def layerName(self):
        return self.name()
    
    def supportedFormats(self):
        return [] #TODO: determine more closely from capabilities

    def supportedCrs(self):
        supportedCrs = self.asset.get("proj:epsg") or self.asset.get("epsg") or self.asset.get("crs") or "3857"
        if type(supportedCrs) is int:
            supportedCrs = f"EPSG:{supportedCrs}"
        return [supportedCrs] #TODO: not fully reliable
    
    def addLayerToProject(self, uri):
        if uri.layerType == QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster):
            self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)
        elif uri.layerType == QgsMapLayerFactory.typeToString(Qgis.LayerType.Vector):
            pass #TODO: implement once vector mimetypes are introduced

    def addToProject(self):
        if self.producesValidLayer():
            uris = self.mimeUris()
            uri = uris[0]
            self.addLayerToProject(uri)
        else:
            warning(self.plugin.iface, "The file format is not supported by the plugin")

    def producesValidLayer(self):
        if self.validLayer == None:
            mediaType = self.asset.get("type", "")
            valid_media_types = {
                "image/tiff; application=geotiff",
                "image/tiff; application=geotiff; profile=cloud-optimized",
                "application/geo+json",
                "application/netcdf",
                "application/x+netcdf"
            }
            self.validLayer = mediaType.lower() in valid_media_types
        return self.validLayer
    
    def actions(self, parent):
        actions = []

        if self.producesValidLayer():
            action_add_to_project = QAction(QIcon(), "Add Layer to Project", parent)
            action_add_to_project.triggered.connect(self.addToProject)
            actions.append(action_add_to_project)

        return actions