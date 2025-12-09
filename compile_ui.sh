#!/bin/bash
pyuic6 -x openeo_plugin/gui/ui/login_dialog.ui -o openeo_plugin/gui/ui/login_dialog.py
pyuic6 -x openeo_plugin/gui/ui/connect_dialog.ui -o openeo_plugin/gui/ui/connect_dialog.py

#replace the imports from PyQt6 with the PyQt version provided by qgis
sed -i 's/from PyQt6 import/from qgis.PyQt import/g' openeo_plugin/gui/ui/login_dialog.py
sed -i 's/from PyQt6 import/from qgis.PyQt import/g' openeo_plugin/gui/ui/connect_dialog.py