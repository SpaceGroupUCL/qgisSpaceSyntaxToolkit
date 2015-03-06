# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2014 by Jorge Gil, UCL
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

from ..utility_functions import *

import socket
import datetime
import select
import os.path


class AnalysisTool(QObject):
    editDatastoreSettings = pyqtSignal()
    #updateDatastoreSettings = pyqtSignal(dict, str)

    def __init__(self, iface, settings, project):
        QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        self.project = project
        self.legend = self.iface.legendInterface()

        # initialise UI
        self.dlg = AnalysisDialog(self.iface.mainWindow())

        # initialise axial analysis classes
        self.verificationThread = None
        self.depthmapAnalysis = DepthmapAnalysis(self.iface)

        # connect signal/slots with main program
        self.project.settingsUpdated.connect(self.setDatastore)
        self.editDatastoreSettings.connect(self.project.showDialog)
        #self.updateDatastoreSettings.connect(self.project.writeSettings)
        self.project.getProject().instance().layerLoaded.connect(self.getProjectSettings)

        # set up GUI signals
        #self.dlg.dialogClosed.connect(self.onHide)
        self.dlg.visibilityChanged.connect(self.onShow)
        self.dlg.analysisDataButton.clicked.connect(self.changeDatastore)
        self.dlg.updateDatastore.connect(self.updateDatastore)
        #self.dlg.analysisNewMapButton.clicked.connect(self.createMapLayer)
        #self.dlg.analysisNewUnlinksButton.clicked.connect(self.axialUnlinks.newAxialUnlinks)
        #self.dlg.analysisNewLinksButton.clicked.connect(self.axialLinks.newAxialLinks)
        #self.dlg.analysisNewOriginsButton.clicked.connect(self.axialOrigins.newAxialOrigins)
        self.dlg.axialVerifyButton.clicked.connect(self.runAxialVerification)
        self.dlg.axialUpdateButton.clicked.connect(self.runAxialUpdate)
        self.dlg.axialVerifyCancelButton.clicked.connect(self.cancelAxialVerification)
        self.dlg.axialReportList.itemSelectionChanged.connect(self.zoomAxialProblem)
        self.dlg.axialDepthmapCalculateButton.clicked.connect(self.runDepthmapAnalysis)
        self.dlg.axialDepthmapCancelButton.clicked.connect(self.cancelDepthmapAnalysis)

        # connect signal/slots with main program
        self.legend.itemAdded.connect(self.updateLayers)
        self.legend.itemRemoved.connect(self.updateLayers)
        self.iface.projectRead.connect(self.updateLayers)
        self.iface.newProjectCreated.connect(self.updateLayers)

        # initialise internal globals
        self.isVisible = False
        self.datastore = dict()
        self.running_analysis = ''
        self.start_time = None
        self.end_time = None
        self.analysis_nodes = 0
        self.current_layer = QgsVectorLayer()
        self.user_id = ''
        self.axial_id = ''
        self.all_ids = []

        # timer to check for analysis result
        self.timer = QTimer()
        self.timer.timeout.connect(self.checkDepthmapAnalysisProgress)

        # define analysis data structures
        self.analysis_layers = {'map':'','unlinks':'','links':'','origins':''}
        self.axial_analysis_settings = {'type':0,'distance':0,'radius':0,'rvalues':'n','output':'',
                                        'fullset':0,'betweenness':1,'newnorm':1,'weight':0,'weightBy':''}
        self.analysis_output = ''


    def unload(self):
        if self.isVisible:
            # Disconnect signals from main program
            self.legend.itemAdded.disconnect(self.updateLayers)
            self.legend.itemRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
            self.project.getProject().instance().layerLoaded.disconnect(self.getProjectSettings)
        self.isVisible = False

    def onShow(self):
        if self.dlg.isVisible():
            # Connect signals to QGIS interface
            self.legend.itemAdded.connect(self.updateLayers)
            self.legend.itemRemoved.connect(self.updateLayers)
            self.iface.projectRead.connect(self.updateLayers)
            self.iface.newProjectCreated.connect(self.updateLayers)
            self.project.getProject().instance().layerLoaded.connect(self.getProjectSettings)
            self.updateLayers()
            self.setDatastore()
            self.isVisible = True
        else:
            # Disconnect signals to QGIS interface
            self.legend.itemAdded.disconnect(self.updateLayers)
            self.legend.itemRemoved.disconnect(self.updateLayers)
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
            self.project.getProject().instance().layerLoaded.disconnect(self.getProjectSettings)
            self.isVisible = False


    ##
    ## manage project and tool settings
    ##
    def getProjectSettings(self):
        # pull relevant settings from project manager
        self.project.readSettings(self.analysis_layers,"analysis")
        self.project.readSettings(self.axial_analysis_settings,"depthmap")
        # update UI
        self.updateLayers()
        if self.axial_analysis_settings['type'] == 0:
            self.dlg.setDepthmapAxialAnalysis()
        else:
            self.dlg.setDepthmapSegmentAnalysis()
        self.dlg.setDepthmapRadiusText(self.axial_analysis_settings['rvalues'])
        self.dlg.setDepthmapWeighted(self.axial_analysis_settings['weight'])
        self.dlg.dlg_depthmap.setRadiusType(self.axial_analysis_settings['radius'])
        self.dlg.dlg_depthmap.setCalculateFull(self.axial_analysis_settings['fullset'])
        self.dlg.dlg_depthmap.setCalculateChoice(self.axial_analysis_settings['betweenness'])
        self.dlg.dlg_depthmap.setCalculateNorm(self.axial_analysis_settings['newnorm'])

    def updateProjectSettings(self):
        self.project.writeSettings(self.analysis_layers,"analysis")
        self.project.writeSettings(self.axial_analysis_settings,"depthmap")

    def changeDatastore(self):
        #signal from UI if data store button is clicked
        self.editDatastoreSettings.emit()

    def updateDatastore(self, name):
        new_datastore = {'name':'','path':'','type':-1,'schema':'','crs':''}
        layer = getLayerByName(name)
        new_datastore['path'] = getLayerPath(layer)
        new_datastore['name'] = os.path.basename(new_datastore['path'])
        new_datastore['crs'] = layer.crs().postgisSrid()
        if 'SpatiaLite' in layer.storageType():
            new_datastore['type'] = 0
        elif 'Shapefile' in layer.storageType():
            new_datastore['type'] = 1
        elif 'PostGIS' in layer.storageType():
            new_datastore['type'] = 2
            new_datastore['schema'] = ''
        if new_datastore['type'] > -1:
            #self.updateDatastoreSettings.emit(new_datastore, 'datastore')
            self.project.writeSettings(new_datastore, 'datastore')
            self.setDatastore()
        else:
            return

    def clearDatastore(self):
        new_datastore = {'name':'','path':'','type':-1,'schema':'','crs':''}
        self.project.writeSettings(new_datastore, 'datastore')
        self.setDatastore()

    def setDatastore(self):
        self.datastore = self.project.getGroupSettings('datastore')
        if 'type' in self.datastore:
            self.datastore['type'] = int(self.datastore['type'])
        # update UI
        txt = ""
        path = ""
        if 'name' in self.datastore:
            if self.datastore['name'] != "" and os.path.exists(self.datastore['path']):
                # get elements for string to identify data store for user
                if 'type' in self.datastore:
                    if self.datastore['type'] == 0:
                        txt = 'SL: '
                    elif self.datastore['type'] == 1:
                        txt = 'SF: '
                    elif self.datastore['type'] == 2:
                        txt = 'PG: '
                txt += self.datastore['name']
                path = self.datastore['path']
        self.dlg.setDatastore(txt, path)

    def isDatastoreSet(self):
        is_set = False
        if self.datastore['name'] == "":
            self.iface.messageBar().pushMessage("Warning","Select a data store to save analysis results.",level=1,duration=5)
        elif not os.path.exists(self.datastore['path']):
            # clear datastore
            self.clearDatastore()
            self.iface.messageBar().pushMessage("Warning","The selected data store cannot be found.",level=1,duration=5)
        else:
            is_set = True
        return is_set

    def getToolkitSettings(self):
        # pull relevant settings from settings manager: self.settings
        # todo: get relevant settings from tool
        pass

    def updateToolkitSettings(self):
        # todo: save layer edit settings to toolkit
        pass

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
        try:
            # fixme: throws NoneType error occasionally when removing layers. trapping it for now.
            layers = getLegendLayers(self.iface,[1],'all')
        except:
            layers = None
        if layers:
            for layer in layers:
                if isLayerProjected(layer):
                    map_list.append(layer.name())
                    links_list.append(layer.name())
        try:
            layers = getLegendLayers(self.iface,[0,1,2],'all')
        except:
            layers = None
        if layers:
            for layer in layers:
                if isLayerProjected(layer):
                    unlinks_list.append(layer.name())
                    origins_list.append(layer.name())
        # default selection
        analysis_map = -1
        analysis_unlinks = -1
        analysis_links = -1
        analysis_origins = -1
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
        # update UI
        self.dlg.setMapLayers(map_list, analysis_map)
        self.dlg.setUnlinksLayers(unlinks_list, analysis_unlinks)
        self.dlg.setLinksLayers(links_list, analysis_links)
        self.dlg.setOriginsLayers(origins_list, analysis_origins)

    def createMapLayer(self):
        # newfeature: create map layer. probably remove this in the future
        if not self.datastore['type']:
            # ask to set datastore
            return
        # get table name
        name = ""
        # create new layer
        #self.axialMap.createAxialMap(name, self.datastore['type'])

    def createAxialFeature(self):
        # newfeature: create a new line with standard attributes. probably remove this in the future
        self.edit_mode = self.dlg.getLayerTab()

    def createUnlinkFeature(self):
        # newfeature: create a new unlink updating attributes. probably remove this in the future
        self.edit_mode = self.dlg.getLayerTab()


    ##
    ## Layer verification functions
    ##
    def runAxialVerification(self):
        self.edit_mode = self.dlg.getLayerTab()
        self.analysis_layers = self.dlg.getAnalysisLayers()
        axial = getLayerByName(self.analysis_layers['map'])
        unlinks = getLayerByName(self.analysis_layers['unlinks'])
        links = getLayerByName(self.analysis_layers['links'])
        origins = getLayerByName(self.analysis_layers['origins'])
        settings = self.dlg.getAxialEditSettings()
        caps = None
        self.axial_id = getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Warning", "The axial layer has invalid or duplicate values in the ID column. Using feature ids instead.", level=1, duration=5)
        if self.edit_mode == 0:
            # get ids (to match the object ids in the map)
            self.user_id = self.axial_id
            if axial.geometryType() == QGis.Line:
                caps = axial.dataProvider().capabilities()
                self.verificationThread = AxialVerification(self.iface.mainWindow(), self, settings, axial, self.user_id, unlinks, links)
            else:
                self.iface.messageBar().pushMessage("Error","Select an axial lines map layer.", level=1, duration=5)
                return False
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Error","All layers must be in the same file format.", level=1, duration=5)
                return False
            caps = unlinks.dataProvider().capabilities()
            self.user_id = getIdField(unlinks)
            if self.user_id == '':
                self.iface.messageBar().pushMessage("Warning", "The unlinks layer has invalid or duplicate values in the ID column. Using feature ids instead.", level=1, duration=5)
            if unlinks.fieldNameIndex("line1") == -1 or unlinks.fieldNameIndex("line2") == -1:
                self.iface.messageBar().pushMessage("Warning", "The unlinks layer is missing the line1 and line2 ID columns. Update IDs to complete the verification.", level=1, duration=5)
            self.verificationThread = UnlinksVerification( self.iface.mainWindow(), self, settings, axial, self.axial_id, unlinks, self.user_id)
        elif self.edit_mode == 2:
            if links and (axial.storageType() != links.storageType()):
                self.iface.messageBar().pushMessage("Error","All layers must be in the same file format.", level=1, duration=5)
                return False
            caps = links.dataProvider().capabilities()
            self.user_id = getIdField(links)
            if self.user_id == '':
                self.iface.messageBar().pushMessage("Warning", "The links layer has invalid or duplicate values in the ID column. Using feature ids instead.", level=1, duration=5)
            if links.fieldNameIndex("line1") == -1 or links.fieldNameIndex("line2") == -1:
                self.iface.messageBar().pushMessage("Warning", "The links layer is missing the line1 and line2 ID columns. Update IDs to complete the verification.", level=1, duration=5)
            # newfeature: check links validity
        elif self.edit_mode == 3:
            if origins and (axial.storageType() != origins.storageType()):
                self.iface.messageBar().pushMessage("Error","All layers must be in the same file format.", level=1, duration=5)
                return False
            caps = origins.dataProvider().capabilities()
            self.user_id = getIdField(origins)
            if self.user_id == '':
                self.iface.messageBar().pushMessage("Warning", "The origins layer has invalid or duplicate values in the ID column. Using feature ids instead.", level=1, duration=5)
            if unlinks.fieldNameIndex("lineid") == -1:
                self.iface.messageBar().pushMessage("Warning", "The unlinks layer is missing the lineid column. Update IDs to complete the verification.", level=1, duration=5)
            # newfeature: check origins validity (for step depth/isovists)
        if not caps & QgsVectorDataProvider.AddFeatures:
            self.iface.messageBar().pushMessage("Info","To edit the selected layer, change to another file format.", level=0, duration=5)
        self.dlg.setAxialVerifyProgressbar(0,100)
        self.dlg.lockAxialEditTab(True)
        self.dlg.clearAxialProblems()
        if self.verificationThread:
            self.verificationThread.verificationFinished.connect(self.processAxialVerificationResults)
            self.verificationThread.verificationProgress.connect(self.dlg.updateAxialVerifyProgressbar)
            self.verificationThread.verificationError.connect(self.cancelAxialVerification)
            self.verificationThread.start()
        return True


    def runAxialUpdate(self):
        self.edit_mode = self.dlg.getLayerTab()
        self.analysis_layers = self.dlg.getAnalysisLayers()
        axial = getLayerByName(self.analysis_layers['map'])
        unlinks = getLayerByName(self.analysis_layers['unlinks'])
        links = getLayerByName(self.analysis_layers['links'])
        origins = getLayerByName(self.analysis_layers['origins'])
        settings = self.dlg.getAxialEditSettings()
        self.axial_id= getIdField(axial)
        if self.axial_id == '':
            self.iface.messageBar().pushMessage("Warning", "The axial layer has invalid or duplicate values in the id column. Using feature ids instead.", level=1, duration=5)
        if self.edit_mode == 0:
            self.user_id = self.axial_id
            # newfeature: update axial ids when layer is shapefile
        elif self.edit_mode == 1:
            if unlinks and (axial.storageType() != unlinks.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = unlinks.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                self.user_id = getIdField(unlinks)
                self.verificationThread = UnlinksIdUpdate(self.iface.mainWindow(), self, unlinks, self.user_id, axial, self.axial_id, settings['unlink_dist'])
        elif self.edit_mode == 2:
            if links and (axial.storageType() != links.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = links.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                # newfeature: update links ids
        elif self.edit_mode == 3:
            if origins and (axial.storageType() != origins.storageType()):
                self.iface.messageBar().pushMessage("Error","The selected layers must be in the same file format.", level=1, duration=5)
                return False
            caps = origins.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                self.dlg.lockAxialEditTab(True)
                self.dlg.clearAxialProblems()
                # newfeature: update origins ids
        self.dlg.setAxialVerifyProgressbar(0,100)
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
        if self.datastore['type'] == 0:
            if self.edit_mode == 0:
                layer = getLayerByName(self.analysis_layers['map'])
            elif self.edit_mode == 1:
                layer = getLayerByName(self.analysis_layers['unlinks'])
            elif self.edit_mode == 2:
                layer = getLayerByName(self.analysis_layers['links'])
            else:
                layer = getLayerByName(self.analysis_layers['origins'])
            connection = getLayerConnection(layer)
            cols = listSpatialiteColumns(connection, layer.name())
            connection.close()
            if len(layer.dataProvider().fields()) == len(cols)-1:
                layer.dataProvider().reloadData()
            else:
                reloadLayer(layer)
        self.dlg.setAxialProblemsFilter(["Layer IDs updated"])
        self.dlg.lockAxialEditTab(False)
        return True

    def cancelAxialVerification(self, txt=""):
        # fixme: check if working at all/for shape files
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
        return True

    def zoomAxialProblem(self):
        # get relevant layer
        idx = self.dlg.getLayerTab()
        layers = self.dlg.getAnalysisLayers()
        layer = None
        name = None
        if idx == 0:
            name = layers['map']
        elif idx == 1:
            name = layers['unlinks']
        elif idx == 2:
            name = layers['links']
        elif idx == 3:
            name = layers['origins']
        if name:
            if name != self.current_layer.name():
                layer = getLayerByName(name)
                self.current_layer = layer
            else:
                layer = self.current_layer
        if layer:
            # get layer ids
            #self.user_id = getIdField(layer)
            if self.user_id == '':
                self.all_ids = layer.allFeatureIds()
            else:
                self.all_ids = getFieldValues(layer, self.user_id)
                layer.setDisplayField(self.user_id)
            # set display field for axial map (always)
            if idx != 0:
                axial_layer = getLayerByName(layers['map'])
                if self.axial_id != '':
                    axial_layer.setDisplayField(self.axial_id)
            if not self.iface.actionMapTips().isChecked():
                self.iface.actionMapTips().trigger()
            # preare features to check
            features = []
            items = self.dlg.getAxialVerifyProblems()
            # select features and zoom
            for id in items:
                if type(id) == list:
                    for i in id:
                        if int(i) in self.all_ids:
                            features.append(int(i))
                else:
                    if int(id) in self.all_ids:
                        features.append(int(id))
            if features:
                if self.user_id == '':
                    layer.setSelectedFeatures(features)
                else:
                    ids = getFeatureListIds(layer,self.user_id,features)
                    layer.setSelectedFeatures(ids.values())
            else:
                layer.setSelectedFeatures([])
            if layer.selectedFeatureCount() > 0:
                self.iface.mapCanvas().setCurrentLayer(layer)
                if not self.legend.isLayerVisible(layer):
                    self.legend.setLayerVisible(layer,True)
                self.iface.mapCanvas().zoomToSelected()
                if layer.geometryType() in (QGis.Polygon, QGis.Line):
                    self.iface.mapCanvas().zoomOut()
                #else:
                    #self.iface.mapCanvas().zoomIn()


    ##
    ## Depthmap analysis functions
    ##
    def getDepthmapConnection(self):
        # todo: get these settings from settings manager
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
            self.iface.messageBar().pushMessage("Warning","Make sure depthmapX is running.", level=1, duration=4)
            connected = False
            self.socket.closeSocket()
        else:
            connected = True
        return connected

    def runDepthmapAnalysis(self):
        # check if there's a datastore defined
        if not self.isDatastoreSet():
            return
        # try to connect to the analysis engine
        if self.connectDepthmapNet():
            self.dlg.clearAxialDepthmapReport()
            # get selected layers
            self.analysis_layers = self.dlg.getAnalysisLayers()
            # get the basic analysis settings
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

            # check if output file/table already exists
            table_exists = False
            if self.datastore['type'] == 0:
                connection = getSpatialiteConnection(self.datastore['path'])
                if connection:
                    table_exists = testSpatialiteTableExists(connection,self.axial_analysis_settings['output'])
                connection.close()
            elif self.datastore['type'] == 1:
                table_exists = testShapeFileExists(self.datastore['path'],self.axial_analysis_settings['output'])
            if table_exists:
                action = QMessageBox.question(None, "Overwrite table", "The output table already exists in:\n %s.\nOverwrite?"% self.datastore['path'],"Ok","Cancel","",1,1)
                if action == 0:
                    pass
                elif action == 1:
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
                self.iface.messageBar().pushMessage("Info","Do not close QGIS or depthmapX while the analysis is running!", level=0, duration=5)
                # start the analysis by sending the command and starting the timer
                bytessent = self.socket.sendData(command)
                #timer to check if results are ready, in milliseconds
                self.timer.start(1000)
                self.running_analysis = 'axial'
            else:
                self.dlg.writeAxialDepthmapReport("Unable to run this analysis. Please check the analysis settings.")
                #self.iface.messageBar().pushMessage("Error","Unable to run this space syntax analysis.", level=2, duration=4)

    def compileDepthmapAnalysisSummary(self):
        message = u"Running analysis for layer '%s':" % self.analysis_layers["map"]
        if self.axial_analysis_settings['type'] == 0:
            txt = "axial"
        else:
            txt = "segment"
        message = message + u"\n   analysis type - %s" % txt
        if self.axial_analysis_settings['distance'] == 0:
            txt = "topological"
        elif self.axial_analysis_settings['distance'] == 1:
            txt = "angular"
        elif self.axial_analysis_settings['distance'] == 2:
            txt = "metric"
        message = message + u"\n   distance - %s" % txt
        if self.axial_analysis_settings['weight'] == 1:
            message = message + u"\n   weighted by - %s" % self.axial_analysis_settings['weightBy']
        if self.axial_analysis_settings['radius'] == 0:
            txt = "topological"
        elif self.axial_analysis_settings['radius'] == 1:
            txt = "angular"
        elif self.axial_analysis_settings['radius'] == 2:
            txt = "metric"
        message = message + u"\n   %s radius - %s" % (txt,self.axial_analysis_settings['rvalues'])
        if self.axial_analysis_settings['betweenness'] == 1:
            message = message + u"\n   calculate choice"
        if self.axial_analysis_settings['fullset'] == 1:
            message = message + u"\n   include advanced measures"
        if self.axial_analysis_settings['newnorm'] == 1:
            message = message + u"\n   calculate NACH and NAIN"
        message = message + u"\n\nStart: %s\n..." % self.start_time.strftime("%d/%m/%Y %H:%M:%S")
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
            pos2 = msg.find(",0 ",pos1)
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
                self.iface.messageBar().pushMessage("Warning","Failed to import the analysis results.",level=1,duration=5)
                self.dlg.writeAxialDepthmapReport(u"Post-processing: Failed!")
            self.end_time = datetime.datetime.now()
            elapsed = self.end_time - self.start_time
            message = u"Total running time: %s" % elapsed
            self.dlg.writeAxialDepthmapReport(message)
            self.dlg.lockAxialDepthmapTab(False)
            self.dlg.setAxialDepthmapProgressbar(0, 100)
        if new_layer:
            existing_names = [layer.name() for layer in getLegendLayers(self.iface)]
            if new_layer.name() in existing_names:
                old_layer = getLegendLayerByName(self.iface,new_layer.name())
                if getLayerPath(new_layer) == getLayerPath(old_layer):
                    QgsMapLayerRegistry.instance().removeMapLayer(old_layer.id())
            QgsMapLayerRegistry.instance().addMapLayer(new_layer)
            new_layer.updateExtents()


    def saveAnalysisResults(self, attributes, types, values, coords):
        # Save results to output
        analysis_layer = getLegendLayerByName(self.iface, self.analysis_layers['map'])
        srid = analysis_layer.crs()
        path = self.datastore['path']
        name = self.analysis_output
        # if it's an axial analysis try to update the existing layer
        new_layer = None
        # must check if data store is still there
        if not self.isDatastoreSet():
            self.iface.messageBar().pushMessage("Warning","The analysis results will be saved in a memory layer.",level=1,duration=5)
        # save output based on data store format and type of analysis
        provider = analysis_layer.storageType()
        create_table = False
        # if it's a segment analysis always create a new layer
        # also if one of these is different: output table name, file type, data store location, number of records
        # this last one is a weak check for changes to the table. making a match of results by id would take ages.
        if self.axial_analysis_settings['type'] == 1 or analysis_layer.name() != name or getLayerPath(analysis_layer) != path or len(values) != analysis_layer.featureCount():
            create_table = True
        # spatialite data store
        if self.datastore['type'] == 0:
            connection = getSpatialiteConnection(path)
            if ('spatialite' not in provider.lower() or create_table):
                res = createSpatialiteTable(connection, path, name, srid.postgisSrid(), attributes, types, 'MULTILINESTRING')
                if res:
                    res = insertSpatialiteValues(connection, name, attributes, values, coords)
                    if res:
                        new_layer = getSpatialiteLayer(connection, path, name)
            else:
                res = addSpatialiteAttributes(connection, name, attributes, types, values)
                # the spatialite layer needs to be removed and re-inserted to display changes
                if res:
                    QgsMapLayerRegistry.instance().removeMapLayer(analysis_layer.id())
                    new_layer = getSpatialiteLayer(connection, path, name)
            connection.close()
        # shapefile data store
        elif self.datastore['type'] == 1:
            if ('shapefile' not in provider.lower() or create_table):
                new_layer = createShapeFileFullLayer(path, name, srid, attributes, types, values, coords)
            else:
                res = addShapeFileAttributes(analysis_layer, attributes, types, values)
        # postgis data store
        elif self.datastore['type'] == 2:
            if ('postgresql' not in provider.lower() or create_table):
                # newfeature: implement PostGIS handling
                pass
        # memory layer data store
        elif self.datastore['type'] == -1:
            # create a memory layer with the results
            # the coords indicates the results columns with x1, y1, x2, y2
            new_layer = createTempLayer(name, srid.postgisSrid(), attributes, types, values, coords)

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
            #print 'r: ' + str(to_read)
            #print 'w: ' + str(to_write)
            #print 'x: ' + str(exception)
            #if to_read or to_write:
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
                if not chunk: break
                msg += chunk
            dump = True
        except socket.error as errormsg:
            msg = errormsg
            dump = False
        return dump, msg

    def receiveData(self, buff=1024, suffix = ''):
        receive = False
        msg = ''
        try:
            while True:
                chunk = self.sock.recv(buff)
                if not chunk: break
                msg += chunk
                if msg.endswith(suffix): break
            receive = True
        except socket.error as errormsg:
            msg = errormsg
            receive = False
        return receive, msg

    def closeSocket(self):
        self.sock.close()
        #self.sock = None