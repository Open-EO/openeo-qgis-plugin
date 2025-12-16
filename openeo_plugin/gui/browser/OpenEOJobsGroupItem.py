# -*- coding: utf-8 -*-
import sip
import openeo

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import pyqtSignal

from qgis.core import QgsDataCollectionItem, QgsApplication

from .OpenEOJobItem import OpenEOJobItem
from .util import getSortAction, getSeparator
from .OpenEOPaginationItem import OpenEOPaginationItem


class OpenEOJobsGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all Batch jobs offered by the corresponding
    openEO provider to the logged in account. Requires Authentication.
    Direct parent to:
    """

    authenticationRequired = pyqtSignal()

    def __init__(self, plugin, parent):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(
            self, parent, "Batch Jobs", plugin.PLUGIN_ENTRY_NAME
        )
        self.plugin = plugin
        self.sortChildrenBy = "default"
        self.limit = 5
        self.nextPage = 0
        self.childJobs = None

        self.setIcon(QgsApplication.getThemeIcon("mIconFolder.svg"))

        # Connect authentication signal to parent's authenticate method
        self.authenticationRequired.connect(parent.authenticate)

    def refresh(self):
        self.depopulate()
        super().refresh()

    def createChildren(self):
        if (
            not self.isAuthenticated()
            and not self.parent().loginStarted
            and not self.parent().forcedLogout
        ):
            self.authenticationRequired.emit()
            return []

        items = []

        jobs = self.childJobs or self.getJobs()
        if self.childJobs is None:
            self.childJobs = jobs

        for i, job in enumerate(jobs):
            item = OpenEOJobItem(
                parent=self, job=job, plugin=self.plugin, index=i
            )
            sip.transferto(item, self)
            items.append(item)
        # create item to load more jobs
        if self.limit:
            loadMore = OpenEOPaginationItem(self.plugin, self)
            sip.transferto(loadMore, self)
            items.append(loadMore)
        return items

    def addChildren(self, children):
        for child in children:
            self.addChildItem(child)
            sip.transferto(child, self)
        self.refresh()

    def loadNextItems(self):
        conn = self.getConnection()
        res = conn.get(
            "/jobs",
            params={"limit": self.limit, "page": self.nextPage},
            expected_status=200,
        ).json()
        newJobs = openeo.rest.models.general.JobListingResponse(
            response_data=res, connection=conn
        )
        self.childJobs = self.childJobs + newJobs
        self.nextPage += 1

        jobItems = []
        for job in newJobs:
            item = OpenEOJobItem(
                parent=self,
                job=job,
                plugin=self.plugin,
            )
            jobItems.append(item)

        self.addChildren(jobItems)
        return

    def getConnection(self):
        return self.parent().getConnection()

    def isAuthenticated(self):
        return self.parent().isAuthenticated()

    def handleDoubleClick(self):
        if not self.parent().loginStarted and not self.isAuthenticated():
            self.parent().authenticate()
        else:
            return super().handleDoubleClick()
        return True

    def getJobs(self):

        try:
            jobs = self.getConnection().list_jobs(limit=self.limit)
            return jobs

        except openeo.rest.OpenEoApiError:
            return []  # this happens when authentication is missing
        except Exception as e:
            self.plugin.logging.error(
                "Can't load list of batch jobs.", error=e
            )
        return []

    def getSortAction(self, title, key):
        return getSortAction(self, title, key, lambda: self.sortBy(key))

    def actions(self, parent):
        actions = []

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        actions.extend(
            [
                getSeparator(parent),
                self.getSortAction("Sort by: Default", "default"),
                self.getSortAction("Sort by: Newest first", "newest"),
                self.getSortAction("Sort by: Oldest first", "oldest"),
                self.getSortAction("Sort by: Title", "title"),
            ]
        )

        return actions

    def sortBy(self, criterion):
        self.sortChildrenBy = criterion
        self.refresh()
