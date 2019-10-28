from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QFileInfo
from qgis.core import QgsProject


class Result():

    def __init__(self, path=None, process_graph=None):
        self.path = path
        #self.graph = process_graph
        self.extent = None
        self.get_extent(process_graph)



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

            # reference layer correctly
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
            if self.extent:
                if "crs" in self.extent:
                    crs.createFromId(int(self.extent["crs"]))

            layer.setCrs(crs)

            QgsProject.instance().addMapLayer(layer)

        if layer.isValid() is True:
            print ("Layer was loaded successfully!")
        else:
            print("Unable to read basename and file path - Your string is probably invalid")

    def get_extent(self, d):
        for k, v in d.items():
            if k == "spatial_extent" or "k" == "extent":
                if 'west' in v:
                    self.extent = v
                return
            else:
                if isinstance(v, dict):
                    self.get_extent(v)
                else:
                    print("{0} : {1}".format(k, v))

#result = Result("test", {'load_collection_QHERQ1446J': {'process_id': 'load_collection', 'arguments': {'id': 'COPERNICUS/S2', 'spatial_extent': {'west': -2.7634, 'south': 43.0408, 'east': -1.121, 'north': 43.8385}, 'temporal_extent': ['2018-04-30', '2018-06-26'], 'bands': ['B4', 'B8']}}, 'filter_bands_OKKNR0337R': {'process_id': 'filter_bands', 'arguments': {'data': {'from_node': 'load_collection_QHERQ1446J'}, 'bands': ['B4']}}, 'normalized_difference_MIUYD7636T': {'process_id': 'normalized_difference', 'arguments': {'band1': {'from_node': 'filter_bands_NDKKL2860V'}, 'band2': {'from_node': 'filter_bands_OKKNR0337R'}}}, 'reduce_EWHEM0849B': {'process_id': 'reduce', 'arguments': {'data': {'from_node': 'normalized_difference_MIUYD7636T'}, 'reducer': {'callback': {'min_XLVEQ4794S': {'process_id': 'min', 'arguments': {'data': {'from_argument': 'data'}}, 'result': True}}}, 'dimension': 'temporal'}}, 'apply_KJPGX0184G': {'process_id': 'apply', 'arguments': {'data': {'from_node': 'reduce_EWHEM0849B'}, 'process': {'callback': {'linear_scale_range_FSZDJ8749S': {'process_id': 'linear_scale_range', 'arguments': {'x': {'from_argument': 'x'}, 'inputMin': -1, 'inputMax': 1, 'outputMin': 0, 'outputMax': 255}, 'result': True}}}}}, 'save_result_FXLSK2896A': {'process_id': 'save_result', 'arguments': {'data': {'from_node': 'apply_KJPGX0184G'}, 'format': 'png'}, 'result': True}, 'filter_bands_NDKKL2860V': {'process_id': 'filter_bands', 'arguments': {'data': {'from_node': 'load_collection_QHERQ1446J'}, 'bands': ['B8']}}})

