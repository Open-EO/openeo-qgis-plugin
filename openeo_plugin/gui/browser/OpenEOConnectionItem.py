# -*- coding: utf-8 -*-
import sip
import openeo
import webbrowser
import json
import pathlib
import os
import tempfile
import datetime

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import QgsApplication
from qgis.core import QgsDataCollectionItem

from . import OpenEOJobsGroupItem
from . import OpenEOServicesGroupItem
from . import OpenEOCollectionsGroupItem
from ..login_dialog import LoginDialog
from ...models.CredentialsModel import Credentials


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
        QgsDataCollectionItem.__init__(
            self, parent, model.name, plugin.PLUGIN_ENTRY_NAME
        )
        self.setIcon(QgsApplication.getThemeIcon("mIconCloud.svg"))
        self.connection = connection
        self.plugin = plugin
        self.model = model
        self.lastAuthCheck = datetime.datetime.min
        self.authenticated = False
        self.forcedLogout = False
        self.loginRequested = False

        self.authenticateStored()

    def createChildren(self):
        capabilities = self.getConnection().capabilities()
        items = []

        self.collectionsGroup = OpenEOCollectionsGroupItem(self.plugin, self)
        sip.transferto(self.collectionsGroup, self)
        items.append(self.collectionsGroup)

        if capabilities.supports_endpoint("/services"):
            self.servicesGroup = OpenEOServicesGroupItem(self.plugin, self)
            sip.transferto(self.servicesGroup, self)
            items.append(self.servicesGroup)

        if capabilities.supports_endpoint("/jobs"):
            self.jobsGroup = OpenEOJobsGroupItem(self.plugin, self)
            sip.transferto(self.jobsGroup, self)
            items.append(self.jobsGroup)

        return items

    def refresh(self):
        self.isAuthenticated(forceRefresh=True)
        if hasattr(self, "collectionsGroup"):
            self.collectionsGroup.refresh()
        if hasattr(self, "servicesGroup"):
            self.servicesGroup.refresh()
        if hasattr(self, "jobsGroup"):
            self.jobsGroup.refresh()

    def remove(self):
        self.deleteLogin()
        self.parent().removeConnection(self)

    def authenticate(self):
        if self.authenticateStored():
            self.refresh()
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.dlg = LoginDialog(
                self.plugin, self.getConnection(), model=self.model
            )
        except Exception as e:
            self.plugin.logging.error("Can't open login dialog.", error=e)
            return
        finally:
            QApplication.restoreOverrideCursor()

        result = self.dlg.exec()

        if result:
            credentials = self.dlg.getCredentials()
            if credentials is not None:
                Credentials().add(credentials)
                self.forcedLogout = False

        self.refresh()

    def authenticateStored(self):
        login = Credentials().get(self.model.id)
        if login:
            if login.loginType == "basic":
                creds = login.credentials
                self.getConnection().authenticate_basic(
                    creds["username"],
                    creds["password"],
                )
                return True
            elif login.loginType == "oidc":
                try:
                    self.getConnection().authenticate_oidc_refresh_token()  # try logging in with refresh token
                    return True
                except openeo.rest.OpenEoClientException as e:
                    self.plugin.logging.debug(
                        f"No valid OpenID Connect refresh token found for connection {self.model.name}",
                        error=e,
                    )
        return False

    def isAuthenticated(self, forceRefresh=False):
        authCacheAge = datetime.timedelta(seconds=60)
        maximumTime = self.lastAuthCheck + authCacheAge
        if (datetime.datetime.now() > maximumTime) or forceRefresh:
            try:
                self.lastAuthCheck = datetime.datetime.now()
                account = self.getConnection().describe_account()
                if account:
                    self.authenticated = True
                else:
                    self.authenticated = False
            except Exception as e:
                self.authenticated = False
                self.plugin.logging.debug(
                    "Can't check authentication status.", error=e
                )
        return self.authenticated

    def getConnection(self):
        if not self.connection:
            self.connection = self.model.connect()
        return self.connection

    def deleteLogin(self):
        Credentials().remove(self.model.id)

    def logout(self):
        self.forcedLogout = True
        self.loginRequested = False
        self.deleteLogin()
        # refresh connection
        self.connection = None
        self.connection = self.getConnection()
        self.refresh()

    def viewProperties(self):
        connection = self.getConnection()
        connection_description = connection.capabilities().capabilities
        connection_url = connection.capabilities().url
        connection_json = json.dumps(connection_description)

        filePath = pathlib.Path(__file__).parent.resolve()
        with open(
            os.path.join(filePath, "..", "connectionProperties.html")
        ) as file:
            connectionInfoHTML = file.read()
        connectionInfoHTML = connectionInfoHTML.replace(
            "{{ json }}", connection_json
        )
        connectionInfoHTML = connectionInfoHTML.replace(
            "{{ url }}", connection_url
        )

        fh, path = tempfile.mkstemp(suffix=".html")
        url = "file://" + path
        with open(path, "w") as fp:
            fp.write(connectionInfoHTML)
        webbrowser.open_new(url)

    def openInWebEditor(self):
        webEditorUrl = self.getConnection().web_editor()
        webbrowser.open(webEditorUrl)

    def actions(self, parent):
        actions = []
        separator = QAction(parent)
        separator.setSeparator(True)

        if not self.isAuthenticated():
            action_authenticate = QAction(
                QIcon(), "Log In (Authenticate)", parent
            )
            action_authenticate.triggered.connect(self.authenticate)
            actions.append(action_authenticate)
            actions.append(separator)
        else:
            action_logout = QAction(QIcon(), "Log Out", parent)
            action_logout.triggered.connect(self.logout)
            actions.append(action_logout)
            actions.append(separator)

        action_properties = QAction(QIcon(), "Details", parent)
        action_properties.triggered.connect(self.viewProperties)
        actions.append(action_properties)

        action_refresh = QAction(
            QgsApplication.getThemeIcon("mActionRefresh.svg"),
            "Refresh",
            parent,
        )
        action_refresh.triggered.connect(self.refresh)
        actions.append(action_refresh)

        action_delete = QAction(
            QgsApplication.getThemeIcon("mActionDeleteSelected.svg"),
            "Remove Connection",
            parent,
        )
        action_delete.triggered.connect(self.remove)
        actions.append(action_delete)

        separator = QAction(parent)
        separator.setSeparator(True)
        actions.append(separator)

        action_webeditor = QAction(QIcon(), "Open in Web Editor", parent)
        action_webeditor.triggered.connect(self.openInWebEditor)
        actions.append(action_webeditor)

        return actions
