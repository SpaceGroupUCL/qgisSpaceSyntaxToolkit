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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Import required modules
from AnalysisDialog import AnalysisDialog
from AxialVerification import *
from UnlinksVerification import *
from LinksVerification import *
from OriginsVerification import *
from DepthmapAnalysis import *

from .. import utility_functions as uf

import socket
import datetime
import select
import os.path


class AnalysisTool(QObject):
    editDatastoreSettings = pyqtSignal()

    def __init__(self, iface, settings, project):
        QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        self.project = project
        self.legend = self.iface.legendInterface()

    def load(self):
        # initialise UI
        self.dlg = AnalysisDialog(self.iface.mainWindow())

        # initialise axial analysis classes
        self.verificationThread = None
        self.depthmapAnalysis = DepthmapAnalysis(self.iface)

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
        self.dlg.axialDepthmapCalculateButton.clicked.connect(self.runDepthmapAnalysis)
        self.dlg.axialDepthmapCancelButton.clicked.connect(self.cancelDepthmapAnalysis)

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
        self.timer.timeout.connect(self.checkDepthmapAnalysisProgress)

        # define analysis data structures
        self.analysis_layers = {'map': "", 'unlinks': "", 'links': "", 'origins': ""}
        self.axial_analysis_settings = {'type': 0, 'distance': 0, 'radius': 0, 'rvalues': "n", 'output': "",
                                        'fullset': 0, 'betweenness': 1, 'newnorm': 1, 'weight': 0, 'weightBy': "",
                                        'stubs': 40, 'id': ""}
        self.user_ids = {'map': "", 'unlinks': "", 'links': "", 'origins': ""}
        self.analysis_output = ""
        self.getProjectSettings()

    def unload(self):
        if self.isVisible:
            # Disconnect signals from main program
            self.legend.itemAdded.disconnect(self.updateLayers)
            self.legend.itemRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.getProjectSettings)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
        self.isVisible = False

    def onShow(self):
        if self.dlg.isVisible():
            # Connect signals to QGIS interface
            self.legend.itemAdded.connect(self.updateLayers)
            self.legend.itemRemoved.connect(self.updateLayers)
            self.iface.projectRead.connect(self.updateLayers)
            self.iface.projectRead.connect(self.getProjectSettings)
            self.iface.newProjectCreated.connect(self.updateLayers)
            self.updateLayers()
            self.setDatastore()
            self.isVisible = True
        else:
            if self.isVisible:
                # Disconnect signals to QGIS interface
                self.legend.itemAdded.disconnect(self.updateLayers)
                self.legend.itemRemoved.disconnect(self.updateLayers)
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
        self.dlg.clearAxialProblems(2)
        self.dlg.clearAxialProblems(3)
        # update graph analysis
        self.dlg.setAxialDepthmapTab(self.axial_analysis_settings)

    def updateProjectSettings(self):
        self.project.writeSettings(self.analysis_layers, "analysis")
        self.project.writeSettings(self.axial_analysis_settings, "depthmap")

    def changeDatastore(self):
        #signal from UI if data store button is clicked
        self.editDatastoreSettings.emit()

    def updateDatastore(self, name):
        new_datastore = {'name': '', 'path': '', 'type': -1, 'schema': '', 'crs': ''}
        layer = uf.getLegendLayerByName(self.iface, name)
        if layer:
            new_datastore['crs'] = layer.crs().postgisSrid()
            if 'SpatiaLite' in layer.storageType():
                new_datastore['type'] = 1
                path = uf.getLayerPath(layer)
                dbname = os.path.basename(path)
                new_datastore['path'] = path
                new_datastore['name'] = dbname
                # create a new connection if not exists
                conn = uf.listSpatialiteConnections()
                if path not in conn['path']:
                    uf.createSpatialiteConnection(dbname, path)
            elif 'PostGIS' in layer.storageType():
                new_datastore['type'] = 2
                layerinfo = uf.getPostgisLayerInfo(layer)
                new_datastore['path'] = layerinfo['database']
                new_datastore['schema'] = layerinfo['schema']
                if 'connection' in layerinfo:
                    new_datastore['name'] = layerinfo['connection']
                else:
                    # create a new connection if not exists
                    uf.createPostgisConnectionSetting(layerinfo['database'], uf.getPostgisConnectionInfo(layer))
                    new_datastore['name'] = layerinfo['database']
            elif 'memory?' not in layer.storageType():  # 'Shapefile'
                new_datastore['type'] = 0
                new_datastore['path'] = uf.getLayerPath(layer)
                new_datastore['name'] = os.path.basename(new_datastore['path'])
            if new_datastore['type'] > -1:
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
                sl_connections = uf.listSpatialiteConnections()
                if len(sl_connections) > 0:
                    if self.datastore['name'] in sl_connections['name'] and self.datastore['path'] == sl_connections['path'][sl_connections['name'].index(self.datastore['name'])]:
                        txt = 'SL: %s' % self.datastore['name']
                        path = self.datastore['path']
                else:
                    uf.createSpatialiteConnection(self.datastore['name'],self.datastore['path'])
                    txt = 'SL: %s' % self.datastore['name']
                    path = self.datastore['path']
            # postgis data store
            elif self.datastore['type'] == 2 and len(uf.listPostgisConnections()) > 0:
                if self.datastore['name'] in uf.listPostgisConnections():
                    txt = 'PG: %s (%s)' % (self.datastore['name'], self.datastore['schema'])
                    path = """dbname='%s' schema='%s'""" % (self.datastore['path'], self.datastore['schema'])
        self.dlg.setDatastore(txt, path)

    def isDatastoreSet(self):
        is_set = False
        name = self.datastore['name']
        path = self.datastore['path']
        schema = self.datastore['schema']
        if self.datastore:
            if name == "":
                self.clearDatastore()
                self.iface.messageBar().pushMessage("Info", "Select a 'Data store' to save analysis results.", level=0, duration=5)
            elif self.datastore['type'] == 0 and not os.path.exists(path):
                is_set = False
            elif self.datastore['type'] == 1 and (name not in uf.listSpatialiteConnections()['name'] or not os.path.exists(path)):
                is_set = False
            elif self.datastore['type'] == 2 and (name not in uf.listPostgisConnections() or schema not in uf.listPostgisSchemas(uf.getPostgisConnection(name))):
                is_set = False
            else:
                is_set = True
           # clear whatever data store settings are saved
            if not is_set:
                self.clearDatastore()
                self.iface.messageBar().pushMessage("Info", "The selected data store cannot be found.", level=0, duration=5)
        else:
            self.clearDatastore()
            self.iface.messageBar().pushMessage("Info", "Select a 'Data store' to save analysis results.", level=0, duration=5)
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
        links_list = []
        origins_list = []
        # default selection
        analysis_map = -1
        analysis_unlinks = -1
        analysis_links = -1
        analysis_origins = -1
        layers = uf.getLegendLayers(self.iface, 'all', 'all')
        if layers:
            for layer in layers:
                # checks if the layer is projected. Geographic coordinates are not supported
                if layer.hasGeometryType() and uf.isLayerProjected(layer):
                    origins_list.append(layer.name())
                    unlinks_list.append(layer.name())
                    if layer.geometryType() == 1: # line geometry
                        map_list.append(layer.name())
                        links_list.append(layer.name())
            # settings preference
            if self.analysis_layers['map'] in map_list:
                analysis_map = map_list.index(self.analysis_layers['map'])
            if self.analysis_layers['unlinks'] in unlinks_list:
                analysis_unlinks = unlinks_list.index(self.analysis_layers['unlinks'])
            if self.analysis_layers['links'] in links_list:
                analysis_links = links_list.index(self.analysis_layers['links'])
            if self.analysis_layers['origins'] in origins_list:
                analysis_origins = origins_list.index(self.analysis_layers['origins'])
            # current selection
            selected_layers = self.dlg.getAnalysisLayers()
            if selected_layers['map'] != '' and selected_layers['map'] in map_list:
                analysis_map = map_list.index(selected_layers['map'])
            if selected_layers['unlinks'] != '' and selected_layers['unlinks'] in unlinks_list:
                analysis_unlinks = unlinks_list.index(selected_layers['unlinks'])
            if selected_layers['links'] != '' and selected_layers['links'] in links_list:
                analysis_links = links_list.index(selected_layers['links'])
            if selected_layers['origins'] != '' and selected_layers['origins'] in origins_list:
                analysis_origins = origins_list.index(selected_layers['origins'])
        else:
            self.dlg.clearAxialDepthmapTab()

        # update UI
        self.dlg.setMapLayers(map_list, analysis_map)
        self.dlg.setUnlinksLayers(unlinks_list, analysis_unlinks)
        self.dlg.setLinksLayers(links_list, analysis_links)
        self.dlg.setOriginsLayers(origins_list, analysis_origins)
        self.dlg.updateAnalysisTabs()
        self.dlg.updateAxialDepthmapTab()

    ##
    ## Layer verification functions
    ##
    def runAxialVerification(self):
        self.edit_mode = self.dlg.getLayerTab()
        self.analysis_layers = self.dlg.getAnalysisLayers()
        axial = uf.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        unlinks = uf.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
        links = uf.getLegendLayerByName(self.iface, self.analysis_layers['links'])
        origins = uf.getLegendLayerByName(self.iface, self.analysis_layers['origins'])
        settings = self.dlg.getAxialEditSettings()
        caps = None
        self.axial_id = uf.getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Info", "The axial layer has invalid values in the ID column. Using feature ids.", level=0, duration=3)
        # verify axial map
        if self.edit_mode == 0:
            # get ids (to match the object ids in the map)
            self.user_ids['map'] = "%s" % self.axial_id
            if axial.geometryType() == QGis.Line:
                caps = axial.dataProvider().capabilities()
                self.verificationThread = AxialVerification(self.iface.mainWindow(), self, settings, axial, self.user_ids['map'], unlinks, links)
            else:
                self.iface.messageBar().pushMessage("Info","Select an axial lines map layer.", level=0, duration=3)
                return False
        # verify unlinks
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Warning","All layers must be in the same file format.", level=1, duration=3)
                return False
            caps = unlinks.dataProvider().capabilities()
            self.user_ids['unlinks'] = uf.getIdField(unlinks)
            if self.user_ids['unlinks'] == '':
                self.iface.messageBar().pushMessage("Info", "The unlinks layer has invalid values in the ID column. Using feature ids.", level=0, duration=3)
            if unlinks.fieldNameIndex("line1") == -1 or unlinks.fieldNameIndex("line2") == -1:
                self.iface.messageBar().pushMessage("Warning", "Line ID columns missing in unlinks layer, please 'Update IDs'.", level=1, duration=3)
                return False
            else:
                self.verificationThread = UnlinksVerification( self.iface.mainWindow(), self, settings, axial, self.axial_id, unlinks, self.user_ids['unlinks'])
        # verify links
        elif self.edit_mode == 2:
            if links and (axial.storageType() != links.storageType()):
                self.iface.messageBar().pushMessage("Warning","All layers must be in the same file format.", level=1, duration=3)
                return False
            caps = links.dataProvider().capabilities()
            self.user_ids['links'] = uf.getIdField(links)
            if self.user_ids['links'] == '':
                self.iface.messageBar().pushMessage("Info", "The links layer has invalid values in the ID column. Using feature ids.", level=0, duration=3)
            if links.fieldNameIndex("line1") == -1 or links.fieldNameIndex("line2") == -1:
                self.iface.messageBar().pushMessage("Warning", "Line ID columns missing in links layer, please 'Update IDs'.", level=1, duration=3)
                return False
            # newfeature: check links validity
        # verify origins
        elif self.edit_mode == 3:
            if origins and (axial.storageType() != origins.storageType()):
                self.iface.messageBar().pushMessage("Warning","All layers must be in the same file format.", level=1, duration=3)
                return False
            caps = origins.dataProvider().capabilities()
            self.user_ids['origins'] = uf.getIdField(origins)
            if self.user_ids['origins'] == '':
                self.iface.messageBar().pushMessage("Info", "The origins layer has invalid values in the ID column. Using feature ids.", level=0, duration=3)
            if unlinks.fieldNameIndex("lineid") == -1:
                self.iface.messageBar().pushMessage("Warning", "Line ID columns missing in origins layer, please 'Update IDs'.", level=1, duration=3)
                return False
            # newfeature: check origins validity (for step depth and isovists)
        if not caps & QgsVectorDataProvider.AddFeatures:
            self.iface.messageBar().pushMessage("Info","To edit the selected layer, change to another file format.", level=0, duration=3)
        #prepare dialog
        self.dlg.lockLayerTab(True)
        self.dlg.setAxialVerifyProgressbar(0,100)
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
        axial = uf.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        unlinks = uf.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
        links = uf.getLegendLayerByName(self.iface, self.analysis_layers['links'])
        origins = uf.getLegendLayerByName(self.iface, self.analysis_layers['origins'])
        settings = self.dlg.getAxialEditSettings()
        self.axial_id = uf.getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Info", "The axial layer has invalid or duplicate values in the id column. Using feature ids instead.", level=0, duration=5)
        # update axial id
        if self.edit_mode == 0:
            self.user_ids['map'] = "%s" % self.axial_id
            # newfeature: update axial ids when layer is shapefile
        # update unlink line ids
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = unlinks.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                ids = uf.getIdFieldNames(unlinks)
                if ids:
                    self.user_ids['unlinks'] = ids[0]
                self.verificationThread = UnlinksIdUpdate(self.iface.mainWindow(), self, unlinks, self.user_ids['unlinks'], axial, self.axial_id, settings['unlink_dist'])
        # update link line ids
        elif self.edit_mode == 2:
            if links and (axial.storageType() != links.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = links.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                ids = uf.getIdFieldNames(links)
                if ids:
                    self.user_ids['links'] = ids[0]
                # newfeature: update links ids
        # update origin line ids
        elif self.edit_mode == 3:
            if origins and (axial.storageType() != origins.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = origins.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                ids = uf.getIdFieldNames(origins)
                if ids:
                    self.user_ids['origins'] = ids[0]
                # newfeature: update origins ids
        # prepare dialog
        self.dlg.lockLayerTab(True)
        self.dlg.setAxialVerifyProgressbar(0,100)
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
            self.iface.messageBar().pushMessage("Error",txt, level=1, duration=5)
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialIdUpdateResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.disconnect(self.cancelAxialIdUpdate)
        except:
            pass
        #self.verificationThread = None
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
        if self.datastore['type'] in (1,2):
            if self.edit_mode == 0:
                layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['map'])
            elif self.edit_mode == 1:
                layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['unlinks'])
            elif self.edit_mode == 2:
                layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['links'])
            else:
                layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['origins'])
            connection = uf.getDBLayerConnection(layer)
            if self.datastore['type'] == 1:
                cols = uf.listSpatialiteColumns(connection, layer.name())
            else:
                info = uf.getPostgisLayerInfo(layer)
                schema = info['schema']
                name = info['table']
                cols = uf.listPostgisColumns(connection, schema, name)
            connection.close()
            # columns-1 to account for the geometry column that is not a field in QGIS
            if len(layer.dataProvider().fields()) == len(cols)-1:
                layer.dataProvider().reloadData()
            else:
                reloadLayer(layer)
        self.dlg.setAxialProblemsFilter(["Layer IDs updated"])
        self.dlg.lockLayerTab(False)
        self.dlg.lockAxialEditTab(False)
        return True

    def cancelAxialVerification(self, txt=""):
        self.verificationThread.stop()
        if txt:
            self.iface.messageBar().pushMessage("Error",txt, level=1, duration=5)
        try:
            self.verificationThread.verificationFinished.disconnect(self.processAxialVerificationResults)
            self.verificationThread.verificationProgress.disconnect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.disconnect(self.cancelAxialVerification)
        except:
            pass
        #self.verificationThread = None
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
            #nodes_list = sorted(set(nodes))
            summary = ["All problems (%s)"%len(nodes)]
            for k, v in results.iteritems():
                if len(v) > 0:
                    summary.append("%s (%s)"%(k.capitalize(),len(v)))
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
        elif idx == 2:
            name = layers['links']
            user_id = self.user_ids['links']
        elif idx == 3:
            name = layers['origins']
            user_id = self.user_ids['origins']
        if name:
            layer = uf.getLegendLayerByName(self.iface,name)
        if layer:
            # get layer ids
            if user_id == '':
                self.all_ids = layer.allFeatureIds()
            else:
                self.all_ids, ids = uf.getFieldValues(layer, user_id)
                layer.setDisplayField(user_id)
            # set display field for axial map (always)
            if idx != 0:
                axial_layer = uf.getLegendLayerByName(self.iface, layers['map'])
                if self.axial_id != '':
                    axial_layer.setDisplayField(self.axial_id)
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
                    layer.setSelectedFeatures(features)
                else:
                    ids = uf.getFeaturesListValues(layer,user_id,features)
                    layer.setSelectedFeatures(ids.keys())
            else:
                layer.setSelectedFeatures([])
            if layer.selectedFeatureCount() > 0:
                self.iface.mapCanvas().setCurrentLayer(layer)
                if not self.legend.isLayerVisible(layer):
                    self.legend.setLayerVisible(layer,True)
                self.iface.mapCanvas().zoomToSelected()
                if layer.geometryType() in (QGis.Polygon, QGis.Line):
                    self.iface.mapCanvas().zoomOut()


    ##
    ## Depthmap analysis functions
    ##
    def getDepthmapConnection(self):
        # newfeature: get these settings from settings manager.
        # no need for it now as it's hardcoded in depthmapXnet.
        connection = {'host':'localhost','port':31337}
        return connection

    def connectDepthmapNet(self):
        connected = False
        connection = self.getDepthmapConnection()
        self.socket = MySocket()
        # connect socket
        result = self.socket.connectSocket(connection['host'],connection['port'])
        # if connection fails give warning and stop analysis
        if result != '':
            self.iface.messageBar().pushMessage("Info","Make sure depthmapXnet is running.", level=0, duration=4)
            connected = False
            self.socket.closeSocket()
        else:
            connected = True
        return connected

    def runDepthmapAnalysis(self):
        # check if there's a datastore defined
        if not self.isDatastoreSet():
            #self.iface.messageBar().pushMessage("Warning","Please select a 'Data store' to save the analysis results.", level=1, duration=4)
            return
        # try to connect to the analysis engine
        if self.connectDepthmapNet():
            self.dlg.clearAxialDepthmapReport()
            # get selected layers
            self.analysis_layers = self.dlg.getAnalysisLayers()
            # get the basic analysis settings
            analysis_layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['map'])
            self.axial_analysis_settings['id'] = uf.getIdField(analysis_layer)
            self.axial_analysis_settings['type'] = self.dlg.getDepthmapAnalysisType()
            self.axial_analysis_settings['weight'] = self.dlg.getDepthmapWeighted()
            self.axial_analysis_settings['weightBy'] = self.dlg.getDepthmapWeightAttribute()
            txt = self.depthmapAnalysis.parseRadii(self.dlg.getDepthmapRadiusText())
            if txt == '':
                self.dlg.writeAxialDepthmapReport("Please verify the radius values.")
                return
            else:
                self.axial_analysis_settings['rvalues'] = txt
            self.axial_analysis_settings['output'] = self.dlg.getAxialDepthmapOutputTable()
            self.analysis_output = self.axial_analysis_settings['output']
            # get the advanced analysis settings
            self.axial_analysis_settings['distance'] = self.dlg.getAxialDepthmapDistanceType()
            self.axial_analysis_settings['radius'] = self.dlg.getAxialDepthmapRadiusType()
            self.axial_analysis_settings['fullset'] = self.dlg.getAxialDepthmapFullset()
            self.axial_analysis_settings['betweenness'] = self.dlg.getAxialDepthmapChoice()
            self.axial_analysis_settings['newnorm'] = self.dlg.getAxialDepthmapNormalised()
            self.axial_analysis_settings['stubs'] = self.dlg.getAxialDepthmapStubs()

            # check if output file/table already exists
            table_exists = False
            if self.datastore['type'] == 0:
                table_exists = uf.testShapeFileExists(self.datastore['path'], self.axial_analysis_settings['output'])
            elif self.datastore['type'] == 1:
                connection = uf.getSpatialiteConnection(self.datastore['path'])
                if connection:
                    table_exists = uf.testSpatialiteTableExists(connection, self.axial_analysis_settings['output'])
                connection.close()
            elif self.datastore['type'] == 2:
                connection = uf.getPostgisConnection(self.datastore['name'])
                if connection:
                    table_exists = uf.testPostgisTableExists(connection, self.datastore['schema'], self.axial_analysis_settings['output'])
                connection.close()
            if table_exists:
                action = QMessageBox.question(None, "Overwrite table", "The output table already exists in:\n %s.\nOverwrite?"% self.datastore['path'],"Ok","Cancel","",1,1)
                if action == 0: # Yes
                    pass
                elif action == 1: # No
                    return
                else:
                    return
            # run the analysis
            command = self.depthmapAnalysis.setupAnalysis(self.analysis_layers, self.axial_analysis_settings)
            if command and command != '':
                self.updateProjectSettings()
                self.start_time = datetime.datetime.now()
                # write a short analysis summary
                message = self.compileDepthmapAnalysisSummary()
                # print message in results window
                self.dlg.writeAxialDepthmapReport(message)
                self.dlg.lockAxialDepthmapTab(True)
                self.iface.messageBar().pushMessage("Info", "Do not close QGIS or depthmapXnet while the analysis is running!", level=0, duration=5)
                # start the analysis by sending the command and starting the timer
                bytessent = self.socket.sendData(command)
                #timer to check if results are ready, in milliseconds
                self.timer.start(1000)
                self.running_analysis = 'axial'
            else:
                self.dlg.writeAxialDepthmapReport("Unable to run this analysis. Please check the input layer and analysis settings.")
                #self.iface.messageBar().pushMessage("Error","Unable to run this space syntax analysis.", level=2, duration=4)
            #self.dlg.lockAxialDepthmapTab(False)

    def compileDepthmapAnalysisSummary(self):
        message = u"Running analysis for map layer '%s':" % self.analysis_layers['map']
        if self.analysis_layers['unlinks']:
            message += u"\n   unlinks layer - '%s'" % self.analysis_layers['unlinks']
        if self.axial_analysis_settings['type'] == 0:
            txt = "axial"
        else:
            txt = "segment"
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
        if self.axial_analysis_settings['type'] == 1 and self.axial_analysis_settings['newnorm'] == 1:
            message += u"\n   calculate NACH and NAIN"
        message += u"\n\nStart: %s\n..." % self.start_time.strftime("%d/%m/%Y %H:%M:%S")
        return message

    def cancelDepthmapAnalysis(self):
        if self.running_analysis == 'axial':
            self.dlg.setAxialDepthmapProgressbar(0, 100)
            self.dlg.lockAxialDepthmapTab(False)
            self.dlg.writeAxialDepthmapReport("Analysis canceled by user.")
        self.timer.stop()
        self.socket.closeSocket()
        self.running_analysis = ''

    def checkDepthmapAnalysisProgress(self):
        error = False
        result = self.socket.isReady()
        if result:
            connected, msg = self.socket.checkData(4096)
            if "--r" in msg or "esult" in msg:
                self.timer.stop()
                # retrieve all the remaining data
                if not msg.endswith("--result--\n"):
                    received, result = self.socket.receiveData(4096,"--result--\n")
                    if received:
                        msg += result
                self.socket.closeSocket()
                # update calculation time
                dt = datetime.datetime.now()
                feedback = u"Finish: %s" % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.writeAxialDepthmapReport(feedback)
                #process the output in the analysis
                self.processDepthmapAnalysisResults(msg)
                self.running_analysis = ''
            elif "--comm: 3," in msg:
                prog = self.updateDepthmapAnalysisProgress(msg)
                if self.running_analysis == 'axial':
                    self.dlg.updateAxialDepthmapProgressbar(prog)
            elif not connected:
                error = True
        else:
            error = True
        if error:
            if self.running_analysis == 'axial':
                self.dlg.setAxialDepthmapProgressbar(0, 100)
                self.dlg.lockAxialDepthmapTab(False)
                self.dlg.writeAxialDepthmapReport("Analysis error.")
            self.timer.stop()
            self.socket.closeSocket()
            self.running_analysis = ''

    def updateDepthmapAnalysisProgress(self,msg):
        # calculate percent done and adjust timer
        relprog = 0
        # extract number of nodes
        if "--comm: 2," in msg:
            pos1 = msg.find("--comm: 2,")
            pos2 = msg.find(",0 ", pos1)
            self.analysis_nodes = msg[(pos1 + 10):pos2]
            step = int(self.analysis_nodes) * 0.2
            self.timer.start(step)
        # extract progress info from string
        progress = msg.split("\n")
        # calculate progress
        if self.analysis_nodes > 0:
            pos1 = progress[-2].find(" 3,")
            pos2 = progress[-2].find(",0 ")
            prog = progress[-2][(pos1 + 3):pos2]
            relprog = (float(prog) / float(self.analysis_nodes)) * 100
        return relprog

    def processDepthmapAnalysisResults(self, msg):
        new_layer = None
        if self.running_analysis == 'axial':
            self.dlg.setAxialDepthmapProgressbar(100, 100)
            attributes, types, values, coords = self.depthmapAnalysis.processAnalysisResult(self.datastore, msg)
            if attributes:
                dt = datetime.datetime.now()
                message = u"Post-processing start: %s\n..." % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.writeAxialDepthmapReport(message)
                new_layer = self.saveAnalysisResults(attributes, types, values, coords)
                # update processing time
                dt = datetime.datetime.now()
                message = u"Post-processing finish: %s" % dt.strftime("%d/%m/%Y %H:%M:%S")
                self.dlg.writeAxialDepthmapReport(message)
            else:
                self.iface.messageBar().pushMessage("Info","Failed to import the analysis results.",level=1,duration=5)
                self.dlg.writeAxialDepthmapReport(u"Post-processing: Failed!")
            self.end_time = datetime.datetime.now()
            elapsed = self.end_time - self.start_time
            message = u"Total running time: %s" % elapsed
            self.dlg.writeAxialDepthmapReport(message)
            self.dlg.lockAxialDepthmapTab(False)
            self.dlg.setAxialDepthmapProgressbar(0, 100)
        if new_layer:
            existing_names = [layer.name() for layer in uf.getLegendLayers(self.iface)]
            if new_layer.name() in existing_names:
                old_layer = uf.getLegendLayerByName(self.iface, new_layer.name())
                if getLayerPath(new_layer) == uf.getLayerPath(old_layer):
                    QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())
            QgsMapLayerRegistry.instance().addMapLayer(new_layer)
            new_layer.updateExtents()


    def saveAnalysisResults(self, attributes, types, values, coords):
        # Save results to output
        res = False
        analysis_layer = uf.getLegendLayerByName(self.iface, self.analysis_layers['map'])
        srid = analysis_layer.crs()
        path = self.datastore['path']
        table = self.analysis_output
        id = self.axial_analysis_settings['id']
        # if it's an axial analysis try to update the existing layer
        new_layer = None
        # must check if data store is still there
        if not self.isDatastoreSet():
            self.iface.messageBar().pushMessage("Warning","The analysis results will be saved in a memory layer.",level=0,duration=5)
        # save output based on data store format and type of analysis
        provider = analysis_layer.storageType()
        create_table = False
        # if it's a segment analysis always create a new layer
        # also if one of these is different: output table name, file type, data store location, number of records
        # this last one is a weak check for changes to the table. making a match of results by id would take ages.
        if analysis_layer.name() != table or self.axial_analysis_settings['type'] == 1 or len(values) != analysis_layer.featureCount():
            create_table = True
        # shapefile data store
        if self.datastore['type'] == 0:
            if uf.getLayerPath(analysis_layer) != path or analysis_layer.name() != table:
                create_table = True
            if 'shapefile' not in provider.lower() or create_table:
                new_layer = uf.createShapeFileFullLayer(path, table, srid, attributes, types, values, coords)
                if new_layer:
                    res = True
                else:
                    res = False
            else:
                res = uf.addShapeFileAttributes(analysis_layer, attributes, types, values)
        # spatialite data store
        elif self.datastore['type'] == 1:
            connection = uf.getSpatialiteConnection(path)
            if not uf.testSpatialiteTableExists(connection, self.axial_analysis_settings['output']):
                create_table = True
            if 'spatialite' not in provider.lower() or create_table:
                res = uf.createSpatialiteTable(connection, path, table, srid.postgisSrid(), attributes, types, 'MULTILINESTRING')
                if res:
                    res = uf.insertSpatialiteValues(connection, table, attributes, values, coords)
                    if res:
                        new_layer = uf.getSpatialiteLayer(connection, path, table)
                        if new_layer:
                            res = True
                        else:
                            res = False
            else:
                res = uf.addSpatialiteAttributes(connection, table, id, attributes, types, values)
                # the spatialite layer needs to be removed and re-inserted to display changes
                if res:
                    QgsMapLayerRegistry.instance().removeMapLayer(analysis_layer.id())
                    new_layer = uf.getSpatialiteLayer(connection, path, table)
                    if new_layer:
                        res = True
                    else:
                        res = False
            connection.close()
        # postgis data store
        elif self.datastore['type'] == 2:
            schema = self.datastore['schema']
            connection = uf.getPostgisConnection(self.datastore['name'])
            if not uf.testPostgisTableExists(connection, self.datastore['schema'], self.axial_analysis_settings['output']):
                create_table = True
            if 'postgresql' not in provider.lower() or create_table:
                res = uf.createPostgisTable(connection, schema, table, srid.postgisSrid(), attributes, types, 'MULTILINESTRING')
                if res:
                    res = uf.insertPostgisValues(connection, schema, table, attributes, values, coords)
                    if res:
                        new_layer = uf.getPostgisLayer(connection, self.datastore['name'], schema, table)
                        if new_layer:
                            res = True
                        else:
                            res = False
            else:
                res = uf.addPostgisAttributes(connection, schema, table, id, attributes, types, values)
                # the postgis layer needs to be removed and re-inserted to display changes
                if res:
                    QgsMapLayerRegistry.instance().removeMapLayer(analysis_layer.id())
                    new_layer = uf.getPostgisLayer(connection, self.datastore['name'], schema, table)
                    if new_layer:
                        res = True
                    else:
                        res = False
            connection.close()
        # memory layer data store
        if self.datastore['type'] == -1 or not res:
            # create a memory layer with the results
            # the coords indicates the results columns with x1, y1, x2, y2
            new_layer = uf.createTempLayer(table, srid.postgisSrid(), attributes, types, values, coords)

        return new_layer


