from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QFileInfo
from qgis.core import QgsProject


class Result():

    def __init__(self, path=None, process_graph=None):
        self.path = path
        self.extent = None
        self.get_extent(process_graph)

    def display(self, layer_name=None):
        """
        Displays an image from the given path on a new created QGIS Layer.
        """
        # Check if string is provided
        if self.path:
            fileInfo = QFileInfo(self.path)
            path = fileInfo.filePath()
            baseName = fileInfo.baseName()
            if layer_name:
                layer = QgsRasterLayer(path, layer_name)
            else:
                layer = QgsRasterLayer(path, baseName)
            # reference layer correctly
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
            if self.extent:
                if "crs" in self.extent:
                    self.extent["crs"] = self.extent["crs"].replace("EPSG:", "")
                    crs.createFromId(int(self.extent["crs"]))

            layer.setCrs(crs)

            if not layer.isValid():
                print("Layer failed to load!")
                return False

            QgsProject.instance().addMapLayer(layer)

            return True

    def get_extent(self, d):
        for k, v in d.items():
            if k == "spatial_extent" or "k" == "extent":
                if v:
                    if 'west' in v:
                        self.extent = v
                    return
            else:
                if isinstance(v, dict):
                    self.get_extent(v)
                else:
                    print("{0} : {1}".format(k, v))