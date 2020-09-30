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
from qgis.core import (Qgis, QgsField, QgsProject, QgsMapLayer, QgsVectorLayer, QgsFeature, QgsVectorFileWriter,
                       QgsDataSourceUri, QgsVectorLayerExporter, QgsMessageLog, QgsFeatureRequest, NULL)

from esstoolkit.utilities import layer_field_helpers as lfh

is_debug = False

ground_floor_attributes = [QgsField("lu_id", QVariant.Int),
                           QgsField("floors", QVariant.Int),
                           QgsField("area", QVariant.Double),
                           QgsField("gf_cat", QVariant.String),
                           QgsField("gf_subcat", QVariant.String),
                           QgsField("gf_ssx", QVariant.String),
                           QgsField("gf_nlud", QVariant.String),
                           QgsField("gf_tcpa", QVariant.String),
                           QgsField("gf_descrip", QVariant.String)]

lower_floor_attributes = [QgsField("lf_cat", QVariant.String),
                          QgsField("lf_subcat", QVariant.String),
                          QgsField("lf_ssx", QVariant.String),
                          QgsField("lf_nlud", QVariant.String),
                          QgsField("lf_tcpa", QVariant.String),
                          QgsField("lf_descrip", QVariant.String)]

upper_floor_attributes = [QgsField("uf_cat", QVariant.String),
                          QgsField("uf_subcat", QVariant.String),
                          QgsField("uf_ssx", QVariant.String),
                          QgsField("uf_nlud", QVariant.String),
                          QgsField("uf_ntcpa", QVariant.String),
                          QgsField("uf_descrip", QVariant.String)]


