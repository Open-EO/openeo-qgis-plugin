# -*- coding: utf-8 -*-
from collections.abc import Iterable
import sip
import webbrowser
import os
import tempfile
import json
import pathlib
import threading

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsApplication
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer

from . import OpenEOStacAssetItem
from ...utils.logging import error, warning

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

        self.assetItems = []

        self.setIcon(QgsApplication.getThemeIcon("mIconTiledScene.svg"))

        self.updateFromData()

    # todo: Not exactly sure why the second argument is needed, but without we get errors.
    def refresh(self, children: Iterable[QgsDataItem] = None):
        super().refresh()
        self.getJob()
        self.updateFromData()

    def updateFromData(self):
        name = self.job.get("title") or self.job.get("id")
        status = self.getStatus()
        statusString = f"({status}) "

        if status != "finished":
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
        stacAssets = []
        try:
            results = self.getConnection().job(self.job["id"]).get_results()
            results = results.get_metadata()

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
        except Exception as e:
            print(e)
        return stacAssets

    def createChildren(self):
        self.assetItems = self.getResults()

        for item in self.assetItems:
            sip.transferto(item, self)

        return self.assetItems

    def viewProperties(self):
        QApplication.setOverrideCursor(Qt.BusyCursor)
        try:
            self.getJob()
            jobJson = json.dumps(self.job)
            results = self.getConnection().job(self.job["id"]).get_results().get_metadata()
            type = results["type"]
            resultJson = json.dumps(results)

            # Item or Collection?
            resultHtml = ""
            if type == "Collection":
                resultHtml = f'<openeo-collection id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-collection>'
            elif type == "Feature":
                resultHtml = f'<openeo-item id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-item>'

            filePath = pathlib.Path(__file__).parent.resolve()
            with open(os.path.join(filePath, "..", "jobProperties.html")) as file:
                jobInfoHTML = file.read()
            jobInfoHTML = jobInfoHTML.replace("<!-- results -->", resultHtml)
            jobInfoHTML = jobInfoHTML.replace("{{ json }}", jobJson)

            fh, path = tempfile.mkstemp(suffix='.html')
            url = 'file://' + path
            with open(path, 'w') as fp:
                fp.write(jobInfoHTML)
            webbrowser.open_new(url)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            raise e
        finally:
            QApplication.restoreOverrideCursor()


    def getStatus(self):
        return self.job.get("status", "unknown")

    def addResultsToProject(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if len(self.assetItems) == 0:
                self.createChildren()

            # create group
            jobName = self.job.get("title") or self.job.get("id")
            project = QgsProject.instance()
            group = project.layerTreeRoot().insertGroup(0, jobName)

            # create layers and add them to group
            allValid = True
            for asset in self.assetItems:
                layer = asset.createLayer()
                if not layer.isValid():
                    allValid = False
                group.addLayer(layer)
        except Exception as e:
            print(e)
            error(
                self.plugin.iface,
                f"Adding Results to Project failed"
            )
        finally:            
            QApplication.restoreOverrideCursor()
            if not allValid:
                warning(self.plugin.iface, "One or more result assets do not produce valid layers")

    def actions(self, parent):
        actions = []

        job_properties = QAction(QIcon(), "Details", parent)
        job_properties.triggered.connect(self.viewProperties)
        actions.append(job_properties)

        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        action_addGroup = QAction(QIcon(), "Add Results to Project", parent)
        action_addGroup.triggered.connect(self.addResultsToProject)
        actions.append(action_addGroup)

        return actions