from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QStyle

from .login_dialog import Ui_LoginDialog

class Ui_DynamicLoginDialog(Ui_LoginDialog):
    """
    Derived class of Ui_LoginDialog.
    dynamically creates authentication options from a list of authentication providers
    """
    def setupUi(self, DynamicLoginDialog, auth_provider_list):
        super().setupUi(DynamicLoginDialog)

        self.internal = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.internal.sizePolicy().hasHeightForWidth())
        self.internal.setSizePolicy(sizePolicy)
        self.internal.setMaximumSize(QtCore.QSize(523, 16777215))
        self.internal.setObjectName("internal")

        self.provider_tabs = []

        for auth_provider in auth_provider_list:
            print(auth_provider)
            tab = {}
            provider_title = auth_provider["title"]

            tab["widget"] = QtWidgets.QWidget()
            tab["widget"].setObjectName(f"tab_{provider_title}")
            tab["widget"].setMaximumSize(QtCore.QSize(523, 16777215))

            tab["verticalLayout"] = QtWidgets.QVBoxLayout(tab["widget"])
            tab["verticalLayout"].setObjectName("verticalLayout")

            if auth_provider["type"] == "basic":
                tab["warningLabel"] = QtWidgets.QLabel(self.internal)
                tab["warningLabel"].setObjectName("warningLabel")
                tab["verticalLayout"].addWidget(tab["warningLabel"])
                tab["usernameLabel"] = QtWidgets.QLabel(self.internal)
                tab["usernameLabel"].setObjectName("usernameLabel")
                tab["verticalLayout"].addWidget(tab["usernameLabel"])
                tab["usernameEdit"] = QtWidgets.QLineEdit(self.internal)
                tab["usernameEdit"].setObjectName("usernameEdit")
                tab["verticalLayout"].addWidget(tab["usernameEdit"])
                tab["passwordLabel"] = QtWidgets.QLabel(self.internal)
                tab["passwordLabel"].setObjectName("passwordLabel")
                tab["verticalLayout"].addWidget(tab["passwordLabel"])
                tab["passwordEdit"] = QtWidgets.QLineEdit(self.internal)
                tab["passwordEdit"].setObjectName("passwordEdit")
                tab["verticalLayout"].addWidget(tab["passwordEdit"])

            if "description" in auth_provider:
                tab["description"] = QtWidgets.QLabel(tab["widget"])
                tab["description"].setObjectName("description")
                tab["verticalLayout"].addWidget(tab["description"])
                tab["description"].setWordWrap(True)

            tab["spacerItem"] = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            tab["verticalLayout"].addItem(tab["spacerItem"])

            tab["authButton"] = QtWidgets.QPushButton(tab["widget"])
            tab["authButton"].setObjectName("authButton")
            tab["verticalLayout"].addWidget(tab["authButton"])

            self.tabWidget.addTab(tab["widget"], auth_provider["title"])
            self.provider_tabs.append(tab)
            
        self.retranslateUi(DynamicLoginDialog)
        QtCore.QMetaObject.connectSlotsByName(DynamicLoginDialog)

    def retranslateUi(self, DynamicLoginDialog):
        super().retranslateUi(DynamicLoginDialog)
        
        _translate = QtCore.QCoreApplication.translate
        if hasattr(self, "provider_tabs"):
            for idx, tab in enumerate(self.provider_tabs):
                auth_provider = self.auth_provider_list[idx]
                if auth_provider["type"] == "basic":
                    tab["usernameLabel"].setText(_translate("LoginDialog", "Username"))
                    tab["passwordLabel"].setText(_translate("LoginDialog", "Password"))
                    tab["authButton"].setText(_translate("LoginDialog", "Authenticate with internal log in")) 
                    tab["warningLabel"].setText(_translate("LoginDialog", "<html><head/><body><p><span style=\" font-weight:700; color:#c01c28;\">warning: </span><span style=\" color:#000000;\">credentials are stored as plain text in project file</span></p></body></html>"))
                else:    
                    tab["authButton"].setText(_translate("LoginDialog", "Log in to ") + auth_provider["title"])
                
                if "description" in auth_provider:
                    tab["description"].setText(auth_provider["description"]) #TODO: use qt info icon