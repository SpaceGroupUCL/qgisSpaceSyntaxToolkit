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
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import *

from . import utility_functions as uf

# import toolkit settings dialog
from .ui_Settings import Ui_SettingsDialog

class SettingsManager(QObject):

    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface
        self.dlg = SettingsDialog()

    def showDialog(self):
        self.dlg.show()

    def getLastDir(self):
        settings = QSettings()
        return settings.value("/esst/lastUsedDir","")

    def setLastDir(self, path):
        settings = QSettings()
        save_path = QFileInfo(path).filePath()
        settings.setValue("/esst/lastUsedDir", save_path)

class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self):

        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        # set up internal GUI signals
        self.closeButtonBox.rejected.connect(self.close)
