# -*- coding: utf-8 -*-
import webbrowser
import os
import tempfile
import json
import pathlib
import requests

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem

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

        # batch job status
        self.refresh()

    def refresh(self):
        super().refresh()
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
        return self.getConnection().job(self.job["id"])
    
    def viewProperties(self):
        job = self.getJob()
        job_description = job.describe()
        job_json = json.dumps(job_description)

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
        return self.getJob().describe()["status"]

    def printJob(self):
        print(self.getJob().describe())

    def actions(self, parent):
        actions = []

        job_properties = QAction(QIcon(), "Details", parent)
        job_properties.triggered.connect(self.viewProperties)
        actions.append(job_properties)

        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        #action_debug = QAction(QIcon(), "print job details", parent)
        #action_debug.triggered.connect(self.printJob)
        #actions.append(action_debug)

        return actions