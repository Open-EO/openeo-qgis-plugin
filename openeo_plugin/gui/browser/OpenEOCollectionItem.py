from urllib.parse import quote
import tempfile
import webbrowser

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsIconUtils
from qgis.core import Qgis
from qgis.core import QgsDataItem
from qgis.core import QgsMimeDataUtils
from qgis.core import QgsMapLayerFactory

from ...utils.wmts import WebMapTileService
from ...utils.logging import warning

class OpenEOCollectionItem(QgsDataItem):
    def __init__(self, parent, collection, plugin, preview=False):
        """Constructor.

        :param parent: the parent DataItem. expected to be an OpenEOCollectionsGroupItem.
        :type parent: QgsDataItem

        :param plugin: Reference to the qgis plugin object. Passing this object
            to the children allows for access to important attributes like
            PLUGIN_NAME and PLUGIN_ENTRY_NAME.
        
        :param collection: dict containing relevant infos about the collection.
        :type url: dict
        """

        name = collection.get("title") or collection.get("id")
        QgsDataItem.__init__(
            self,
            type = Qgis.BrowserItemType.Custom,
            parent = parent,
            name = name,
            path = None,
            providerKey = plugin.PLUGIN_ENTRY_NAME
        )

        self.collection = collection
        self.plugin = plugin
        self.preview = preview #whether the collection contains a wmts preview

        self.uris = []

        # Has no children, set as populated to avoid the expand arrow
        self.setState(QgsDataItem.Populated)

    def icon(self):
        if self.preview:
            return QgsIconUtils.iconRaster()
        return QgsIconUtils.iconTiledScene()

    def hasDragEnabled(self):
        return self.preview
    
    def layerName(self):
        return self.name()
    
    def supportedFormats(self):
        return [] #TODO: determine more closely from capabilities
    
    def supportedCrs(self):
        return ["EPSG:3857"] #TODO: determine more closely from capabilities
    
    def getConnection(self):
        return self.parent().getConnection()

    def createUri(self, link):
        title = link.get("title") or ""
        rel = link.get("rel") or ""

        uri = QgsMimeDataUtils.Uri()
        uri.layerType = QgsMapLayerFactory.typeToString(Qgis.LayerType.Raster)  
        uri.providerKey = "wms"
        uri.name = self.layerName()
        if len(title) > 0 and title != uri.name:
            uri.name += f" - {title}"
        uri.supportedFormats = self.supportedFormats() # todo: do we need to set this more specifically?
        uri.supportedCrs = self.supportedCrs() # todo: set more specific supportedCrs below

        # different map service formats
        if rel == "xyz":
            uri.uri = f"type=xyz&url={link["href"]}/"+quote("{z}/{y}/{x}")
            return uri
        elif rel == "wmts":
            wmtsUrl = link["href"]+"?service=wmts&request=getCapabilities"
            wmts = WebMapTileService(wmtsUrl)
            targetCRS = "EPSG::3857"
            
            tileMatrixSet = None
            for tms_id, tms in list(wmts.tilematrixsets.items()):
                if targetCRS in tms.crs: 
                    tileMatrixSet = tms_id
                    break
            layerID = None
            layerID = list(wmts.contents)[0]
            styleID = wmts.contents[layerID].styles

            #TODO: determine more URI parameters programmatically
            uri.uri = f"crs=EPSG:3857&styles=default&tilePixelRatio=0&format=image/png&layers={layerID}&tileMatrixSet={tileMatrixSet}&url={link["href"]}"
            return uri
        else:
            return None
    
    def mimeUris(self):
        if not self.preview:
            return []

        #see if uri has already been created
        # TODO: in the current state this only supports single URIs, should not be an issue for the used types.
        if len(self.uris) != 0:
            return self.uris

        mimeUris = []

        webMapLinks = self.parent().getWebMapLinks(self.collection)
        if len(webMapLinks) == 0:
            warning(self.plugin.iface, "Could not detect a layer from the given source.")
            return mimeUris

        QApplication.setOverrideCursor(Qt.BusyCursor)

        #TODO: what if operation takes way too long?
        for link in webMapLinks:
            try:
                mimeUri = self.createUri(link)
                mimeUris.append(mimeUri)
            except Exception as e:
                print(e)
                warning(
                    self.plugin.iface,
                    f"Loading the map service {link['href']} failed."
                )
        
        QApplication.restoreOverrideCursor()

        self.uris = mimeUris

        return mimeUris

    
    def addToProject(self):
        if not self.preview:
            return
        
        uris = self.mimeUris()
        uri = uris[0]
        self.plugin.iface.addRasterLayer(uri.uri, uri.name, uri.providerKey)

    def viewProperties(self):
        collection_link = None
        
        links = self.collection["links"]
        for link in links:
            if link["rel"] == "self":
                collection_link = link["href"]
                break
        
        collectionInfoHTML = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Collections</title>
              <style id="styles">
                body {{
                  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, Cantarell, 'Open Sans', sans-serif;
                }}
                h2, h3 {{
                  color: #58965A;
                  border-bottom: 1px solid black;
                  font-weight: 600;
                  padding: 0.25rem;
                }}
                h3 {{
                  font-size: 2rem;
                }}
                h3 {{
                  font-size: 1.5rem;
                }}

                a {{
                  color: #84ABD5;
                }}
              </style>
            </head>
            <body>
              <p id="loading" style="display: block;">Loading data…</p>
              <openeo-collection id="data" style="display: none;"></openeo-collection>
            </body>
              <script src="https://cdn.jsdelivr.net/npm/@openeo/vue-components@2/assets/openeo.min.js"></script>
              <script>
              fetch('{collection_link}')
                .then(function(response) {{
                  return response.json();
                }})
                .then(function(data) {{
                  console.log(data);
                  var elem = document.getElementById("data");
                  elem.data = data;
                  elem.style.display = "block";

                  var css = document.getElementById("styles").cloneNode(true);
                  elem.shadowRoot.appendChild(css);

                  document.getElementById("loading").style.display = "none";
                }})
                .catch(function(err) {{
                  console.error('Fetch error:', err);
                }});</script>
            </html>"""
        fh, path = tempfile.mkstemp(suffix='.html')
        url = 'file://' + path
        with open(path, 'w') as fp:
            fp.write(collectionInfoHTML)
        webbrowser.open_new(url)


    def actions(self, parent):
        actions = []

        if self.preview:
            action_add_to_project = QAction(QIcon(), "Add Layer to Project", parent)
            action_add_to_project.triggered.connect(self.addToProject)
            actions.append(action_add_to_project)

        action_properties = QAction(QIcon(), "Collection Properties", parent)
        action_properties.triggered.connect(self.viewProperties)
        actions.append(action_properties)

        return actions