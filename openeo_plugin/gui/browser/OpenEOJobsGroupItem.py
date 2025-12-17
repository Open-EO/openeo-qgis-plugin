# -*- coding: utf-8 -*-
import sip
import openeo
from urllib.parse import urlparse
from urllib.parse import parse_qs

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

        self.limit = 5
        self.nextPage = 0

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
        if (not self.paginator) and (self.nextPage is not None):
            self.paginator = OpenEOPaginationItem(self.plugin, self)
            sip.transferto(self.paginator, self)
        if self.paginator:
            self.paginator.setLoadedItems(len(jobs))
            items.append(self.paginator)
        return items

    def addChildren(self, children):
        for child in children:
            self.addChildItem(child)
            sip.transferto(child, self)
        self.refresh()

    def getLink(self, links, rel):
        link = next(
            (
                link
                for link in links
                if link.get("rel") == rel and link.get("href")
            ),
            None,
        )
        return link.get("href") if link else None

    def getNextPageParameters(self, url):
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        limit = query.get("limit", [None])[0]
        page = query.get("page", [None])[0]
        return limit, page

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
        currentAmount = len(self.childJobs)
        self.childJobs = self.childJobs + newJobs
        nextLink = self.getLink(res["links"], "next")
        self.limit, self.nextPage = self.getNextPageParameters(nextLink)

        jobItems = []
        for i, job in enumerate(newJobs):
            item = OpenEOJobItem(
                parent=self,
                job=job,
                plugin=self.plugin,
                index=currentAmount + i,
            )
            jobItems.append(item)

        if self.nextPage is None:
            self.paginator = None

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
