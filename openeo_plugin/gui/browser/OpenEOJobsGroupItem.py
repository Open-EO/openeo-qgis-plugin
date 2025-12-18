# -*- coding: utf-8 -*-
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

    def __init__(self, parent):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(
            self, parent, "Batch Jobs", parent.plugin.PLUGIN_ENTRY_NAME
        )
        self.plugin = parent.plugin
        self.sortChildrenBy = "default"
        self.nextPageDataItem = None
        self.nextLink = None
        self.count = -1

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

        jobs = self.getJobs()
        self.nextLink = self.getLink(jobs.links, "next")

        for job in jobs:
            self.count += 1
            item = OpenEOJobItem(parent=self, job=job, index=self.count)
            items.append(item)

        # create item to load more jobs
        if self.nextLink is not None:
            self.nextPageDataItem = OpenEOPaginationItem(self)
            items.append(self.nextPageDataItem)

        return items

    def getLink(self, links, rel):
        link = next(
            (link for link in links if link.rel == rel and link.href),
            None,
        )
        return link.href if link else None

    def loadNextItems(self):
        # todo: this should be done via the Python client, but it's not supported yet
        # https://github.com/Open-EO/openeo-python-client/issues/677
        conn = self.getConnection()
        res = conn.get(
            self.nextLink,
            expected_status=200,
        ).json()
        newJobs = openeo.rest.models.general.JobListingResponse(
            response_data=res, connection=conn
        )

        # JobListingResponse doesn't otherwise join properly
        self.nextLink = self.getLink(newJobs.links, "next")

        # remove next page button
        self.deleteChildItem(self.nextPageDataItem)
        self.nextPageDataItem = None

        # add new job items
        for job in newJobs:
            self.count += 1
            item = OpenEOJobItem(
                parent=self,
                job=job,
                index=self.count,
            )
            self.addChildItem(item, refresh=True)

        # re-add next page button if needed
        if self.nextLink is not None:
            self.nextPageDataItem = OpenEOPaginationItem(self)
            self.addChildItem(self.nextPageDataItem, refresh=True)

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
            return self.getConnection().list_jobs()

        except openeo.rest.OpenEoApiError:
            # when authentication is missing
            pass
        except Exception as e:
            self.plugin.logging.error(
                "Can't load list of batch jobs.", error=e
            )
        return openeo.rest.models.general.JobListingResponse([])

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
