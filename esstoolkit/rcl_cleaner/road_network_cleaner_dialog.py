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
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, Qt

import os.path
import resources

from DbSettings_dialog import DbSettingsDialog
from ClSettings_dialog import ClSettingsDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'road_network_cleaner_dialog_base.ui'))


class RoadNetworkCleanerDialog(QtGui.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, available_dbs, parent=None):
        """Constructor."""
        super(RoadNetworkCleanerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #self.outputCleaned.setText("cleaned")

        # Setup the progress bar
        self.cleaningProgress.setMinimum(0)
        self.cleaningProgress.setMaximum(100)
        # Setup some defaults
        self.decimalsSpin.setRange(1, 16)
        self.decimalsSpin.setSingleStep(1)
        self.decimalsSpin.setValue(6)
        self.decimalsSpin.setDisabled(True)

        self.memoryRadioButton.setChecked(True)
        self.shpRadioButton.setChecked(False)
        self.postgisRadioButton.setChecked(False)
        self.browseCleaned.setDisabled(True)

        self.outputCleaned.setDisabled(False)
        if available_dbs:
            self.postgisRadioButton.setDisabled(False)
            self.dbsettings_dlg = DbSettingsDialog(available_dbs)
            self.dbsettings_dlg.setDbOutput.connect(self.setDbOutput)
            self.postgisRadioButton.clicked.connect(self.setDbOutput)
        else:
            self.postgisRadioButton.setDisabled(True)

        self.clsettings_dlg = ClSettingsDialog()

        # add GUI signals
        self.snapCheckBox.stateChanged.connect(self.set_enabled_tolerance)
        self.browseCleaned.clicked.connect(self.setOutput)

        self.memoryRadioButton.clicked.connect(self.setTempOutput)
        self.memoryRadioButton.clicked.connect(self.update_output_text)
        self.shpRadioButton.clicked.connect(self.setShpOutput)

        self.settingsButton.clicked.connect(self.openClSettings)

        if self.memoryRadioButton.isChecked():
            self.outputCleaned.setText('cleaned')

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def getNetwork(self):
        return self.inputCombo.currentText()

    def getOutput(self):
        if self.outputCleaned.text() != 'cleaned':
            return self.outputCleaned.text()
        else:
            return None

    def popActiveLayers(self, layers_list):
        self.inputCombo.clear()
        if layers_list:
            self.inputCombo.addItems(layers_list)
            self.lockGUI(False)
        else:
            self.lockGUI(True)

    def lockGUI(self, onoff):
        self.snapCheckBox.setDisabled(onoff)
        self.set_enabled_tolerance()
        self.memoryRadioButton.setDisabled(onoff)
        self.shpRadioButton.setDisabled(onoff)
        self.postgisRadioButton.setDisabled(onoff)
        self.outputCleaned.setDisabled(onoff)
        self.disable_browse()
        self.unlinksCheckBox.setDisabled(onoff)
        self.errorsCheckBox.setDisabled(onoff)
        self.cleanButton.setDisabled(onoff)

    def getTolerance(self):
        if self.snapCheckBox.isChecked():
            return self.decimalsSpin.value()
        else:
            return None

    def disable_browse(self):
        if self.memoryRadioButton.isChecked():
            self.browseCleaned.setDisabled(True)
        else:
            self.browseCleaned.setDisabled(False)

    def get_errors(self):
        return self.errorsCheckBox.isChecked()

    def get_unlinks(self):
        return self.unlinksCheckBox.isChecked()

    def update_output_text(self):
        if self.memoryRadioButton.isChecked():
            return "cleaned"
        else:
            return

    def get_output_type(self):
        if self.shpRadioButton.isChecked():
            return 'shp'
        elif self.postgisRadioButton.isChecked():
            return 'postgis'
        else:
            return 'memory'

    def set_enabled_tolerance(self):
        if self.snapCheckBox.isChecked():
            self.decimalsSpin.setDisabled(False)
        else:
            self.decimalsSpin.setDisabled(True)

    def get_settings(self):
        settings = {'input': self.getNetwork(), 'output': self.getOutput(), 'tolerance': self.getTolerance(),
                    'errors': self.get_errors(), 'unlinks': self.get_unlinks(),  'user_id': None, 'output_type': self.get_output_type()}
        return settings

    def get_dbsettings(self):
        settings = self.dbsettings_dlg.getDbSettings()
        return settings

    def setOutput(self):
        if self.shpRadioButton.isChecked():
            self.file_name = QtGui.QFileDialog.getSaveFileName(self, "Save output file ", "cleaned_network", '*.shp')
            if self.file_name:
                self.outputCleaned.setText(self.file_name)
            else:
                self.outputCleaned.clear()
        elif self.postgisRadioButton.isChecked():
            self.dbsettings_dlg.show()
            # Run the dialog event loop
            result2 = self.dbsettings_dlg.exec_()
            self.dbsettings = self.dbsettings_dlg.getDbSettings()
        return

    def setDbOutput(self):
        self.disable_browse()
        if self.postgisRadioButton.isChecked():
            self.outputCleaned.clear()
            try:
                self.dbsettings = self.dbsettings_dlg.getDbSettings()
                db_layer_name = "%s:%s:%s" % (self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                self.outputCleaned.setText(db_layer_name)
            except:
                self.outputCleaned.clear()
            self.outputCleaned.setDisabled(True)

    def setTempOutput(self):
        self.disable_browse()
        temp_name = 'cleaned'
        self.outputCleaned.setText(temp_name)
        self.outputCleaned.setDisabled(False)

    def setShpOutput(self):
        self.disable_browse()
        try:
            self.outputCleaned.setText(self.file_name)
        except :
            self.outputCleaned.clear()
        self.outputCleaned.setDisabled(True)

    def openClSettings(self):
        self.clsettings_dlg.show()
        result1 = self.clsettings_dlg.exec_()