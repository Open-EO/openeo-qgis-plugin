import requests
from pathlib import Path
from urllib.parse import urlparse, urljoin

from qgis.PyQt.QtWidgets import QAction, QApplication
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

from .util import getSeparator
from ...utils.filetypes import MEDIATYPES, EXTENSIONS
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
        self.uris = None
        self.fileType = None
        self.layerType = None

        self._init()

    def _init(self):
        self.fileType = self.detectFileType()
        if self.fileType:
            self.layerType = self.fileType.get("layer")

        if self.layerType is not None:
            icon = QgsIconUtils.iconForLayerType(self.layerType)
            self.setIcon(icon)
        else:
            self.setIcon(QgsApplication.getThemeIcon("mIconFile.svg"))

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def detectFileType(self):
        mediaType = self.asset.get("type", "").lower()
        if mediaType in MEDIATYPES:
            return MEDIATYPES[mediaType]

        href = self.asset.get("href", "")
        url = urlparse(href)
        path = Path(url.path)
        ext = path.suffix.lower().lstrip(".")
        if ext in EXTENSIONS:
            return EXTENSIONS[ext]

    def mimeUris(self):
        if self.uris is not None:
            return self.uris

        if self.fileType is None:
            return [None]

        uri = QgsMimeDataUtils.Uri()
        layerType = self.fileType.get("layer")
        uri.providerKey = self.fileType["engine"]
        if layerType:
            uri.layerType = QgsMapLayerFactory.typeToString(layerType)
        uri.name = self.layerName()
        uri.supportedFormats = self.supportedFormats()
        if self.fileType.get("crs", True):
            uri.supportedCrs = self.supportedCrs()

        if self.fileType.get("download", False):
            url = self.downloadAsset().as_uri()
        else:
            url = self.resolveUrl()
            scheme = urlparse(url).scheme
            if scheme == "http" or scheme == "https" or scheme == "ftp":
                url = f"/vsicurl/{url}"
            elif scheme == "s3":
                url = f"/vsis3/{url[5:]}"  # remove 's3://'

        if self.fileType.get("vsi"):
            url = f"{self.fileType['vsi']}{url}"

        uri.uri = url

        return [uri]

    def hasDragEnabled(self):
        return self.producesValidLayer()

    def layerName(self):
        return self.name()

    def supportedFormats(self):
        if self.fileType:
            format = self.fileType.get("format")
            if format:
                return [format]
        return []

    def getStac(self):
        return self.parent().results or None

    def supportedCrs(self):
        stac = self.getStac()
        candidates = [
            self.asset.get("proj:code"),
            self.asset.get("proj:epsg"),
            self.fileType.get("crs"),
        ]
        if stac:
            properties = stac.get("properties", {})
            candidates.append(properties.get("proj:code"))
            candidates.append(properties.get("proj:epsg"))

        supportedCrs = next(
            (crs for crs in candidates if crs is not None), None
        )
        if type(supportedCrs) is int:
            supportedCrs = f"EPSG:{supportedCrs}"

        return [supportedCrs]

    def producesValidLayer(self):
        validLayerTypes = {
            Qgis.LayerType.Raster,
            Qgis.LayerType.Vector,
        }
        return self.layerType in validLayerTypes

    def createLayer(self, addToProject=True):
        if addToProject is None:
            addToProject = True  # when the method is passed as a callable
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

    def actions(self, parent):
        actions = []

        if self.producesValidLayer():
            action_add_to_project = QAction(
                QgsApplication.getThemeIcon("mActionAddLayer.svg"),
                "Add Layer to Project",
                parent,
            )
            action_add_to_project.triggered.connect(self.createLayer)
            actions.append(action_add_to_project)

        action_download = QAction(
            QgsApplication.getThemeIcon("downloading_svg.svg"),
            "Download",
            parent,
        )
        action_download.triggered.connect(self.download)
        actions.append(action_download)

        action_downloadTo = QAction(
            QgsApplication.getThemeIcon("downloading_svg.svg"),
            "Download to...",
            parent,
        )
        action_downloadTo.triggered.connect(self.downloadTo)
        actions.append(action_downloadTo)

        actions.append(getSeparator(parent))

        action_copy_url = QAction(
            QgsApplication.getThemeIcon("mActionEditCopy.svg"),
            "Copy URL",
            parent,
        )
        action_copy_url.triggered.connect(self.copyUrlToClipboard)
        actions.append(action_copy_url)

        return actions

    # Method to copy URL to clipboard
    def copyUrlToClipboard(self):
        url = self.resolveUrl()
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        self.plugin.logging.success("Copied URL to clipboard")
