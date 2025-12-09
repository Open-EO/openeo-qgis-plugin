# import os
import threading
import io
import re
import time
import sys
import webbrowser
import openeo

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QMessageBox

from .ui.login_dialog_tab import Ui_DynamicLoginDialog
from ..models.CredentialsModel import CredentialsModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
# Ui_LoginDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/login_dialog.ui'))


class LoginDialog(QtWidgets.QDialog, Ui_DynamicLoginDialog):
    """
    This class is responsible for showing the provider-authentication window to set up authentication with the backend.
    """

    def __init__(self, plugin, connection, model=None):
        super(LoginDialog, self).__init__()
        QApplication.setStyle("cleanlooks")

        self.plugin = plugin
        self.connection = connection
        self.activeAuthProvider = None
        self.credentials = None

        if hasattr(self.connection, "list_auth_providers"):
            self.auth_provider_list = self.connection.list_auth_providers()
        else:
            # todo: remove this when the openEO Python client has been updated to support this method
            self.auth_provider_list = self.list_auth_providers()

        self.setupUi(self, auth_provider_list=self.auth_provider_list)
        # TODO: don't forget this during localization
        self.titleLabel.setText(f"Log in to {model.name}")

        # check for device_code_flow
        # TODO: ask for ClientID if it doesnt support that
        for i, auth_provider in enumerate(self.auth_provider_list):
            if auth_provider["type"] == "oidc":
                if not self._supportsDeviceCodeFlow(auth_provider):
                    self.tabWidget.setTabEnabled(
                        i, False
                    )  # for now, grey out tabs that don't support devicecodeflow
                    self.tabWidget.setTabToolTip(
                        i,
                        "Authentication provider does not support the OpenID Connect Device Code Flow",
                    )

        return

    # todo: remove this when the openEO Python client has been updated to support this method
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

    def login(self):
        # get the currently active tab to log in with
        auth_provider_idx = self.tabWidget.currentIndex()
        auth_provider = self.auth_provider_list[auth_provider_idx]
        self.activeAuthProvider = (
            auth_provider  # so the connectionItem can access it
        )
        tab = self.provider_tabs[auth_provider_idx]

        if auth_provider["type"] == "basic":
            self.username = tab["usernameEdit"].text()
            self.password = tab["passwordEdit"].text()
            self.activeAuthProvider = auth_provider
            if self.authenticate(auth_provider):
                self.accept()  # Close the dialog
            return

        elif auth_provider["type"] == "oidc" and auth_provider:
            self.authenticate(auth_provider, tab)

    def authenticate(self, auth_provider, tab=None):
        if auth_provider["type"] == "basic":
            try:
                self.connection.authenticate_basic(
                    self.username, self.password
                )
                # TODO: add checkmark to select whether to save login
                self.credentials = CredentialsModel(
                    loginType=auth_provider["type"],
                    loginName=self.username,
                    password=self.password,
                )
                return True
            except openeo.rest.OpenEoApiError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("Login Failed")
                msg.setInformativeText("Account name or password incorrect")
                msg.setWindowTitle("Login Failed")
                msg.exec()
                return False
            except Exception as e:
                self.plugin.logging.error(
                    "Can't log in with HTTP Basic.", error=e
                )
                return False

        elif auth_provider["type"] == "oidc":
            capture_buffer = io.StringIO()
            try:
                # open a browser window when prompted
                auth_thread = threading.Thread(
                    target=self._run_auth, args=(capture_buffer,)
                )
                auth_thread.start()

                # Add waiting indicator to window
                tab["authButton"].setDisabled(True)
                btn_text = tab["authButton"].text()
                tab["authButton"].setText("Waiting for authentication...")
                QApplication.processEvents()

                # Monitor output buffer for URL as it appears
                url_found = None
                while auth_thread.is_alive():
                    output = capture_buffer.getvalue()
                    urls = re.findall(r"https?:\/\/[^\s]+", output)
                    if urls:
                        url_found = urls[0]
                        break
                    time.sleep(0.1)  # short wait before checking again

                if url_found:
                    self.plugin.logging.info(
                        f"Opening browser to: {url_found}"
                    )
                    webbrowser.open(url_found)
                else:
                    pass

                auth_thread.join()
                self.credentials = CredentialsModel(
                    loginType=auth_provider["type"]
                )
                self.accept()  # Close the dialog
                return True
            except AttributeError:
                self.plugin.logging.error(
                    "Can't log in with OpenID Connect as the connection is missing."
                )

                self.reject()
                return False
            except Exception as e:
                self.plugin.logging.error(
                    "Can't log in with OpenID Connect.", error=e
                )
                return False
            finally:
                # reset waiting indicator
                tab["authButton"].setDisabled(False)
                tab["authButton"].setText(btn_text)

    def getCredentials(self):
        return self.credentials

    def _run_auth(self, capture_buffer):
        # Redirect stdout for this thread only
        old_stdout = sys.stdout
        sys.stdout = capture_buffer
        try:
            self.connection.authenticate_oidc()
        finally:
            sys.stdout = old_stdout

    def _supportsDeviceCodeFlow(self, auth_provider):
        # check if auth provider has a list of default clients that support device code flow
        support = False
        if "default_clients" not in auth_provider:
            return support
        for client in auth_provider["default_clients"]:
            if (
                "urn:ietf:params:oauth:grant-type:device_code+pkce"
                in client["grant_types"]
            ):
                support = True

        return support
