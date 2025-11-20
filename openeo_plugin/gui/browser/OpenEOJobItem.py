# -*- coding: utf-8 -*-
from collections.abc import Iterable
import sip
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
from qgis.core import QgsStacExtent

from . import OpenEOStacAssetItem

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

        self.setIcon(QgsIconUtils.iconTiledScene())

        self.updateFromData()

    # todo: Not exactly sure why the second argument is needed, but without we get errors.
    def refresh(self, children: Iterable[QgsDataItem] = None):
        self.getJob()
        super().refresh()
        self.updateFromData()

    def updateFromData(self):
        name = self.job.get("title") or self.job.get("id")
        status = self.getStatus()
        statusString = f"({status}) "

        if not status == "finished":
            #TODO: may not be foolproof. can finished jobs without assets exist?
            self.setState(QgsDataItem.Populated)
        self.setName(statusString + name)

    def hasDragEnabled(self):
        return False
    
    def getConnection(self):
        return self.parent().getConnection()
    
    def getJob(self):
        self.job = self.getConnection().job(self.job["id"]).describe()
        self.updateFromData()
        return self.job
    
    def getResults(self):
        results = self.getConnection().job(self.job["id"]).get_results()
        results = results.get_metadata()
        stacAssets = []
        # get the stac item
        assets = results.get("assets", [])
        # create stac-asset items
        for key in assets:
            assetItem = OpenEOStacAssetItem(
                assetDict=assets[key],
                parent=self,
                plugin=self.plugin
            )
            stacAssets.append(assetItem)
            
        return stacAssets

    def createChildren(self):
        assetItems = self.getResults()

        for item in assetItems:
            sip.transferto(item, self)

        return assetItems

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