import pathlib

from qgis.core import QgsApplication, QgsMessageLog, Qgis
from datetime import datetime

class Logging():
    def __init__(self, iface, logger: QgsMessageLog=None):
        self.developerMode = False
        self.iface = iface
        self.tag = 'openEO'
        self.logPath = pathlib.Path.home() / 'openeo_qgis_log.txt'
        self.messageLog = logger if logger else QgsApplication.messageLog()
        self.messageLog.messageReceived.connect(self.on_message)

    def on_message(self, message, tag, level):
        if tag != self.tag:
            return

        title = self.getTitle(level)
        match level:
            case Qgis.Warning:
                duration = 20
            case Qgis.Critical:
                duration = 20
            case _: # Info & Success
                duration = 10
        
        self.iface.messageBar().pushMessage(
            title,
            message,
            level=level,
            duration=duration
        )

    def success(self, message):
        self._handleMessage(message, level=Qgis.Success)

    def warning(self, message, error=None):
        self._handleMessage(message, level=Qgis.Warning, error=error)

    def error(self, message, error=None):
        self._handleMessage(message, level=Qgis.Critical, error=error)

    def info(self, message):
        self._handleMessage(message, level=Qgis.Info)

    def debug(self, message, error=None):
        self._handleMessage(message, level=Qgis.Info, show=False, error=error)

    def getTitle(self, level: Qgis.MessageLevel, show = True) -> str:
        match level:
            case Qgis.Success:
                return "Success"
            case Qgis.Warning:
                return "Warning"
            case Qgis.Critical:
                return "Error"
            case _:
                return "Info" if show else "Debug"

    def _handleMessage(
            self,
            message: str,
            level: Qgis.MessageLevel=Qgis.Info,
            error: Exception=None,
            show: bool=True
        ):
        message = str(message)
        if isinstance(error, Exception):
            message += f" Reason: {str(error)}"

        debug = level == Qgis.Info and not show
        if not debug or self.developerMode:
            self.messageLog.logMessage(message, self.tag, level, notifyUser=show)

        if self.developerMode:
            title = self.getTitle(level, show)
            self._addToLogFile(f"[{title}] {message}")

    def _addToLogFile(self, message):
        if not self.logPath:
            return

        try:
            with open(self.logPath, 'a') as logFile:
                logFile.write(str(datetime.now()).ljust(28))
                logFile.write(message)
                logFile.write('\n')
        except Exception as e:
            self.logPath = None
            self.logMessage(
                f"Failed to write to log file: {str(e)}",
                tag='openEO',
                level=Qgis.Info,
                show=False
            )