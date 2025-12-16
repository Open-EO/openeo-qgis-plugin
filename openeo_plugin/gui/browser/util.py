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
