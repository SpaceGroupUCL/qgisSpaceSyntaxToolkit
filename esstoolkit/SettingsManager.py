# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015 UCL, Jorge Gil
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from . import utility_functions as uf

# import toolkit settings dialog
from ui_Settings import Ui_SettingsDialog

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
        settings.setValue("/esst/lastUsedDir", QFileInfo(path).filePath())

class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self):

        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        # set up internal GUI signals
        QObject.connect(self.closeButtonBox,SIGNAL("rejected()"),self.close)
