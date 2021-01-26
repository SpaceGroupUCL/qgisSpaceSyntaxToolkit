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

from __future__ import absolute_import

import datetime
import os.path

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import (QObject, QTimer, pyqtSignal, QVariant)
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import (QgsProject, QgsVectorDataProvider, Qgis, QgsWkbTypes)

from esstoolkit.utilities import shapefile_helpers as shph, layer_field_helpers as lfh, db_helpers as dbh
# Import required modules
from .AnalysisDialog import AnalysisDialog
from .AnalysisEngine import AnalysisEngine
from .AxialVerification import AxialVerification
from .DepthmapEngine import DepthmapEngine
from .DepthmapNetEngine import DepthmapNetEngine
from .UnlinksVerification import UnlinksVerification, UnlinksIdUpdate


class AnalysisTool(QObject):
    editDatastoreSettings = pyqtSignal()

    def __init__(self, iface, settings, project):
        QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        self.project = project
        self.legend = QgsProject.instance().mapLayers()
        self.analysis_engine = DepthmapNetEngine(self.iface)
        self.running_analysis = ''

    def load(self):
        # initialise UI
        self.dlg = AnalysisDialog(self.iface.mainWindow())

        # initialise axial analysis classes
        self.verificationThread = None

        # connect signal/slots with main program
        self.project.settingsUpdated.connect(self.setDatastore)
        self.editDatastoreSettings.connect(self.project.showDialog)

        # set up GUI signals
        self.dlg.visibilityChanged.connect(self.onShow)
        self.dlg.analysisDataButton.clicked.connect(self.changeDatastore)
        self.dlg.updateDatastore.connect(self.updateDatastore)
        self.dlg.axialVerifyButton.clicked.connect(self.runAxialVerification)
        self.dlg.axialUpdateButton.clicked.connect(self.runAxialUpdate)
        self.dlg.axialVerifyCancelButton.clicked.connect(self.cancelAxialVerification)
        self.dlg.axialReportList.itemSelectionChanged.connect(self.zoomAxialProblem)
        self.dlg.axialDepthmapCalculateButton.clicked.connect(self.run_analysis)
        self.dlg.axialDepthmapCancelButton.clicked.connect(self.cancel_analysis)

        # initialise internal globals
        self.isVisible = False
        self.datastore = dict()
        self.running_analysis = ""
        self.start_time = None
        self.end_time = None
        self.analysis_nodes = 0
        self.axial_id = ""
        self.all_ids = []
        self.current_layer = None

        # timer to check for analysis result
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_analysis_progress)

        # define analysis data structures
        self.analysis_layers = {'map': "", 'unlinks': "", 'map_type': 0}
        self.axial_analysis_settings = {'type': 0, 'distance': 0, 'radius': 0, 'rvalues': "n", 'output': "",
                                        'fullset': 0, 'betweenness': 1, 'newnorm': 1, 'weight': 0, 'weightBy': "",
                                        'stubs': 40, 'id': ""}
        self.user_ids = {'map': "", 'unlinks': ""}
        self.analysis_output = ""
        self.getProjectSettings()

    def unload(self):
        if self.isVisible:
            # Disconnect signals from main program
            QgsProject.instance().layersAdded.disconnect(self.updateLayers)
            QgsProject.instance().layersRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.getProjectSettings)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
        self.isVisible = False

    def onShow(self):
        if self.dlg.isVisible():
            # Connect signals to QGIS interface
            QgsProject.instance().layersAdded.connect(self.updateLayers)
            QgsProject.instance().layersRemoved.connect(self.updateLayers)
            self.iface.projectRead.connect(self.updateLayers)
            self.iface.projectRead.connect(self.getProjectSettings)
            self.iface.newProjectCreated.connect(self.updateLayers)
            self.updateLayers()
            self.setDatastore()
            self.isVisible = True
        else:
            if self.isVisible:
                # Disconnect signals to QGIS interface
                QgsProject.instance().layersAdded.disconnect(self.updateLayers)
                QgsProject.instance().layersRemoved.disconnect(self.updateLayers)
                self.iface.projectRead.disconnect(self.updateLayers)
                self.iface.projectRead.disconnect(self.getProjectSettings)
                self.iface.newProjectCreated.disconnect(self.updateLayers)
            self.isVisible = False

    ##
    ## manage project and tool settings
    ##
    def getProjectSettings(self):
        # pull relevant settings from project manager
        self.project.readSettings(self.analysis_layers, "analysis")
        self.project.readSettings(self.axial_analysis_settings, "depthmap")
        # update UI
        self.dlg.clearAxialProblems(0)
        self.dlg.clearAxialProblems(1)
        # update graph analysis
        self.dlg.set_axial_depthmap_tab(self.axial_analysis_settings)

    def updateProjectSettings(self):
        self.project.writeSettings(self.analysis_layers, "analysis")
        self.project.writeSettings(self.axial_analysis_settings, "depthmap")

    def changeDatastore(self):
        # signal from UI if data store button is clicked
        self.editDatastoreSettings.emit()

    def updateDatastore(self, name):
        new_datastore = {'name': '', 'path': '', 'type': -1, 'schema': '', 'crs': ''}
        layer = lfh.getLegendLayerByName(self.iface, name)
        if layer:
            new_datastore['crs'] = layer.crs().postgisSrid()
            if 'SpatiaLite' in layer.storageType():
                new_datastore['type'] = 1
                path = lfh.getLayerPath(layer)
                dbname = os.path.basename(path)
                new_datastore['path'] = path
                new_datastore['name'] = dbname
                # create a new connection if not exists
                conn = dbh.listSpatialiteConnections()
                if path not in conn['path']:
                    dbh.createSpatialiteConnection(dbname, path)
            elif 'PostGIS' in layer.storageType():
                new_datastore['type'] = 2
                layerinfo = dbh.getPostgisLayerInfo(layer)
                if layerinfo['service']:
                    path = layerinfo['service']
                else:
                    path = layerinfo['database']
                new_datastore['path'] = path
                new_datastore['schema'] = layerinfo['schema']
                if 'connection' in layerinfo:
                    new_datastore['name'] = layerinfo['connection']
                else:
                    # create a new connection if not exists
                    dbh.createPostgisConnectionSetting(path, dbh.getPostgisConnectionInfo(layer))
                    new_datastore['name'] = path
            elif 'memory?' not in layer.storageType():  # 'Shapefile'
                new_datastore['type'] = 0
                new_datastore['path'] = lfh.getLayerPath(layer)
                new_datastore['name'] = os.path.basename(new_datastore['path'])
            if new_datastore['type'] in (0, 1, 2):
                self.project.writeSettings(new_datastore, 'datastore')
                self.setDatastore()
            else:
                return
        else:
            return

    def clearDatastore(self):
        new_datastore = {'name': '', 'path': '', 'type': -1, 'schema': '', 'crs': ''}
        self.project.writeSettings(new_datastore, 'datastore')
        self.setDatastore()

    def setDatastore(self):
        self.datastore = self.project.getGroupSettings('datastore')
        if 'type' in self.datastore:
            self.datastore['type'] = int(self.datastore['type'])
        else:
            self.datastore['type'] = -1
        # update UI
        txt = ""
        path = ""
        if 'name' in self.datastore and self.datastore['name'] != "":
            # get elements for string to identify data store for user
            # shape file data store
            if self.datastore['type'] == 0 and os.path.exists(self.datastore['path']):
                txt = 'SF: %s' % self.datastore['name']
                path = self.datastore['path']
            # spatialite data store
            elif self.datastore['type'] == 1 and os.path.exists(self.datastore['path']):
                sl_connections = dbh.listSpatialiteConnections()
                if len(sl_connections) > 0:
                    if self.datastore['name'] in sl_connections['name'] and self.datastore['path'] == \
                            sl_connections['path'][sl_connections['name'].index(self.datastore['name'])]:
                        txt = 'SL: %s' % self.datastore['name']
                        path = self.datastore['path']
                else:
                    dbh.createSpatialiteConnection(self.datastore['name'], self.datastore['path'])
                    txt = 'SL: %s' % self.datastore['name']
                    path = self.datastore['path']
            # postgis data store
            elif self.datastore['type'] == 2 and len(dbh.listPostgisConnectionNames()) > 0:
                if self.datastore['name'] in dbh.listPostgisConnectionNames():
                    txt = 'PG: %s (%s)' % (self.datastore['name'], self.datastore['schema'])
                    path = """dbname='%s' schema='%s'""" % (self.datastore['path'], self.datastore['schema'])
        self.dlg.setDatastore(txt, path)

    def isDatastoreSet(self):
        is_set = False
        if self.datastore:
            name = self.datastore['name']
            path = self.datastore['path']
            schema = self.datastore['schema']
            if name == "":
                self.clearDatastore()
                self.iface.messageBar().pushMessage("Info", "Select a 'Data store' to save analysis results.", level=0,
                                                    duration=5)
            elif self.datastore['type'] == 0 and not os.path.exists(path):
                is_set = False
            elif self.datastore['type'] == 1 and (
                    name not in dbh.listSpatialiteConnections()['name'] or not os.path.exists(path)):
                is_set = False
            elif self.datastore['type'] == 2 and (
                    name not in dbh.listPostgisConnectionNames() or schema not in dbh.listPostgisSchemas(
                dbh.getPostgisConnection(name))):
                is_set = False
            else:
                is_set = True
            # clear whatever data store settings are saved
            if not is_set:
                self.clearDatastore()
                self.iface.messageBar().pushMessage("Info", "The selected data store cannot be found.", level=0,
                                                    duration=5)
        else:
            self.clearDatastore()
            self.iface.messageBar().pushMessage("Info", "Select a 'Data store' to save analysis results.", level=0,
                                                duration=5)
        return is_set

    ##
    ## Manage layers
    ##
    def updateLayers(self):
        if self.iface.actionMapTips().isChecked():
            self.iface.actionMapTips().trigger()
        # layer names by geometry type
        map_list = []
        unlinks_list = []
        # default selection
        analysis_map = -1
        analysis_unlinks = -1
        map_type = 0
        layers = lfh.getLegendLayers(self.iface, 'all', 'all')
        if layers:
            for layer in layers:
                # checks if the layer is projected. Geographic coordinates are not supported
                if layer.isSpatial() and lfh.isLayerProjected(layer):
                    unlinks_list.append(layer.name())
                    if layer.geometryType() == 1:  # line geometry
                        map_list.append(layer.name())
            # settings preference
            if self.analysis_layers['map'] in map_list:
                analysis_map = map_list.index(self.analysis_layers['map'])
                map_type = self.analysis_layers['map_type']
            if self.analysis_layers['unlinks'] in unlinks_list:
                analysis_unlinks = unlinks_list.index(self.analysis_layers['unlinks'])
            # current selection
            selected_layers = self.dlg.getAnalysisLayers()
            if selected_layers['map'] != '' and selected_layers['map'] in map_list:
                analysis_map = map_list.index(selected_layers['map'])
                map_type = selected_layers['map_type']
            if selected_layers['unlinks'] != '' and selected_layers['unlinks'] in unlinks_list:
                analysis_unlinks = unlinks_list.index(selected_layers['unlinks'])
        else:
            self.dlg.clear_analysis_tab()

        # update UI
        self.dlg.set_map_layers(map_list, analysis_map, map_type)
        self.dlg.set_unlinks_layers(unlinks_list, analysis_unlinks)
        self.dlg.update_analysis_tabs()
        self.dlg.update_analysis_tab()

    ##
    ## Layer verification functions
    ##
    def runAxialVerification(self):
        self.edit_mode = self.dlg.getLayerTab()
        self.analysis_layers = self.dlg.getAnalysisLayers()
        axial = lfh.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        unlinks = lfh.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
        settings = self.dlg.getAxialEditSettings()
        caps = None
        self.axial_id = lfh.getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Info",
                                                "The axial layer has invalid values in the ID column. Using feature ids.",
                                                level=0, duration=3)
        # verify axial map
        if self.edit_mode == 0:
            # get ids (to match the object ids in the map)
            self.user_ids['map'] = "%s" % self.axial_id
            if axial.geometryType() == QgsWkbTypes.LineGeometry:
                caps = axial.dataProvider().capabilities()
                self.verificationThread = AxialVerification(self.iface.mainWindow(), self, settings, axial,
                                                            self.user_ids['map'], unlinks)
            else:
                self.iface.messageBar().pushMessage("Info", "Select an axial lines map layer.", level=0, duration=3)
                return False
        # verify unlinks
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Warning", "All layers must be in the same file format.", level=1,
                                                    duration=3)
                return False
            caps = unlinks.dataProvider().capabilities()
            self.user_ids['unlinks'] = lfh.getIdField(unlinks)
            if self.user_ids['unlinks'] == '':
                self.iface.messageBar().pushMessage("Info",
                                                    "The unlinks layer has invalid values in the ID column. Using feature ids.",
                                                    level=0, duration=3)
            if unlinks.dataProvider().fieldNameIndex("line1") == -1 or \
                    unlinks.dataProvider().fieldNameIndex("line2") == -1:
                self.iface.messageBar().pushMessage("Warning",
                                                    "Line ID columns missing in unlinks layer, please 'Update IDs'.",
                                                    level=1, duration=3)
                return False
            else:
                self.verificationThread = UnlinksVerification(self.iface.mainWindow(), self, settings, axial,
                                                              self.axial_id, unlinks, self.user_ids['unlinks'])
        if not caps & QgsVectorDataProvider.AddFeatures:
            self.iface.messageBar().pushMessage("Info", "To edit the selected layer, change to another file format.",
                                                level=0, duration=3)
        # prepare dialog
        self.dlg.lockLayerTab(True)
        self.dlg.setAxialVerifyProgressbar(0, 100)
        self.dlg.lockAxialEditTab(True)
        self.dlg.clearAxialVerifyReport()
        self.dlg.clearAxialProblems()
        if self.verificationThread:
            self.verificationThread.verificationFinished.connect(self.processAxialVerificationResults)
            self.verificationThread.verificationProgress.connect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.connect(self.cancelAxialVerification)
            self.verificationThread.start()
        return

    def runAxialUpdate(self):
        self.edit_mode = self.dlg.getLayerTab()
        self.analysis_layers = self.dlg.getAnalysisLayers()
        axial = lfh.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        unlinks = lfh.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
        settings = self.dlg.getAxialEditSettings()
        self.axial_id = lfh.getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Info",
                                                "The axial layer has invalid or duplicate values in the id column. Using feature ids instead.",
                                                level=0, duration=5)
        # update axial id
        if self.edit_mode == 0:
            self.user_ids['map'] = "%s" % self.axial_id
            # todo: update axial ids when layer is shapefile
        # update unlink line ids
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Error", "The selected layers must be in the same file format.",
                                                    level=1, duration=5)
                return False
            caps = unlinks.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                ids = lfh.getIdFieldNames(unlinks)
                if ids:
                    self.user_ids['unlinks'] = ids[0]
                self.verificationThread = UnlinksIdUpdate(self.iface.mainWindow(), self, unlinks,
                                                          self.user_ids['unlinks'], axial, self.axial_id,
                                                          settings['unlink_dist'])
        # prepare dialog
        self.dlg.lockLayerTab(True)
        self.dlg.setAxialVerifyProgressbar(0, 100)
        self.dlg.lockAxialEditTab(True)
        self.dlg.clearAxialVerifyReport()
        self.dlg.clearAxialProblems()
        if self.verificationThread:
            self.verificationThread.verificationFinished.connect(self.processAxialIdUpdateResults)
            self.verificationThread.verificationProgress.connect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.connect(self.cancelAxialIdUpdate)
            self.verificationThread.start()
        return

    def cancelAxialIdUpdate(self, txt=""):
        self.verificationThread.stop()
        if txt:
            self.iface.messageBar().pushMessage("Error", txt, level=1, duration=5)
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialIdUpdateResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.disconnect(self.cancelAxialIdUpdate)
        except:
            pass
        # self.verificationThread = None
        self.dlg.updateAxialVerifyProgressbar(0)
        self.dlg.lockLayerTab(False)
        self.dlg.lockAxialEditTab(False)

    def processAxialIdUpdateResults(self):
        # stop thread
        self.verificationThread.stop()
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialIdUpdateResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
        except:
            pass
        self.verificationThread = None
        # reload the layer if columns were added with the ID update
        if self.datastore['type'] in (1, 2):
            if self.edit_mode == 0:
                layer = lfh.getLegendLayerByName(self.iface, self.analysis_layers['map'])
            elif self.edit_mode == 1:
                layer = lfh.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
            connection = dbh.getDBLayerConnection(layer)
            if self.datastore['type'] == 1:
                cols = dbh.listSpatialiteColumns(connection, layer.name())
            else:
                info = dbh.getPostgisLayerInfo(layer)
                schema = info['schema']
                name = info['table']
                cols = dbh.listPostgisColumns(connection, schema, name)
            connection.close()
            # columns-1 to account for the geometry column that is not a field in QGIS
            if len(layer.dataProvider().fields()) == len(cols) - 1:
                layer.dataProvider().reloadData()
            else:
                lfh.reloadLayer(layer)
        self.dlg.setAxialProblemsFilter(["Layer IDs updated"])
        self.dlg.lockLayerTab(False)
        self.dlg.lockAxialEditTab(False)
        return True

    def cancelAxialVerification(self, txt=""):
        self.verificationThread.stop()
        if txt:
            self.iface.messageBar().pushMessage("Error", txt, level=1, duration=5)
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialVerificationResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.disconnect(self.cancelAxialVerification)
        except:
            pass
        # self.verificationThread = None
        self.dlg.updateAxialVerifyProgressbar(0)
        self.dlg.lockLayerTab(False)
        self.dlg.lockAxialEditTab(False)

    def processAxialVerificationResults(self, results, nodes):
        # stop thread
        self.verificationThread.stop()
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialVerificationResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
        except:
            pass
        self.verificationThread = None
        self.dlg.setAxialProblems(results, nodes)
        # build summary for filter Combo
        self.dlg.lockAxialEditTab(False)
        if len(nodes) > 0:
            # nodes_list = sorted(set(nodes))
            summary = ["All problems (%s)" % len(nodes)]
            for k, v in results.items():
                if len(v) > 0:
                    summary.append("%s (%s)" % (k.capitalize(), len(v)))
        else:
            summary = ["No problems found!"]
        self.dlg.setAxialProblemsFilter(summary)
        self.dlg.lockLayerTab(False)
        return True

    def zoomAxialProblem(self):
        # get relevant layer
        idx = self.dlg.getLayerTab()
        layers = self.dlg.getAnalysisLayers()
        layer = None
        name = None
        user_id = ''
        if idx == 0:
            name = layers['map']
            user_id = self.user_ids['map']
        elif idx == 1:
            name = layers['unlinks']
            user_id = self.user_ids['unlinks']
        if name:
            layer = lfh.getLegendLayerByName(self.iface, name)
        if layer:
            # get layer ids
            if user_id == '':
                self.all_ids = layer.allFeatureIds()
            else:
                self.all_ids, ids = lfh.getFieldValues(layer, user_id)
                layer.setDisplayExpression('"field_name" = {0}'.format(user_id))
            # set display field for axial map (always)
            if idx != 0:
                axial_layer = lfh.getLegendLayerByName(self.iface, layers['map'])
                if self.axial_id != '':
                    axial_layer.setDisplayExpression('"field_name" = {0}'.format(self.axial_id))
            if not self.iface.actionMapTips().isChecked():
                self.iface.actionMapTips().trigger()
            # prepare features to check
            features = []
            items = self.dlg.getAxialVerifyProblems()
            for id in items:
                if type(id) == list:
                    for i in id:
                        if int(i) in self.all_ids:
                            features.append(int(i))
                else:
                    if int(id) in self.all_ids:
                        features.append(int(id))
            # select features and zoom
            if features:
                if user_id == '':
                    layer.selectByIds(features)
                else:
                    ids = lfh.getFeaturesListValues(layer, user_id, features)
                    layer.selectByIds(list(ids.keys()))
            else:
                layer.selectByIds([])
            if layer.selectedFeatureCount() > 0:
                self.iface.mapCanvas().setCurrentLayer(layer)
                layerNode = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
                if not layerNode.isVisible():
                    layerNode.setItemVisibilityChecked(True)
                self.iface.mapCanvas().zoomToSelected()
                if layer.geometryType() in (QgsWkbTypes.Polygon, QgsWkbTypes.Point):
                    self.iface.mapCanvas().zoomOut()

    def run_analysis(self):
        # check if there's a datastore defined
        if not self.isDatastoreSet():
            # self.iface.messageBar().pushMessage("Warning","Please select a 'Data store' to save the analysis results.", level=1, duration=4)
            return
        # try to connect to the analysis engine
        if self.analysis_engine.ready():
            self.dlg.clear_analysis_report()
            # get selected layers
            self.analysis_layers = self.dlg.getAnalysisLayers()
            # get analysis type based on map and axial/segment choice
            if self.dlg.get_analysis_type() == 0:
                self.axial_analysis_settings['type'] = 0
            else:
                if self.dlg.getSegmentedMode() == 0:
                    self.axial_analysis_settings['type'] = 1
                else:
                    self.axial_analysis_settings['type'] = 2
            # get the basic analysis settings
            analysis_layer = lfh.getLegendLayerByName(self.iface, self.analysis_layers['map'])
            self.axial_analysis_settings['id'] = lfh.getIdField(analysis_layer)
            self.axial_analysis_settings['weight'] = self.dlg.get_analysis_weighted()
            self.axial_analysis_settings['weightBy'] = self.dlg.get_analysis_weight_attribute()
            txt = DepthmapEngine.parse_radii(self.dlg.get_analysis_radius_text())
            if txt == '':
                self.dlg.write_analysis_report("Please verify the radius values.")
                return
            else:
                self.axial_analysis_settings['rvalues'] = txt
            self.axial_analysis_settings['output'] = self.dlg.get_analysis_output_table()
            self.analysis_output = self.axial_analysis_settings['output']
            # get the advanced analysis settings
            self.axial_analysis_settings['distance'] = self.dlg.get_analysis_distance_type()
            self.axial_analysis_settings['radius'] = self.dlg.get_analysis_radius_type()
            self.axial_analysis_settings['fullset'] = self.dlg.get_analysis_fullset()
            self.axial_analysis_settings['betweenness'] = self.dlg.get_analysis_choice()
            self.axial_analysis_settings['newnorm'] = self.dlg.get_analysis_normalised()
            self.axial_analysis_settings['stubs'] = self.dlg.get_analysis_stubs()

            # check if output file/table already exists
            table_exists = False
            if self.datastore['type'] == 0:
                table_exists = shph.testShapeFileExists(self.datastore['path'], self.axial_analysis_settings['output'])
            elif self.datastore['type'] == 1:
                connection = dbh.getSpatialiteConnection(self.datastore['path'])
                if connection:
                    table_exists = dbh.testSpatialiteTableExists(connection, self.axial_analysis_settings['output'])
                connection.close()
            elif self.datastore['type'] == 2:
                connection = dbh.getPostgisConnection(self.datastore['name'])
                if connection:
                    table_exists = dbh.testPostgisTableExists(connection, self.datastore['schema'],
                                                              self.axial_analysis_settings['output'])
                connection.close()
            if table_exists:
                action = QMessageBox.question(None, "Overwrite table",
                                              "The output table already exists in:\n %s.\nOverwrite?" % self.datastore[
                                                  'path'], QMessageBox.Ok | QMessageBox.Cancel)
                if action == QMessageBox.Ok:  # Yes
                    pass
                elif action == QMessageBox.Cancel:  # No
                    return
                else:
                    return
            # run the analysis
            analysis_ready = self.analysis_engine.setup_analysis(self.analysis_layers, self.axial_analysis_settings)
            if analysis_ready:
                self.updateProjectSettings()
                self.start_time = datetime.datetime.now()
                # write a short analysis summary
                message = self.compile_analysis_summary()
                # print message in results window
                self.dlg.write_analysis_report(message)
                self.dlg.lock_analysis_tab(True)
                self.iface.messageBar().pushMessage("Info",
                                                    "Do not close QGIS or depthmapXnet while the analysis is running!",
                                                    level=0, duration=5)
                self.analysis_engine.start_analysis()
                # timer to check if results are ready, in milliseconds
                self.timer.start(1000)
                self.running_analysis = 'axial'
            else:
                self.dlg.write_analysis_report(
                    "Unable to run this analysis. Please check the input layer and analysis settings.")

    def compile_analysis_summary(self):
        message = u"Running analysis for map layer '%s':" % self.analysis_layers['map']
        if self.analysis_layers['unlinks']:
            message += u"\n   unlinks layer - '%s'" % self.analysis_layers['unlinks']
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
        message += u"\n\nStart: %s\n..." % self.start_time.strftime("%d/%m/%Y %H:%M:%S")
        return message

    def cancel_analysis(self):
        if self.running_analysis == 'axial':
            self.dlg.set_analysis_progressbar(0, 100)
            self.dlg.lock_analysis_tab(False)
            self.dlg.write_analysis_report("Analysis canceled by user.")
        self.timer.stop()
        self.analysis_engine.cleanup()
        self.running_analysis = ''

    def check_analysis_progress(self):
        try:
            step, progress = self.analysis_engine.get_progress(self.axial_analysis_settings, self.datastore)
            if not progress:
                # no progress, just wait...
                return
            elif progress == 100:
                self.timer.stop()
                # update calculation time
                dt = datetime.datetime.now()
                feedback = u"Finish: %s" % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.write_analysis_report(feedback)
                # process the output in the analysis
                self.process_analysis_results(self.analysis_engine.analysis_results)
                self.running_analysis = ''
            else:
                if self.running_analysis == 'axial':
                    self.dlg.update_analysis_progressbar(progress)
                    if step > 0:
                        self.timer.start(step)
        except AnalysisEngine.AnalysisEngineError as engine_error:
            if self.running_analysis == 'axial':
                self.dlg.set_analysis_progressbar(0, 100)
                self.dlg.lock_analysis_tab(False)
                self.dlg.write_analysis_report("Analysis error: " + str(engine_error))
            self.timer.stop()
            self.analysis_engine.cleanup()
            self.running_analysis = ''

    def process_analysis_results(self, analysis_results: AnalysisEngine.AnalysisResults):
        new_layer = None
        if self.running_analysis == 'axial':
            self.dlg.set_analysis_progressbar(100, 100)
            if analysis_results.attributes:
                dt = datetime.datetime.now()
                message = u"Post-processing start: %s\n..." % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.write_analysis_report(message)
                new_layer = self.save_analysis_results(analysis_results.attributes, analysis_results.types,
                                                       analysis_results.values, analysis_results.coords)
                # update processing time
                dt = datetime.datetime.now()
                message = u"Post-processing finish: %s" % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.write_analysis_report(message)
            else:
                self.iface.messageBar().pushMessage("Info", "Failed to import the analysis results.", level=1,
                                                    duration=5)
                self.dlg.write_analysis_report(u"Post-processing: Failed!")
            self.end_time = datetime.datetime.now()
            elapsed = self.end_time - self.start_time
            message = u"Total running time: %s" % elapsed
            self.dlg.write_analysis_report(message)
            self.dlg.lock_analysis_tab(False)
            self.dlg.set_analysis_progressbar(0, 100)
        if new_layer:
            existing_names = [layer.name() for layer in lfh.getLegendLayers(self.iface)]
            if new_layer.name() in existing_names:
                old_layer = lfh.getLegendLayerByName(self.iface, new_layer.name())
                if lfh.getLayerPath(new_layer) == lfh.getLayerPath(old_layer):
                    QgsProject.instance().removeMapLayer(old_layer.id())
            QgsProject.instance().addMapLayer(new_layer)
            new_layer.updateExtents()

    def save_analysis_results(self, attributes, types, values, coords):
        # Save results to output
        res = False
        analysis_layer = lfh.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        srid = analysis_layer.crs()
        path = self.datastore['path']
        table = self.analysis_output
        id = self.axial_analysis_settings['id']
        # if it's an axial analysis try to update the existing layer
        new_layer = None
        # must check if data store is still there
        if not self.isDatastoreSet():
            self.iface.messageBar().pushMessage("Warning", "The analysis results will be saved in a memory layer.",
                                                level=0, duration=5)
        # save output based on data store format and type of analysis
        provider = analysis_layer.storageType()
        create_table = False
        # if it's a segment analysis always create a new layer
        # also if one of these is different: output table name, file type, data store location, number of records
        # this last one is a weak check for changes to the table. making a match of results by id would take ages.
        if analysis_layer.name() != table or self.axial_analysis_settings['type'] == 1 or len(
                values) != analysis_layer.featureCount():
            create_table = True
        # shapefile data store
        if self.datastore['type'] == 0:
            existing_layer_path = lfh.getLayerPath(analysis_layer) + "/" + analysis_layer.name() + ".shp"
            new_layer_path = path + "/" + table + ".shp"
            original_table_name = table

            if len(values) != analysis_layer.featureCount() and existing_layer_path == new_layer_path:
                # we can't overwrite the file anymore because the number of lines is not the same,
                # force a new file, by appending a number at the end
                overwrite_counter = 1
                while os.path.isfile(new_layer_path):
                    # repeat until no such path exists
                    table = original_table_name + "_" + str(overwrite_counter)
                    new_layer_path = path + "/" + table + ".shp"
                    overwrite_counter = overwrite_counter + 1
                    if overwrite_counter > 1000:
                        self.iface.messageBar().pushMessage("Error",
                                                            "Existing file and newly suggested file have different "
                                                            "number of lines, but can not create new file as too many "
                                                            "existing duplicates",
                                                            level=Qgis.Critical, duration=5)

            if original_table_name != table:
                self.iface.messageBar().pushMessage("Warning",
                                                    "Existing file and newly suggested file have different "
                                                    "number of lines, new file created with different name",
                                                    level=Qgis.Warning, duration=5)
            if original_table_name == table and \
                    (lfh.getLayerPath(analysis_layer) != path or analysis_layer.name() != table):
                create_table = True

            # convert type of choice columns to float
            for attr in attributes:
                if 'CH' in attr:
                    idx = attributes.index(attr)
                    types[idx] = QVariant.Double
            # write a new file
            if 'shapefile' not in provider.lower() or create_table:
                new_layer = shph.create_shapefile_full_layer_data_provider(path, table, srid, attributes,
                                                                           types, values, coords)
                if new_layer:
                    res = True
                else:
                    res = False
            # or append to an existing file
            else:
                res = shph.addShapeFileAttributes(analysis_layer, attributes, types, values)
        # spatialite data store
        elif self.datastore['type'] == 1:
            connection = dbh.getSpatialiteConnection(path)
            if not dbh.testSpatialiteTableExists(connection, self.axial_analysis_settings['output']):
                create_table = True
            if 'spatialite' not in provider.lower() or create_table:
                res = dbh.createSpatialiteTable(connection, path, table, srid.postgisSrid(), attributes, types,
                                                'MULTILINESTRING')
                if res:
                    res = dbh.insertSpatialiteValues(connection, table, attributes, values, coords)
                    if res:
                        new_layer = dbh.getSpatialiteLayer(connection, path, table)
                        if new_layer:
                            res = True
                        else:
                            res = False
            else:
                res = dbh.addSpatialiteAttributes(connection, table, id, attributes, types, values)
                # the spatialite layer needs to be removed and re-inserted to display changes
                if res:
                    QgsProject.instance().removeMapLayer(analysis_layer.id())
                    new_layer = dbh.getSpatialiteLayer(connection, path, table)
                    if new_layer:
                        res = True
                    else:
                        res = False
            connection.close()
        # postgis data store
        elif self.datastore['type'] == 2:
            schema = self.datastore['schema']
            connection = dbh.getPostgisConnection(self.datastore['name'])
            if not dbh.testPostgisTableExists(connection, self.datastore['schema'],
                                              self.axial_analysis_settings['output']):
                create_table = True
            if 'postgresql' not in provider.lower() or create_table:
                res = dbh.createPostgisTable(connection, schema, table, srid.postgisSrid(), attributes, types,
                                             'MULTILINESTRING')
                if res:
                    res = dbh.insertPostgisValues(connection, schema, table, attributes, values, coords)
                    if res:
                        new_layer = dbh.getPostgisLayer(connection, self.datastore['name'], schema, table)
                        if new_layer:
                            res = True
                        else:
                            res = False
            else:
                res = dbh.addPostgisAttributes(connection, schema, table, id, attributes, types, values)
                # the postgis layer needs to be removed and re-inserted to display changes
                if res:
                    QgsProject.instance().removeMapLayer(analysis_layer.id())
                    new_layer = dbh.getPostgisLayer(connection, self.datastore['name'], schema, table)
                    if new_layer:
                        res = True
                    else:
                        res = False
            connection.close()
        # memory layer data store
        if self.datastore['type'] == -1 or not res:
            # create a memory layer with the results
            # the coords indicates the results columns with x1, y1, x2, y2
            new_layer = lfh.createTempLayer(table, srid.postgisSrid(), attributes, types, values, coords)

        return new_layer
