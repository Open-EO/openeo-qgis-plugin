import requests
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import urljoin

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
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

from ..directory_dialog import DirectoryDialog
from ...utils.downloadTask import DownloadAssetTask


class OpenEOStacAssetItem(QgsDataItem):
    def __init__(self, assetDict, key, parent, plugin, stac_url=None):
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
            type=Qgis.BrowserItemType.Custom,
            parent=parent,
            name=assetDict.get("title", key),
            path=None,
            providerKey=plugin.PLUGIN_ENTRY_NAME,
        )

        self.asset = assetDict
        self.baseurl = stac_url
        self.key = key
        self.plugin = plugin
        self.uris = None  # initialise
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
        uriString = ""

        if (
            "image/tiff; application=geotiff" in self.asset.get("type", "")
        ) or ("image/vnd.stac.geotiff" in self.asset.get("type", "")):
            uri.layerType = QgsMapLayerFactory.typeToString(
                Qgis.LayerType.Raster
            )
            uri.providerKey = "gdal"
            uri.name = self.layerName()
            uri.supportedFormats = self.supportedFormats()
            uri.supportedCrs = self.supportedCrs()

            # create the uri string
            href = self.resolveUrl()
            if href.startswith("http") or href.startswith("ftp"):
                uriString = f"/vsicurl/{href}"
                # if len(authcfg) > 0:
                #    uriString += f" authcfg='{authcfg}'"
            elif href.startswith("s3://"):
                uriString = f"/vsis3/{href[5:]}"
            else:
                uriString = href
            uri.uri = uriString

        if (
            ("application/x+netcdf" in self.asset.get("type", ""))
            or ("application/x-netcdf" in self.asset.get("type", ""))
            or ("application/netcdf" in self.asset.get("type", ""))
        ):
            # this assumes Raster layer
            uri.providerKey = "gdal"
            uri.supportedFormats = self.supportedFormats()
            uri.supportedCrs = self.supportedCrs()
            href = self.resolveUrl()
            if href.startswith("http") or href.startswith("ftp"):
                uriString = f"/vsicurl/{href}"
            elif href.startswith("s3://"):
                uriString = f"/vsis3/{href[5:]}"
            else:
                uriString = href
            uri.uri = uriString

        return [uri]

    def hasDragEnabled(self):
        return self.producesValidLayer()

    def layerName(self):
        return self.name()

    def supportedFormats(self):
        return []  # TODO: determine more closely from capabilities

    def supportedCrs(self):
        supportedCrs = (
            self.asset.get("proj:epsg")
            or self.asset.get("epsg")
            or self.asset.get("crs")
            or "3857"
        )
        if type(supportedCrs) is int:
            supportedCrs = f"EPSG:{supportedCrs}"
        return [supportedCrs]  # TODO: not fully reliable

    def getLayerType(self):
        mediaType = self.asset.get("type", "")
        mediaType = mediaType.lower()
        mediaTypes = {
            "image/tiff; application=geotiff": Qgis.LayerType.Raster,
            "image/tiff; application=geotiff; profile=cloud-optimized": Qgis.LayerType.Raster,
            "application/geo+json": Qgis.LayerType.Vector,
            "application/netcdf": Qgis.LayerType.Raster,
            "application/x+netcdf": Qgis.LayerType.Raster,
            "application/x-netcdf": Qgis.LayerType.Raster,
        }
        if mediaType in mediaTypes:
            return mediaTypes[mediaType]
        return None

    def producesValidLayer(self):
        validLayer = False
        layerType = self.getLayerType()
        validLayerTypes = {
            QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster),
            QgsMapLayerFactory.typeToString(Qgis.LayerType.Vector),
        }
        if layerType is not None:
            validLayer = (
                QgsMapLayerFactory.typeToString(layerType) in validLayerTypes
            )
        return validLayer

    def createLayer(self, addToProject=True):
        if not addToProject:
            addToProject = True  # This is necessary for when the method is given as a callable
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
                uri.providerKey,
            )
            if addToProject:
                project = QgsProject.instance()
                project.addMapLayer(layer)
            return layer
        else:
            self.plugin.logging.warning(
                "The file format is not supported by the plugin."
            )
        return None

    def resolveUrl(self):
        href = self.asset.get("href")
        if (
            self.baseurl and href and bool(urlparse(href).netloc)
        ):  # if relative URL
            return urljoin(self.baseurl, href)
        return href

    def download(self):
        path = self.downloadFolder()
        self.queueDownloadTask(path)

    def downloadAsset(self, dir=None):
        href = self.resolveUrl()

        if not href:
            raise ValueError(
                "Asset is missing 'href' and cannot be downloaded."
            )

        dir = Path(dir) if dir else self.downloadFolder()

        local = self.asset.get("file:local_path")
        if local:
            path = dir / local
        else:
            remote_path = Path(urlparse(href).path)
            path = dir / remote_path.name

        path.parent.mkdir(parents=True, exist_ok=True)

        # check if file exists and append a number if it does
        filename = path.stem
        i = 2
        while path.exists():
            path = path.with_stem(f"{filename}_({i})")
            i += 1

        # stream data to file
        with requests.get(href, stream=True) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(
                    chunk_size=10 * 1024 * 1024
                ):  # 10 MB chunk size
                    f.write(chunk)

        return path

    def downloadFolder(self):
        return Path.home() / "Downloads"

    def downloadTo(self):
        downloadPath = self.downloadFolder()

        # prepare file dialog
        dlg = DirectoryDialog()
        dlg.setDirectory(str(downloadPath))

        # get directory to download to
        dir = dlg.selectDirectory()
        if not dir:
            return

        self.queueDownloadTask(dir)

    def queueDownloadTask(self, dir, openDestination=True):
        # Store references for signal handlers
        plugin = self.plugin
        assetName = self.name()

        # Create custom task with signals
        downloadTask = DownloadAssetTask(
            f"Download Asset: {assetName}", self.downloadAsset, dir
        )

        # Connect signals to slots that can safely interact with GUI
        def on_download_complete():
            plugin.logging.success(
                f"Finished downloading asset {assetName} to {dir}."
            )
            if openDestination:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(dir)))

        def on_download_error():
            plugin.logging.error(
                f"Can't download the asset {assetName} to {dir}.",
                error=downloadTask.exception,
            )

        # Connect task finished signal based on success/failure
        downloadTask.taskCompleted.connect(on_download_complete)
        downloadTask.taskTerminated.connect(on_download_error)

        # Add task to manager
        taskManager = QgsApplication.taskManager()
        taskManager.addTask(downloadTask)
        plugin.logging.info(f"Downloading: {assetName}")

    def debug(self):
        breakpoint()

    def actions(self, parent):
        actions = []

        if self.producesValidLayer():
            action_add_to_project = QAction(
                QIcon(), "Add Layer to Project", parent
            )
            action_add_to_project.triggered.connect(self.createLayer)
            actions.append(action_add_to_project)

        action_download = QAction(QIcon(), "Download", parent)
        action_download.triggered.connect(self.download)
        actions.append(action_download)

        action_downloadTo = QAction(QIcon(), "Download to...", parent)
        action_downloadTo.triggered.connect(self.downloadTo)
        actions.append(action_downloadTo)

        debug = QAction(QIcon(), "debug", parent)
        debug.triggered.connect(self.debug)
        actions.append(debug)

        return actions