class LanduseTool(QObject):

    def __init__(self, iface, dockwidget):
        QObject.__init__(self)
        self.iface = iface
        self.legend = QgsProject.instance().mapLayers()
        self.canvas = self.iface.mapCanvas()

        self.dockwidget = dockwidget
        self.ludlg = self.dockwidget.ludlg
        self.ludlg.LUincGFcheckBox.setChecked(1)
        self.plugin_path = os.path.dirname(__file__)
        self.lu_layer = None

        # signals from dockwidget
        self.dockwidget.updateLUIDButton.clicked.connect(self.updateIDLU)
        self.dockwidget.useExistingLUcomboBox.currentIndexChanged.connect(self.loadLULayer)
        self.dockwidget.updateLUButton.clicked.connect(self.updateSelectedLUAttribute)
        self.dockwidget.pushButtonNewLUFile.clicked.connect(self.updatebuildingLayers)

        # signals from new landuse dialog
        self.ludlg.create_new_layer.connect(self.newLULayer)
        self.ludlg.selectbuildingCombo.currentIndexChanged.connect(self.popIdColumn)
        self.ludlg.createNewLUFileCheckBox.stateChanged.connect(self.updatebuildingLayers)

    #######
    #   Data functions
    #######

    # Add building layers from the legend to combobox in Create New file pop up dialogue
    def updatebuildingLayers(self):
        self.ludlg.selectbuildingCombo.clear()
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        # identify relevant layers
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == 2:
                    layer_list.append(layer.name())
        # update combo if necessary
        if layer_list:
            self.ludlg.createNewLUFileCheckBox.setEnabled(True)
            self.ludlg.selectbuildingCombo.addItems(layer_list)
            # activate combo if checked
            if self.ludlg.createNewLUFileCheckBox.checkState() == 2:
                self.ludlg.selectbuildingCombo.setEnabled(True)
                self.ludlg.selectIDbuildingCombo.setEnabled(True)
            else:
                self.ludlg.selectbuildingCombo.setEnabled(False)
                self.ludlg.selectIDbuildingCombo.setEnabled(False)
            self.popIdColumn()
        else:
            self.ludlg.createNewLUFileCheckBox.setEnabled(False)
            self.ludlg.selectbuildingCombo.setEnabled(False)
            self.ludlg.selectIDbuildingCombo.setEnabled(False)

    def popIdColumn(self):
        self.ludlg.selectIDbuildingCombo.clear()
        field_names = []
        layer = self.getSelectedLULayer()
        if layer and layer.dataProvider():
            field_names = [field.name() for field in layer.dataProvider().fields()]
        self.ludlg.selectIDbuildingCombo.addItems(field_names)

    def getSelectedLULayer(self):
        layer_name = self.ludlg.selectbuildingCombo.currentText()
        self.building_layer = lfh.getLegendLayerByName(self.iface, layer_name)
        return self.building_layer

    # Update the F_ID column of the Frontage layer
    def updateIDLU(self):
        layer = self.dockwidget.setLULayer()
        features = layer.getFeatures()
        i = 1
        layer.startEditing()
        for feat in features:
            feat['lu_id'] = i
            i += 1
            layer.updateFeature(feat)
        layer.commitChanges()
        layer.startEditing()

    def isRequiredLULayer(self, layer, type):
        if layer.type() == QgsMapLayer.VectorLayer \
                and layer.geometryType() == type:
            if lfh.layerHasFields(layer, ['gf_cat', 'gf_subcat']):
                return True

        return False

    # Add Frontage layer to combobox if conditions are satisfied
    def updateLULayer(self):
        self.disconnectLULayer()
        self.dockwidget.useExistingLUcomboBox.clear()
        self.dockwidget.useExistingLUcomboBox.setEnabled(False)
        layers = self.legend.values()
        type = 2
        for lyr in layers:
            if self.isRequiredLULayer(lyr, type):
                self.dockwidget.useExistingLUcomboBox.addItem(lyr.name(), lyr)

        if self.dockwidget.useExistingLUcomboBox.count() > 0:
            self.dockwidget.useExistingLUcomboBox.setEnabled(True)
            self.lu_layer = self.dockwidget.setLULayer()
            self.connectLULayer()

    # Create New Layer
    def newLULayer(self):

        if self.ludlg.LUincUFcheckBox.checkState() == 0 and self.ludlg.LUincLFcheckBox.checkState() == 0 and self.ludlg.LUincGFcheckBox.checkState() == 0:
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Select floors')
            msgBar.pushWidget(msg, Qgis.Info, 10)

        else:
            idcolumn = self.ludlg.getSelectedLULayerID()
            # if create from existing building layer
            if self.ludlg.createNewLUFileCheckBox.isChecked():
                print('aaaa')
                building_layer = self.getSelectedLULayer()
                crs = building_layer.crs()
                vl = QgsVectorLayer("Polygon?crs=" + crs.authid(), "memory:landuse", "memory")
            else:
                # create memory layer
                vl = QgsVectorLayer("Polygon?crs=", "memory:landuse", "memory")
            provider = vl.dataProvider()
            # provider.addAttributes([])

            if self.ludlg.LUincGFcheckBox.checkState() == 2:
                provider.addAttributes(ground_floor_attributes)
                self.dockwidget.LUGroundfloorradioButton.setEnabled(1)

            if self.ludlg.LUincLFcheckBox.checkState() == 2:
                provider.addAttributes(lower_floor_attributes)
                self.dockwidget.LULowerfloorradioButton.setEnabled(1)

            if self.ludlg.LUincUFcheckBox.checkState() == 2:
                provider.addAttributes(upper_floor_attributes)
                self.dockwidget.LULowerfloorradioButton.setEnabled(1)

            vl.updateFields()
            # if create from existing building layer
            if self.ludlg.createNewLUFileCheckBox.isChecked():

                null_attr = []
                provider.addAttributes([QgsField('build_id', QVariant.String)])

                if self.ludlg.LUincGFcheckBox.checkState() == 2:
                    # TODO: has removed [QgsField("Build_ID", QVariant.Int)] +
                    provider.addAttributes(ground_floor_attributes)
                    self.dockwidget.LUGroundfloorradioButton.setEnabled(1)
                    null_attr += [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                if self.ludlg.LUincLFcheckBox.checkState() == 2:
                    provider.addAttributes(lower_floor_attributes)
                    self.dockwidget.LULowerfloorradioButton.setEnabled(1)
                    null_attr += [NULL, NULL, NULL, NULL, NULL, NULL]

                if self.ludlg.LUincUFcheckBox.checkState() == 2:
                    provider.addAttributes(upper_floor_attributes)
                    self.dockwidget.LULowerfloorradioButton.setEnabled(1)
                    null_attr += [NULL, NULL, NULL, NULL, NULL, NULL]

                new_feat_list = []
                i = 1
                for feat in building_layer.getFeatures():
                    new_feat = QgsFeature()
                    new_feat.setAttributes([i] + null_attr + [feat[idcolumn]])
                    i += 1
                    new_feat.setGeometry(feat.geometry())
                    new_feat_list.append(new_feat)

                vl.updateFields()
                provider.addFeatures(new_feat_list)
                vl.commitChanges()

            if self.ludlg.lu_shp_radioButton.isChecked():  # layer_type == 'shapefile':

                path = self.ludlg.lineEditLU.text()

                if path and path != '':

                    filename = os.path.basename(path)
                    location = os.path.abspath(path)

                    QgsVectorFileWriter.writeAsVectorFormat(vl, location, "ogr", vl.crs(), "ESRI Shapefile")
                    print('cri', vl.crs().authid())
                    input2 = self.iface.addVectorLayer(location, filename[:-4], "ogr")
                else:
                    input2 = 'invalid data source'

            elif self.ludlg.lu_postgis_radioButton.isChecked():

                db_path = self.ludlg.lineEditLU.text()
                if db_path and db_path != '':
                    (database, schema, table_name) = db_path.split(':')
                    db_con_info = self.ludlg.dbsettings_dlg.available_dbs[database]
                    uri = QgsDataSourceUri()
                    # passwords, usernames need to be empty if not provided or else connection will fail
                    if 'service' in list(db_con_info.keys()):
                        uri.setConnection(db_con_info['service'], '', '', '')
                    elif 'password' in list(db_con_info.keys()):
                        uri.setConnection(db_con_info['host'], db_con_info['port'], db_con_info['dbname'],
                                          db_con_info['user'], db_con_info['password'])
                    else:
                        print(db_con_info)  # db_con_info['host']
                        uri.setConnection('', db_con_info['port'], db_con_info['dbname'], '', '')
                    uri.setDataSource(schema, table_name, "geom")
                    error = QgsVectorLayerExporter.importLayer(vl, uri.uri(), "postgres", vl.crs(), False, False)
                    if error[0] != 0:
                        print("Error when creating postgis layer: ", error[1])
                        input2 = 'duplicate'
                    else:
                        input2 = QgsVectorLayer(uri.uri(), table_name, "postgres")
                else:
                    input2 = 'invalid data source'

            else:
                input2 = vl

            if input2 == 'invalid data source':
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'Specify output path!')
                msgBar.pushWidget(msg, Qgis.Info, 10)
            elif input2 == 'duplicate':
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'Land use layer already exists!')
                msgBar.pushWidget(msg, Qgis.Info, 10)
            elif not input2:
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'Land use layer failed to load!')
                msgBar.pushWidget(msg, Qgis.Info, 10)
            else:
                QgsProject.instance().addMapLayer(input2)
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'Land use layer created!')
                msgBar.pushWidget(msg, Qgis.Info, 10)
                input2.startEditing()

        self.updateLULayer()
        self.ludlg.closePopUpLU()
        self.ludlg.lineEditLU.clear()

    # Set layer as frontage layer and apply thematic style
    def loadLULayer(self):
        # disconnect any current frontage layer
        self.disconnectLULayer()
        if self.dockwidget.useExistingLUcomboBox.count() > 0:
            self.lu_layer = self.dockwidget.setLULayer()
            qml_path = self.plugin_path + "/styles/landuseThematic.qml"
            self.lu_layer.loadNamedStyle(qml_path)
            self.lu_layer.startEditing()
            # connect signals from layer
            self.connectLULayer()

    def connectLULayer(self):
        if self.lu_layer:
            self.lu_layer.selectionChanged.connect(self.dockwidget.addLUDataFields)
            self.lu_layer.featureAdded.connect(self.logLUFeatureAdded)
            self.lu_layer.featureDeleted.connect(self.dockwidget.clearLUDataFields)

    def disconnectLULayer(self):
        if self.lu_layer:
            self.lu_layer.selectionChanged.disconnect(self.dockwidget.addLUDataFields)
            self.lu_layer.featureAdded.disconnect(self.logLUFeatureAdded)
            self.lu_layer.featureDeleted.disconnect(self.dockwidget.clearLUDataFields)
            self.lu_layer = None

    # Draw New Feature
    def logLUFeatureAdded(self, fid):

        if is_debug:
            QgsMessageLog.logMessage("feature added, id = " + str(fid))

        v_layer = self.dockwidget.setLULayer()
        inputid = v_layer.featureCount()
        luarea = 0

        data = v_layer.dataProvider()
        categorytext = self.dockwidget.lucategorylistWidget.currentItem().text()
        subcategorytext = self.dockwidget.lusubcategorylistWidget.currentItem().text()
        floortext = self.dockwidget.spinBoxlufloors.value()
        description = self.dockwidget.LUtextedit.toPlainText()
        ssxcode = self.dockwidget.lineEdit_luSSx.text()
        nludcode = self.dockwidget.lineEdit_luNLUD.text()
        tcpacode = self.dockwidget.lineEdit_luTCPA.text()

        updateID = data.fieldNameIndex("lu_id")
        updatefloors = data.fieldNameIndex("floors")
        updatearea = data.fieldNameIndex("area")

        GFupdate1 = data.fieldNameIndex("gf_cat")
        GFupdate2 = data.fieldNameIndex("gf_subcat")
        GFupdate3 = data.fieldNameIndex("gf_ssx")
        GFupdate4 = data.fieldNameIndex("gf_nlud")
        GFupdate5 = data.fieldNameIndex("gf_tcpa")
        GFupdate6 = data.fieldNameIndex("gf_descrip")

        LFupdate1 = data.fieldNameIndex("lf_cat")
        LFupdate2 = data.fieldNameIndex("lf_subcat")
        LFupdate3 = data.fieldNameIndex("lf_ssx")
        LFupdate4 = data.fieldNameIndex("lf_nlud")
        LFupdate5 = data.fieldNameIndex("lf_tcpa")
        LFupdate6 = data.fieldNameIndex("lf_descrip")

        UFupdate1 = data.fieldNameIndex("uf_cat")
        UFupdate2 = data.fieldNameIndex("uf_subcat")
        UFupdate3 = data.fieldNameIndex("uf_ssx")
        UFupdate4 = data.fieldNameIndex("uf_nlud")
        UFupdate5 = data.fieldNameIndex("uf_ntcpa")
        UFupdate6 = data.fieldNameIndex("uf_descrip")

        v_layer.changeAttributeValue(fid, updateID, inputid, True)
        if floortext > 0:
            v_layer.changeAttributeValue(fid, updatefloors, floortext, True)
        # attributes of individual floors
        if self.dockwidget.LUGroundfloorradioButton.isChecked():
            v_layer.changeAttributeValue(fid, GFupdate1, categorytext, True)
            v_layer.changeAttributeValue(fid, GFupdate2, subcategorytext, True)
            v_layer.changeAttributeValue(fid, GFupdate3, ssxcode, True)
            v_layer.changeAttributeValue(fid, GFupdate4, nludcode, True)
            v_layer.changeAttributeValue(fid, GFupdate5, tcpacode, True)
            v_layer.changeAttributeValue(fid, GFupdate6, description, True)
        if self.dockwidget.LULowerfloorradioButton.isChecked():
            v_layer.changeAttributeValue(fid, LFupdate1, categorytext, True)
            v_layer.changeAttributeValue(fid, LFupdate2, subcategorytext, True)
            v_layer.changeAttributeValue(fid, LFupdate3, ssxcode, True)
            v_layer.changeAttributeValue(fid, LFupdate4, nludcode, True)
            v_layer.changeAttributeValue(fid, LFupdate5, tcpacode, True)
            v_layer.changeAttributeValue(fid, LFupdate6, description, True)
        if self.dockwidget.LUUpperfloorradioButton.isChecked():
            v_layer.changeAttributeValue(fid, UFupdate1, categorytext, True)
            v_layer.changeAttributeValue(fid, UFupdate2, subcategorytext, True)
            v_layer.changeAttributeValue(fid, UFupdate3, ssxcode, True)
            v_layer.changeAttributeValue(fid, UFupdate4, nludcode, True)
            v_layer.changeAttributeValue(fid, UFupdate5, tcpacode, True)
            v_layer.changeAttributeValue(fid, UFupdate6, description, True)

        # area can be obtained after the layer is added
        request = QgsFeatureRequest().setFilterExpression(u'"lu_id" = %s' % inputid)
        features = v_layer.getFeatures(request)
        for feat in features:
            geom = feat.geometry()
            luarea = geom.area()
        v_layer.changeAttributeValue(fid, updatearea, luarea, True)

        v_layer.updateFields()
        # lets let the user decide when to change these fields
        # self.dockwidget.setLufloors(0)
        # self.dockwidget.LUtextedit.clear()

    # Update Feature
    def updateSelectedLUAttribute(self):
        mc = self.canvas
        layer = self.dockwidget.setLULayer()
        features = layer.selectedFeatures()

        categorytext = self.dockwidget.lucategorylistWidget.currentItem().text()
        subcategorytext = self.dockwidget.lusubcategorylistWidget.currentItem().text()
        floortext = self.dockwidget.spinBoxlufloors.value()
        description = self.dockwidget.LUtextedit.toPlainText()
        ssxcode = self.dockwidget.lineEdit_luSSx.text()
        nludcode = self.dockwidget.lineEdit_luNLUD.text()
        tcpacode = self.dockwidget.lineEdit_luTCPA.text()

        for feat in features:
            if floortext > 0:
                feat["floors"] = floortext
            geom = feat.geometry()
            feat["area"] = geom.area()
            layer.updateFeature(feat)
            if self.dockwidget.LUGroundfloorradioButton.isChecked():
                feat["gf_cat"] = categorytext
                feat["gf_subcat"] = subcategorytext
                feat["gf_ssx"] = ssxcode
                feat["gf_nlud"] = nludcode
                feat["gf_tcpa"] = tcpacode
                feat["gf_descrip"] = description
                layer.updateFeature(feat)
            if self.dockwidget.LULowerfloorradioButton.isChecked():
                feat["lf_cat"] = categorytext
                feat["lf_subcat"] = subcategorytext
                feat["lf_ssx"] = ssxcode
                feat["lf_nlud"] = nludcode
                feat["lf_tcpa"] = tcpacode
                feat["lf_descrip"] = description
                layer.updateFeature(feat)
            if self.dockwidget.LUUpperfloorradioButton.isChecked():
                feat["uf_cat"] = categorytext
                feat["uf_subcat"] = subcategorytext
                feat["uf_ssx"] = ssxcode
                feat["uf_nlud"] = nludcode
                feat["uf_ntcpa"] = tcpacode
                feat["uf_descrip"] = description
                layer.updateFeature(feat)

        self.dockwidget.addLUDataFields()
        # lets let the user decide when to change these fields
        # self.dockwidget.setLufloors(0)
        # self.dockwidget.LUtextedit.clear()
