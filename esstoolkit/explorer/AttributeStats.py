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
# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *

from .. import utility_functions as uf


class AttributeStats(QThread):
    calculationFinished = pyqtSignal(dict, list)
    calculationProgress = pyqtSignal(int)
    calculationError = pyqtSignal(str)

    def __init__(self, parentThread, parentObject, layer, attribute):
        QThread.__init__(self, parentThread)
        self.parent = parentObject
        self.running = False
        self.layer = layer
        self.attribute = attribute


    def run(self):
        pass