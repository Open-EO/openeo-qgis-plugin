import requests
import pathlib
from pathlib import Path
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl

from qgis.core import QgsDataItem
from qgis.core import Qgis
from qgis.core import QgsProject
from qgis.core import QgsIconUtils
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import QgsCoordinateTransformContext
from qgis.core import QgsApplication

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
        self.uris = None #initialise
        self.uris = self.mimeUris()

        layerType = self.getLayerType()
        if layerType: 
            icon = QgsIconUtils.iconForLayerType(layerType)
            self.setIcon(icon)
        else:
            self.setIcon(QgsApplication.getThemeIcon("mIconFile.svg"))
        
        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

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
    
    def getLayerType(self):
        mediaType = self.asset.get("type", "")
        mediaType = mediaType.lower()
        mediaTypes = {
            "image/tiff; application=geotiff": Qgis.LayerType.Raster,
            "image/tiff; application=geotiff; profile=cloud-optimized": Qgis.LayerType.Raster,
            "application/geo+json": Qgis.LayerType.Vector,
            "application/netcdf": Qgis.LayerType.Raster,
            "application/x+netcdf": Qgis.LayerType.Raster
        }
        if mediaType in mediaTypes:
            return mediaTypes[mediaType]
        return None

    def producesValidLayer(self):
        validLayer = False
        layerType = self.getLayerType()
        validLayerTypes = {
            QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster),
            QgsMapLayerFactory.typeToString(Qgis.LayerType.Vector)
        }
        if layerType != None:
            validLayer = QgsMapLayerFactory.typeToString(layerType) in validLayerTypes
        return validLayer
    
    def createLayer(self, addToProject=True):
        if not addToProject:
            addToProject = True #This is necessary for when the method is given as a callable
        if self.producesValidLayer():
            uris = self.mimeUris()
            uri = uris[0]
            layerOptions = QgsMapLayerFactory.LayerOptions(
                transformContext=QgsCoordinateTransformContext()
            )
            layer = QgsMapLayerFactory.createLayer(
                uri.uri, 
                uri.name, 
                QgsMapLayerFactory.typeFromString(uri.layerType)[0],
                layerOptions, 
                uri.providerKey
            )
            if addToProject:
                project = QgsProject.instance()
                project.addMapLayer(layer)
            return layer
        else:
            self.plugin.logging.error("The file format is not supported by the plugin.")
        return None
    
    def downloadAsset(self, dir=None):
        try:
            QApplication.setOverrideCursor(Qt.BusyCursor)
            href = self.asset.get("href")
            if not href:
                self.plugin.logging.error("Asset is missing 'href' and cannot be downloaded.")
                return
            
            r = requests.get(href)
            if not dir:
                path = Path.home() / 'Downloads' / self.name()
            else: 
                path = Path(dir) / self.name()

            #check if file exists and append a number if it does
            filename, extension = os.path.splitext(path)
            i = 1
            while os.path.exists(path):
                path = f"{filename} ({i}){extension}"
                i += 1

            #save file
            with open(path, 'wb') as f:
                f.write(r.content)
            self.plugin.logging.success(f"File saved to {path}")
        except Exception as e:
            self.plugin.logging.error(f"Can't download the asset {href}.", error=e)
        finally:
            QApplication.restoreOverrideCursor()

    def downloadTo(self):
        downloadPath = pathlib.Path.home() / 'Downloads'
        dir = QFileDialog.getExistingDirectory(
            caption="Save Result to...",
            directory=str(downloadPath)
        )
        try:
            self.downloadAsset(dir=dir)
            dirStr = f"file://{str(dir)}"
            QDesktopServices.openUrl(QUrl(dirStr, QUrl.TolerantMode))
        except Exception as e:
            self.plugin.logging.error(f"Can't save asset to directory {dir}.", error=e)
        finally:
            QApplication.restoreOverrideCursor()

    def actions(self, parent):
        actions = []

        if self.producesValidLayer():
            action_add_to_project = QAction(QIcon(), "Add Layer to Project", parent)
            action_add_to_project.triggered.connect(self.createLayer)
            actions.append(action_add_to_project)
        
        action_download = QAction(QIcon(), "Download", parent)
        action_download.triggered.connect(self.downloadAsset)
        actions.append(action_download)

        action_downloadTo = QAction(QIcon(), "Download to...", parent)
        action_downloadTo.triggered.connect(self.downloadTo)
        actions.append(action_downloadTo)

        return actions