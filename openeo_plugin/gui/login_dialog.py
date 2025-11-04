import os
import openeo

from qgis.PyQt import uic
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

#from .ui.login_dialog import Ui_SpatialDialog as FORM_CLASS

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
# use this if the pb_tool compiled version of the dialog doesn't work
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/login_dialog.ui'))

class LoginDialog(QtWidgets.QDialog, FORM_CLASS):
    """
    This class is responsible for showing the provider-authencication window to set up authentication with the backend.
    """
    def __init__(self, connection=None, parent=None, iface=None):

        super(LoginDialog, self).__init__(parent)

        self.iface = iface
        self.parent = parent
        self.connection = connection
        
        QApplication.setStyle("cleanlooks")
        self.setupUi(self)

        #TODO: don"t forget this during localization
        self.titleLabel.setText(f"Log in to {connection.name}")
        
        #TODO: get auth provider list
        #TODO: check that it supports deviceCodeFlow
        #TODO: ask for ClientID if it doesnt support that
        self.auth_provider_list = [{"title": "openeo", "description":"this is an example provider"}, {"title": "otherExample", "description":""}]

        self.populateTabs()

        return
    
    def populateTabs(self):
        for auth_provider in self.auth_provider_list:
            tab = UI_TabContent(auth_provider)
            self.tabWidget.addTab(tab.getWidget(), auth_provider["title"])

        return
    
class UI_TabContent:
    def __init__(self, auth_provider, TabContent=None):
        provider_title = auth_provider["title"]

        self.widget = QtWidgets.QWidget()
        self.widget.setObjectName(f"tab_{provider_title}")
        #todo sizepolicy?
        self.widget.setMaximumSize(QtCore.QSize(523, 16777215))

        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")

        self.description = QtWidgets.QLabel(self.widget)
        self.description.setObjectName("description")
        self.verticalLayout.addWidget(self.description)
        self.description.setText(auth_provider["description"])

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.authButton = QtWidgets.QPushButton(self.widget)
        self.authButton.setObjectName("authButton")
        self.verticalLayout.addWidget(self.authButton)

        self.retranslateUi(auth_provider)

    def getWidget(self):
        return self.widget

    def retranslateUi(self, auth_provider):
        _translate = QtCore.QCoreApplication.translate
        self.authButton.setText(_translate("SpatialDialog", "Log in to ") + auth_provider["title"])