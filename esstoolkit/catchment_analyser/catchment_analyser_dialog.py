# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-05-19
# copyright            : (C) 2016 by Space Syntax Limited
# author               : Laurens Versluis
# email                : l.versluis@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" Network based catchment analysis
"""

from __future__ import absolute_import

import os

from qgis.PyQt.QtWidgets import (QDialog, QFileDialog)
from qgis.PyQt.uic import loadUiType

from .DbSettings_dialog import DbSettingsDialog

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'catchment_analyser_dialog_base.ui'))


class CatchmentAnalyserDialog(QDialog, FORM_CLASS):
    def __init__(self, available_dbs, parent=None):
        """Constructor."""
        super(CatchmentAnalyserDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Output internal GUI signals
        self.nameCheck.stateChanged.connect(self.activateName)
        self.distancesText.setPlaceholderText("Separate with a comma")
        # TODO: self.networkText.setPlaceholderText("Save as temporary layer...")
        self.networkSaveButton.clicked.connect(self.setOutput)
        self.cancelButton.clicked.connect(self.stopRunning)
        self.analysisButton.clicked.connect(self.setRunning)

        self.memoryRadioButton.setChecked(True)

        # Setup the progress bar
        self.analysisProgress.setMinimum(0)
        self.analysisProgress.setMaximum(100)
        self.is_running = False

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
        self.memoryRadioButton.clicked.connect(self.setTempOutput)
        self.setTempOutput()
        self.shpRadioButton.clicked.connect(self.setShpOutput)
        # self.networkText.setDisabled(True)
        # self.nameCombo.setDisabled(True)

    def setOutput(self):
        if self.shpRadioButton.isChecked():
            self.file_name, _ = QFileDialog.getSaveFileName(self, "Save output file ", self.getNetwork() + "_catchment",
                                                            '*.shp')
            if self.file_name:
                self.networkText.setText(self.file_name)
            else:
                self.networkText.clear()
        elif self.postgisRadioButton.isChecked():
            self.dbsettings_dlg.show()
            # Run the dialog event loop
            self.dbsettings_dlg.exec_()
            self.dbsettings = self.dbsettings_dlg.getDbSettings()
        return

    def setDbOutput(self):
        self.disable_browse()
        if self.postgisRadioButton.isChecked():
            self.networkText.clear()
            self.networkText.setDisabled(True)

    def setDbPath(self):
        if self.postgisRadioButton.isChecked():
            try:
                self.dbsettings = self.dbsettings_dlg.getDbSettings()
                db_layer_name = "%s:%s:%s" % (
                    self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                self.networkText.setText(db_layer_name)
            except:
                self.networkText.clear()

    def setShpOutput(self):
        self.disable_browse()
        try:
            self.networkText.setText(self.file_name)
        except:
            self.networkText.clear()
        self.networkText.setDisabled(True)

    def disable_browse(self):
        if self.memoryRadioButton.isChecked():
            self.networkSaveButton.setDisabled(True)
        else:
            self.networkSaveButton.setDisabled(False)

    def setTempOutput(self):
        self.disable_browse()
        temp_name = self.getNetwork() + "_catchment"
        self.networkText.setText(temp_name)
        self.networkText.setDisabled(False)

    def setNetworkLayers(self, names):
        layers = ['-----']
        if names:
            layers = []
            layers.extend(names)
            self.analysisButton.setEnabled(True)
            self.lockGUI(False)
        else:
            self.lockGUI(True)
        self.networkCombo.clear()
        self.networkCombo.addItems(layers)

    def getNetwork(self):
        return self.networkCombo.currentText()

    def setCostFields(self, names):
        self.costCombo.clear()
        if names:
            # self.costCheck.setEnabled(True)
            self.costCombo.addItems(['length'] + names)
        else:
            fields = ['-----']
            self.costCombo.addItems('length')
            self.costCombo.addItems(fields)

    def getCostField(self):
        if self.costCombo.currentText() == '':
            cost_field = None
        else:
            cost_field = self.costCombo.currentText()
        return cost_field

    def setOriginLayers(self, names):
        layers = ['-----']
        if names:
            layers = []
            layers.extend(names)
            self.analysisButton.setEnabled(True)
        else:
            self.nameCheck.setEnabled(False)
            self.analysisButton.setEnabled(False)
        self.originsCombo.clear()
        self.originsCombo.addItems(layers)

    def getOrigins(self):
        return self.originsCombo.currentText()

    def activateName(self):
        # print 'activateName'
        if self.nameCheck.isChecked():
            self.nameCombo.setEnabled(True)
        else:
            self.nameCombo.setEnabled(False)

    def setNameFields(self, names):
        self.nameCombo.clear()
        # print 'setNameFields'
        if names:
            self.nameCheck.setEnabled(True)
            self.nameCombo.addItems(names)
        else:
            self.nameCheck.setEnabled(False)
            # self.nameCombo.setEnabled(False)
            fields = ['-----']
            self.nameCombo.addItems(fields)

    def getName(self):
        if self.nameCheck.isChecked():
            return self.nameCombo.currentText()
        else:
            return None

    def getDistances(self):
        if self.distancesText.text():
            distances = self.distancesText.text().split(',')
            return distances

    def getNetworkTolerance(self):
        return self.networkTolSpin.value()

    def getPolygonTolerance(self):
        return self.polygonTolSpin.value()

    def setNetworkOutput(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save output file ", "catchment_network", '*.shp')
        if file_name:
            self.networkText.setText(file_name)

    def getNetworkOutput(self):
        return self.networkText.text()

    def setRunning(self):
        self.is_running = True

    def stopRunning(self):
        if self.is_running:
            self.is_running = False
        else:
            self.closeDialog()

    def lockGUI(self, onoff):

        self.networkCombo.setDisabled(onoff)
        self.costCombo.setDisabled(onoff)
        self.originsCombo.setDisabled(onoff)
        self.nameCheck.setDisabled(onoff)
        self.nameCombo.setDisabled(onoff)

        self.distancesText.setDisabled(onoff)
        self.networkTolSpin.setDisabled(onoff)
        self.polygonTolSpin.setDisabled(onoff)

        self.memoryRadioButton.setDisabled(onoff)
        self.shpRadioButton.setDisabled(onoff)
        self.postgisRadioButton.setDisabled(onoff)

        self.networkText.setDisabled(onoff)
        self.networkSaveButton.setDisabled(onoff)

        self.polygonCheck.setDisabled(onoff)
        self.analysisButton.setDisabled(onoff)

        return

    def getOutput(self):
        if self.shpRadioButton.isChecked():
            shp_path = self.networkText.text()
            return shp_path, shp_path[:-4] + "_plg.shp"
        elif self.postgisRadioButton.isChecked():
            try:
                database, schema, table_name = self.networkText.text().split(':')
                db_path = self.dbsettings_dlg.connstring, schema, table_name
                db_path_u = list(db_path)
                db_path_u[2] = db_path_u[2] + '_plg'
                return db_path, tuple(db_path_u)
            except ValueError:
                return '', ''
        else:
            temp_name = self.networkText.text()
            return temp_name, temp_name + '_plg'

    def get_output_type(self):
        if self.shpRadioButton.isChecked():
            return 'shapefile'
        elif self.postgisRadioButton.isChecked():
            return 'postgis'
        else:
            return 'memory'

    def closeEvent(self, QCloseEvent):
        self.closeDialog()

    def closeDialog(self):
        self.costCombo.clear()
        self.costCombo.setEnabled(True)
        self.nameCombo.clear()
        self.nameCombo.setEnabled(False)
        self.nameCheck.setCheckState(False)
        self.distancesText.clear()
        self.networkTolSpin.setValue(1)
        self.polygonTolSpin.setValue(20)
        self.networkText.clear()
        self.analysisProgress.reset()
        self.close()
