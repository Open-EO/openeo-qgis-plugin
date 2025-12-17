# -*- coding: utf-8 -*-
from collections.abc import Iterable
import dateutil.parser

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication, QAction

from qgis.core import (
    Qgis,
    QgsDataItem,
    QgsMimeDataUtils,
    QgsMapLayerFactory,
    QgsApplication,
)

from .util import getSeparator, showLogs, showInBrowser
from ...utils.wmts import WebMapTileService


class OpenEOServiceItem(QgsDataItem):
    def __init__(self, parent, service, index):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param service: dict containing relevant infos about the openEO web service that is created.
        :type url: dict
        """

        name = service.get("title") or service.get("id")
        QgsDataItem.__init__(
            self,
            type=Qgis.BrowserItemType.Custom,
            parent=parent,
            name=name,
            path=None,
            providerKey=parent.plugin.PLUGIN_ENTRY_NAME,
        )

        self.setIcon(QgsApplication.getThemeIcon("mIconTiledScene.svg"))

        self.service = service
        self.serviceID = self.service["id"]
        self.plugin = parent.plugin
        self.index = index

        self.uris = []

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

        self.updateFromData()

    def refresh(self, children: Iterable[QgsDataItem] | bool = False):
        if children is False:
            self.getService()
            return super().refresh()
        else:
            return super().refresh(children)

    def updateFromData(self):
        name = self.getTitle()
        status = "(enabled) "
        if not self.isEnabled():
            status = "(disabled) "
        self.setName(status + name)

    def sortKey(self):
        sortBy = self.parent().sortChildrenBy
        if sortBy == "title":
            return self.getTitle().lower()
        elif sortBy == "oldest" or sortBy == "newest":
            try:
                created = self.service.get("created", "")
                timestamp = dateutil.parser.isoparse(created).timestamp()
                if sortBy == "newest":
                    timestamp *= -1
                return int(timestamp)
            except Exception:
                return 0
        else:  # default, keep initial backend order
            return self.index

    def hasDragEnabled(self):
        return True

    def layerName(self):
        return self.name()

    def supportedFormats(self):
        return []  # TODO: determine more closely from capabilities

    def supportedCrs(self):
        return ["EPSG:3857"]  # TODO: determine more closely from capabilities

    def getConnection(self):
        return self.parent().getConnection()

    def createBaseUri(self, link):
        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
        uri.providerKey = "wms"
        # todo: do we need to set this more specifically?
        uri.supportedFormats = []
        uri.supportedCrs = []

        uri.name = self.layerName()
        title = link.get("title") or ""
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"

        return uri

    def createXYZ(self, link):
        uri = self.createBaseUri(link)
        uri.supportedCrs = ["EPSG:3857"]
        uri.uri = f"type=xyz&url={link['url']}"
        return uri

    def createWMTS(self, link):
        # todo: Currently only supports KVP encoding, not REST
        # todo: does not support wmts:dimensions
        wmtsUrl = link["url"] + "?service=wmts&request=getCapabilities"
        wmts = WebMapTileService(wmtsUrl)

        layers = link.get("wmts:layer")
        if layers:
            if isinstance(layers, str):
                layers = [layers]
            else:
                layers = list(layers)
        else:
            layers = list(wmts.contents)

        mediaType = link.get("type", "")
        style = None
        tileMatrixSet = None
        crs = None

        uris = []
        for layer in layers:
            uri = self.createBaseUri(link)

            # Get layer info from WMTS capabilities
            lyr = wmts.contents.get(layer)
            if lyr:
                if not mediaType and hasattr(lyr, "formats") and lyr.formats:
                    mediaType = lyr.formats[0]

                if hasattr(lyr, "styles") and lyr.styles:
                    style = (
                        list(lyr.styles.keys())[0]
                        if isinstance(lyr.styles, dict)
                        else lyr.styles[0]
                    )

                if hasattr(lyr, "tilematrixsets") and lyr.tilematrixsets:
                    tileMatrixSet = list(lyr.tilematrixsets)[0]
                    tms = wmts.tilematrixsets.get(tileMatrixSet)
                    if tms and hasattr(tms, "crs"):
                        crs = tms.crs

            # Fallback if no tileMatrixSet found
            if not tileMatrixSet:
                tileMatrixSet = "EPSG:3857"
            if not crs:
                crs = "EPSG:3857"
            if not mediaType:
                mediaType = "image/png"
            if not style:
                style = "default"

            uri.uri = f"crs={crs}&styles={style}&tilePixelRatio=0&format={mediaType}&layers={layer}&tileMatrixSet={tileMatrixSet}&url={link['href']}"
            uris.append(uri)

        return uris

    def createUri(self, link):
        type = link.get("type") or ""
        if type == "xyz":
            return self.createXYZ(link)
        elif type == "wmts":
            return self.createWMTS(link)
        return None

    def mimeUris(self):
        # see if uri has already been created
        # TODO: in the current state this only supports single URIs, should not be an issue for the used types.
        if len(self.uris) != 0:
            return self.uris

        mimeUris = []

        service = self.service
        if not service:
            self.plugin.logging.warning(
                "The given service is not supported or is invalid."
            )
            return mimeUris

        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        try:
            mimeUri = self.createUri(service)
            if mimeUri:
                mimeUris.append(mimeUri)
            else:
                self.plugin.logging.error(
                    f"Can't visualize the service {service['url']}. Not a valid service type"
                )
        except Exception as e:
            self.plugin.logging.error(
                f"Can't visualize the service {service['url']}.", error=e
            )
        finally:
            QApplication.restoreOverrideCursor()

        self.uris = mimeUris

        return mimeUris

    def getTitle(self):
        if not self.service:
            return "n/a"
        return self.service.get("title") or self.service.get("id")

    def addToProject(self):
        uris = self.mimeUris()
        uri = uris[0]
        self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    # todo: remove once we update the Python client to 0.48.0
    # see https://github.com/Open-EO/openeo-python-client/pull/841
    def getLogs(self):
        response_data = (
            self.getConnection()
            .get(f"/services/{self.service['id']}/logs", expected_status=200)
            .json()
        )
        return response_data.get("logs", [])

    def viewLogs(self):
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        try:
            # see https://github.com/Open-EO/openeo-python-client/pull/841
            logs = self.getLogs()
            # logs = self.getServiceClass().logs()
            showLogs(logs, self.getTitle())
        except Exception as e:
            self.plugin.logging.error(
                f"Can't show logs for service {self.getTitle()}.", error=e
            )
        finally:
            QApplication.restoreOverrideCursor()

    def viewProperties(self):
        self.getService()
        showInBrowser(
            "serviceProperties",
            {
                "service": self.service,
            },
        )

    def getService(self):
        self.service = self.getServiceClass().describe_service()
        self.updateFromData()
        return self.service

    def getServiceClass(self):
        return self.getConnection().service(self.service["id"])

    def isEnabled(self):
        return self.service.get("enabled", False)

    def actions(self, parent):
        actions = []

        if self.isEnabled():
            action_add_to_project = QAction(
                QgsApplication.getThemeIcon("mActionAddLayer.svg"),
                "Add Layer to Project",
                parent,
            )
            action_add_to_project.triggered.connect(self.addToProject)
            actions.append(action_add_to_project)
            actions.append(getSeparator(parent))

        action_properties = QAction(
            QgsApplication.getThemeIcon("propertyicons/metadata.svg"),
            "Details",
            parent,
        )
        action_properties.triggered.connect(self.viewProperties)
        actions.append(action_properties)

        action_logs = QAction(
            QgsApplication.getThemeIcon("mIconDataDefine.svg"),
            "View Logs",
            parent,
        )
        action_logs.triggered.connect(self.viewLogs)
        actions.append(action_logs)

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        return actions
