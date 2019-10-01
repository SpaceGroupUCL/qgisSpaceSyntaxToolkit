# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetworkCleaner
                                 A QGIS plugin
 This plugin cleans the road centre line topology
                             -------------------
        begin                : 2016-10-10
        copyright            : (C) 2016 by Spece Syntax Ltd
        email                : I.Kolovou@spacesyntax.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RoadNetworkCleaner class from file RoadNetworkCleaner.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from road_network_cleaner import RoadNetworkCleaner
    return RoadNetworkCleaner(iface)
