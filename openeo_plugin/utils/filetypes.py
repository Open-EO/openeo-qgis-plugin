from qgis.core import QgsMapLayerFactory, Qgis

raster = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
vector = QgsMapLayerFactory.typeToString(Qgis.LayerType.Vector)

# layer: The QGIS layer type (see above)
# format: The driver name as used by the GDAL/OGR engine
# engine: The data provider engine in QGIS
#         (usually "gdal" for raster or "ogr" for vector)
# crs: (optional) The CRS to use when loading the data
# mediaTypes: List of supported media types types for file format detection
# fileExtensions: List of supported file extensions to use for file format
#                 detection when media type is not present. Avoid duplicates.
# vsi: (optional, experimental) A VSI prefix to use when loading the data
# download: (optional, experimental) Whether the file format must be downloaded
#           so that QGIS can read it (e.g. zipped formats and CSV)
FILETYPES = {
    # SPATIAL FORMATS
    "geotiff": {
        "layer": raster,
        "format": "GTiff",
        "engine": "gdal",
        "mediaTypes": [
            "image/tiff; application=geotiff",
            "image/tiff; application=geotiff; profile=cloud-optimized",
        ],
        "fileExtensions": ["tif", "tiff"],
    },
    "geojson": {
        "layer": vector,
        "format": "GeoJSON",
        "engine": "ogr",
        "crs": "EPSG:4326",
        "mediaTypes": [
            "application/geo+json",
            "application/vnd.geo+json",
        ],
        "fileExtensions": ["geojson"],
    },
    "netcdf": {
        "layer": raster,
        "format": "netCDF",
        "engine": "gdal",
        "mediaTypes": [
            "application/netcdf",
            "application/x-netcdf",
        ],
        "fileExtensions": ["nc"],
    },
    "geoparquet": {
        "layer": vector,
        "format": "Parquet",
        "engine": "ogr",
        "mediaTypes": [
            "application/vnd.apache.parquet",
            "application/parquet; profile=geo",
        ],
        "fileExtensions": ["parquet", "geoparquet"],
    },
    # todo: untested
    # "zipped_zarr": {
    #     "layer": raster,
    #     "format": "Zarr",
    #     "engine": "gdal",
    #     "mediaTypes": [
    #         "application/zip",
    #         # https://github.com/Open-EO/openeo-geopyspark-driver/issues/1465
    #         "application/octet-stream",
    #     ],
    #     "fileExtensions": ["zip"],
    #     "vsi": "/vsizip/",
    #     "download": True
    # },
    # NON-SPATIAL FORMATS just for property inspection
    # "csv": {
    #     "format": "CSV",
    #     "engine": "delimitedtext",
    #     "mediaTypes": [
    #         "text/csv",
    #         "application/csv",
    #     ],
    #     "fileExtensions": ["csv"],
    #     "download": True
    # },
}

MEDIATYPES = {}
EXTENSIONS = {}
for ft in FILETYPES.values():
    for mt in ft["mediaTypes"]:
        MEDIATYPES[mt] = ft
    for ext in ft["fileExtensions"]:
        EXTENSIONS[ext] = ft
