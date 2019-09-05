# openeo-qgis-plugin
QGIS Plugin to connect and use openEO compliant backends.

Compatible with openeo API version 0.4.0 and above

Tested with QGIS 3.4.8-Madeira

## About

The openEO QGIS Plugin "OpenEO Connector" allows for connecting to an openEO backend, managing the user jobs and load the results into a new QGIS Layer. It is also possible to create a new job, by defining a custom process graph and sending it to the backend. The process graph editor is in an early stage, so it is recommended to just copy the complete process graph into the process graph text field.  

### Features

* Connecting to an openeo compliant backend (openAPI version above 0.4.0)
* Listing all available collections ("Load Collection" combobox) and processes ("Add Process" combobox) including parameters (see table under the process combobox) of the backend
* Spatial extent selection ("Add Spatial Extent" combobox) by: 
    * Current extent of the QGIS map canvas
    * Drawing rectangle/boundingbox on the QGIS map 
    * Drawing polygon on the QGIS map(generates minimum bounding box for the whole polygon area)
    * Load Extent of a QGIS Layer
    * Load Extent from a Shapefile on the filesystem
    * Manual input of the spatial extent
* Temporal Extent selection via calendar widgets ("Select Star and End Date" button)
* Creating a "load_collection" process with the selected spatial filter, temporal filter and collection id ("Load" button)
* Sending the process graph ("Process Graph" text field) to the backend to create a new job at the backend ("Create Job" button)
* Open the official openeo web editor at the system browser ("Create New Job in Web Editor" button)
* List all jobs of the user at the backend.
* The jobs can be executed or the result displayed at the QGIS map. There is also a description or error message displayed at the job table.
   
Need some additional features? Leave an issue at this repository!

## Building

To build the plugin and deploy to your plugin directory you will need the [pb_tool](http://g-sherman.github.io/plugin_build_tool/) CLI tool.

To compile the plugin run the following command in the root directory of this repository:
 
    pb_tool compile
     
Compiling is needed any time the resources.py file needs to be rebuilt. 

To deploy the application to your QGIS plugins directory run the following command and reload the plugin within QGIS:

    pb_tool deploy 

It's recommended to use the Plugin Reloader plugin within QGIS to easily reload the plugin during development.

## Usage

First you have to connect to the server with your user credentials in the upper part of the Window. Then all existing jobs are displayed at the "Jobs" tab. There the jobs can be executed again or displayed in QGIS. In the "New Job" tab it is possible to create a new process graph and to send it to the backend to create a new job. The process graph editor is in an early stage, so it is recommended to just copy the complete process graph into the process graph text field. 

The following Screenshots show how it looks like:

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/create_processgraph.png" alt="create-processgraph" width="900"/>

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/job_list.png" alt="job-list" width="900"/>



## Troubleshooting 

#### QGIS cannot find plugin 

Change pb_tool.cfg settings:

Mac

    plugin_path: /Users/{USER}/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/

Linux

    plugin_path: /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins

Windows

    plugin_path: C:\Users\{USER}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
