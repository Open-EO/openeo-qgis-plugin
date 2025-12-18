# -*- coding: utf-8 -*-
import openeo
import webbrowser
import datetime

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QApplication

from qgis.core import QgsApplication, QgsDataCollectionItem

from .util import getSeparator, showInBrowser
from .OpenEOJobsGroupItem import OpenEOJobsGroupItem
from .OpenEOServicesGroupItem import OpenEOServicesGroupItem
from .OpenEOCollectionsGroupItem import OpenEOCollectionsGroupItem
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

    def __init__(self, model, parent, connection=None):
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
            self, parent, model.name, parent.plugin.PLUGIN_ENTRY_NAME
        )
        self.setIcon(QgsApplication.getThemeIcon("mIconCloud.svg"))
        self.connection = connection
        self.plugin = parent.plugin
        self.model = model
        self.lastAuthCheck = datetime.datetime.min
        self.authenticated = False
        self.forcedLogout = False
        self.loginStarted = False

        self.authenticateStored()

    def createChildren(self):
        capabilities = self.getConnection().capabilities()
        items = []

        self.collectionsGroup = OpenEOCollectionsGroupItem(self)
        items.append(self.collectionsGroup)

        if capabilities.supports_endpoint("/services"):
            self.servicesGroup = OpenEOServicesGroupItem(self)
            items.append(self.servicesGroup)

        if capabilities.supports_endpoint("/jobs"):
            self.jobsGroup = OpenEOJobsGroupItem(self)
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
        if self.loginStarted:
            return
        self.forcedLogout = False

        if self.authenticateStored():
            self.refresh()
            return

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            if hasattr(self.connection, "list_auth_providers"):
                auth_provider_list = self.connection.list_auth_providers()
            else:
                # todo: remove this when the openEO Python client has been updated to support this method
                auth_provider_list = self.list_auth_providers()
        except Exception as e:
            self.plugin.logging.error(
                "Can't get the identity providers from the server. Please try again later.",
                error=e,
            )
            return
        finally:
            QApplication.restoreOverrideCursor()

        try:
            self.loginStarted = True
            self.dlg = LoginDialog(
                self.plugin,
                self.getConnection(),
                model=self.model,
                auth_providers=auth_provider_list,
            )
            result = self.dlg.exec()

            if result:
                credentials = self.dlg.getCredentials()
                if credentials is not None:
                    Credentials().add(credentials)
                self.refresh()
        except Exception as e:
            self.plugin.logging.error("Login failed.", error=e)
            return
        finally:
            self.loginStarted = False

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

    # todo: remove this when the openEO Python client has been updated to support this method
    # see https://github.com/Open-EO/openeo-python-client/pull/826
    def list_auth_providers(self) -> list[dict]:
        providers = []
        cap = self.connection.capabilities()

        # Add OIDC providers
        oidc_path = "/credentials/oidc"
        if cap.supports_endpoint(oidc_path, method="GET"):
            try:
                data = self.connection.get(
                    oidc_path, expected_status=200
                ).json()
                if isinstance(data, dict):
                    for provider in data.get("providers", []):
                        provider["type"] = "oidc"
                        providers.append(provider)
            except openeo.rest.OpenEoApiError as e:
                self.plugin.logging.error(
                    "Can't load the OpenID Connect provider list.", error=e
                )

        # Add Basic provider
        basic_path = "/credentials/basic"
        if cap.supports_endpoint(basic_path, method="GET"):
            providers.append(
                {
                    "id": basic_path,
                    "issuer": self.connection.build_url(basic_path),
                    "type": "basic",
                    "title": "Internal",
                    "description": "The HTTP Basic authentication method is mostly used for development and testing purposes.",
                }
            )

        return providers

    def getConnection(self):
        if not self.connection:
            self.connection = self.model.connect()
        return self.connection

    def deleteLogin(self):
        Credentials().remove(self.model.id)

    def logout(self):
        self.forcedLogout = True
        self.loginStarted = False
        self.deleteLogin()
        # refresh connection
        self.connection = None
        self.connection = self.getConnection()
        self.refresh()

    def viewProperties(self):
        capabilities = self.getConnection().capabilities()
        showInBrowser(
            "connectionProperties",
            {
                "capabilities": capabilities.capabilities,
                "url": capabilities.url,
            },
        )

    def openInWebEditor(self):
        webEditorUrl = self.getConnection().web_editor()
        webbrowser.open(webEditorUrl)

    def actions(self, parent):
        actions = []

        if not self.isAuthenticated():
            action_authenticate = QAction(
                QgsApplication.getThemeIcon("locked.svg"),
                "Log In (Authenticate)",
                parent,
            )
            action_authenticate.triggered.connect(self.authenticate)
            actions.append(action_authenticate)
        else:
            action_logout = QAction(
                QgsApplication.getThemeIcon("unlocked.svg"), "Log Out", parent
            )
            action_logout.triggered.connect(self.logout)
            actions.append(action_logout)

        actions.append(getSeparator(parent))

        action_properties = QAction(
            QgsApplication.getThemeIcon("propertyicons/metadata.svg"),
            "Details",
            parent,
        )
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

        actions.append(getSeparator(parent))

        action_webeditor = QAction(QIcon(), "Open in Web Editor", parent)
        action_webeditor.triggered.connect(self.openInWebEditor)
        actions.append(action_webeditor)

        return actions
