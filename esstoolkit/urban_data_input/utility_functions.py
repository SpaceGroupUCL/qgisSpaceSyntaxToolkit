# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UrbanDataInputDockWidget
                                 A QGIS plugin
 Urban Data Input Tool for QGIS
                             -------------------
        begin                : 2016-06-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Abhimanyu Acharya/ Space Syntax Limited
        email                : a.acharya@spacesyntax.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import print_function
from builtins import str
from qgis.core import (QgsProject, QgsMapLayer, QgsDataSourceUri, QgsVectorLayer, QgsMessageLog, Qgis)
import os.path
import psycopg2

import traceback
from qgis.PyQt.QtCore import QSettings
import operator
import itertools

from .. import layer_field_helpers as lfh

def isRequiredLayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = lfh.getFieldNames(layer)
        if 'f_group' in fieldlist and 'f_type' in fieldlist:
            return True

    return False

def isRequiredEntranceLayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = lfh.getFieldNames(layer)
        if 'e_category' in fieldlist and 'e_subcat' in fieldlist:
            return True

    return False

def isRequiredLULayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = lfh.getFieldNames(layer)
        if 'gf_cat' in fieldlist and 'gf_subcat' in fieldlist:
            return True

    return False
