# -*- coding: utf-8 -*-
from collections.abc import Iterable
import dateutil.parser
import sip
import json
import pathlib

from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtWidgets import QAction, QApplication
from qgis.PyQt.QtGui import QDesktopServices

from qgis.core import Qgis, QgsDataItem, QgsApplication, QgsProject

from .util import getSeparator, showLogs, showInBrowser
from .OpenEOStacAssetItem import OpenEOStacAssetItem
from ..directory_dialog import DirectoryDialog
from ...utils.downloadTask import DownloadJobAssetsTask

mayHaveResults = ["running", "canceled", "finished", "error"]

isActiveStates = ["queued", "running", "unknown"]


class OpenEOJobItem(QgsDataItem):
    def __init__(self, parent, job, plugin, index):
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
        self.index = index

        self.assetItems = []

        self.setIcon(QgsApplication.getThemeIcon("mIconTiledScene.svg"))

        self.updateFromData()

    def getJobClass(self):
        return self.getConnection().job(self.job["id"])

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

    def sortKey(self):
        sortBy = self.parent().sortChildrenBy
        if sortBy == "title":
            return self.getTitle().lower()
        elif sortBy == "oldest" or sortBy == "newest":
            try:
                created = self.job.get("created", "")
                timestamp = dateutil.parser.isoparse(created).timestamp()
                if sortBy == "newest":
                    timestamp *= -1
                return int(timestamp)
            except Exception:
                return 0
        else:  # default, keep initial backend order
            return self.index

    def hasDragEnabled(self):
        return False

    def getConnection(self):
        return self.parent().getConnection()

    def getJob(self, force=False):
        batchjob = self.getJobClass()
        if force:
            try:
                self.job = batchjob.describe()
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
                results = batchjob.get_results()
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
            jobResultLink = (
                self.getLink("self")
                or self.getJobClass().get_results_metadata_url()
            )
            # create stac-asset items
            for key in assets:
                assetItem = OpenEOStacAssetItem(
                    assetDict=assets[key],
                    key=key,
                    parent=self,
                    plugin=self.plugin,
                    stac_url=jobResultLink,
                )
                self.assetItems.append(assetItem)
                sip.transferto(assetItem, self)

    def viewProperties(self):
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        try:
            self.getJob(force=self.getStatus() in isActiveStates)
            resultJson = json.dumps(self.results)
            # Item or Collection?
            stacType = self.results["type"] if self.results else None
            if stacType == "Collection":
                resultHtml = f'<openeo-collection id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-collection>'
            elif stacType == "Feature":
                resultHtml = f'<openeo-item id="component"><script prop="data" type="application/json">{resultJson}</script></openeo-item>'
            else:
                resultHtml = ""

            showInBrowser(
                "jobProperties",
                {
                    "job": self.job,
                    "results": resultHtml,
                },
            )
        except Exception as e:
            self.plugin.logging.error(
                f"Can't show job details for job {self.getTitle()}.", error=e
            )
        finally:
            QApplication.restoreOverrideCursor()

    def viewLogs(self):
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        try:
            logs = self.getJobClass().logs()
            showLogs(logs, self.getTitle())
        except Exception as e:
            self.plugin.logging.error(
                f"Can't show logs for job {self.getTitle()}.", error=e
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
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
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
        dlg = DirectoryDialog()
        dlg.setDirectory(str(downloadPath))

        # get directory to download to
        dir = dlg.selectDirectory()
        if not dir:
            return

        # Store references for signal handlers
        plugin = self.plugin
        job_title = self.job.get("title") or self.job.get("id")

        # Create custom task
        downloadTask = DownloadJobAssetsTask(
            f"Download job results: {job_title}", self, dir
        )

        # Connect signals to slots that can safely interact with GUI
        def on_download_complete():
            if downloadTask.canceled:
                plugin.logging.info(f"Download canceled: {job_title}")
                return

            errors = downloadTask.errors
            total = downloadTask.total_assets

            if errors == total:
                if errors > 1:
                    plugin.logging.error("No results were downloaded.")
                # Single error already logged during download
            else:
                if errors > 0:
                    plugin.logging.warning(
                        f"Finished downloading results with {errors} errors to {dir}."
                    )
                else:
                    plugin.logging.success(
                        f"Finished downloading all results to {dir}."
                    )
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(dir)))

        def on_download_error():
            if downloadTask.canceled:
                plugin.logging.info(f"Download canceled: {job_title}")
            else:
                plugin.logging.error(
                    "Download failed", error=downloadTask.exception
                )

        # Connect task finished signals
        downloadTask.taskCompleted.connect(on_download_complete)
        downloadTask.taskTerminated.connect(on_download_error)

        # Add task to manager
        taskManager = QgsApplication.taskManager()
        taskManager.addTask(downloadTask)
        plugin.logging.info(f"Downloading: {job_title}")

    def actions(self, parent):
        actions = []

        action_addGroup = QAction(
            QgsApplication.getThemeIcon("mActionAddLayer.svg"),
            "Add Results to Project",
            parent,
        )
        action_addGroup.triggered.connect(self.addResultsToProject)
        actions.append(action_addGroup)

        actions_saveResultsTo = QAction(
            QgsApplication.getThemeIcon("downloading_svg.svg"),
            "Download Results to...",
            parent,
        )
        actions_saveResultsTo.triggered.connect(self.saveResultsTo)
        actions.append(actions_saveResultsTo)

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

        action_copy_url = QAction(
            QgsApplication.getThemeIcon("mActionEditCopy.svg"),
            "Copy STAC metadata URL",
            parent,
        )
        action_copy_url.triggered.connect(self.copyUrlToClipboard)
        actions.append(action_copy_url)

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        return actions

    def getLink(self, rel):
        if not self.results:
            return None

        link = next(
            (
                link
                for link in self.results.get("links", [])
                if link.get("rel") == rel and link.get("href")
            ),
            None,
        )
        return link.get("href") if link else None

    # Method to copy URL to clipboard
    def copyUrlToClipboard(self):
        self.getJob()

        public = "public"
        url = self.getLink("canonical")
        if not url:
            public = "NON-public"
            url = self.getJobClass().get_results_metadata_url()

        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        self.plugin.logging.success(f"Copied {public} URL to clipboard")
