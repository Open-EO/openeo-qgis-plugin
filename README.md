# openeo-qgis-plugin
QGIS Plugin to connect and use openEO compliant backends.

Compatible with backends compialnt wit openeo API version 0.4.0 and above. Full functionality is only provided for version 1.0.0-rc2.

Tested with QGIS 3.4.8-Madeira, but works with QGIS >= 3.0.0.

## About

The openEO QGIS Plugin "OpenEO" allows connecting to an openEO backend, managing the user ([batch](https://openeo.org/documentation/1.0/glossary.html#data-processing-modes)) jobs and load the resulting images into a new QGIS Layer. It is also possible to adapt jobs by changing and adding processes. Even though it is generally possible to create own process graphs from scretch it is recommended to use the [openEO web editor](https://editor.openeo.org/).  

### Features

* Listing all openeo compliant backends with minimum API version 0.4.0 listet at the [openEO Hub](http://hub.openeo.org/) 
* Connecting to an openeo compliant backend (openAPI version above 0.4.0, 1.0.0-rc2 recommended)
* Listing all available collections ("Load Collection" combobox) and processes ("Add Process" combobox) including parameters (see table under the process combobox) of the backend
* Spatial extent selection ("Add Spatial Extent" combobox) by: 
    * Current extent of the QGIS map canvas
    * Drawing rectangle/boundingbox on the QGIS map 
    * Drawing polygon on the QGIS map(generates minimum bounding box for the whole polygon area)
    * Load Extent of a QGIS Layer
    * Load Extent from a Shapefile on the filesystem
    * Manual input of the spatial extent
* Temporal extent selection via calendar widgets ("Select Star and End Date" button)
* Creating a new job at the backend ("Create Job" button)
* Adapt existing jobs by adapting process arguments and add new processes to the process graph.
* Open the official openeo web editor at the system browser ("Create New Job in Web Editor" button)
* List all jobs of the user at the backend.
* The jobs can be executed and/or the result displayed at the QGIS map. There is also a description displayed at the job table.
* List of openEO services of the user and possibility to show them in QGIS. 
   
Need some additional features? Leave an issue at this repository!

## Install

There are two options on installing the plugin to your local QGIS Desktop application:

### Install via Plugin Manager

This is the recommended way if you want to get the **most recent stable** version of the plugin.

1. Start QGIS Desktop application
2. Go to "Plugins" and then "Manage and Install Plugins" 
3. Go to "Settings" and make sure that "Show also experimental plugins" is activated
4. Go to "Not Installed" and search for "OpenEO" 
5. Click on "OpenEO" and click "Install"
6. The openEO logo should be visible in the toolbar

### Install from GitHub repository

This is the recommended way if you want to get the **most recent** version of the plugin.

1. Download this repository as zip file
2. Start QGIS Desktop application
3. Go to "Plugins" and then "Manage and Install Plugins" 
4. Click on "Install from ZIP" and choose the downloaded zip file
5. Press "Install Plugin"
6. You may have to activate it in the plugin manager (in "Installed")
7. The openEO logo should be visible in the toolbar

## Usage

First you have to connect to the server with your user credentials in the upper part of the Window. Then all existing jobs are displayed at the "Jobs" tab. There the jobs can be executed and displayed in QGIS. Pressing the "pencil" button on an job entry, a job adaption window will be displayed and the job can be edited and sent as a new job to the backend.  

The following Screenshots show how it looks like:

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/create_processgraph.png" alt="create-processgraph" width="900"/>

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/job_list.png" alt="job-list" width="900"/>

## Building

To build the plugin and deploy to your plugin directory you will need the [pb_tool](http://g-sherman.github.io/plugin_build_tool/) CLI tool.

To compile the plugin run the following command in the root directory of this repository:
 
    pb_tool compile
     
Compiling is needed any time the resources.py file needs to be rebuilt. 

To deploy the application to your QGIS plugins directory run the following command and reload the plugin within QGIS:

    pb_tool deploy 

It's recommended to use the Plugin Reloader plugin within QGIS to easily reload the plugin during development.

## Troubleshooting 

#### QGIS cannot find plugin 

Change pb_tool.cfg settings:

Mac

    plugin_path: /Users/{USER}/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/

Linux

    plugin_path: /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins

Windows

    plugin_path: C:\Users\{USER}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
