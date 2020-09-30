# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-06-03
# copyright            : (C) 2016 by Abhimanyu Acharya/(C) 2016 by Space Syntax Limited’.
# author               : Abhimanyu Acharya
# email                : a.acharya@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import print_function

import os
# Import the PyQt and QGIS libraries
from builtins import str
from builtins import zip

from qgis.PyQt.QtCore import (QObject, QVariant)
from qgis.core import (QgsProject, QgsMapLayer, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsVectorFileWriter,
                       QgsDataSourceUri, QgsVectorLayerExporter, QgsMessageLog, QgsFeatureRequest,
                       QgsVectorDataProvider, NULL, QgsWkbTypes, Qgis)

from esstoolkit.utilities import layer_field_helpers as lfh


class FrontageTool(QObject):

    def __init__(self, iface, dockwidget):
        QObject.__init__(self)

        self.iface = iface
        self.legend = QgsProject.instance().mapLayers()
        self.dockwidget = dockwidget
        self.frontagedlg = self.dockwidget.frontagedlg
        self.canvas = self.iface.mapCanvas()
        self.plugin_path = os.path.dirname(__file__)
        self.frontage_layer = None

        # signals from dockwidget
        self.dockwidget.loadFrontageLayer.connect(self.loadFrontageLayer)
        self.dockwidget.updateIDButton.clicked.connect(self.updateID)
        self.dockwidget.updateLengthButton.clicked.connect(self.updateLength)
        self.dockwidget.updateFacadeButton.clicked.connect(self.updateSelectedFrontageAttribute)
        self.dockwidget.updateIDPushButton.clicked.connect(self.pushID)
        self.dockwidget.pushIDcomboBox.currentIndexChanged.connect(self.updatepushWidgetList)
        self.dockwidget.hideshowButton.clicked.connect(self.hideFeatures)
        self.dockwidget.pushButtonNewFile.clicked.connect(self.updateLayers)

        # signals from new frontage dialog
        self.frontagedlg.create_new_layer.connect(self.newFrontageLayer)
        self.frontagedlg.createNewFileCheckBox.stateChanged.connect(self.updateLayers)

    #######
    #   Data functions
    #######

    # Update the f_id column of the Frontage layer
    def updateID(self):
        layer = self.dockwidget.setFrontageLayer()
        features = layer.getFeatures()
        i = 1
        layer.startEditing()
        for feat in features:
            feat['f_id'] = i
            i += 1
            layer.updateFeature(feat)
        layer.commitChanges()
        layer.startEditing()

    def isRequiredLayer(self, layer, type):
        if layer.type() == QgsMapLayer.VectorLayer \
                and layer.geometryType() == type:
            if lfh.layerHasFields(layer, ['f_group', 'f_type']):
                return True

        return False

    # Add Frontage layer to combobox if conditions are satisfied
    def updateFrontageLayer(self):
        self.dockwidget.useExistingcomboBox.clear()
        self.dockwidget.useExistingcomboBox.setEnabled(False)
        self.disconnectFrontageLayer()
        layers = self.legend.values()
        type = 1
        for lyr in layers:
            if self.isRequiredLayer(lyr, type):
                self.dockwidget.useExistingcomboBox.addItem(lyr.name(), lyr)

        if self.dockwidget.useExistingcomboBox.count() > 0:
            self.dockwidget.useExistingcomboBox.setEnabled(True)
            self.frontage_layer = self.dockwidget.setFrontageLayer()
            self.connectFrontageLayer()

    # Add building layers from the legend to combobox on main widget window
    def updateLayersPushID(self):
        self.dockwidget.pushIDcomboBox.clear()
        layers = self.legend.values()
        layer_list = []

        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QgsWkbTypes.Polygon:
                    self.dockwidget.pushIDcomboBox.setEnabled(False)
                    self.dockwidget.pushIDcomboBox.addItem(layer.name(), layer)

    # Add building layers from the legend to combobox in Create New file pop up dialogue
    def updateLayers(self):
        self.frontagedlg.selectLUCombo.clear()
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        # identify relevant layers
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == 2:
                    layer_list.append(layer.name())
        # update combo if necessary
        if layer_list:
            self.frontagedlg.createNewFileCheckBox.setEnabled(True)
            self.frontagedlg.selectLUCombo.addItems(layer_list)
            # activate combo if checked
            if self.frontagedlg.createNewFileCheckBox.checkState() == 2:
                self.frontagedlg.selectLUCombo.setEnabled(True)
            else:
                self.frontagedlg.selectLUCombo.setEnabled(False)
        else:
            self.frontagedlg.createNewFileCheckBox.setEnabled(False)
            self.frontagedlg.selectLUCombo.setEnabled(False)

    # Get building layer selected in the combo box
    def getSelectedLayer(self):
        layer_name = self.frontagedlg.selectLUCombo.currentText()
        self.LU_layer = lfh.getLegendLayerByName(self.iface, layer_name)
        return self.LU_layer

    # Set layer as frontage layer and apply thematic style
    def loadFrontageLayer(self):
        # disconnect any current frontage layer
        self.disconnectFrontageLayer()
        if self.dockwidget.useExistingcomboBox.count() > 0:
            self.frontage_layer = self.dockwidget.setFrontageLayer()
            qml_path = self.plugin_path + "/styles/frontagesThematic.qml"
            self.frontage_layer.loadNamedStyle(qml_path)
            self.frontage_layer.startEditing()
            # connect signals from layer
            self.connectFrontageLayer()

    def connectFrontageLayer(self):
        if self.frontage_layer:
            self.frontage_layer.selectionChanged.connect(self.dockwidget.addDataFields)
            self.frontage_layer.featureAdded.connect(self.logFeatureAdded)
            self.frontage_layer.featureDeleted.connect(self.dockwidget.clearDataFields)

    def disconnectFrontageLayer(self):
        if self.frontage_layer:
            self.frontage_layer.selectionChanged.disconnect(self.dockwidget.addDataFields)
            self.frontage_layer.featureAdded.disconnect(self.logFeatureAdded)
            self.frontage_layer.featureDeleted.disconnect(self.dockwidget.clearDataFields)
            self.frontage_layer = None

    # Create New Layer
    def newFrontageLayer(self):

        # always create a memory layer first

        if self.frontagedlg.createNewFileCheckBox.isChecked():
            building_layer = self.getSelectedLayer()
            crs = building_layer.crs()
            vl = QgsVectorLayer("LineString?crs=" + crs.authid(), "memory:frontages", "memory")

        else:
            vl = QgsVectorLayer("LineString?crs=", "memory:frontages", "memory")
        provider = vl.dataProvider()
        provider.addAttributes([QgsField("f_id", QVariant.Int),
                                QgsField("f_group", QVariant.String),
                                QgsField("f_type", QVariant.String),
                                QgsField("f_length", QVariant.Double)])
        vl.updateFields()

        # use building layer - explode
        if self.frontagedlg.createNewFileCheckBox.isChecked():
            print('building layer')
            exploded_features = []
            i = 1
            for f in building_layer.getFeatures():
                points = f.geometry().asPolygon()[0]  # get list of points
                for (p1, p2) in zip(points[:-1], points[1:]):
                    i += 1
                    feat = QgsFeature()
                    line_geom = QgsGeometry.fromPolyline([p1, p2])
                    feat.setAttributes([i, NULL, NULL, line_geom.geometry().length()])
                    feat.setId(i)
                    feat.setGeometry(line_geom)
                    exploded_features.append(feat)
            print('building layer2')
            vl.updateFields()
            vl.startEditing()
            provider.addFeatures(exploded_features)
            vl.commitChanges()
            print('building layer3')

        if self.frontagedlg.f_shp_radioButton.isChecked():  # layer_type == 'shapefile':

            path = self.frontagedlg.lineEditFrontages.text()

            if path and path != '':
                filename = os.path.basename(path)
                location = os.path.abspath(path)

                QgsVectorFileWriter.writeAsVectorFormat(vl, location, "ogr", None, "ESRI Shapefile")
                vl = self.iface.addVectorLayer(location, filename[:-4], "ogr")
            else:
                vl = 'invalid data source'

        elif self.frontagedlg.f_postgis_radioButton.isChecked():

            db_path = self.frontagedlg.lineEditFrontages.text()
            if db_path and db_path != '':

                (database, schema, table_name) = (self.frontagedlg.lineEditFrontages.text()).split(':')
                db_con_info = self.frontagedlg.dbsettings_dlg.available_dbs[database]
                uri = QgsDataSourceUri()
                # passwords, usernames need to be empty if not provided or else connection will fail
                if 'service' in list(db_con_info.keys()):
                    uri.setConnection(db_con_info['service'], '', '', '')  # db_con_info['dbname']
                elif 'password' in list(db_con_info.keys()):
                    uri.setConnection(db_con_info['host'], db_con_info['port'], db_con_info['dbname'],
                                      db_con_info['user'], db_con_info['password'])
                else:
                    print(db_con_info)  # db_con_info['host']
                    uri.setConnection('', db_con_info['port'], db_con_info['dbname'], '',
                                      '')  # , db_con_info['user'], '')
                uri.setDataSource(schema, table_name, "geom")
                error = QgsVectorLayerExporter.importLayer(vl, uri.uri(), "postgres", vl.crs(), False, False)
                if error[0] != 0:
                    print("Error when creating postgis layer: ", error[1])
                    vl = 'duplicate'
                else:
                    vl = QgsVectorLayer(uri.uri(), table_name, "postgres")

            else:
                vl = 'invalid data source'

        if vl == 'invalid data source':
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Specify  output path!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
        elif vl == 'duplicate':
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Fronatges layer already exists!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
        elif not vl:
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Frontages layer failed to load!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
        else:
            QgsProject.instance().addMapLayer(vl)
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Frontages layer created!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
            vl.startEditing()
            if self.isRequiredLayer(self.iface, vl, type):
                self.dockwidget.useExistingcomboBox.addItem(vl.name(), vl)

        # self.updateFrontageLayer() This is creating problems with signals - REMOVE

        # TODO: updateLength function should receive a layer as input. It would be used earlier
        self.frontagedlg.closePopUp()

    # Draw New Feature
    def logFeatureAdded(self, fid):

        QgsMessageLog.logMessage("feature added, id = " + str(fid))

        mc = self.canvas
        v_layer = self.dockwidget.setFrontageLayer()
        features = v_layer.getFeatures()
        inputid = v_layer.featureCount()
        frontagelength = 0

        data = v_layer.dataProvider()
        update1 = data.fieldNameIndex("f_group")
        update2 = data.fieldNameIndex("f_type")
        update3 = data.fieldNameIndex("f_id")
        update4 = data.fieldNameIndex("f_length")

        categorytext = self.dockwidget.frontagescatlistWidget.currentItem().text()
        subcategorytext = self.dockwidget.frontagessubcatlistWidget.currentItem().text()

        v_layer.changeAttributeValue(fid, update1, categorytext, True)
        v_layer.changeAttributeValue(fid, update2, subcategorytext, True)
        v_layer.changeAttributeValue(fid, update3, inputid, True)

        # length can be obtained after the layer is added
        request = QgsFeatureRequest().setFilterExpression(u'"f_id" = %s' % inputid)
        features = v_layer.getFeatures(request)
        for feat in features:
            geom = feat.geometry()
            frontagelength = geom.length()
        v_layer.changeAttributeValue(fid, update4, frontagelength, True)

        v_layer.updateFields()

    # Update Feature Length
    def updateLength(self):
        layer = self.dockwidget.setFrontageLayer()
        if layer:
            features = layer.getFeatures()
            for feat in features:
                geom = feat.geometry()
                feat['f_length'] = geom.length()
                layer.updateFeature(feat)

    # Update Feature
    def updateSelectedFrontageAttribute(self):
        mc = self.canvas
        layer = self.dockwidget.setFrontageLayer()
        features = layer.selectedFeatures()

        categorytext = self.dockwidget.frontagescatlistWidget.currentItem().text()
        subcategorytext = self.dockwidget.frontagessubcatlistWidget.currentItem().text()

        for feat in features:
            feat['f_group'] = categorytext
            feat['f_type'] = subcategorytext
            geom = feat.geometry()
            feat['f_length'] = geom.length()
            layer.updateFeature(feat)
        self.dockwidget.addDataFields()

    # Hide features with NULL value
    def hideFeatures(self):
        mc = self.canvas
        layer = self.dockwidget.setFrontageLayer()
        if self.dockwidget.hideshowButton.isChecked():
            qml_path = self.plugin_path + "/styles/frontagesThematic_NULL.qml"
            layer.loadNamedStyle(qml_path)
            mc.refresh()

        else:
            qml_path = self.plugin_path + "/styles/frontagesThematic.qml"
            layer.loadNamedStyle(qml_path)
            mc.refresh()

    def updatepushWidgetList(self):
        self.dockwidget.pushIDlistWidget.clear()
        buildinglayer = self.dockwidget.getSelectedLayerPushID()
        if buildinglayer:
            fields = buildinglayer.fields()
            field_names = [field.name() for field in fields]
            self.dockwidget.pushIDlistWidget.addItems(field_names)

        else:
            self.dockwidget.pushIDlistWidget.clear()

    # Push data from column in the buildings layer to the frontages layer
    def pushID(self):
        buildinglayer = self.dockwidget.getSelectedLayerPushID()

        mc = self.canvas
        frontlayer = self.dockwidget.setFrontageLayer()
        frontlayer.startEditing()

        buildingID = self.dockwidget.pushIDlistWidget.currentItem().text()
        # print buildingID
        newColumn = "b_" + buildingID
        frontlayer_pr = frontlayer.dataProvider()
        frontlayer_pr.addAttributes([QgsField(newColumn, QVariant.Int)])
        frontlayer.commitChanges()
        frontlayer.startEditing()
        frontlayer_caps = frontlayer_pr.capabilities()

        for buildfeat in buildinglayer.getFeatures():
            for frontfeat in frontlayer.getFeatures():
                if frontfeat.geometry().intersects(buildfeat.geometry()):
                    frontlayer.startEditing()

                    if frontlayer_caps & QgsVectorDataProvider.ChangeAttributeValues:
                        frontfeat[newColumn] = buildfeat[buildingID]
                        frontlayer.updateFeature(frontfeat)
                        frontlayer.commitChanges()
