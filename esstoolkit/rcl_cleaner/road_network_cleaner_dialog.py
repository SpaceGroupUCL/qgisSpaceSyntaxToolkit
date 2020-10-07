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

""" This module helps clean a road centre line map.
"""

from __future__ import absolute_import

import os.path

from qgis.PyQt import QtGui, uic, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QDialog

from .DbSettings_dialog import DbSettingsDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'road_network_cleaner_dialog_base.ui'))


class RoadNetworkCleanerDialog(QDialog, FORM_CLASS):
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

        # Setup the progress bar
        self.cleaningProgress.setMinimum(0)
        self.cleaningProgress.setMaximum(100)
        # Setup some defaults
        self.snapSpinBox.setRange(1, 30)
        self.snapSpinBox.setSingleStep(1)
        self.snapSpinBox.setValue(10)
        self.angularChangeSpinBox.setRange(1, 45)
        self.angularChangeSpinBox.setSingleStep(1)
        self.angularChangeSpinBox.setValue(10)

        self.memoryRadioButton.setChecked(True)
        self.shpRadioButton.setChecked(False)
        self.postgisRadioButton.setChecked(False)
        self.browseCleaned.setDisabled(True)

        self.outputCleaned.setDisabled(False)
        if available_dbs:
            pass
        else:
            available_dbs = {}
        self.postgisRadioButton.setDisabled(False)

        # initialise nut do not connect to popschemas
        self.dbsettings_dlg = DbSettingsDialog(available_dbs)
        self.dbsettings_dlg.setDbOutput.connect(self.setDbOutput)
        self.postgisRadioButton.clicked.connect(self.setDbOutput)
        self.dbsettings_dlg.dbCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.schemaCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.nameLineEdit.textChanged.connect(self.setDbPath)

        # add GUI signals§
        self.browseCleaned.clicked.connect(self.setOutput)
        self.mergeCheckBox.stateChanged.connect(self.toggleMergeSettings)
        self.mergeCollinearCheckBox.stateChanged.connect(self.toggleMergeCollinearSettings)

        self.memoryRadioButton.clicked.connect(self.setTempOutput)
        self.setTempOutput()
        self.shpRadioButton.clicked.connect(self.setShpOutput)

        self.dataSourceCombo.addItems(['OpenStreetMap', 'OrdnanceSurvey', 'other'])
        self.lockSettingsGUI(True)
        self.dataSourceCombo.currentIndexChanged.connect(self.setClSettings)

        self.errorsCheckBox.setCheckState(2)
        self.unlinksCheckBox.setCheckState(2)

        self.editDefaultButton.clicked.connect(lambda i=False: self.lockSettingsGUI(i))
        self.setClSettings()
        self.lockSettingsGUI(True)
        self.outputCleaned.setDisabled(True)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def toggleMergeCollinearSettings(self):
        # untick the self.mergeCollinearCheckBox
        if self.mergeCollinearCheckBox.isChecked():
            self.mergeCheckBox.setCheckState(0)
        return

    def toggleMergeSettings(self):
        if self.mergeCheckBox.isChecked():
            self.mergeCollinearCheckBox.setCheckState(0)
        return

    def setClSettings(self):
        if self.dataSourceCombo.currentText() == 'OpenStreetMap':
            self.snapCheckBox.setCheckState(2)
            self.simplifyCheckBox.setCheckState(2)
            self.snapSpinBox.setValue(10)
            self.angularChangeSpinBox.setValue(10)
            self.breakCheckBox.setCheckState(2)
            self.mergeCheckBox.setCheckState(2)
            self.orphansCheckBox.setCheckState(2)

            self.lockSettingsGUI(True)

        elif self.dataSourceCombo.currentText() == 'OrdnanceSurvey':
            self.snapCheckBox.setCheckState(2)
            self.simplifyCheckBox.setCheckState(2)
            self.snapSpinBox.setValue(10)
            self.angularChangeSpinBox.setValue(10)
            self.breakCheckBox.setCheckState(0)
            self.mergeCheckBox.setCheckState(2)
            self.orphansCheckBox.setCheckState(2)
            self.lockSettingsGUI(True)

        else:
            self.lockSettingsGUI(False)

        return

    def getNetwork(self):
        return self.inputCombo.currentText()

    def getOutput(self):
        if self.shpRadioButton.isChecked():
            shp_path = self.outputCleaned.text()
            return shp_path, shp_path[:-4] + "_u.shp", shp_path[:-4] + "_errors.shp"
        elif self.postgisRadioButton.isChecked():
            try:
                database, schema, table_name = self.outputCleaned.text().split(':')
                db_path = self.dbsettings_dlg.connstring, schema, table_name
                db_path_u = list(db_path)
                db_path_u[2] = db_path_u[2] + '_u'
                db_path_errors = list(db_path)
                db_path_errors[2] = db_path_u[2] + '_errors'
                return db_path, tuple(db_path_u), tuple(db_path_errors)
            except ValueError:
                return '', '', ''
        else:
            temp_name = self.outputCleaned.text()
            return temp_name, temp_name + '_u', temp_name + '_errors'

    def popActiveLayers(self, layers_list):
        self.inputCombo.clear()
        if layers_list:
            self.inputCombo.addItems(layers_list)
            self.lockGUI(False)
        else:
            self.lockGUI(True)
            self.lockSettingsGUI(True)

    def lockGUI(self, onoff):
        self.editDefaultButton.setDisabled(onoff)
        self.memoryRadioButton.setDisabled(onoff)
        self.shpRadioButton.setDisabled(onoff)
        self.postgisRadioButton.setDisabled(onoff)
        self.outputCleaned.setDisabled(onoff)
        self.disable_browse()
        self.unlinksCheckBox.setDisabled(onoff)
        self.errorsCheckBox.setDisabled(onoff)
        self.cleanButton.setDisabled(onoff)
        self.dataSourceCombo.setDisabled(onoff)
        self.inputCombo.setDisabled(onoff)

    def lockSettingsGUI(self, onoff):
        self.orphansCheckBox.setDisabled(onoff)
        self.mergeCheckBox.setDisabled(onoff)
        self.mergeCollinearCheckBox.setDisabled(onoff)
        self.breakCheckBox.setDisabled(onoff)
        self.snapCheckBox.setDisabled(onoff)
        self.simplifyCheckBox.setDisabled(onoff)
        self.snapSpinBox.setDisabled(onoff)
        self.angularChangeSpinBox.setDisabled(onoff)
        self.angleSpinBox.setDisabled(onoff)

    def getTolerance(self):
        if self.snapCheckBox.isChecked():
            return self.snapSpinBox.value()
        else:
            return 0

    def getSimplificationTolerance(self):
        if self.simplifyCheckBox.isChecked():
            return self.angularChangeSpinBox.value()
        else:
            return 0

    def getBreakages(self):
        if self.breakCheckBox.isChecked():
            return True
        else:
            return False

    def getMerge(self):
        if self.mergeCheckBox.isChecked():
            return 'intersections'
        elif self.mergeCollinearCheckBox.isChecked():
            return 'collinear'
        else:
            return None

    def getCollinearThreshold(self):
        return self.angleSpinBox.value()

    def getOrphans(self):
        if self.orphansCheckBox.isChecked():
            return True
        else:
            return False

    def disable_browse(self):
        if self.memoryRadioButton.isChecked():
            self.browseCleaned.setDisabled(True)
        else:
            self.browseCleaned.setDisabled(False)

    def get_errors(self):
        return self.errorsCheckBox.isChecked()

    def get_unlinks(self):
        return self.unlinksCheckBox.isChecked()

    def get_output_type(self):
        if self.shpRadioButton.isChecked():
            return 'shapefile'
        elif self.postgisRadioButton.isChecked():
            return 'postgis'
        else:
            return 'memory'

    def fix_unlinks(self):
        if self.dataSourceCombo.currentText() == 'OrdnanceSurvey':
            return True
        else:
            return None

    def get_settings(self):
        break_at_vertices, merge_type, snap_threshold, orphans, fix_unlinks = self.getBreakages(), self.getMerge(), self.getTolerance(), self.getOrphans(), self.fix_unlinks()
        getUnlinks = self.get_unlinks()
        settings = {'input': self.getNetwork(), 'output': self.getOutput(), 'snap': snap_threshold,
                    'break': break_at_vertices, 'merge': merge_type, 'orphans': orphans,
                    'errors': self.get_errors(), 'unlinks': getUnlinks, 'collinear_angle': self.getCollinearThreshold(),
                    'simplification_threshold': self.getSimplificationTolerance(),
                    'fix_unlinks': fix_unlinks, 'output_type': self.get_output_type(),
                    'progress_ranges': self.get_progress_ranges(break_at_vertices, merge_type, snap_threshold,
                                                                getUnlinks, fix_unlinks)}
        return settings

    @staticmethod
    def get_progress_ranges(break_at_vertices, merge_type, snap_threshold, getUnlinks, fix_unlinks):

        # hard-coded ranges
        weights = {'break': 4, 'load': 2, 'snap': 2, 'merge': 1, 'unlinks': 1, 'clean': 1, 'fix': 1}
        total_range = 95
        total_pr_w = weights['load']
        total_pr_w += (float(2) * weights['clean'])  # 2 cleanings are happening by default
        if break_at_vertices:
            total_pr_w += weights['break']
        if merge_type in ('intersections', 'collinear'):
            total_pr_w += weights['merge']
        if snap_threshold != 0:
            total_pr_w += weights['snap']
            total_pr_w += weights['clean']
        if getUnlinks:
            total_pr_w += weights['unlinks']
        if fix_unlinks:
            total_pr_w += weights['fix']

        factor = total_range / float(total_pr_w)
        load_range = weights['load'] * float(factor)
        cl1_range = weights['clean'] * float(factor)
        cl2_range = 0
        cl3_range = cl1_range
        break_range, merge_range, snap_range, unlinks_range, fix_range = 0, 0, 0, 0, 0
        if break_at_vertices:
            break_range = weights['break'] * float(factor)
        if merge_type in ('intersections', 'collinear'):
            merge_range = weights['merge'] * float(factor)
        if snap_threshold != 0:
            snap_range = weights['snap'] * float(factor)
            cl2_range = cl1_range
        if fix_unlinks:
            fix_range = weights['fix'] * float(factor)
        if getUnlinks:
            unlinks_range = weights['unlinks'] * float(factor)

        return [load_range, cl1_range, cl2_range, cl3_range, break_range, merge_range, snap_range, unlinks_range,
                fix_range]

    def get_dbsettings(self):
        settings = self.dbsettings_dlg.getDbSettings()
        return settings

    def setOutput(self):
        if self.shpRadioButton.isChecked():
            self.file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save output file ", self.getNetwork() + "_cl",
                                                                      '*.shp')
            if self.file_name:
                self.outputCleaned.setText(self.file_name)
            else:
                self.outputCleaned.clear()
        elif self.postgisRadioButton.isChecked():
            self.dbsettings_dlg.show()
            # Run the dialog event loop
            # result2 = self.dbsettings_dlg.exec_()
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
        return

    def setTempOutput(self):
        self.disable_browse()
        temp_name = self.getNetwork() + "_cl"
        self.outputCleaned.setText(temp_name)
        self.outputCleaned.setDisabled(False)

    def setShpOutput(self):
        self.disable_browse()
        try:
            self.outputCleaned.setText(self.file_name)
        except:
            self.outputCleaned.clear()
        self.outputCleaned.setDisabled(True)
