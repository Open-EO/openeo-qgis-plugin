import datetime
import json
import os
import tempfile
import webbrowser
from pathlib import Path

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsApplication


def getSortAction(item, title, key, callback):
    if item.sortChildrenBy == key:
        icon = QgsApplication.getThemeIcon(
            "algorithms/mAlgorithmCheckGeometry.svg"
        )
    else:
        icon = QIcon()
    action = QAction(icon, title, item)
    action.triggered.connect(callback)
    return action


def getSeparator(parent):
    separator = QAction(parent)
    separator.setSeparator(True)
    return separator


def showLogs(logs, title):
    showInBrowser(
        "logFileView",
        {
            "logs": logs,
            "title": title,
            "logTimestamp": str(datetime.datetime.now()),
        },
    )


def showInBrowser(file, vars):
    filePath = Path(__file__).parent.resolve()
    with open(filePath / f"../{file}.html") as file:
        logHTML = file.read()

    for key, value in vars.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        logHTML = logHTML.replace(f"<!-- {key} -->", value)

    try:
        fh, path = tempfile.mkstemp(suffix=".html", text=True)
    except IOError:
        fh, path = tempfile.mkstemp(
            suffix=".html", dir=downloadFolder(), text=True
        )

    with os.fdopen(fh, "w", encoding="utf-8") as tmpfile:
        tmpfile.write(logHTML)

    path = Path(path).resolve().as_uri()
    webbrowser.open_new(path)


def downloadFolder():
    return Path.home() / "Downloads"
