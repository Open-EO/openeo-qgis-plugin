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


def getWmtsStyleAndFormat(layer):
    """
    Extract style and format from WMTS layer metadata.

    :param layer: WMTS ContentMetadata layer object
    :return: tuple of (style, format) strings
    """
    # Get default style or first available style
    style = "default"
    if layer.styles:
        for style_id, style_info in layer.styles.items():
            if style_info.get("isDefault", False):
                style = style_id
                break
        else:
            # If no default style found, use the first one
            style = list(layer.styles.keys())[0]

    # Get first available format or fallback to image/png
    format = "image/png"
    if layer.formats:
        format = layer.formats[0]

    return style, format
