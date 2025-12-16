from qgis.core import Qgis

FILETYPES = {
    # SPATIAL FORMATS
    "geotiff": {
        "layer": Qgis.LayerType.Raster,
        "format": "geotiff",
        "engine": "gdal",
        "mediaTypes": [
            "image/tiff; application=geotiff",
            "image/tiff; application=geotiff; profile=cloud-optimized",
        ],
        "fileExtensions": ["tif", "tiff"],
    },
    "geojson": {
        "layer": Qgis.LayerType.Vector,
        "format": "geojson",
        "engine": "ogr",
        "crs": "EPSG:4326",
        "mediaTypes": [
            "application/geo+json",
            "application/vnd.geo+json",
        ],
        "fileExtensions": ["geojson"],
    },
    "netcdf": {
        "layer": Qgis.LayerType.Raster,
        "format": "netcdf",
        "engine": "gdal",
        "mediaTypes": [
            "application/netcdf",
            "application/x-netcdf",
        ],
        "fileExtensions": ["nc"],
    },
    "geoparquet": {
        "layer": Qgis.LayerType.Vector,
        "format": "geoparquet",
        "engine": "ogr",
        "mediaTypes": [
            "application/vnd.apache.parquet",
            "application/parquet; profile=geo",
        ],
        "fileExtensions": ["parquet", "geoparquet"],
    },
    # todo: untested
    # "zipped_zarr": {
    #     "layer": Qgis.LayerType.Raster,
    #     "format": "zarr",
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
    #     "format": "csv",
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
