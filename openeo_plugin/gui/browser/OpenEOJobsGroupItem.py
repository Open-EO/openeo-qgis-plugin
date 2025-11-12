# -*- coding: utf-8 -*-
import sip

from qgis.core import QgsDataCollectionItem
from qgis.core import QgsApplication

from . import OpenEOJobItem

class OpenEOJobsGroupItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that groups together all Batch jobs offered by the corresponding
    openEO provider to the logged in account. Requires Authentication.
    Direct parent to:
    """
    def __init__(self, plugin, parent):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param parent_connection: the parent DataItem. expected to be OpenEOConnectionItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(self, parent, "Batch Jobs", plugin.PLUGIN_ENTRY_NAME)
        self.plugin = plugin

        self.populate() #removes expand icon

    def createChildren(self):
        if not self.isAuthenticated():
            return []
        items = []
        jobs = self.getJobs()
        for job in jobs:
            item = OpenEOJobItem(
                parent = self,
                job = job,
                plugin =  self.plugin,
            )
            sip.transferto(item, self)
            items.append(item)
        return items
    
    def icon(self):
        icon = QgsApplication.getThemeIcon("mIconFolder.svg")
        return icon
    
    def addChildren(self, children):
        for child in children:
            self.addChildItem(child)
        self.refresh()

    def getConnection(self):
        return self.parent().getConnection()
    
    def isAuthenticated(self):
        return self.parent().isAuthenticated()
    
    def handleDoubleClick(self):
        if not self.isAuthenticated():
            self.parent().authenticate()
            self.refresh()
            #TODO: handle child items
        return super().handleDoubleClick()
    
    def getJobs(self):
        #TODO: how to handle pagination
        jobs = self.getConnection().list_jobs()
        return jobs
