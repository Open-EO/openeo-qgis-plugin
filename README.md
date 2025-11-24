# openeo-qgis-plugin
QGIS Plugin to connect and use openEO compliant backends.

Compatible with backends compliant with openEO API version 1.0.0 and above. Full functionality is only provided for version 1.0.0-rc2.

Minimum required version QGIS 3.8

## About

The openEO QGIS Plugin "OpenEO" allows connecting to openEO backends, list the user ([batch](https://openeo.org/documentation/1.0/glossary.html#data-processing-modes)) jobs and load the resulting images into a new QGIS Layer. For creating process graphs, it is recommended to use the [openEO web editor](https://editor.openeo.org/).  

### Features

* List all openEO compliant backends listed at the [openEO Hub](http://hub.openeo.org/) 
* Connect to an openEO compliant backend
* Authenticate connections to backends: Supports:
    * Basic authentication (username, password)
    * OpenID Connect authentication (device code flow)
* List available collections, Web services, and Batch Jobs in the Qgis Browser
* Add Preview of available Collections as QGIS Layers
* Add web services as QGIS Layers
* Add Batch Job results as QGIS Layers
* View Details for:
    * Connections
    * Batch Jobs
    * Collections
    * Web Services
* Open the official openEO Web Editor in the systems system browser
   
Need some additional features? Leave an issue at this repository!

## Install

There are two options on installing the plugin to your local QGIS Desktop application:

### Install via Plugin Manager

Not yet supported (TODO)

### Install from GitHub repository

This is the recommended way if you want to get the **most recent** version of the plugin.

**TODO: may need steps for the openEO python dependency**

1. Download or clone this repository
2. compress the `./openeo_plugin` directory in a .zip file
2. Start QGIS Desktop application
3. Go to "Plugins" and then "Manage and Install Plugins" 
4. Click on "Install from ZIP" and choose the created zip file
5. Press "Install Plugin"
6. You may have to activate it in the plugin manager (in "Installed")
7. The openEO logo should be visible in the toolbar

## Usage

1. After successful installation, an "openEO" entry will be visible in the QGIS Browser (the resource manager that can usually be found on the left side).
2. Create a new openEO connection by right clicking and either selecting a provider from the available list provided by openEO Hub or enter connection details by yourself
3. You may now expand the openEO entry with the little "Plus" symbol that appears next to it
4. (Optional) Right click on the created connection and select "log In" to authenticate your connection.
5. you can find collections, batch jobs, and web services that are visible to the authenticated user inside the folder icons with the corresponding names.

**TODO: add screenshots**

## Building

To build the plugin and deploy to your plugin directory you will need the [pb_tool](http://g-sherman.github.io/plugin_build_tool/) CLI tool.

To compile the plugin run the following command in the `./openeo_plugin` directory of this repository:
 
    pb_tool compile
     
Compiling is needed any time the resources.py file needs to be rebuilt. 

## Troubleshooting 

TODO
