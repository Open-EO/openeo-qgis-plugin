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
    try:
        showInBrowser(
            "logFileView",
            {
                "logs": logs,
                "title": title,
                "logTimestamp": str(datetime.datetime.now()),
            },
        )
    except Exception as e:
        print(e)


def getTempDir():
    if "FLATPAK_SANDBOX_DIR" in os.environ:
        flatpak_id = os.environ.get("FLATPAK_ID")
        uid = os.getuid()
        # The usual path pattern where Flatpak stores persistent data
        path = f"/run/user/{uid}/.flatpak/{flatpak_id}/tmp"
        return path
    else:
        return tempfile.gettempdir()


def showInBrowser(file, vars):
    filePath = Path(__file__).parent.resolve()
    with open(filePath / f"../{file}.html") as file:
        logHTML = file.read()

    for key, value in vars.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        logHTML = logHTML.replace(f"<!-- {key} -->", value)

    fh, path = tempfile.mkstemp(suffix=".html", text=True)
    with open(path, "w") as tmpfile:
        tmpfile.write(logHTML)

    rel_to_tmp = os.path.relpath(path, "/tmp")
    path = os.path.join(getTempDir(), rel_to_tmp)
    path = Path(path).as_uri()
    webbrowser.open_new(path)


def downloadFolder():
    p = Path.home() / "Downloads"
    p.mkdir(parents=True, exist_ok=True)
    return p
