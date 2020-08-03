# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NetworkSegmenter
                                 A QGIS plugin
 This plugin segments an axial map
                             -------------------
        begin                : 2018-02-23
        copyright            : (C) 2018 by Space Syntax Ltd.
        email                : i.kolovou@spacesyntax.com
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
from __future__ import absolute_import


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NetworkSegmenter class from file NetworkSegmenter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .network_segmenter import NetworkSegmenter
    return NetworkSegmenter(iface)
