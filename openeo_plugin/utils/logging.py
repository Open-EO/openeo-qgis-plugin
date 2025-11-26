import pathlib
from qgis.core import QgsMessageLog, Qgis
from datetime import datetime


def debug(message):
    QgsMessageLog.logMessage(message, level=Qgis.Info)


def info(iface, message, duration=5):
    QgsMessageLog.logMessage(message, level=Qgis.Info)
    iface.messageBar().pushMessage(
        "Info",
        message,
        level=Qgis.Info,
        duration=duration
    )


def warning(iface, message, duration=5):
    QgsMessageLog.logMessage(message, level=Qgis.Warning)
    iface.messageBar().pushMessage(
        "Warning",
        message,
        level=Qgis.Warning,
        duration=duration
    )


def error(iface, message, duration=5):
    QgsMessageLog.logMessage(message, level=Qgis.Critical)
    iface.messageBar().pushMessage(
        "Error",
        message,
        level=Qgis.Critical,
        duration=duration
    )

class Logging():
    def __init__(self, iface, duration=5):
        self.iface = iface

    def warning(self, message):
        self.logError(f"[WARNING] {message}")
        self.iface.messageBar().pushMessage(
            "Warning",
            message,
            level=Qgis.Warning,
            duration=duration
        )

    def error(self, message):
        errorMessage = self.createErrorMessage(message)
        self.logError(errorMessage)
        self.printError(errorMessage)
        self.showErrorToUser(errorMessage)

    def showErrorToUser(self, message, duration=5):
        message = str(message) #stringify in case it isn't
        self.iface.messageBar().pushMessage(
            "Error",
            message,
            level=Qgis.Critical,
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
        return f"{prefix}{message}"
        
