# -*- coding: utf-8 -*-
import sip
import openeo

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem

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

        if not self.connection:
            self.connection = model.connect()

    def createChildren(self):
        if not self.connection:
            self.connection = openeo.connect(self.model.url)
        
        #TODO: children for collections, batch-jobs, services
        items = []
        
        # create Collections group
        collections = OpenEOCollectionsGroupItem(self.plugin, self)
        sip.transferto(collections, self)
        items.append(collections)

        return items
    
    def remove(self):
        self.parent().removeConnection(self)

    def authenticate(self):
        #TODO: check if authentication exists first

        settings = QgsSettings()
        self.dlg = LoginDialog(
            connection=self.connection,
            model=self.model,
            iface=self.plugin.iface
            )
        
        result = self.dlg.exec()

        if result:
            authProvider = self.dlg.activeAuthProvider
            print(authProvider)
            if authProvider["type"] == "basic":
                try:
                    self.connection.authenticate_basic(self.dlg.username, self.dlg.password)
                except AttributeError:
                    self.plugin.iface.messageBar().pushMessage("Error", "login failed. connection missing")
                print(self.connection)
            elif authProvider["type"] == "oidc":
                try:
                    self.connection.authenticate_oidc()
                except AttributeError:
                    self.plugin.iface.messageBar().pushMessage("Error", "login failed. connection missing")
                print(self.connection)
            else:
                return
            return

    def getConnection(self):
        return self.connection
    
    def actions(self, parent):
        action_authenticate = QAction(QIcon(), "Authentication (Login)", parent)
        action_authenticate.triggered.connect(self.authenticate)
        action_delete = QAction(QIcon(), "Remove Connection", parent)
        action_delete.triggered.connect(self.remove)
        actions = [action_authenticate,action_delete]
        return actions