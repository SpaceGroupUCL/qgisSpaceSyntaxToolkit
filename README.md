qgisSpaceSyntaxToolkit
======================

# Space Syntax Toolkit for QGIS

The “Space Syntax Toolkit” is a [QGIS](http://www.qgis.org/en/site/) plug-in for spatial network and statistical analysis. It provides a front-end for the [depthmapX](https://varoudis.github.io/depthmapX/) software within QGIS, offering user friendly space syntax analysis workflows in a GIS environment. It is primarily aimed at supporting the standard space syntax methodology, and enhancing its workflows with standard GIS data, analysis and visualisation features. However, the added functionality can be of general benefit to QGIS users by introducing new tools for exploratory spatial data analysis. The plug-in is being developed by Jorge Gil at the Space Syntax Laboratory, The Bartlett, UCL.

Currently the “Space Syntax Toolkit” consists of two modules: “Graph analysis” and “Attributes explorer”.
The “Graph analysis” module supports the verification and analysis of the spatial network model. This consists of an axial map layer, representing the urban street network, and an unlinks layer, indicating bridges and tunnels with no level crossing. The module offers a verification tool to check the geometric and topological integrity of each layer, helping correct any problems before running the analysis. The axial and segment analysis is performed in depthmapXnet, via a direct link from QGIS, which receives and prepares the results once the calculations are completed.
The “Attributes explorer” module supports the visual and statistical exploration of the analysis results. It provides quick analysis of individual quantitative attributes of a selected layer, mapping the values using simplified symbology settings, displaying essential descriptive statistics, and plotting basic interactive charts (histogram and scatter plot).


## Where to find...
* The toolkit source code can be downloaded from the 'esstools' folder.
* The latest packaged plug-in can be found in the 'downloads' folder. It includes installation instructions. At the moment it is not yet available as a QGIS managed plugin.
* Documentation can be obtained from the 'documents' folder.
* A sample dataset is in the 'data' folder, for experimenting with the plugin and following the documentation .

## Requirements
* QGIS (2.0 or above) - [http://www.qgis.org/en/site/](http://www.qgis.org/en/site/)

For complete functionality and optimal performance the plugin has the following pre-requisites:
* depthmapXnet - [http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet](http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet)
* python igraph - [http://igraph.org/python/](http://igraph.org/python/)
* pyqtgraph - [http://www.pyqtgraph.org/](http://www.pyqtgraph.org/)

