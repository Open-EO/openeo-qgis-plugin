# -*- coding: utf-8 -*-
import sip
import openeo

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem

from . import OpenEOJobsGroupItem
from . import OpenEOServicesGroupItem
from . import OpenEOCollectionsGroupItem
from ..login_dialog import LoginDialog

class OpenEOConnectionItem(QgsDataCollectionItem):
    """
    QgsDataCollectionItem that contains a connection to an OpenEO provider.
    Direct parent to:
     - OpenEOCollectionsGroupItem
     - OpenEo_batchjob_group_item
     - OpenEo_services_group_item 
    """
    def __init__(self, plugin, model, parent, connection=None):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param model: The model of the OpenEORootItem. This will be displayed in the
            Browser.
        :type model: ConnectionModel

        :param parent: the parent DataItem. expected to be an OpenEORootItem.
        :type parent: QgsDataItem
        """
        QgsDataCollectionItem.__init__(self, parent, model.name, plugin.PLUGIN_ENTRY_NAME)
        self.connection = connection
        self.plugin = plugin
        self.model = model

    def createChildren(self):
        #ensure a connection exists first
        self.getConnection()
        
        items = []
        
        # create Collections group
        collections = OpenEOCollectionsGroupItem(self.plugin, self)
        sip.transferto(collections, self)
        services = OpenEOServicesGroupItem(self.plugin, self)
        sip.transferto(services, self)
        jobs = OpenEOJobsGroupItem(self.plugin, self)
        sip.transferto(jobs, self)
        
        items.append(collections)
        items.append(services)
        items.append(jobs)

        return items
    
    def remove(self):
        self.parent().removeConnection(self)

    def authenticate(self):
        if self.isAuthenticated():
            # this shouldnt be reached since the action is already disabled in this case
            return

        settings = QgsSettings() #TODO: save auth info
        self.dlg = LoginDialog(
            connection=self.getConnection(),
            model=self.model,
            iface=self.plugin.iface
            )
        
        result = self.dlg.exec()

        if result:
            authProvider = self.dlg.activeAuthProvider
            if authProvider["type"] == "basic":
                try:
                    self.getConnection().authenticate_basic(self.dlg.username, self.dlg.password)
                except AttributeError:
                    self.plugin.iface.messageBar().pushMessage("Error", "login failed. connection missing")
                    return

            elif authProvider["type"] == "oidc":
                try:
                    self.getConnection().authenticate_oidc()
                except AttributeError:
                    self.plugin.iface.messageBar().pushMessage("Error", "login failed. connection missing")
                    return

        return
    
    def isAuthenticated(self):
        try:
            account = self.getConnection().describe_account()
            if account:
                return True
            else:
                return False
        except Exception:
            return False

    def getConnection(self):         
        if not self.connection:
            self.connection = self.model.connect()
        return self.connection
    
    def actions(self, parent):
        action_authenticate = QAction(QIcon(), "Authentication (Login)", parent)
        action_authenticate.triggered.connect(self.authenticate)
        action_delete = QAction(QIcon(), "Remove Connection", parent)
        action_delete.triggered.connect(self.remove)

        action_authenticate.setEnabled(not self.isAuthenticated())

        actions = [action_authenticate,action_delete]
        return actions