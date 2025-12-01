import pathlib
from qgis.core import QgsMessageLog, Qgis
from datetime import datetime

class Logging():
    def __init__(self, iface):
        self.iface = iface 
        self.messageLog = QgsMessageLog()

    def warning(self, message, duration=5):
        self.logError(f"[WARNING] {message}")
        self.iface.messageBar().pushMessage(
            "Warning",
            message,
            level=Qgis.Warning,
            duration=duration
        )

    def error(self, message, errorMessage=None):
        error = self.createErrorMessage(message)
        if not errorMessage:
            errorMessage = error
        self.logError(error)
        self.showErrorToUser(errorMessage)

    def showErrorToUser(self, message, duration=5):
        message = str(message) #stringify in case it isn't
        self.messageLog.logMessage(message, tag='openEO', notifyUser=True, level=Qgis.Critical)

    def showSuccessToUser(self, message, duration = 5):
        message = str(message) #stringify in case it isn't
        self.iface.messageBar().pushMessage(
            "Success",
            message,
            level=Qgis.Success,
            duration=duration
        )

    def info(self, message, duration = 5):
        message = str(message) #stringify in case it isn't
        self.iface.messageBar().pushMessage(
            "Info",
            message,
            level=Qgis.Info,
            duration=duration
        )

    @staticmethod
    def logError(message, dir=None):
        message = str(message) #stringify in case it isn't
        if not dir:
            #log to home directory
            dir = pathlib.Path.home() / 'openeo_qgis_log.txt'
        # create logfile if not exists
        try:
            open(dir, 'x')
        except FileExistsError:
            pass #nothing because file exists
        
        with open(dir, 'a') as logFile:    
            logFile.write(message)
            logFile.write('\n')

    @staticmethod
    def printError(message):
        print(message)
    
    @staticmethod
    def createErrorMessage(message):
        message = str(message) #stringify in case it isn't
        timestamp = str(datetime.now())
        prefix = timestamp.ljust(28, " ") #write padded timestamp
        prefix = f"{prefix}:"
        return f"{prefix} {message}"
        
