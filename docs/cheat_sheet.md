# Contribution cheat-sheet 

Python knowledge and QGIS plugin development knowledge is recommended 

- Plugin source: https://github.com/Open-EO/openeo-qgis-plugin
- PyQGIS developer cookbook: https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/index.html
- QGIS Python API: https://qgis.org/pyqgis/master/
- QGIS source: https://github.com/qgis/QGIS
- openEO python client documentation: https://openeo.org/documentation/1.0/python/

## Directory

```
.
├── compile_ui.sh
├── html
├── images
├── LICENSE
├── openeo_plugin
│   ├── gui
│   ├── i18n
│   ├── images
│   ├── __init__.py
│   ├── metadata.txt
│   ├── models
│   ├── requirements.txt
│   ├── resources.py
│   ├── resources.qrc
│   ├── scripts
│   └── utils
├── README.md
└── requirements-dev.txt
```

`./openeo_plugin` contains the main data of the python plugin

## Development cheat-sheet

### Setup

- clone repository: `git clone https://github.com/Open-EO/openeo-qgis-plugin`
- Find QGIS profile directory. In QGIS: `Settings > User Profiles > Open Active Profile Folder`
- create a symbolic link of `./openeo_plugin` in your qgis profile folder at `.../profiles/{profile_name}/python/plugins/`. This installs your in-development plugin into QGIS.
- Install the QGIS plugin "qpip": https://plugins.qgis.org/plugins/a00_qpip/ if the openEO python-client is not installed globally. This allows you to install `openeo` into your QGIS python environment.
- Install the QGIS plugin "Plugin Reloader": https://plugins.qgis.org/plugins/plugin_reloader/. This allows you to reload your plugin after you have made changes, without having to restart QGIS.

### GUI

To build the plugin GUI files you will need the [pb_tool](http://g-sherman.github.io/plugin_build_tool/) CLI tool.

If you wish to make alterations to the QT-based modals of the plugin (login- and connect-dialog), edit the `.ui` files in `./gui/ui` with the QT editor of your choice. Once done, run the script in `./compile_ui.sh` to generate the `.py` files of your gui elements.

> NOTE:
> Treat the `.ui` files as your "ground truth". While manual changes to the `.py` files in `./gui/ui` are possible, they become overwritten as soon as the `compile_ui.sh` script is run.

### Program structure

The plugin makes use of the QGIS Python API: https://qgis.org/pyqgis/master/.
It is heavily recommended to keep it nearby for reference, as most of the classes within the plugin are specializations of classes from the Python API.

- Entrypoint: `./__init__.py`
	- Here, the `OpenEO.initGui()` method serves to set up the root of the plugin within the QGIS browser

#### Browser Items

Within the QGIS browser, the nested elements are specializations of the class [QgsDataItem](https://qgis.org/pyqgis/master/core/QgsDataItem.html) and its descendants.

- The root of the Plugin elements within the Browser is the class `OpenEORootItem(QgsDataCollectionItem)`. 
	- its children are created in `OpenEORootItem.createChildren()`. Other classes that are capable of bearing children use the same method.

- The right-click menu of a data-item is defined in the class method `actions()`.
- Each openEO data-item refers to the root-class `OpenEO` by the attribute `self.plugin`
- Each openEO data-item refers to its parent item by the attribute `self.parent()`
- Each openEO data-item that is part of a connection refers to openEO-python-client representation of said connection by `self.getConnection()`.

### Dependencies

Development uses on the following dev-dependencies:

```bash
pip install -r requirements-dev.txt  # For development
```

### Debugging

- **Python Console**: Use the QGIS Python Console (`Plugins > Python Console`) to debug and test code interactively
- For debugging using breakpoints, use the plugin **QGIS devtools**: https://plugins.qgis.org/plugins/devtools/

### Code Style

Follow PEP 8 Python code style guidelines. Use the tools specified in `requirements-dev.txt` for linting and formatting. Use the ruff pre-commit hook to automatically check code style before committing.

