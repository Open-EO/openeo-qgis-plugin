# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsSettings, QgsDataCollectionItem, QgsApplication

from .util import getSeparator
from .OpenEOConnectionItem import OpenEOConnectionItem
from ..connect_dialog import ConnectDialog
from ...utils.settings import SettingsPath
from ...models.ConnectionModel import ConnectionModel


class OpenEORootItem(QgsDataCollectionItem):
    """
    Implementation of QgsDataCollectionItem. The root of the plugin within the browser view
    Direct parent to:
     - OpenEOConnectionItem
    """

    def __init__(self, plugin, name=None, parent=None):
        """Constructor.

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.

        :param name: The name of the OpenEORootItem. This will be displayed in the
            Browser.
        :type name: str

        :param parent: the parent DataItem. Root is not expected to have one.
        :type parent: QgsDataItem
        """
        name = plugin.PLUGIN_NAME if not name else name
        provider_key = plugin.PLUGIN_ENTRY_NAME
        QgsDataCollectionItem.__init__(self, parent, name, provider_key)
        self.plugin = plugin
        self.setIcon(QIcon(self.getImagePath("icon_small.png")))

        # get saved connections from QgsSettings
        settings = QgsSettings()
        models = map(
            ConnectionModel.fromDict,
            settings.value(SettingsPath.SAVED_CONNECTIONS.value),
        )
        self.saved_connections = list(
            models
        )  # map needs to be turned into a list

    def createChildren(self):
        items = []
        for model in self.saved_connections:
            item = self.createConnectionItem(model)
            items.append(item)
        return items

    def createConnectionItem(self, model, connection=None):
        return OpenEOConnectionItem(
            model=model, parent=self, connection=connection
        )

    def getImagePath(self, name):
        dirname = os.path.join(os.path.dirname(__file__), "../../images")
        return os.path.join(dirname, name)

    def addConnection(self):
        settings = QgsSettings()
        self.dlg = ConnectDialog(self.plugin)
        self.dlg.show()
        result = self.dlg.exec()

        model = self.dlg.getModel()
        if result and model:
            connection = self.dlg.getConnection()
            self.saved_connections.append(model)

            # save the model persistently
            reprs = settings.value(SettingsPath.SAVED_CONNECTIONS.value)
            reprs.append(model.toDict())
            settings.setValue(SettingsPath.SAVED_CONNECTIONS.value, reprs)

            item = self.createConnectionItem(model, connection=connection)
            self.addChildItem(item, refresh=True)

            # start authentication flow
            item.authenticate()

    def removeConnection(self, data_item):
        self.saved_connections.remove(data_item.model)

        # update the saved connection models
        settings = QgsSettings()
        reprs = map(lambda c: c.toDict(), self.saved_connections)
        settings.setValue(SettingsPath.SAVED_CONNECTIONS.value, list(reprs))

        self.deleteChildItem(data_item)

    def removeSavedLogins(self):
        self.plugin.clearLogins()
        self.plugin.logging.info("All saved logins details have been removed")
        self.depopulate()
        self.populate()

    def removeAllConnections(self):
        self.plugin.clearSettings()
        self.plugin.initSettings()
        self.plugin.logging.info("All saved logins details have been removed")
        self.saved_connections = list()
        self.depopulate()

    def actions(self, parent):
        actions = []

        action_new_connection = QAction(
            QgsApplication.getThemeIcon("mActionAdd.svg"),
            "New openEO Connection",
            parent,
        )
        action_new_connection.triggered.connect(self.addConnection)
        actions.append(action_new_connection)

        actions.append(getSeparator(parent))

        actions_logout_all = QAction(
            QgsApplication.getThemeIcon("unlocked.svg"),
            "Logout from all connections",
            parent,
        )
        actions_logout_all.triggered.connect(self.removeSavedLogins)
        actions.append(actions_logout_all)

        actions_clear_settings = QAction(
            QgsApplication.getThemeIcon("mActionDeleteSelected.svg"),
            "Remove all connections",
            parent,
        )
        actions_clear_settings.triggered.connect(self.removeAllConnections)
        actions.append(actions_clear_settings)

        return actions
