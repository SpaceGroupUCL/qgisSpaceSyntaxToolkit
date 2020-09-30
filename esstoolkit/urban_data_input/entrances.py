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

from qgis.PyQt.QtCore import (QObject, QVariant)
from qgis.core import (QgsProject, QgsVectorLayer, QgsField, QgsCoordinateReferenceSystem, QgsVectorFileWriter,
                       QgsDataSourceUri, QgsVectorLayerExporter, QgsMessageLog, QgsMapLayer, Qgis)

from esstoolkit.utilities import layer_field_helpers as lfh


class EntranceTool(QObject):

    def __init__(self, iface, dockwidget):
        QObject.__init__(self)
        self.iface = iface
        self.legend = QgsProject.instance().mapLayers()
        self.canvas = self.iface.mapCanvas()

        self.dockwidget = dockwidget
        self.entrancedlg = self.dockwidget.entrancedlg

        self.plugin_path = os.path.dirname(__file__)

        self.entrance_layer = None

        # signals from dockwidget
        self.dockwidget.updateEntranceButton.clicked.connect(self.updateSelectedEntranceAttribute)
        self.dockwidget.updateEntranceIDButton.clicked.connect(self.updateIDEntrances)
        self.dockwidget.useExistingEntrancescomboBox.currentIndexChanged.connect(self.loadEntranceLayer)

        # signals from new entrance dialog
        self.entrancedlg.create_new_layer.connect(self.newEntranceLayer)

    #######
    #   Data functions
    #######

    # Update the F_ID column of the Frontage layer
    def updateIDEntrances(self):
        layer = self.dockwidget.setEntranceLayer()
        features = layer.getFeatures()
        i = 1
        layer.startEditing()
        for feat in features:
            feat['e_id'] = i
            i += 1
            layer.updateFeature(feat)

        layer.commitChanges()
        layer.startEditing()

    def isRequiredEntranceLayer(self, layer, type):
        if layer.type() == QgsMapLayer.VectorLayer \
                and layer.geometryType() == type:
            if lfh.layerHasFields(layer, ['e_category', 'e_subcat']):
                return True

        return False

    # Add Frontage layer to combobox if conditions are satisfied
    def updateEntranceLayer(self):
        # disconnect any current entrance layer
        self.disconnectEntranceLayer()
        self.dockwidget.useExistingEntrancescomboBox.clear()
        self.dockwidget.useExistingEntrancescomboBox.setEnabled(False)
        layers = self.legend.values()
        type = 0
        for lyr in layers:
            if self.isRequiredEntranceLayer(lyr, type):
                self.dockwidget.useExistingEntrancescomboBox.addItem(lyr.name(), lyr)

        if self.dockwidget.useExistingEntrancescomboBox.count() > 0:
            self.dockwidget.useExistingEntrancescomboBox.setEnabled(True)
            self.entrance_layer = self.dockwidget.setEntranceLayer()
            self.connectEntranceLayer()

    # Create New Layer
    def newEntranceLayer(self):

        vl = QgsVectorLayer("Point?crs=", "memory:Entrances", "memory")

        provider = vl.dataProvider()
        provider.addAttributes([QgsField("e_id", QVariant.Int),
                                QgsField("e_category", QVariant.String),
                                QgsField("e_subcat", QVariant.String),
                                QgsField("e_level", QVariant.Double)])

        vl.updateFields()
        if self.entrancedlg.e_shp_radioButton.isChecked():  # layer_type == 'shapefile':

            path = self.entrancedlg.lineEditEntrances.text()
            if path and path != '':
                filename = os.path.basename(path)
                location = os.path.abspath(path)
                crs = QgsCoordinateReferenceSystem()
                crs.createFromSrid(3857)
                QgsVectorFileWriter.writeAsVectorFormat(vl, location, "ogr", crs, "ESRI Shapefile")
                vl = self.iface.addVectorLayer(location, filename[:-4], "ogr")
            else:
                vl = 'invalid data source'

        elif self.entrancedlg.e_postgis_radioButton.isChecked():

            db_path = self.entrancedlg.lineEditEntrances.text()
            if db_path and db_path != '':

                (database, schema, table_name) = db_path.split(':')
                db_con_info = self.entrancedlg.dbsettings_dlg.available_dbs[database]
                uri = QgsDataSourceUri()
                # passwords, usernames need to be empty if not provided or else connection will fail
                if 'service' in list(db_con_info.keys()):
                    uri.setConnection(db_con_info['service'], '', '', '')
                elif 'password' in list(db_con_info.keys()):
                    uri.setConnection(db_con_info['host'], db_con_info['port'], db_con_info['dbname'],
                                      db_con_info['user'],
                                      db_con_info['password'])
                else:
                    print(db_con_info)  # db_con_info['host']
                    uri.setConnection('', db_con_info['port'], db_con_info['dbname'], '', '')
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
            msg = msgBar.createMessage(u'Specify output path!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
        elif vl == 'duplicate':
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Fronatges layer already exists!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
        elif not vl:
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Entrance layer failed to load!')
            msgBar.pushWidget(msg, Qgis.Info, 10)

        else:
            QgsProject.instance().addMapLayer(vl)
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Entrances layer created!')
            msgBar.pushWidget(msg, Qgis.Info, 10)
            vl.startEditing()

        self.updateEntranceLayer()
        self.entrancedlg.closePopUpEntrances()

    # Set layer as entrance layer and apply thematic style
    def loadEntranceLayer(self):
        # disconnect any current entrance layer
        self.disconnectEntranceLayer()
        if self.dockwidget.useExistingEntrancescomboBox.count() > 0:
            self.entrance_layer = self.dockwidget.setEntranceLayer()
            qml_path = self.plugin_path + "/styles/entrancesThematic.qml"
            self.entrance_layer.loadNamedStyle(qml_path)
            self.entrance_layer.startEditing()
            self.connectEntranceLayer()

    def connectEntranceLayer(self):
        if self.entrance_layer:
            self.entrance_layer.featureAdded.connect(self.logEntranceFeatureAdded)
            self.entrance_layer.selectionChanged.connect(self.dockwidget.addEntranceDataFields)
            self.entrance_layer.featureDeleted.connect(self.dockwidget.clearEntranceDataFields)

    def disconnectEntranceLayer(self):
        if self.entrance_layer:
            self.entrance_layer.selectionChanged.disconnect(self.dockwidget.addEntranceDataFields)
            self.entrance_layer.featureAdded.disconnect(self.logEntranceFeatureAdded)
            self.entrance_layer.featureDeleted.disconnect(self.dockwidget.clearEntranceDataFields)
            self.entrance_layer = None

            # Draw New Feature

    def logEntranceFeatureAdded(self, fid):

        QgsMessageLog.logMessage("feature added, id = " + str(fid))

        mc = self.canvas
        v_layer = self.dockwidget.setEntranceLayer()
        feature_Count = v_layer.featureCount()
        features = v_layer.getFeatures()
        inputid = 0

        if feature_Count == 1:
            inputid = 1

        elif feature_Count > 1:
            inputid = feature_Count

        data = v_layer.dataProvider()
        update1 = data.fieldNameIndex("e_category")
        update2 = data.fieldNameIndex("e_subcat")
        update3 = data.fieldNameIndex("e_id")
        update4 = data.fieldNameIndex("e_level")

        categorytext = self.dockwidget.ecategorylistWidget.currentItem().text()
        subcategorytext = self.dockwidget.esubcategorylistWidget.currentItem().text()
        accessleveltext = self.dockwidget.eaccesscategorylistWidget.currentItem().text()

        v_layer.changeAttributeValue(fid, update1, categorytext, True)
        v_layer.changeAttributeValue(fid, update2, subcategorytext, True)
        v_layer.changeAttributeValue(fid, update3, inputid, True)
        v_layer.changeAttributeValue(fid, update4, accessleveltext, True)
        v_layer.updateFields()

    # Update Feature
    def updateSelectedEntranceAttribute(self):
        mc = self.canvas
        layer = self.dockwidget.setEntranceLayer()
        features = layer.selectedFeatures()

        categorytext = self.dockwidget.ecategorylistWidget.currentItem().text()
        subcategorytext = self.dockwidget.esubcategorylistWidget.currentItem().text()
        accessleveltext = self.dockwidget.eaccesscategorylistWidget.currentItem().text()

        for feat in features:
            feat['e_category'] = categorytext
            feat['e_subcat'] = subcategorytext
            feat['e_level'] = accessleveltext
            layer.updateFeature(feat)
        self.dockwidget.addEntranceDataFields()
