# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""
This script initializes the plugin, making it known to QGIS.
"""

from __future__ import absolute_import


def classFactory(iface):
    # load essToolkit class from file essToolkit
    from .EssToolkit import EssToolkit
    return EssToolkit(iface)
