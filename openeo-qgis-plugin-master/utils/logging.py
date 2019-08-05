from qgis.core import QgsMessageLog, Qgis


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
