from openeo.rest.models.general import Link

from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory
from qgis.core import Qgis

from .wmts import WebMapTileService


class WMTSLink(Link):
    def __init__(self, rel, href, type=None, title=None, wmts_layer=None):
        super().__init__(rel, href, type, title)
        self.wmts_layer = wmts_layer

    @classmethod
    def from_dict(cls, data: dict) -> Link:
        """Build :py:class:`Link` from dictionary (e.g. parsed JSON representation)."""
        return cls(
            rel=data["rel"],
            href=data["href"],
            type=data.get("type"),
            title=data.get("title"),
            wmts_layer=data.get("wmts:layer"),
        )


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
        title = link.title or ""
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"

        return uri

    @classmethod
    def createXYZ(cls, link, layerName):
        href = link.href
        uri = cls.createBaseUri(link, layerName)
        uri.supportedCrs = ["EPSG:3857"]
        uri.uri = f"type=xyz&url={href}"
        return uri

    @classmethod
    def createWMTS(cls, link, layerName):
        # todo: Currently only supports KVP encoding, not REST
        # todo: does not support wmts:dimensions
        wmtsUrl = link.href
        wmtsUrl = f"{wmtsUrl}?service=wmts&request=getCapabilities"
        wmts = WebMapTileService(wmtsUrl)

        layers = link.wmts_layer
        if layers:
            if isinstance(layers, str):
                layers = [layers]
            else:
                layers = list(layers)
        else:
            layers = list(wmts.contents)

        mediaType = link.type
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

            uri.uri = f"crs={crs}&styles={style}&tilePixelRatio=0&format={mediaType}&layers={layer}&tileMatrixSet={tileMatrixSet}&url={link.href}"
            uris.append(uri)

        return uris
