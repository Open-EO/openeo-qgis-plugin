# -*- coding: utf-8 -*-
import os
import pathlib

from qgis.core import QgsApplication, QgsSettings

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication

from .gui.browser import OpenEOItemProvider
from .utils.settings import SettingsPath
from .utils.logging import Logging
from .models.CredentialsModel import Credentials


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OpenEO class from file OpenEO.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #

    return OpenEO(iface)


class OpenEO:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "OpenEO_{}.qm".format(locale)
        )

        # Set up logging and messaging
        logger = QgsApplication.messageLog()
        self.logging = Logging(self.iface, logger)

        # initialize settings
        self.initSettings()

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr("&openEO")

        self.PLUGIN_NAME = "openEO"
        self.PLUGIN_ENTRY_NAME = "openEO"

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("OpenEO", message)

    def addAction(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        return

    def initGui(self):
        """Create the browser entries inside the QGIS GUI."""

        self.list_items_provider = OpenEOItemProvider(self)
        QgsApplication.instance().dataItemProviderRegistry().addProvider(
            self.list_items_provider
        )
        self.list_items_provider_key = (
            self.list_items_provider.dataProviderKey()
        )

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin item from the QGIS browser."""
        QgsApplication.instance().dataItemProviderRegistry().removeProvider(
            self.list_items_provider
        )

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start:
            self.first_start = False
            # self.dlg = OpenEODialog() #not needed at this moment as no main dialog is currently considered

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def getPluginVersion(self):
        filePath = pathlib.Path(__file__).parent.resolve()
        with open(os.path.join(filePath, "metadata.txt"), "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("version="):
                    return line[len("version=") :]
        return None  # In case no version line is found

    def clearLogins(self):
        Credentials().clear()

    def clearSettings(self):
        settings = QgsSettings()
        settings.remove(SettingsPath.SAVED_CONNECTIONS.value)
        settings.remove(SettingsPath.SAVED_LOGINS.value)
        settings.remove(SettingsPath.PLUGIN_VERSION.value)

    def initSettings(self):
        """Checks for existing plugin settings or sets them up if they don't exist"""
        settings = QgsSettings()
        saved_connections_value = settings.value(
            SettingsPath.SAVED_CONNECTIONS.value
        )
        if not saved_connections_value:
            settings.setValue(SettingsPath.SAVED_CONNECTIONS.value, [])

        old_version = (
            settings.value(SettingsPath.PLUGIN_VERSION.value) or "2.0-beta.2"
        )
        Credentials().update(old_version)
        settings.setValue(
            SettingsPath.PLUGIN_VERSION.value, self.getPluginVersion()
        )
