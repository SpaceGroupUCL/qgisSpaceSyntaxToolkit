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

from PyQt4 import QtCore, QtGui
from ui_DepthmapAdvanced import Ui_DepthmapAdvancedDialog


class DepthmapAdvancedDialog(QtGui.QDialog, Ui_DepthmapAdvancedDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)

        # internal GUI signals
        self.axialDistanceCombo.currentIndexChanged.connect(self.setDistanceType)
        self.axialRadiusCombo.currentIndexChanged.connect(self.setRadiusType)

        # hide unused UI buttons
        self.axialDistanceLabel.hide()
        self.axialDistanceCombo.hide()

    def setDistanceType(self, idx):
        self.axialDistanceCombo.setCurrentIndex(idx)

    def setRadiusType(self, idx):
        self.axialRadiusCombo.setCurrentIndex(idx)

    def setCalculateNorm(self,onoff):
        self.axialCalculateNormCheck.setChecked(onoff)

    def setCalculateFull(self,onoff):
        self.axialCalculateFullCheck.setChecked(onoff)

    def setCalculateChoice(self,onoff):
        self.axialCalculateChoiceCheck.setChecked(onoff)