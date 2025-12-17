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
        self.childJobs = None
        self.paginator = None

        self.limit = 2
        self.nextLink = None

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

        jobs = self.childJobs or self.getJobs()  # childJobs?

        self.nextLink = self.getLink(jobs.links, "next")
        if self.childJobs is None:
            self.childJobs = jobs

        for i, job in enumerate(jobs):
            item = OpenEOJobItem(
                parent=self, job=job, plugin=self.plugin, index=i
            )
            sip.transferto(item, self)
            items.append(item)

        # create item to load more jobs
        if self.nextLink is not None:
            self.paginator = OpenEOPaginationItem(self.plugin, self)
            sip.transferto(self.paginator, self)
            items.append(self.paginator)

        return items

    def getLink(self, links, rel):
        link = next(
            (link for link in links if link.rel == rel and link.href),
            None,
        )
        return link.href if link else None

    def loadNextItems(self):
        conn = self.getConnection()
        res = conn.get(
            self.nextLink,
            expected_status=200,
        ).json()
        currentAmount = len(self.childJobs)
        newJobs = openeo.rest.models.general.JobListingResponse(
            response_data=res, connection=conn
        )

        # JobListingResponse doesn't otherwise join properly
        res["jobs"] = self.childJobs + res["jobs"]
        self.childJobs = openeo.rest.models.general.JobListingResponse(
            response_data=res, connection=conn
        )
        self.nextLink = self.getLink(newJobs.links, "next")

        if self.nextLink is None:
            sip.transferback(self.paginator)
            self.deleteChildItem(self.paginator)
            self.paginator = None

        jobItems = []
        for i, job in enumerate(newJobs):
            item = OpenEOJobItem(
                parent=self,
                job=job,
                plugin=self.plugin,
                index=currentAmount + i,
            )
            sip.transferto(item, self)
            jobItems.append(item)
            self.addChildItem(item, refresh=True)

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
            # when authentication is missing
            return openeo.rest.models.general.JobListingResponse([])
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
