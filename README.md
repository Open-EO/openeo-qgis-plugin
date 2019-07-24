# openeo-qgis-plugin
QGIS Plugin to connect and use openEO compliant backends.


## About

The openEO QGIS Plugin "OpenEO Connector" allows for connecting to an openEO backend, managing the user jobs and load the results into a new QGIS Layer. It is also possible to create a new job, by defining a custom process graph and sending it to the backend. The process graph editor is in an early stage, so it is recommended to just copy the complete process graph into the process graph text field.  

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

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/create_processgraph.png" alt="create-processgraph" width="700"/>

<img src="https://github.com/Open-EO/openeo-qgis-plugin/raw/master/examples/job_list.png" alt="job-list" width="700"/>


## Troubleshooting 

#### QGIS cannot find plugin 

Change pb_tool.cfg settings:

Mac

    plugin_path: /Users/{USER}/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/

Linux

    plugin_path: /home/{USER}/.local/share/QGIS/QGIS3/profiles/default/python/plugins

Windows

    plugin_path: C:\Users\{USER}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
