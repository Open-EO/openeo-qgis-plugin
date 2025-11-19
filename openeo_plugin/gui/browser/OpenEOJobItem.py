# -*- coding: utf-8 -*-
from collections.abc import Iterable
import webbrowser
import os
import tempfile
import json
import pathlib

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsStacItem
from qgis.core import QgsStacCollection
from qgis.core import QgsJsonUtils
from qgis.core import QgsStacLink
from qgis.core import QgsStacAsset
from qgis.core import QgsBox3D

class OpenEOJobItem(QgsDataItem):
    def __init__(self, parent, job, plugin):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param job: dict containing relevant infos about the batch job that is created.
        :type url: dict
        """

        name = job.get("title") or job.get("id")
        QgsDataItem.__init__(
            self,
            type = Qgis.BrowserItemType.Custom,
            parent = parent,
            name = name,
            path = None,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

        self.job = job
        self.plugin = plugin

        self.uris = []

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

        self.updateFromData()

    # todo: Not exactly sure why the second argument is needed, but without we get errors.
    def refresh(self, children: Iterable[QgsDataItem] = None):
        self.getJob()
        super().refresh()
        self.updateFromData()

    def updateFromData(self):
        name = self.job.get("title") or self.job.get("id")
        status = f"({self.getStatus()}) "
        self.setName(status + name)

    def icon(self):
        return QgsIconUtils.iconTiledScene()

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
    
    def getJob(self):
        self.job = self.getConnection().job(self.job["id"]).describe()
        self.updateFromData()
        return self.job
    
    def getResults(self):
        results = self.getConnection().job(self.job["id"]).get_results()
        results = results.get_metadata()
        # create a job results object. from the metadata of a JobResults object. that should result in a stacItem or stacCollection
        # https://api.openeo.org/#tag/Batch-Jobs/operation/list-results
        # https://qgis.org/pyqgis/master/core/QgsStacItem.html#qgis.core.QgsStacItem
        # STAC-item: type=Feature  STAC-collection: type=Collection
        if results.get("type") == "Feature":
            # create stac item
            bbox = results.get("assets").get("bbox")
            result = QgsStacItem(
                id = results.get("id"),
                version = results.get("stac_version"),
                geometry = QgsJsonUtils.geometryFromGeoJson(results.get("geometry")),
                properties = results.get("properties"),
                links = self._asQgsStacLinks(results.get("links", [])),
                assets = self._asQgsStacAssets(results.get("assets"), []),
                bbox = QgsBox3D(x=bbox[0],x2=bbox[2],y=bbox[1],y2=bbox[3])
            )
            return result
        elif results.get("type") == "Collection":
            # create stac collection
            pass

    def _asQgsStacAssets(self, dict):
        assets = []
        for assetTitle in dict:
            # I dont know where the CS info and other cube:dimensions info goes
            stacAsset = QgsStacAsset(
                href = dict[assetTitle].get('href', None),
                title = dict[assetTitle].get('title', None),
                description = dict[assetTitle].get('description', None),
                mediaType = dict[assetTitle].get('type', None),
                roles = dict[assetTitle].get('roles', None)
            )
            assets.append(stacAsset)
        return assets

    def _asQgsStacLinks(self, dict):
        links = []
        for link in dict:
            stacLink = QgsStacLink(
                href = link.get('href', None),
                relation = link.get('rel', None),
                mediaType = link.get('type', None),
                title = link.get('title', None)
            )
            links.append(stacLink)
        return links

    def viewProperties(self):
        self.getJob()
        job_json = json.dumps(self.job)

        filePath = pathlib.Path(__file__).parent.resolve()
        with open(os.path.join(filePath, "..", "jobProperties.html")) as file:
            jobInfoHTML = file.read()
        jobInfoHTML = jobInfoHTML.replace("{{ json }}", job_json)
        
        fh, path = tempfile.mkstemp(suffix='.html')
        url = 'file://' + path
        with open(path, 'w') as fp:
            fp.write(jobInfoHTML)
        webbrowser.open_new(url)

    def getStatus(self):
        return self.job.get("status", "unknown")
    
    def printJobMetadata(self):
        print(self.getResults())

    def actions(self, parent):
        actions = []

        job_properties = QAction(QIcon(), "Details", parent)
        job_properties.triggered.connect(self.viewProperties)
        actions.append(job_properties)

        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        action_debug = QAction(QIcon(), "debug", parent)
        action_debug.triggered.connect(self.printJobMetadata)
        actions.append(action_debug)

        return actions