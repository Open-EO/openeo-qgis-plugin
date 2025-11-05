from PyQt5 import QtWidgets
from PyQt5 import QtCore

from .login_dialog import Ui_LoginDialog

class Ui_DynamicLoginDialog(Ui_LoginDialog):
    """
    Derived class of Ui_LoginDialog.
    dynamically creates authentication options from a list of authentication providers
    """
    def setupUi(self, DynamicLoginDialog, auth_provider_list):
        super().setupUi(DynamicLoginDialog)

        self.provider_tabs = []

        for auth_provider in auth_provider_list:
            tab = {}
            provider_title = auth_provider["title"]

            tab["widget"] = QtWidgets.QWidget()
            tab["widget"].setObjectName(f"tab_{provider_title}")
            #todo sizepolicy?
            tab["widget"].setMaximumSize(QtCore.QSize(523, 16777215))

            tab["verticalLayout"] = QtWidgets.QVBoxLayout(tab["widget"])
            tab["verticalLayout"].setObjectName("verticalLayout")

            tab["description"] = QtWidgets.QLabel(tab["widget"])
            tab["description"].setObjectName("description")
            tab["verticalLayout"].addWidget(tab["description"])
            tab["description"].setText(auth_provider["description"])

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

        for idx, tab in enumerate(self.provider_tabs):
            tab["authButton"].setText(_translate("LoginDialog", "Log in to ") + self.auth_provider_list[idx]["title"])