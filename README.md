qgisSpaceSyntaxToolkit
======================

# Space Syntax Toolkit for QGIS

The “Space Syntax Toolkit” is a [QGIS](http://www.qgis.org/en/site/) plug-in for spatial network and statistical analysis. It provides a front-end for the [depthmapX](https://varoudis.github.io/depthmapX/) software within QGIS, offering user friendly space syntax analysis workflows in a GIS environment. It is primarily aimed at supporting the standard space syntax methodology, and enhancing its workflows with standard GIS data, analysis and visualisation features. However, the added functionality can be of general benefit to QGIS users by introducing new tools for exploratory spatial data analysis. The plug-in is being developed by Jorge Gil at the Space Syntax Laboratory, The Bartlett, UCL.

Currently the “Space Syntax Toolkit” consists of two modules: “Graph analysis” and “Attributes explorer”.
The “Graph analysis” module supports the verification and analysis of the spatial network model. This consists of an axial map layer, representing the urban street network, and an unlinks layer, indicating bridges and tunnels with no level crossing. The module offers a verification tool to check the geometric and topological integrity of each layer, helping correct any problems before running the analysis. The axial and segment analysis is performed in depthmapXnet, via a direct link from QGIS, which receives and prepares the results once the calculations are completed.
The “Attributes explorer” module supports the visual and statistical exploration of the analysis results. It provides quick analysis of individual quantitative attributes of a selected layer, mapping the values using simplified symbology settings, displaying essential descriptive statistics, and plotting basic interactive charts (histogram and scatter plot).

## Where to find...
* The toolkit source code can be downloaded from the 'esstoolkit' folder.
* The latest release can be found in the 'releases' tab. The plugin is not yet available in the QGIS plugins manager, installation instructions are below.
* Documentation can be obtained from the 'documents' folder.
* A sample dataset is in the 'data' folder, for experimenting with the plugin and following the documentation .

## Requirements
* QGIS (2.0 or above) - [http://www.qgis.org/en/site/](http://www.qgis.org/en/site/)
* depthmapXnet - [http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet](http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet)

## Installation
At the moment, the plug-in is not available through the QGIS plugins repository and plugins manager. To install it you need to download and unzip the esstoolkit.zip file and copy the esstoolkit folder into the QGIS plugins directory:
* MS Windows: C:\Users\[your user name]\.qgis2\python\plugins\
* Mac OSX: Users/[your user name]/.qgis2/python/plugins/
* Linux: home/[your user name]/.qgis2/python/plugins/

This directory is in a hidden folder and you must make hidden files visible.
Under Mac OSX, you can also open it in Finder by selecting 'Go > Go To Folder...' and typing '~/.qgis2/python/plugins/'.

If you cannot find it it's because you haven't installed any QGIS plugins yet. You can either install one plugin, or create the 'python/plugins' folder manually.

After copying the esstoolkit folder, once you start QGIS the 'Space Syntax Toolkit' plugin will be available in the plugin manager window. Check the box next to it to load the plugin and create the menu and toolbar buttons.
To use any of the tools select the appropriate button in the plugins toolbar, or in the 'Space Syntax Toolkit' section of the 'Plugins' menu.
