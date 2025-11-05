#import os
#import openeo

#from qgis.PyQt import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from .ui.login_dialog_tab import Ui_DynamicLoginDialog

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
#Ui_LoginDialog, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/login_dialog.ui'))

class LoginDialog(QtWidgets.QDialog, Ui_DynamicLoginDialog):
    """
    This class is responsible for showing the provider-authencication window to set up authentication with the backend.
    """
    def __init__(self, connection=None, model=None, parent=None, iface=None):

        super(LoginDialog, self).__init__(parent)

        self.iface = iface
        self.parent = parent
        self.connection = connection
        #TODO: get auth provider list
        #TODO: check that it supports deviceCodeFlow
        #TODO: ask for ClientID if it doesnt support that
        self.auth_provider_list = self.connection.list_auth_providers()
        #self.auth_provider_list = [{"title": "openeo", "description":"this is an example provider"}, {"title": "otherExample", "description":""}]

        QApplication.setStyle("cleanlooks")
        
        self.setupUi(self, auth_provider_list=self.auth_provider_list)
        #TODO: don't forget this during localization
        self.titleLabel.setText(f"Log in to {model.name}")

        return
