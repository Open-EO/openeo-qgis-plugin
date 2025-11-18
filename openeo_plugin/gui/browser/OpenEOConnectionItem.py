# -*- coding: utf-8 -*-
import sip
import openeo
from openeo.rest.auth.config import RefreshTokenStore

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import QgsApplication
from qgis.core import QgsSettings
from qgis.core import QgsDataCollectionItem

from . import OpenEOJobsGroupItem
from . import OpenEOServicesGroupItem
from . import OpenEOCollectionsGroupItem
from ..login_dialog import LoginDialog
from ...utils.settings import SettingsPath
from ...utils.logging import warning, debug

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
        self.setIcon(QgsApplication.getThemeIcon("mIconCloud.svg"))
        self.connection = connection
        self.plugin = plugin
        self.model = model

        login = self.getLogin()
        if login:
            self.getConnection().authenticate_basic(login["loginName"], login["password"])


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
    
    def refreshChildren(self):
        if hasattr(self, "collectionsGroup"):
            self.collectionsGroup.refresh()
            self.collectionsGroup.refreshChildren()
        if hasattr(self, "servicesGroup"):
            self.servicesGroup.refresh()
            self.collectionsGroup.refreshChildren()
        if hasattr(self, "jobsGroup"):
            self.jobsGroup.refresh()
            self.collectionsGroup.refreshChildren()

    def remove(self):
        self.deleteLogin()
        self.parent().removeConnection(self)

    def authenticate(self):
        if self.isAuthenticated():
            # this shouldnt be reached since the action is already disabled in this case
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.dlg = LoginDialog(
            connection=self.getConnection(),
            model=self.model,
            parent=self,
            iface=self.plugin.iface
            )
        QApplication.restoreOverrideCursor()

        result = self.dlg.exec()

        if result:
            pass
        
        self.refreshChildren()
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
    
    def saveLogin(self, name, password):
        settings = QgsSettings()
        loginInfo = {
            "id": str(self.model.id),
            "loginName": name,
            "password": password,
        }
        logins = settings.value(SettingsPath.SAVED_LOGINS.value)
        logins.append(loginInfo)
        settings.setValue(SettingsPath.SAVED_LOGINS.value, logins)

    def getLogin(self):
        settings = QgsSettings()
        loginInfo = None # return None if no login has been saved
        logins = settings.value(SettingsPath.SAVED_LOGINS.value)
        for login in logins:
            if login["id"] == str(self.model.id):
                loginInfo = login
        return loginInfo

    def deleteLogin(self):
        settings = QgsSettings()

        # for deleting basic login
        logins = settings.value(SettingsPath.SAVED_LOGINS.value)
        for i, login in enumerate(logins):
            if login["id"] == str(self.model.id):
                logins.pop(i)
        settings.setValue(SettingsPath.SAVED_LOGINS.value, logins)

        # for deleting oidc refresh tokens
        try:
            # determine the key for the refresh token storage
            _g = openeo.rest.auth.oidc.DefaultOidcClientGrant
            provider_id, client_info = self.getConnection()._get_oidc_provider_and_client_info(
                provider_id=None, client_id=None, client_secret=None,
                default_client_grant_check=lambda grants: (
                        _g.REFRESH_TOKEN in grants and (_g.DEVICE_CODE in grants or _g.DEVICE_CODE_PKCE in grants)
                )
            )
            # overwrite refresh tokens
            RefreshTokenStore().set(client_info.provider.issuer, value={})
        except openeo.rest.OpenEoClientException as e:
            print(e)
            # this happens when the connection does not support oidc
            return
    
    def logout(self):
        self.deleteLogin()
        # refresh connection
        self.connection = None
        self.connection = self.getConnection()
        self.refreshChildren()
    
    def copyUrl(self):
        QApplication.clipboard().setText(self.getConnection()._orig_url)

    def actions(self, parent):
        actions = []
        if not self.isAuthenticated():
            action_authenticate = QAction(QIcon(), "Authentication (Login)", parent)
            action_authenticate.triggered.connect(self.authenticate)
            actions.append(action_authenticate)
        else:
            action_logout = QAction(QIcon(), "Log Out", parent)
            action_logout.triggered.connect(self.logout)
            actions.append(action_logout)
        
        action_copyUrl = QAction(QIcon(), "Copy Endpoint URL", parent)
        action_copyUrl.triggered.connect(self.copyUrl)
        actions.append(action_copyUrl)
        action_delete = QAction(QIcon(), "Remove Connection", parent)
        action_delete.triggered.connect(self.remove)
        actions.append(action_delete)
        action_refresh = QAction(QIcon(), "Refresh", parent)
        action_refresh.triggered.connect(self.refreshChildren)
        actions.append(action_refresh)

        return actions