# socket class with adapted methods and error trapping, derived from QObject to support Signals
class MySocket(QObject):
    def __init__(self, s=None):
        QObject.__init__(self)
        if s is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = s

    def connectSocket(self, host, port):
        msg = ''
        try:
            self.sock.connect((host, port))
        except socket.error as errormsg:
            msg = errormsg.strerror
            #msg = errormsg.errno
        return msg

    def sendData(self, data):
        size = len(data)
        sent = False
        totalsent = 0
        try:
            while totalsent < size:
                sent = self.sock.send(data[totalsent:])
                if sent == False:
                    raise IOError("Socket connection broken")
                totalsent = totalsent + sent
            sent = True
            msg = totalsent
        except socket.error as errormsg:
            #self.closeSocket()
            sent = False
            msg = errormsg
        return sent, str(msg)

    def isReady(self):
        try:
            to_read, to_write, exception = select.select([self.sock],[],[self.sock], 0)
            if exception:
                waiting = False
            else:
                waiting = True
        except:
            waiting = False
        return waiting

    def checkData(self, buff=1):
        check = False
        msg = ''
        try:
            msg = self.sock.recv(buff)
            if msg == '':
                check = False
            else:
                check = True
        except socket.error as errormsg:
            msg = errormsg
            check = False
        return check, msg

    def dumpData(self, buff=1):
        dump = False
        msg = ''
        try:
            while True:
                chunk = self.sock.recv(buff)
                if not chunk:
                    break
                msg += chunk
            dump = True
        except socket.error as errormsg:
            msg = errormsg
            dump = False
        return dump, msg

    def receiveData(self, buff=1024, suffix=''):
        receive = False
        msg = ''
        try:
            while True:
                chunk = self.sock.recv(buff)
                if not chunk:
                    break
                msg += chunk
                if msg.endswith(suffix):
                    break
            receive = True
        except socket.error as errormsg:
            msg = errormsg
            receive = False
        return receive, msg

    def closeSocket(self):
        self.sock.close()
        #self.sock = None