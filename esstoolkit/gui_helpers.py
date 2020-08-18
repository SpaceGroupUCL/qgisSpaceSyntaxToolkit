# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essToolkit
                            Space Syntax Toolkit
 Set of tools for essential space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015, UCL
        author               : Jorge Gil
        email                : jorge.gil@ucl.ac.uk
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

from builtins import zip
from builtins import str
from builtins import range
from qgis.PyQt.QtCore import (QVariant, QSettings)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (QgsProject, QgsMapLayer, QgsDataSourceUri, QgsVectorLayer, QgsCredentials, QgsVectorDataProvider, QgsFields, QgsField, QgsPoint, QgsGeometry, QgsFeature, QgsVectorFileWriter, QgsFeatureRequest, QgsSpatialIndex, QgsCoordinateTransformContext, QgsWkbTypes)

import psycopg2 as pgsql
import numpy as np

import os.path
import math
import sys
from itertools import zip_longest

#------------------------------
# General functions
#------------------------------
# Display an error message via Qt message box
def pop_up_error(msg=''):
    # newfeature: make this work with the new messageBar
    QMessageBox.warning(None, 'error', '%s' % msg)


#------------------------------
# Canvas functions
#------------------------------
# Display a message in the QGIS canvas
def showMessage(iface, msg, type='Info', lev=1, dur=2):
    iface.messageBar().pushMessage(type,msg,level=lev,duration=dur)


def getCanvasColour(iface):
    colour = iface.mapCanvas().canvasColor()
    return colour