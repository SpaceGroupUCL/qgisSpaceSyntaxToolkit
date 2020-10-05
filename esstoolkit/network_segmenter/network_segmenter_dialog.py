# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-11-10
# copyright            : (C) 2016 by Space Syntax Ltd
# author               : Ioanna Kolovou
# email                : i.kolovou@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""
This module helps segment a road centre line map.
"""

from __future__ import absolute_import

import os.path

from qgis.PyQt import QtGui, uic, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog

from .DbSettings_dialog import DbSettingsDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'network_segmenter_dialog_base.ui'))


class NetworkSegmenterDialog(QDialog, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, available_dbs, parent=None):
        """Constructor."""
        super(NetworkSegmenterDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # self.outputCleaned.setText("segmented")

        # Setup the progress bar
        self.segmentingProgress.setMinimum(0)
        self.segmentingProgress.setMaximum(100)
        # Setup some defaults
        self.stubsCheckBox.setDisabled(False)
        self.stubsCheckBox.setChecked(True)
        self.stubsSpin.setSuffix('%')
        self.stubsSpin.setRange(1, 60)
        self.stubsSpin.setSingleStep(10)
        self.stubsSpin.setValue(40)
        self.stubsSpin.setDisabled(True)

        self.bufferSpinBox.setSuffix('m')
        self.bufferSpinBox.setRange(0, 50)
        self.bufferSpinBox.setSingleStep(0.01)
        self.bufferSpinBox.setValue(1)
        self.bufferSpinBox.setDisabled(False)

        self.memoryRadioButton.setChecked(True)
        self.shpRadioButton.setChecked(False)
        self.postgisRadioButton.setChecked(False)
        self.networkSaveButton.setDisabled(True)

        self.outputCleaned.setDisabled(False)
        if available_dbs:
            pass
        else:
            available_dbs = {}
        self.postgisRadioButton.setDisabled(False)

        # initialise nut do not connect to popschemas
        self.dbsettings_dlg = DbSettingsDialog(available_dbs)
        self.postgisRadioButton.clicked.connect(self.setDbOutput)
        self.dbsettings_dlg.dbCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.schemaCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.nameLineEdit.textChanged.connect(self.setDbPath)

        # add GUI signals
        self.stubsCheckBox.stateChanged.connect(self.set_enabled_tolerance)
        self.networkSaveButton.clicked.connect(self.setOutput)

        self.memoryRadioButton.clicked.connect(self.setTempOutput)
        self.setTempOutput()
        self.shpRadioButton.clicked.connect(self.setShpOutput)
        self.outputCleaned.setDisabled(True)

        # if self.memoryRadioButton.isChecked():
        #    self.outputCleaned.setText(self.getNetwork() + "_seg")
        # if self.postgisRadioButton.isChecked():
        #    self.dbsettings_dlg.nameLineEdit.setText(self.getNetwork() + "_seg")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def getNetwork(self):
        return self.inputCombo.currentText()

    def getUnlinks(self):
        if self.unlinksCombo.currentText() == 'no unlinks':
            return None
        else:
            return self.unlinksCombo.currentText()

    def getOutput(self):
        if self.shpRadioButton.isChecked():
            shp_path = self.outputCleaned.text()
            return shp_path, shp_path[:-4] + "_breakpoints.shp"
        elif self.postgisRadioButton.isChecked():
            try:
                database, schema, table_name = self.outputCleaned.text().split(':')
                db_path = self.dbsettings_dlg.connstring, schema, table_name
                db_path_errors = list(db_path)
                db_path_errors[2] = db_path[2] + '_breakpoints'
                return db_path, tuple(db_path_errors)
            except ValueError:
                return '', ''
        else:
            temp_name = self.outputCleaned.text()
            return temp_name, temp_name + '_breakpoints'

    def popActiveLayers(self, layers_list):
        self.inputCombo.clear()
        if layers_list:
            self.inputCombo.addItems(layers_list)
            self.lockGUI(False)
        else:
            self.lockGUI(True)

    def popUnlinksLayers(self, layers_list):
        self.unlinksCombo.clear()
        self.unlinksCombo.addItems(['no unlinks'] + layers_list)

    def lockGUI(self, onoff):
        self.stubsCheckBox.setDisabled(onoff)
        self.set_enabled_tolerance()
        self.memoryRadioButton.setDisabled(onoff)
        self.shpRadioButton.setDisabled(onoff)
        self.postgisRadioButton.setDisabled(onoff)
        self.outputCleaned.setDisabled(onoff)
        self.disable_browse()
        self.breakagesCheckBox.setDisabled(onoff)
        self.runButton.setDisabled(onoff)
        self.bufferSpinBox.setDisabled(onoff)
        self.stubsSpin.setDisabled(onoff)
        self.inputCombo.setDisabled(onoff)
        self.unlinksCombo.setDisabled(onoff)

    def getStubRatio(self):
        if self.stubsCheckBox.isChecked():
            return self.stubsSpin.value() / (float(100))
        else:
            return None

    def getBuffer(self):
        buf_value = self.bufferSpinBox.value()
        if buf_value != 0:
            return self.bufferSpinBox.value()
        else:
            return 0  # TODO or none?

    def disable_browse(self):
        if self.memoryRadioButton.isChecked():
            self.networkSaveButton.setDisabled(True)
        else:
            self.networkSaveButton.setDisabled(False)

    def get_breakages(self):
        return self.breakagesCheckBox.isChecked()

    def get_output_type(self):
        if self.shpRadioButton.isChecked():
            return 'shapefile'
        elif self.postgisRadioButton.isChecked():
            return 'postgis'
        else:
            return 'memory'

    def set_enabled_tolerance(self):
        if self.stubsCheckBox.isChecked():
            self.stubsSpin.setDisabled(False)
        else:
            self.stubsSpin.setDisabled(True)

    def get_settings(self):
        settings = {'input': self.getNetwork(), 'unlinks': self.getUnlinks(), 'output': self.getOutput(),
                    'stub_ratio': self.getStubRatio(),
                    'errors': self.get_breakages(), 'buffer': self.getBuffer(), 'output_type': self.get_output_type()}
        return settings

    def get_dbsettings(self):
        settings = self.dbsettings_dlg.getDbSettings()
        return settings

    def setOutput(self):
        if self.shpRadioButton.isChecked():
            self.file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save output file ", self.getNetwork() + "_seg",
                                                                      '*.shp')
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

            self.outputCleaned.setDisabled(True)

    def setDbPath(self):
        if self.postgisRadioButton.isChecked():
            try:
                self.dbsettings = self.dbsettings_dlg.getDbSettings()
                db_layer_name = "%s:%s:%s" % (
                    self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                self.outputCleaned.setText(db_layer_name)
            except:
                self.outputCleaned.clear()

    def setTempOutput(self):
        self.disable_browse()
        temp_name = self.getNetwork() + "_seg"
        self.outputCleaned.setText(temp_name)
        self.outputCleaned.setDisabled(False)

    def setShpOutput(self):
        self.disable_browse()
        try:
            self.outputCleaned.setText(self.file_name)
        except:
            self.outputCleaned.clear()
        self.outputCleaned.setDisabled(True)
