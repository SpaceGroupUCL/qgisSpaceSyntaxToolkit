qgisSpaceSyntaxToolkit
======================

# Space Syntax Toolkit for QGIS

## News
03.06.2016 – Subscribe to the new [Space Syntax Toolkit mailing list on JISCMAIL](https://www.jiscmail.ac.uk/cgi-bin/webadmin?A0=SPACESYNTAX-TOOLKIT) for discussions, suggestions, and the latest news. You can send an e-mail to the list (spacesyntax-toolkit at jiscmail.ac.uk) if you need support using the toolkit.

## About
The “Space Syntax Toolkit” is a [QGIS](http://www.qgis.org/en/site/) plug-in for spatial network and statistical analysis. It provides a front-end for the [depthmapX](https://varoudis.github.io/depthmapX/) software within QGIS, offering user friendly space syntax analysis workflows in a GIS environment. It is primarily aimed at supporting the standard space syntax methodology, and enhancing its workflows with standard GIS data, analysis and visualisation features. However, the added functionality can be of general benefit to QGIS users by introducing new tools for exploratory spatial data analysis. The plug-in was originally developed by Jorge Gil for the Space Syntax Laboratory, The Bartlett, UCL.

Currently the “Space Syntax Toolkit” consists of two modules: “Graph analysis” and “Attributes explorer”.
The “Graph analysis” module supports the verification and analysis of the spatial network model. This consists of an axial map layer, representing the urban street network, and an unlinks layer, indicating bridges and tunnels with no level crossing. The module offers a verification tool to check the geometric and topological integrity of each layer, helping correct any problems before running the analysis. The axial and segment analysis is performed in depthmapXnet, via a direct link from QGIS, which receives and prepares the results once the calculations are completed.
The “Attributes explorer” module supports the visual and statistical exploration of the analysis results. It provides quick analysis of individual quantitative attributes of a selected layer, mapping the values using simplified symbology settings, displaying essential descriptive statistics, and plotting basic interactive charts (histogram and scatter plot).

## Installation
The plug-in can be installed from the QGIS Plugins Manager, and updates become automatically available once submitted to the QGIS plugins repository.

## Support
If you encounter problems when using the software, please check the documentation and the current issues list for solutions. If it's a new problem, you can add the issue to the list.
If you need help using the toolkit in your space syntax research, you can send an e-mail to the mailing list (spacesyntax-toolkit at jiscmail.ac.uk) for support from the user community.

## Software Requirements
* QGIS (2.0 or above) - [http://www.qgis.org/en/site/](http://www.qgis.org/en/site/)
* depthmapXnet - [http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet](http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet)

## Where to find...
* The toolkit source code can be downloaded from the 'esstoolkit' folder.
* Documentation can be obtained from the 'documents' folder.
* A sample dataset is in the 'data' folder, for experimenting with the plugin and following the documentation.
* The latest release can be found in the 'releases' tab. The easiest way to obtain the above materials is from the zip file of the latest release. 

## More about space syntax theory and methods...
To better aunderstand and be able to use the plug-in more effectively, users must become familiar with space syntax theories and methods. These are two essential resources:
* Online Training Platform: [http://otp.spacesyntax.net/](http://otp.spacesyntax.net/)
* Space Syntax methodology. A teaching textbook for the MSc Spatial Design: Architecture & Cities: [http://discovery.ucl.ac.uk/1415080/](http://discovery.ucl.ac.uk/1415080/)
