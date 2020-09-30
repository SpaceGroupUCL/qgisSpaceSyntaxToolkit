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

from builtins import str

from qgis.PyQt import QtWidgets

from .ui_DepthmapAdvanced import Ui_DepthmapAdvancedDialog


class DepthmapAdvancedDialog(QtWidgets.QDialog, Ui_DepthmapAdvancedDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)

        # internal GUI signals
        self.axialDistanceCombo.currentIndexChanged.connect(self.setDistanceType)
        self.axialRadiusCombo.currentIndexChanged.connect(self.setRadiusType)
        self.axialStubsEdit.editingFinished.connect(self.checkRemoveStubs)

        # hide unused UI buttons
        self.axialDistanceLabel.hide()
        self.axialDistanceCombo.hide()

    def setDistanceType(self, idx):
        self.axialDistanceCombo.setCurrentIndex(idx)

    def disableDistanceType(self, onoff):
        self.axialDistanceLabel.setDisabled(onoff)
        self.axialDistanceCombo.setDisabled(onoff)

    def setRadiusType(self, idx):
        self.axialRadiusCombo.setCurrentIndex(idx)

    def disableRadiusType(self, onoff):
        self.axialRadiusLabel.setDisabled(onoff)
        self.axialRadiusCombo.setDisabled(onoff)

    def setCalculateNorm(self, onoff):
        self.axialCalculateNormCheck.setChecked(onoff)

    def disableCalculateNorm(self, onoff):
        self.axialCalculateNormCheck.setDisabled(onoff)

    def setCalculateFull(self, onoff):
        self.axialCalculateFullCheck.setChecked(onoff)

    def disableCalculateFull(self, onoff):
        self.axialCalculateFullCheck.setDisabled(onoff)

    def setCalculateChoice(self, onoff):
        self.axialCalculateChoiceCheck.setChecked(onoff)

    def setRemoveStubs(self, value):
        self.axialStubsEdit.clear()
        self.axialStubsEdit.setText(str(value))

    def disableRemoveStubs(self, onoff):
        self.axialStubsLabel.setDisabled(onoff)
        self.axialStubsEdit.setDisabled(onoff)

    def checkRemoveStubs(self):
        try:
            int(self.axialStubsEdit.text())
            self.closeButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(False)
            self.closeButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setToolTip('')
        except ValueError:
            self.closeButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setDisabled(True)
            self.closeButtonBox.button(QtWidgets.QDialogButtonBox.Ok).setToolTip(
                'Please enter a valid stubs removal % (integer).')
