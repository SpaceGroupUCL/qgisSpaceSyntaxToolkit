# Space Syntax Toolkit for QGIS

## News
03.07.2017 - SST workshop at the 11th International Space Syntax Symposium, in Lisbon, Portugal

30.06.2017 - SST 0.2.0 has been released, including several new modules.

06.11.2016 - For the latest information on the Space Syntax Toolkit you should now consult the [Wiki](https://github.com/SpaceGroupUCL/qgisSpaceSyntaxToolkit/wiki) and its [FAQ](https://github.com/SpaceGroupUCL/qgisSpaceSyntaxToolkit/wiki).

03.06.2016 – Subscribe to the new [Space Syntax Toolkit mailing list on JISCMAIL](https://www.jiscmail.ac.uk/cgi-bin/webadmin?A0=SPACESYNTAX-TOOLKIT) for discussions, suggestions, and the latest news. You can send an e-mail to the list (spacesyntax-toolkit at jiscmail.ac.uk) if you need support using the toolkit.

## About
The “Space Syntax Toolkit” is a [QGIS](http://www.qgis.org/en/site/) plugin offering user friendly space syntax analysis workflows in a GIS environment. It provides a front-end for the [depthmapX](https://varoudis.github.io/depthmapX/) software within QGIS, for seamless spatial network analysis. Furthermore, it includes tools for urban data management and analysis, namely land use, entrances, frontages, pedestrian movement, road centre lines, and service areas.

Originally developed by Jorge Gil at the Space Syntax Laboratory, The Bartlett, UCL, the plugin includes contributions from:
* [Space Syntax Limited](https://github.com/spacesyntax) - Ioanna Kovolou, Abhimanyu Acharya, Stephen Law, Laurens Versluis

## Installation
The plug-in can be installed from the QGIS Plugins Manager, and updates become automatically available once submitted to the QGIS plugins repository.

## Software Requirements
* QGIS (2.14 or above) - [http://www.qgis.org/en/site/](http://www.qgis.org/en/site/)
* depthmapXnet - [http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet](http://archtech.gr/varoudis/depthmapX/?dir=depthmapXnet)

## Support
If you need help using the toolkit in your space syntax research, you can send an e-mail to the mailing list (spacesyntax-toolkit@jiscmail.ac.uk) for support from the user community.
If you encounter problems when using the software, please check the [Wiki](https://github.com/SpaceGroupUCL/qgisSpaceSyntaxToolkit/wiki) and the current [issues list](https://github.com/SpaceGroupUCL/qgisSpaceSyntaxToolkit/issues) for solutions. If it's a new problem, you can add the issue to the [issues list](https://github.com/SpaceGroupUCL/qgisSpaceSyntaxToolkit/issues).

## Where to find...
* The toolkit source code can be downloaded from the 'esstoolkit' folder.
* Documentation can be obtained from the 'documents' folder.
* A sample dataset is in the 'data' folder, for experimenting with the plugin and following the documentation.

## Development notes:
* Development of this module has been done primarily using PyCharm, with the top folder (qgisSpaceSyntaxToolkit) selected and the QGIS python selected as an interpreter. This allows for having a similar module loading process as QGIS itself.
* Unit tests reside in the esstoolkit/tests directory, but have to be carrie out from the top directory of the repository (qgisSpaceSyntaxToolkit).
