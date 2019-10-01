# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrawingTool
                                 A QGIS plugin
 Drawing tool for axial lines, segment lines and unlinks.
                             -------------------
        begin                : 2019-06-16
        copyright            : (C) 2019 by Space Syntax Limited
        email                : i.kolovou@spaceyntax.com
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
    """Load DrawingTool class from file DrawingTool.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .DrawingTool import DrawingTool
    return DrawingTool(iface)
