import pathlib
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QThread
from datetime import datetime

class Logging():
    def __init__(self, iface):
        self.iface = iface
        self.messageLog = QgsMessageLog()
        self.logPath = pathlib.Path.home() / 'openeo_qgis_log.txt'

    def success(self, message, title="Success"):
        self.handleMessage(message, title=title, level=Qgis.Success)

    def warning(self, message, title="Warning", error=None):
        self.handleMessage(message, title=title, level=Qgis.Warning, error=error)

    def error(self, message, title="Error", error=None):
        self.handleMessage(message, title=title, level=Qgis.Critical, error=error)

    def info(self, message, title="Info"):
        self.handleMessage(message, title=title, level=Qgis.Info)

    def debug(self, message, error=None):
        self.handleMessage(message, level=Qgis.Info, show=False, error=error)

    def handleMessage(
            self,
            message: str,
            title: str="",
            level: Qgis.MessageLevel=Qgis.Info,
            error: Exception=None,
            show: bool=True
        ):
        message = str(message)
        if isinstance(error, Exception):
            message += f" | Reason: {str(error)}"

        match level:
            case Qgis.Success:
                duration = 10
            case Qgis.Warning:
                duration = 20
            case Qgis.Critical:
                duration = 20
            case _: # Info
                duration = 10

        app = QApplication.instance()
        isUiThread = app is not None and QThread.currentThread() == app.thread()

        self.messageLog.logMessage(
            message,
            tag='openEO',
            notifyUser=not isUiThread,
            level=level
        )

        self.addToLogFile(f"[{title}] {message}")

        if show and isUiThread:
            self.iface.messageBar().pushMessage(
                title,
                message,
                level=level,
                duration=duration
            )
        # todo: We should also handle non-UI thread messages in a better way (e.g. via signals)
        

    def addToLogFile(self, message):
        if not self.logPath:
            return

        try:
            with open(self.logPath, 'a') as logFile:
                logFile.write(str(datetime.now()).ljust(28))
                logFile.write(message)
                logFile.write('\n')
        except Exception as e:
            self.logPath = None
            self.messageLog.logMessage(
                f"Failed to write to log file: {str(e)}",
                tag='openEO',
                level=Qgis.Warning
            )