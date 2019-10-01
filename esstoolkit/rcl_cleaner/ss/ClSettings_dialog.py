# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetworkCleanerDialog
                                 A QGIS plugin
 This plugin clean a road centre line map.
                             -------------------
        begin                : 2016-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Space SyntaxLtd
        email                : i.kolovou@spacesyntax.com
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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, Qt

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ClSettings_dialog_base.ui'))


class ClSettingsDialog(QtGui.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(ClSettingsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.invalidsCheckBox.setDisabled(True)
        self.invalidsCheckBox.setChecked(True)

        self.pointsCheckBox.setDisabled(True)
        self.pointsCheckBox.setChecked(True)
        self.multipartsCheckBox.setDisabled(True)
        self.multipartsCheckBox.setChecked(True)
        self.selfinterCheckBox.setDisabled(True)
        self.selfinterCheckBox.setChecked(True)
        self.duplicatesCheckBox.setDisabled(True)
        self.duplicatesCheckBox.setChecked(True)
        self.overlapsCheckBox.setDisabled(True)
        self.overlapsCheckBox.setChecked(True)
        self.closedplCheckBox.setDisabled(True)
        self.closedplCheckBox.setChecked(True)

        self.breakCheckBox.setDisabled(True)
        self.breakCheckBox.setChecked(True)
        self.mergeCheckBox.setDisabled(True)
        self.mergeCheckBox.setChecked(True)
        self.orphansCheckBox.setDisabled(True)
        self.orphansCheckBox.setChecked(True)


    def getCleaningSettings(self):
        return {'break': self.breakCheckBox.isChecked(), 'merge': self.mergeCheckBox.isChecked(), 'orphans': self.orphansCheckBox.isChecked()}

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()