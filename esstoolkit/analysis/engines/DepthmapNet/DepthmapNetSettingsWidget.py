# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# copyright            : (C) 2021 by Space Syntax Ltd.
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
# contributor          : Petros Koutsolampros
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from esstoolkit.analysis.engines.DepthmapNet.DepthmapAdvancedDialog import DepthmapAdvancedDialog
from .ui_DepthmapNetSettingsWidget import Ui_DepthmapNetSettingsWidget
from esstoolkit.utilities import layer_field_helpers as lfh, shapefile_helpers as shph, db_helpers as dbh, \
    utility_functions as uf
from esstoolkit.utilities.utility_functions import overrides
from esstoolkit.analysis.engines.SettingsWidget import SettingsWidget
from qgis.PyQt.QtCore import (pyqtSignal)
from qgis.PyQt.QtWidgets import (QMessageBox)


class DepthmapNetSettingsWidget(SettingsWidget, Ui_DepthmapNetSettingsWidget):
    dialogClosed = pyqtSignal()
    updateDatastore = pyqtSignal(str)

    @overrides(SettingsWidget)
    def __init__(self, dock_widget):
        SettingsWidget.__init__(self, dock_widget)
        # Set up the user interface from Designer.
        self.setupUi(self)

        self.axial_analysis_type = 0

        self.dlg_depthmap = DepthmapAdvancedDialog()

        self.axial_analysis_settings = {'type': 0, 'distance': 0, 'radius': 0, 'rvalues': "n", 'output': "",
                                        'fullset': 0, 'betweenness': 1, 'newnorm': 1, 'weight': 0, 'weightBy': "",
                                        'stubs': 40, 'id': "", 'valid': False}

        self.axialDepthmapWeightCheck.toggled.connect(self.set_depthmap_weighted)
        self.axialDepthmapAxialRadio.clicked.connect(self.set_depthmap_axial_analysis)
        self.axialDepthmapSegmentRadio.clicked.connect(self.set_depthmap_segment_analysis)
        self.axialDepthmapSettingsButton.clicked.connect(self.show_axial_depthmap_advanced_settings)
        self.axialDepthmapRadiusText.editingFinished.connect(self.check_depthmap_input_text)
        self.axialDepthmapOutputText.editingFinished.connect(self.check_depthmap_input_text)

    #
    # manage project and tool settings
    #
    def get_project_settings(self, project):
        # pull relevant settings from project manager
        project.readSettings(self.axial_analysis_settings, "depthmap")
        # update graph analysis
        self.set_axial_depthmap_tab(self.axial_analysis_settings)

    def update_project_settings(self, project):
        project.writeSettings(self.axial_analysis_settings, "depthmap")

    def lock_widgets(self, onoff):
        self.axialDepthmapAxialRadio.setDisabled(onoff)
        self.axialDepthmapSegmentRadio.setDisabled(onoff)
        self.axialDepthmapRadiusText.setDisabled(onoff)
        self.axialDepthmapOutputText.setDisabled(onoff)
        self.axialDepthmapSettingsButton.setDisabled(onoff)
        self.axialDepthmapWeightCheck.setDisabled(onoff)
        if onoff:
            self.axialDepthmapWeightCheck.setDisabled(onoff)
        else:
            self.set_depthmap_weighted(self.get_analysis_weighted())

    def set_defaults(self):
        self.axialDepthmapAxialRadio.setChecked(True)
        self.set_depthmap_radius_text('n')
        self.axialDepthmapWeightCheck.setChecked(False)
        self.axialDepthmapOutputText.clear()
        self.dockWidget.analysisProgressBar.setValue(0)
        self.dockWidget.analysisProgressOutput.clear()

    def set_depthmap_axial_analysis(self):
        self.axial_analysis_type = 0
        self.set_depthmap_radius_text('n')
        self.update_settings()

    def dock_widget_settings_changed(self):
        if self.dockWidget.getSegmentedMode() == 2:
            self.axialDepthmapSegmentRadio.setChecked(True)
            self.set_depthmap_segment_analysis()

    def set_depthmap_segment_analysis(self):
        if self.dockWidget.getSegmentedMode() == 0:
            self.axial_analysis_type = 1
        else:
            self.axial_analysis_type = 2
        self.set_depthmap_radius_text('n')
        self.update_settings()

    def set_depthmap_radius_text(self, txt):
        self.axialDepthmapRadiusText.setText(txt)

    def check_depthmap_input_text(self):
        if self.axialDepthmapRadiusText.text() != '' and self.axialDepthmapOutputText.text() != '':
            self.dockWidget.runAnalysisButton.setDisabled(False)
            self.set_axial_depthmap_calculate_tooltip('')
        else:
            self.dockWidget.runAnalysisButton.setDisabled(True)
            self.set_axial_depthmap_calculate_tooltip('Check if the radius values and output table name are correct.')

    def set_depthmap_weighted(self, state):
        if state == 1:
            self.axialDepthmapWeightCombo.setDisabled(False)
        else:
            self.axialDepthmapWeightCombo.setDisabled(True)

    def update_settings(self):
        # update weights combo box and output name
        layer = lfh.getLayerByName(self.dockWidget.layers[0]['name'])
        txt, idxs = lfh.getNumericFieldNames(layer)
        if self.axial_analysis_type == 0:
            self.set_axial_depthmap_output_table(self.dockWidget.layers[0]['name'])
            # self.axialDepthmapAxialRadio.setDisabled(False)
            txt.insert(0, "Line Length")
        elif self.axial_analysis_type == 1:
            self.set_axial_depthmap_output_table(self.dockWidget.layers[0]['name'] + '_segment')
            # self.axialDepthmapAxialRadio.setDisabled(False)
            txt.insert(0, "Segment Length")
        elif self.axial_analysis_type == 2:
            self.set_axial_depthmap_output_table(self.dockWidget.layers[0]['name'] + '_analysis')
            # self.axialDepthmapSegmentRadio.setChecked(True)
            self.axialDepthmapAxialRadio.setDisabled(True)
            # txt.insert(0, "Segment Length")
        self.set_depthmap_weight_attributes(txt)
        self.update_axial_depthmap_advanced_settings()
        # self.clearAxialDepthmapReport()

    def set_depthmap_weight_attributes(self, txt):
        self.axialDepthmapWeightCombo.clear()
        self.axialDepthmapWeightCombo.addItems(txt)
        self.axialDepthmapWeightCombo.setCurrentIndex(0)

    def get_analysis_type(self):
        return self.axial_analysis_type

    def get_analysis_radius_text(self):
        return self.axialDepthmapRadiusText.text()

    def get_analysis_weighted(self):
        if self.axialDepthmapWeightCheck.isChecked():
            return 1
        else:
            return 0

    def get_analysis_weight_attribute(self):
        return self.axialDepthmapWeightCombo.currentText()

    def set_axial_depthmap_output_table(self, txt):
        self.axialDepthmapOutputText.setText(txt)

    def get_analysis_output_table(self):
        return self.axialDepthmapOutputText.text()

    def update_axial_depthmap_advanced_settings(self):
        # these settings are only available in segment analysis
        if self.axial_analysis_type == 1:  # segment analysis
            self.dlg_depthmap.setDistanceType(1)
            self.dlg_depthmap.disableDistanceType(True)
            self.dlg_depthmap.setRadiusType(2)
            self.dlg_depthmap.disableRadiusType(False)
            self.dlg_depthmap.disableCalculateFull(True)
            self.dlg_depthmap.disableCalculateNorm(False)
            self.dlg_depthmap.disableRemoveStubs(False)
        elif self.axial_analysis_type == 2:  # rcl and segment map analysis
            self.dlg_depthmap.setDistanceType(1)
            self.dlg_depthmap.disableDistanceType(True)
            self.dlg_depthmap.setRadiusType(2)
            self.dlg_depthmap.disableRadiusType(False)
            self.dlg_depthmap.disableCalculateFull(True)
            self.dlg_depthmap.disableCalculateNorm(False)
            self.dlg_depthmap.disableRemoveStubs(True)
        elif self.axial_analysis_type == 0:  # and axial analysis alternative
            self.dlg_depthmap.setDistanceType(0)
            self.dlg_depthmap.disableDistanceType(True)
            self.dlg_depthmap.setRadiusType(0)
            self.dlg_depthmap.disableRadiusType(True)
            self.dlg_depthmap.disableCalculateFull(False)
            self.dlg_depthmap.disableCalculateNorm(True)
            self.dlg_depthmap.disableRemoveStubs(True)

    def show_axial_depthmap_advanced_settings(self):
        self.dlg_depthmap.show()

    def get_analysis_distance_type(self):
        return self.dlg_depthmap.axialDistanceCombo.currentIndex()

    def get_analysis_radius_type(self):
        return self.dlg_depthmap.axialRadiusCombo.currentIndex()

    def get_analysis_fullset(self):
        if self.dlg_depthmap.axialCalculateFullCheck.isChecked():
            return 1
        else:
            return 0

    def get_analysis_choice(self):
        if self.dlg_depthmap.axialCalculateChoiceCheck.isChecked():
            return 1
        else:
            return 0

    def get_analysis_normalised(self):
        if self.dlg_depthmap.axialCalculateNormCheck.isChecked():
            return 1
        else:
            return 0

    def get_analysis_stubs(self):
        return self.dlg_depthmap.axialStubsEdit.text()

    #####
    # Functions of the depthmapX remote tab
    #####
    def set_axial_depthmap_tab(self, settings):
        if settings is not None:
            # set the type of analysis
            if 'type' in settings:
                self.axial_analysis_type = settings['type']
                if settings['type'] == 0:
                    self.axialDepthmapAxialRadio.setChecked(True)
                    self.axialDepthmapAxialRadio.setDisabled(False)
                elif settings['type'] == 1:
                    self.axialDepthmapSegmentRadio.setChecked(True)
                    self.axialDepthmapAxialRadio.setDisabled(False)
                elif settings['type'] == 2:
                    self.axialDepthmapSegmentRadio.setChecked(True)
                    self.axialDepthmapAxialRadio.setDisabled(True)
            # if project specifies radii set them, for same type of analysis
            if 'rvalues' in settings:
                self.set_depthmap_radius_text(settings['rvalues'])
            else:
                self.set_depthmap_radius_text("n")
            # project use of weights
            if 'weight' in settings:
                self.axialDepthmapWeightCheck.setChecked(settings['weight'])
                # self.set_depthmap_weighted(settings['weight'])
            else:
                self.axialDepthmapWeightCheck.setChecked(False)
                # self.set_depthmap_weighted(0)
            # project output name
            if 'output' in settings:
                self.set_axial_depthmap_output_table(settings['output'])
            # project calculate full set of advanced measures
            if 'fullset' in settings:
                self.dlg_depthmap.setCalculateFull(settings['fullset'])
            else:
                self.dlg_depthmap.setCalculateFull(False)
            # project calculate betweenness
            if 'betweenness' in settings:
                self.dlg_depthmap.setCalculateChoice(settings['betweenness'])
            else:
                self.dlg_depthmap.setCalculateChoice(True)
            # project list of radii
            if 'radius' in settings:
                self.dlg_depthmap.setRadiusType(settings['radius'])
            else:
                self.dlg_depthmap.setRadiusType(2)
            # project calculate new normalised segment measures
            if 'newnorm' in settings:
                self.dlg_depthmap.setCalculateNorm(settings['newnorm'])
            else:
                self.dlg_depthmap.setCalculateNorm(True)
            # project remove stubs setting for segment map creation
            if 'stubs' in settings:
                self.dlg_depthmap.setRemoveStubs(settings['stubs'])
            else:
                self.dlg_depthmap.setRemoveStubs(40)

    def prepare_analysis_settings(self, analysis_layer, datastore):
        self.axial_analysis_settings['valid'] = False
        # get analysis type based on map and axial/segment choice
        if self.get_analysis_type() == 0:
            self.axial_analysis_settings['type'] = 0
        else:
            if self.dockWidget.getSegmentedMode() == 0:
                self.axial_analysis_settings['type'] = 1
            else:
                self.axial_analysis_settings['type'] = 2
        # get the basic analysis settings
        self.axial_analysis_settings['id'] = lfh.getIdField(analysis_layer)
        self.axial_analysis_settings['weight'] = self.get_analysis_weighted()
        self.axial_analysis_settings['weightBy'] = self.get_analysis_weight_attribute()
        txt = SettingsWidget.parse_radii(self.get_analysis_radius_text(), True)
        if txt == '':
            self.dockWidget.write_analysis_report("Please verify the radius values.")
            return
        else:
            self.axial_analysis_settings['rvalues'] = txt
        self.axial_analysis_settings['output'] = self.get_analysis_output_table()

        # get the advanced analysis settings
        self.axial_analysis_settings['distance'] = self.get_analysis_distance_type()
        self.axial_analysis_settings['radius'] = self.get_analysis_radius_type()
        self.axial_analysis_settings['fullset'] = self.get_analysis_fullset()
        self.axial_analysis_settings['betweenness'] = self.get_analysis_choice()
        self.axial_analysis_settings['newnorm'] = self.get_analysis_normalised()
        self.axial_analysis_settings['stubs'] = self.get_analysis_stubs()

        # check if output file/table already exists
        table_exists = False
        if datastore['type'] == 0:
            table_exists = shph.testShapeFileExists(datastore['path'], self.axial_analysis_settings['output'])
        elif datastore['type'] == 1:
            connection = dbh.getSpatialiteConnection(datastore['path'])
            if connection:
                table_exists = dbh.testSpatialiteTableExists(connection, self.axial_analysis_settings['output'])
            connection.close()
        elif datastore['type'] == 2:
            connection = dbh.getPostgisConnection(datastore['name'])
            if connection:
                table_exists = dbh.testPostgisTableExists(connection, datastore['schema'],
                                                          self.axial_analysis_settings['output'])
            connection.close()
        if table_exists:
            action = QMessageBox.question(None, "Overwrite table",
                                          "The output table already exists in:\n %s.\nOverwrite?" % datastore[
                                              'path'], QMessageBox.Ok | QMessageBox.Cancel)
            if action == QMessageBox.Ok:  # Yes
                pass
            elif action == QMessageBox.Cancel:  # No
                return
            else:
                return
        self.axial_analysis_settings['valid'] = True

    def get_analysis_settings(self):
        return self.axial_analysis_settings

    def get_analysis_summary(self):
        message = ""
        if self.axial_analysis_settings['type'] == 0:
            txt = "axial"
        elif self.axial_analysis_settings['type'] == 1:
            txt = "segment"
        elif self.axial_analysis_settings['type'] == 2:
            txt = "segment input"
        message += u"\n   analysis type - %s" % txt
        if self.axial_analysis_settings['type'] == 1:
            message += u"\n   stubs removal - %s" % self.axial_analysis_settings['stubs']
        if self.axial_analysis_settings['distance'] == 0:
            txt = "topological"
        elif self.axial_analysis_settings['distance'] == 1:
            txt = "angular"
        elif self.axial_analysis_settings['distance'] == 2:
            txt = "metric"
        message += u"\n   distance - %s" % txt
        if self.axial_analysis_settings['weight'] == 1:
            message += u"\n   weighted by - %s" % self.axial_analysis_settings['weightBy']
        if self.axial_analysis_settings['radius'] == 0:
            txt = "topological"
        elif self.axial_analysis_settings['radius'] == 1:
            txt = "angular"
        elif self.axial_analysis_settings['radius'] == 2:
            txt = "metric"
        message += u"\n   %s radius - %s" % (txt, self.axial_analysis_settings['rvalues'])
        if self.axial_analysis_settings['betweenness'] == 1:
            message += u"\n   calculate choice"
        if self.axial_analysis_settings['fullset'] == 1:
            message += u"\n   include advanced measures"
        if self.axial_analysis_settings['type'] in (1, 2) and self.axial_analysis_settings['newnorm'] == 1:
            message += u"\n   calculate NACH and NAIN"
        return message

    def set_axial_depthmap_calculate_tooltip(self, txt):
        self.dockWidget.runAnalysisButton.setToolTip(txt)
