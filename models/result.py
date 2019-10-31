from qgis.core import QgsRasterLayer
from qgis.PyQt.QtCore import QFileInfo
from qgis.core import QgsProject

class Result():

    def __init__(self, path=None):
        self.path = path

    def display(self):
        """
        Displays an image from the given path on a new created QGIS Layer.
        """
        # Check if string is provided
        if self.path:
            fileInfo = QFileInfo(self.path)
            path = fileInfo.filePath()
            baseName = fileInfo.baseName()
            layer = QgsRasterLayer(path, baseName)
            QgsProject.instance().addMapLayer(layer)

        if layer.isValid() is True:
            print
            "Layer was loaded successfully!"

        else:
            print
            "Unable to read basename and file path - Your string is probably invalid"