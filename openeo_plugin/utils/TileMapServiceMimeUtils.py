from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import Qgis

from .wmts import WebMapTileService


class TileMapServiceMimeUtils:
    @classmethod
    def createBaseUri(cls, link, layerName):
        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)
        uri.providerKey = "wms"
        # todo: do we need to set this more specifically?
        uri.supportedFormats = []
        uri.supportedCrs = []

        uri.name = layerName
        title = link.get("title") or ""
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"

        return uri

    @classmethod
    def createXYZ(cls, link, layerName):
        href = link.get("href") or link.get("url")
        uri = cls.createBaseUri(link, layerName)
        uri.supportedCrs = ["EPSG:3857"]
        uri.uri = f"type=xyz&url={href}"
        return uri

    @classmethod
    def createWMTS(cls, link, layerName):
        # todo: Currently only supports KVP encoding, not REST
        # todo: does not support wmts:dimensions
        wmtsUrl = link.get("href") or link.get("url")
        wmtsUrl = f"{wmtsUrl}?service=wmts&request=getCapabilities"
        wmts = WebMapTileService(wmtsUrl)

        layers = link.get("wmts:layer")
        if layers:
            if isinstance(layers, str):
                layers = [layers]
            else:
                layers = list(layers)
        else:
            layers = list(wmts.contents)

        mediaType = link.get("type", "")
        style = None
        tileMatrixSet = None
        crs = None

        uris = []
        for layer in layers:
            uri = cls.createBaseUri(link, layerName)

            # Get layer info from WMTS capabilities
            lyr = wmts.contents.get(layer)
            if lyr:
                if not mediaType and hasattr(lyr, "formats") and lyr.formats:
                    mediaType = lyr.formats[0]

                if hasattr(lyr, "styles") and lyr.styles:
                    style = (
                        list(lyr.styles.keys())[0]
                        if isinstance(lyr.styles, dict)
                        else lyr.styles[0]
                    )

                if hasattr(lyr, "tilematrixsets") and lyr.tilematrixsets:
                    tileMatrixSet = list(lyr.tilematrixsets)[0]
                    tms = wmts.tilematrixsets.get(tileMatrixSet)
                    if tms and hasattr(tms, "crs"):
                        crs = tms.crs

            # Fallback if no tileMatrixSet found
            if not tileMatrixSet:
                tileMatrixSet = "EPSG:3857"
            if not crs:
                crs = "EPSG:3857"
            if not mediaType:
                mediaType = "image/png"
            if not style:
                style = "default"

            uri.uri = f"crs={crs}&styles={style}&tilePixelRatio=0&format={mediaType}&layers={layer}&tileMatrixSet={tileMatrixSet}&url={link['href']}"
            uris.append(uri)

        return uris
