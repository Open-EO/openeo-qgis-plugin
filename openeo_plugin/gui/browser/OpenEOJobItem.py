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
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtCore import QUrl

from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsApplication
from qgis.core import QgsProject

from . import OpenEOStacAssetItem

mayHaveResults = ["running", "canceled", "finished", "error"]

isActiveStates = ["queued", "running", "unknown"]


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
            type=Qgis.BrowserItemType.Custom,
            parent=parent,
            name=name,
            path=None,
            providerKey=plugin.PLUGIN_ENTRY_NAME,
        )

        self.job = job
        self.results = None
        self.plugin = plugin

        self.assetItems = []

        self.setIcon(QgsApplication.getThemeIcon("mIconTiledScene.svg"))

        self.updateFromData()

    def refresh(self, children: Iterable[QgsDataItem] | bool = False):
        self.depopulate()
        if children is False:
            self.getJob(force=True)
            return super().refresh()
        else:
            return super().refresh(children)

    def updateFromData(self):
        name = self.job.get("title") or self.job.get("id")
        status = self.getStatus()
        statusString = f"({status}) "
        self.setName(statusString + name)

    def hasDragEnabled(self):
        return False

    def getConnection(self):
        return self.parent().getConnection()

    def getJob(self, force=False):
        job = self.getConnection().job(self.job["id"])
        if force:
            try:
                self.job = job.describe()
                self.updateFromData()
            except Exception as e:
                self.plugin.logging.error(
                    f"Can't load job '{self.getTitle()}'.", error=e
                )
                return self.job

        if (
            force or self.results is None
        ) and self.getStatus() in mayHaveResults:
            try:
                results = job.get_results()
                if results is not None:
                    self.results = results.get_metadata()
                else:
                    self.results = None
            except Exception as e:
                self.plugin.logging.error(
                    f"Can't load results for job {self.getTitle()}.", error=e
                )

        return self.job

    def createChildren(self):
        self.populateAssetItems()
        return self.assetItems

    def populateAssetItems(self):
        self.getJob()
        self.assetItems = []
        if self.results is not None:
            # get the stac item
            assets = self.results.get("assets", [])
            # create stac-asset items
            for key in assets:
                assetItem = OpenEOStacAssetItem(
                    assetDict=assets[key],
                    key=key,
                    parent=self,
                    plugin=self.plugin,
                )
                self.assetItems.append(assetItem)
                sip.transferto(assetItem, self)

    def viewProperties(self):
        QApplication.setOverrideCursor(Qt.BusyCursor)
        try:
            self.getJob(force=self.getStatus() in isActiveStates)
            jobJson = json.dumps(self.job)
            type = self.results["type"] if self.results else None
            resultJson = json.dumps(self.results)

            # Item or Collection?
            resultHtml = ""
            if type == "Collection":
                resultHtml = f'<openeo-collection id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-collection>'
            elif type == "Feature":
                resultHtml = f'<openeo-item id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-item>'

            filePath = pathlib.Path(__file__).parent.resolve()
            with open(
                os.path.join(filePath, "..", "jobProperties.html")
            ) as file:
                jobInfoHTML = file.read()
            jobInfoHTML = jobInfoHTML.replace("<!-- results -->", resultHtml)
            jobInfoHTML = jobInfoHTML.replace("{{ json }}", jobJson)

            fh, path = tempfile.mkstemp(suffix=".html")
            url = "file://" + path
            with open(path, "w") as fp:
                fp.write(jobInfoHTML)
            webbrowser.open_new(url)
        except Exception as e:
            self.plugin.logging.error(
                f"Can't show job details for job {self.getTitle()}.", error=e
            )
        finally:
            QApplication.restoreOverrideCursor()

    def getStatus(self):
        if not self.job:
            return "unknown"
        return self.job.get("status", "unknown")

    def getTitle(self):
        if not self.job:
            return "n/a"
        return self.job.get("title") or self.job.get("id")

    def addResultsToProject(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        allValid = True
        try:
            self.populateAssetItems()
            # create group
            jobName = self.getTitle()
            project = QgsProject.instance()
            group = project.layerTreeRoot().insertGroup(0, jobName)

            # create layers and add them to group
            for asset in self.assetItems:
                layer = asset.createLayer(addToProject=False)
                if not layer.isValid():
                    allValid = False
                project.addMapLayer(
                    layer, False
                )  # add to project without showing
                group.addLayer(layer)  # add to the group
        except Exception as e:
            self.plugin.logging.error(
                f"Can't add results to project for job {self.getTitle()}.",
                error=e,
            )
        finally:
            QApplication.restoreOverrideCursor()
            if not allValid:
                self.plugin.logging.warning(
                    f"One or more result assets for job {self.getTitle()} can't be visualized"
                )

    def saveResultsTo(self):
        downloadPath = pathlib.Path.home() / "Downloads"

        # prepare file dialog
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.FileMode.Directory)
        dlg.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        dlg.setDirectory(str(downloadPath))
        dlg.setWindowTitle("Download Results to...")

        result = dlg.exec()

        if result:
            # prepare progress bar
            progressbar = QProgressBar()
            self.plugin.iface.messageBar().pushWidget(progressbar)
            progressBarWidget = self.plugin.iface.messageBar().currentItem()

            dir = dlg.selectedUrls()[0]
            if dir.isLocalFile() or dir.isEmpty():
                dir = dir.toLocalFile()
            else:
                dir = dir.toString()

            def downloadAssets():
                self.populateAssetItems()
                errors = 0
                for i, asset in enumerate(self.assetItems):
                    try:
                        asset.downloadAsset(dir=dir)
                        progress = int((i / len(self.assetItems)) * 100)
                        progressbar.setValue(progress)
                    except Exception as e:
                        errors += 1
                        self.plugin.logging.error(
                            f"Can't download the asset {asset.name()}.",
                            error=e,
                        )

                if errors == len(self.assetItems):
                    if errors == 1:
                        pass  # Error already logged above
                    else:
                        self.plugin.iface.messageBar().popWidget(
                            progressBarWidget
                        )
                        self.plugin.logging.error(
                            "No results were downloaded."
                        )
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(dir)))
                    if errors > 0:
                        self.plugin.iface.messageBar().popWidget(
                            progressBarWidget
                        )
                        self.plugin.logging.warning(
                            f"Finished downloading results with {errors} errors to {dir}."
                        )
                    else:
                        self.plugin.iface.messageBar().popWidget(
                            progressBarWidget
                        )
                        self.plugin.logging.success(
                            f"Finished downloading all results to {dir}."
                        )

            threading.Thread(target=downloadAssets, daemon=True).start()

    def actions(self, parent):
        actions = []

        job_properties = QAction(QIcon(), "Details", parent)
        job_properties.triggered.connect(self.viewProperties)
        actions.append(job_properties)

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        action_addGroup = QAction(QIcon(), "Add Results to Project", parent)
        action_addGroup.triggered.connect(self.addResultsToProject)
        actions.append(action_addGroup)

        actions_saveResultsTo = QAction(
            QIcon(), "Download Results to...", parent
        )
        actions_saveResultsTo.triggered.connect(self.saveResultsTo)
        actions.append(actions_saveResultsTo)

        return actions
