# -*- coding: utf-8 -*-
import webbrowser
import os
import tempfile
import json
import pathlib

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory

from ...utils.wmts import WebMapTileService
from ...utils.logging import warning

class OpenEOServiceItem(QgsDataItem):
    def __init__(self, parent, service, plugin):
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
            type = Qgis.BrowserItemType.Custom,
            parent = parent,
            name = name,
            path = None,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

        self.setIcon(QgsIconUtils.iconTiledScene())

        self.service = service
        self.plugin = plugin

        self.uris = []

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

        #enabled / disabled

    def hasDragEnabled(self):
        return True
    
    def layerName(self):
        return self.name()
    
    def supportedFormats(self):
        return [] #TODO: determine more closely from capabilities
    
    def supportedCrs(self):
        return ["EPSG:3857"] #TODO: determine more closely from capabilities
    
    def getConnection(self):
        return self.parent().getConnection()
    
    def createUri(self, link):
        title = link.get("title") or ""
        mapType = link.get("type") or ""

        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)  
        uri.providerKey = "wms"
        uri.name = self.layerName()
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"
        uri.supportedFormats = self.supportedFormats() # todo: do we need to set this more specifically?
        uri.supportedCrs = self.supportedCrs() # todo: set more specific supportedCrs below

        # different map service formats
        if mapType.lower() == "xyz":
            uri.uri = f"type=xyz&url={link["url"]}"
            return uri
        elif mapType.lower() == "wmts":
            wmtsUrl = link["url"]+"?service=wmts&request=getCapabilities"
            wmts = WebMapTileService(wmtsUrl)
            targetCRS = "EPSG::3857"
            
            tileMatrixSet = None
            for tms_id, tms in list(wmts.tilematrixsets.items()):
                if targetCRS in tms.crs: 
                    tileMatrixSet = tms_id
                    break
            layerID = None
            layerID = list(wmts.contents)[0]
            styleID = wmts.contents[layerID].styles

            #TODO: determine more URI parameters programmatically
            uri.uri = f"crs=EPSG:3857&styles=default&tilePixelRatio=0&format=image/png&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={link["href"]}"
            return uri
        elif mapType.lower() == "wms":
            #TODO
            return
        else:
            return None
        
    def mimeUris(self):
        #see if uri has already been created
        # TODO: in the current state this only supports single URIs, should not be an issue for the used types.
        if len(self.uris) != 0:
            return self.uris

        mimeUris = []

        service = self.service
        if not service:
            warning(self.plugin.iface, "Could not detect a layer from the given source.")
            return mimeUris

        QApplication.setOverrideCursor(Qt.BusyCursor)

        #TODO: what if operation takes way too long?
        try:
            mimeUri = self.createUri(service)
            if mimeUri:
                mimeUris.append(mimeUri)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            print(e)
            warning(
                self.plugin.iface,
                f"Loading the map service {service['url']} failed."
            )
        
        QApplication.restoreOverrideCursor()

        self.uris = mimeUris

        return mimeUris

    def addToProject(self):
        uris = self.mimeUris()
        uri = uris[0]
        self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    def viewProperties(self):
        service = self.getConnection().service(self.service["id"])
        service_description = service.describe_service()
        service_json = json.dumps(service_description)

        filePath = pathlib.Path(__file__).parent.resolve()
        with open(os.path.join(filePath, "..", "serviceProperties.html")) as file:
            serviceInfoHTML = file.read()
        serviceInfoHTML = serviceInfoHTML.replace("{{ json }}", service_json)
        
        fh, path = tempfile.mkstemp(suffix='.html')
        url = 'file://' + path
        with open(path, 'w') as fp:
            fp.write(serviceInfoHTML)
        webbrowser.open_new(url)

    def actions(self, parent):
        actions = []

        action_add_to_project = QAction(QIcon(), "Add Layer to Project", parent)
        action_add_to_project.triggered.connect(self.addToProject)
        actions.append(action_add_to_project)
        
        action_properties = QAction(QIcon(), "Details", parent)
        action_properties.triggered.connect(self.viewProperties)
        actions.append(action_properties)

        return actions