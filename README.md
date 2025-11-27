# openeo-qgis-plugin
QGIS Plugin to connect and use openEO compliant backends.

Compatible with backends compliant with openEO API version 1.0.0 and above.

Minimum required version QGIS 3.8. tested on 3.42

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

### Install via Plugin Browser

Not yet supported

### Install from GitHub repository

This is the recommended way if you want to get the **most recent** version of the plugin.

1. Download or clone the repository `git clone https://github.com/Open-EO/openeo-qgis-plugin`
2. navigate into the plugin directory `cd openeo-qgis-plugin`
3. zip the plugin directory `zip -r openeo_plugin.zip openeo_plugin
4. open QGIS and select "Plugins" > "Manage and install Plugins"
5. select "Install from ZIP", choose the created zip file, and press "Install Plugin"
![Install from Zip dialog](images/plugins_install.png)
6. The plugin "qpip" will be installed as a dependency. This is currently used to install the required openeo python client dependencies
	- Press "OK" on the Plugin Dependencies Manager prompt, then press "OK" on the qpip prompt 
    ![plugin dependency manager asking to install qpip](images/plugin_dependencies.png)
    ![qpip asking to install python dependencies](images/qpip.png)
7. After a successful installation, an "openEO" entry will be visible in the QGIS browser on the left side 
    ![alt text](images/browser_view.png)

#### Troubleshooting
If the installation of qpip or openeo does not happen automatically, try installing qpip beforehand using the plugin manager.
if use of qpip is not desired, `pip install openeo` may be used to install the necessary python dependency.

## Usage

1. After successful installation, an "openEO" entry will be visible in the QGIS Browser (the resource manager that can usually be found on the left side).
2. Create a new openEO connection by right clicking and either selecting a provider from the available list provided by openEO Hub or enter connection details by yourself
3. You may now expand the openEO entry with the little "Plus" symbol that appears next to it
4. (Optional) Right click on the created connection and select "log In" to authenticate your connection.
5. you can find collections, batch jobs, and web services that are visible to the authenticated user inside the folder icons with the corresponding names.

## Development

To build the plugin and deploy to your plugin directory you will need the [pb_tool](http://g-sherman.github.io/plugin_build_tool/) CLI tool.

To compile the plugin run the following command in the `./openeo_plugin` directory of this repository:
 
    pb_tool compile
     
Compiling is needed any time the resources.py file needs to be rebuilt. 
