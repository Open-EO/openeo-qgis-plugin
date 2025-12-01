#import os
import threading
import io
import re
import time
import sys
import webbrowser
import openeo

#from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtWidgets import QMessageBox

from .ui.login_dialog_tab import Ui_DynamicLoginDialog

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
#Ui_LoginDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/login_dialog.ui'))

class LoginDialog(QtWidgets.QDialog, Ui_DynamicLoginDialog):
    """
    This class is responsible for showing the provider-authencication window to set up authentication with the backend.
    """
    def __init__(self, connection=None, model=None, parent=None, iface=None):

        super(LoginDialog, self).__init__()
        QApplication.setStyle("cleanlooks")

        self.iface = iface
        self.parent = parent
        self.plugin = parent.plugin
        self.connection = connection
        self.activeAuthProvider = None
        
        if hasattr(self.connection, 'list_auth_providers'):
            self.auth_provider_list = self.connection.list_auth_providers()
        else:
            # todo: remove this when the openEO Python client has been updated to support this method
            self.auth_provider_list = self.list_auth_providers()
        
        self.setupUi(self, auth_provider_list=self.auth_provider_list)
        #TODO: don't forget this during localization
        self.titleLabel.setText(f"Log in to {model.name}")

        # check for device_code_flow
        #TODO: ask for ClientID if it doesnt support that
        for i, auth_provider in enumerate(self.auth_provider_list):
            if auth_provider["type"] == "oidc":
                if not self._supportsDeviceCodeFlow(auth_provider):
                    self.tabWidget.setTabEnabled(i, False) #for now, grey out tabs that don't support devicecodeflow
                    self.tabWidget.setTabToolTip(i, "Authentication provider does not support the OpenID Connect Device Code Flow")

        return

    # todo: remove this when the openEO Python client has been updated to support this method
    def list_auth_providers(self) -> list[dict]:
        providers = []
        cap = self.connection.capabilities()

        # Add OIDC providers
        oidc_path = "/credentials/oidc"
        if cap.supports_endpoint(oidc_path, method="GET"):
            try:
                data = self.connection.get(oidc_path, expected_status=200).json()
                if isinstance(data, dict):
                    for provider in data.get("providers", []):
                        provider["type"] = "oidc"
                        providers.append(provider)
            except openeo.rest.OpenEoApiError as e:
                self.parent.logging.warning(self.iface, f"Unable to load the OpenID Connect provider list: {e.message}")

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
        self.activeAuthProvider = auth_provider # so the connectionItem can access it
        tab = self.provider_tabs[auth_provider_idx]

        if auth_provider["type"] == "basic":
            self.username = tab["usernameEdit"].text()
            self.password = tab["passwordEdit"].text()
            self.activeAuthProvider = auth_provider
            if self.authenticate(auth_provider):
                self.accept() # Close the dialog
            return
        
        elif auth_provider["type"] == "oidc" and auth_provider:
            self.authenticate(auth_provider, tab)
    
    def authenticate(self, auth_provider, tab=None):
        if auth_provider["type"] == "basic":
            try:
                self.parent.getConnection().authenticate_basic(self.username, self.password)
                #TODO: add checkmark to select whether to save login
                self.parent.saveLogin(auth_provider["type"],self.username, self.password)
                return True
            except openeo.rest.OpenEoApiError as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Login Failed")
                msg.setInformativeText('Account name or password incorrect')
                msg.setWindowTitle("Login Failed")
                msg.exec_()
            except Exception as e:
                self.parent.logging.warning(self.iface, "Login Failed: something went wrong. See log for details")
                print(str(e))
                return False

        elif auth_provider["type"] == "oidc":
            capture_buffer = io.StringIO()
            try:
                # open a browser window when prompted
                auth_thread = threading.Thread(target=self._run_auth, args=(capture_buffer,))
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
                    urls = re.findall(r'https?:\/\/[^\s]+', output)
                    if urls:
                        url_found = urls[0]
                        break
                    time.sleep(0.1)  # short wait before checking again

                if url_found:
                    msg = f"Opening browser to: {url_found}"
                    self.parent.logging.info(self.iface, msg)
                    webbrowser.open(url_found)
                else:
                    #self.iface.messageBar().pushMessage("Error", "No URL found before the login has been cancelled by QGIS. Please try again.")
                    print("No URL found before auth finished.")

                auth_thread.join()
                self.parent.saveLogin(auth_provider["type"])
                self.accept() # Close the dialog
                return
            except AttributeError:
                self.iface.messageBar().pushMessage("Error", "Login failed as the connection is missing. Please try again.")
                
                self.reject()
                return
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Authentication Failed")
                msg.setInformativeText('See logs for details')
                msg.setWindowTitle("Authentication Failed")
                msg.exec_()
                print(str(e))
                return False

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
            if "urn:ietf:params:oauth:grant-type:device_code+pkce" in client ["grant_types"]:
               support = True 

        return support