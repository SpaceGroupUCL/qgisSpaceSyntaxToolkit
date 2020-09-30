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

from .ui_VerificationSettings import Ui_VerificationSettingsDialog
from esstoolkit.utilities import utility_functions as uf


class VerificationSettingsDialog(QtWidgets.QDialog, Ui_VerificationSettingsDialog):
    def __init__(self, settings):
        QtWidgets.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.setupUi(self)

        # internal GUI signals
        self.axialThresholdEdit.editingFinished.connect(self.checkSettingsValues)
        self.axialMinimumEdit.editingFinished.connect(self.checkSettingsValues)
        self.unlinksThresholdEdit.editingFinished.connect(self.checkSettingsValues)
        self.linksThresholdEdit.editingFinished.connect(self.checkSettingsValues)
        self.closeButtonBox.accepted.connect(self.updateSettings)
        self.closeButtonBox.rejected.connect(self.restoreSettings)

        # hide unused UI buttons
        self.linksThresholdLabel.hide()
        self.linksThresholdEdit.hide()

        #
        self.ok = self.closeButtonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.settings = settings
        self.restoreSettings()

    def checkSettingsValues(self):
        ax_min = self.axialMinimumEdit.text()
        ax_dist = self.axialThresholdEdit.text()
        unlink_dist = self.unlinksThresholdEdit.text()
        link_dist = self.linksThresholdEdit.text()
        if uf.isNumeric(ax_min) and uf.isNumeric(ax_dist) and uf.isNumeric(unlink_dist) and uf.isNumeric(link_dist):
            self.ok.setDisabled(False)
        else:
            self.ok.setToolTip("Check if the settings values are correct.")
            self.ok.setDisabled(True)

    def restoreSettings(self):
        self.axialThresholdEdit.setText(str(self.settings['ax_dist']))
        self.axialMinimumEdit.setText(str(self.settings['ax_min']))
        self.unlinksThresholdEdit.setText(str(self.settings['unlink_dist']))
        self.linksThresholdEdit.setText(str(self.settings['link_dist']))

    def updateSettings(self):
        self.settings['ax_dist'] = float(self.axialThresholdEdit.text())
        self.settings['ax_min'] = float(self.axialMinimumEdit.text())
        self.settings['unlink_dist'] = float(self.unlinksThresholdEdit.text())
        self.settings['link_dist'] = float(self.linksThresholdEdit.text())
