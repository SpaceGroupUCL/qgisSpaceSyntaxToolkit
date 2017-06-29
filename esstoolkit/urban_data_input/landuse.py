# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UrbanDataInput
                                 A QGIS plugin
 Urban Data Input Tool for QGIS
                              -------------------
        begin                : 2016-06-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Abhimanyu Acharya/(C) 2016 by Space Syntax Limited’.
        email                : a.acharya@spacesyntax.com
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
import os
from PyQt4.QtCore import *
from PyQt4 import QtGui
from qgis.core import *
from qgis.gui import *
from . import utility_functions as uf

is_debug = False


class LanduseTool(QObject):

    def __init__(self, iface, dockwidget):
        QObject.__init__(self)
        self.iface = iface
        self.legend = self.iface.legendInterface()
        self.canvas = self.iface.mapCanvas()

        self.dockwidget = dockwidget
        self.ludlg = self.dockwidget.ludlg
        self.ludlg.LUincGFcheckBox.setChecked(1)
        self.plugin_path = os.path.dirname(os.path.dirname(__file__))
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
        layers = self.iface.legendInterface().layers()
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
        self.building_layer = uf.getLegendLayerByName(self.iface, layer_name)
        return self.building_layer

# Update the F_ID column of the Frontage layer
    def updateIDLU(self):
        layer = self.dockwidget.setLULayer()
        features = layer.getFeatures()
        i = 1
        layer.startEditing()
        for feat in features:
            feat['LU_ID'] = i
            i += 1
            layer.updateFeature(feat)
        layer.commitChanges()
        layer.startEditing()

# Add Frontage layer to combobox if conditions are satisfied
    def updateLULayer(self):
        self.disconnectLULayer()
        self.dockwidget.useExistingLUcomboBox.clear()
        self.dockwidget.useExistingLUcomboBox.setEnabled(False)
        layers = self.legend.layers()
        type = 2
        for lyr in layers:
            if uf.isRequiredLULayer(self.iface, lyr, type):
                self.dockwidget.useExistingLUcomboBox.addItem(lyr.name(), lyr)

        if self.dockwidget.useExistingLUcomboBox.count() > 0:
            self.dockwidget.useExistingLUcomboBox.setEnabled(True)
            self.lu_layer = self.dockwidget.setLULayer()
            self.connectLULayer()

# Create New Layer
    def newLULayer(self):

        if self.ludlg.LUincUFcheckBox.checkState() == 0 and self.ludlg.LUincLFcheckBox.checkState() == 0 and self.ludlg.LUincGFcheckBox.checkState() == 0:
            msgBar = self.iface.messageBar()
            msg = msgBar.createMessage(u'Select Floors')
            msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

        else:
            if self.ludlg.createNewLUFileCheckBox.checkState() == 0 or self.ludlg.selectbuildingCombo.count() == 0:
                # Save to file
                if self.ludlg.lineEditLU.text() != "":
                    path = self.ludlg.lineEditLU.text()
                    filename = os.path.basename(path)
                    location = os.path.abspath(path)

                    destCRS = self.canvas.mapRenderer().destinationCrs()
                    vl = QgsVectorLayer("Polygon?crs=" + destCRS.toWkt(), "memory:Land use", "memory")

                    provider = vl.dataProvider()
                    provider.addAttributes([])

                    if self.ludlg.LUincGFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("LU_ID", QVariant.Int),
                                             QgsField("Floors", QVariant.Int),
                                             QgsField("Area", QVariant.Double),
                                             QgsField("GF_Cat", QVariant.String),
                                             QgsField("GF_SubCat", QVariant.String),
                                             QgsField("GF_SSx", QVariant.String),
                                             QgsField("GF_NLUD", QVariant.String),
                                             QgsField("GF_TCPA", QVariant.String),
                                             QgsField("GF_Descrip", QVariant.String)])
                        self.dockwidget.LUGroundfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincLFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("LF_Cat", QVariant.String),
                                             QgsField("LF_SubCat", QVariant.String),
                                             QgsField("LF_SSx", QVariant.String),
                                             QgsField("LF_NLUD", QVariant.String),
                                             QgsField("LF_TCPA", QVariant.String),
                                             QgsField("LF_Descrip", QVariant.String)])
                        self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincUFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("UF_Cat", QVariant.String),
                                             QgsField("UF_SubCat", QVariant.String),
                                             QgsField("UF_SSx", QVariant.String),
                                             QgsField("UF_NLUD", QVariant.String),
                                             QgsField("UF_TCPA", QVariant.String),
                                             QgsField("UF_Descrip", QVariant.String)])
                        self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                    vl.updateFields()
                    features = vl.getFeatures()
                    i = 1
                    vl.startEditing()
                    for feat in features:
                        feat['LU_ID'] = i
                        i += 1
                        vl.updateFeature(feat)
                    vl.commitChanges()
                    vl.startEditing()
                    QgsMapLayerRegistry.instance().addMapLayer(vl)

                    QgsVectorFileWriter.writeAsVectorFormat(vl, location, "CP1250", None, "ESRI Shapefile")

                    QgsMapLayerRegistry.instance().removeMapLayers([vl.id()])

                    input2 = self.iface.addVectorLayer(location, filename, "ogr")
                    QgsMapLayerRegistry.instance().addMapLayer(input2)

                    if not input2:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'Layer failed to load!' + location)
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

                    else:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'New Land Use Layer Created:' + location)
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)
                        input2.startEditing()

                else:
                    # Save to memory, no base land use layer
                    destCRS = self.canvas.mapRenderer().destinationCrs()
                    vl = QgsVectorLayer("Polygon?crs=" + destCRS.toWkt(), "memory:Land use", "memory")
                    QgsMapLayerRegistry.instance().addMapLayer(vl)


                    if not vl:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'Layer failed to load!')
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

                    else:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'New Land Use Layer Created:')
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

                        vl.startEditing()

                        edit1 = vl.dataProvider()

                        if self.ludlg.LUincGFcheckBox.checkState() == 2:
                            edit1.addAttributes([QgsField("LU_ID", QVariant.Int),
                                                QgsField("Floors", QVariant.Int),
                                                QgsField("Area", QVariant.Double),
                                                QgsField("GF_Cat", QVariant.String),
                                                QgsField("GF_SubCat", QVariant.String),
                                                QgsField("GF_SSx", QVariant.String),
                                                QgsField("GF_NLUD", QVariant.String),
                                                QgsField("GF_TCPA", QVariant.String),
                                                QgsField("GF_Descrip", QVariant.String)])
                            self.dockwidget.LUGroundfloorradioButton.setEnabled(1)

                        if self.ludlg.LUincLFcheckBox.checkState() == 2:
                            edit1.addAttributes([QgsField("LF_Cat", QVariant.String),
                                                QgsField("LF_SubCat", QVariant.String),
                                                QgsField("LF_SSx", QVariant.String),
                                                QgsField("LF_NLUD", QVariant.String),
                                                QgsField("LF_TCPA", QVariant.String),
                                                QgsField("LF_Descrip", QVariant.String)])
                            self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                        if self.ludlg.LUincUFcheckBox.checkState() == 2:
                            edit1.addAttributes([QgsField("UF_Cat", QVariant.String),
                                                QgsField("UF_SubCat", QVariant.String),
                                                QgsField("UF_SSx", QVariant.String),
                                                QgsField("UF_NLUD", QVariant.String),
                                                QgsField("UF_TCPA", QVariant.String),
                                                QgsField("UF_Descrip", QVariant.String)])
                            self.dockwidget.LUUpperfloorradioButton.setEnabled(1)

                    vl.updateFields()
                    features = vl.getFeatures()
                    i = 1
                    vl.startEditing()
                    for feat in features:
                        feat['LU_ID'] = i
                        i += 1
                        vl.updateFeature(feat)
                    vl.commitChanges()
                    vl.startEditing()

            if self.ludlg.createNewLUFileCheckBox.checkState() == 2:
                idcolumn = self.ludlg.getSelectedLULayerID()
                # Save to file
                if self.ludlg.lineEditLU.text() != "":
                    path = self.ludlg.lineEditLU.text()
                    filename = os.path.basename(path)
                    location = os.path.abspath(path)

                    destCRS = self.canvas.mapRenderer().destinationCrs()

                    vl = self.getSelectedLULayer()

                    nl = QgsVectorLayer("Polygon?crs=" + destCRS.toWkt(), "memory:Land use", "memory")
                    provider = nl.dataProvider()

                    QgsMapLayerRegistry.instance().addMapLayer(nl)


                    if self.ludlg.LUincGFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("Build_ID", QVariant.Int),
                                                QgsField("LU_ID", QVariant.Int),
                                                QgsField("Floors", QVariant.Int),
                                                QgsField("Area", QVariant.Double),
                                                QgsField("GF_Cat", QVariant.String),
                                                QgsField("GF_SubCat", QVariant.String),
                                                QgsField("GF_SSx", QVariant.String),
                                                QgsField("GF_NLUD", QVariant.String),
                                                QgsField("GF_TCPA", QVariant.String),
                                                QgsField("GF_Descrip", QVariant.String)])
                        self.dockwidget.LUGroundfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincLFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("LF_Cat", QVariant.String),
                                                QgsField("LF_SubCat", QVariant.String),
                                                QgsField("LF_SSx", QVariant.String),
                                                QgsField("LF_NLUD", QVariant.String),
                                                QgsField("LF_TCPA", QVariant.String),
                                                QgsField("LF_Descrip", QVariant.String)])
                        self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincUFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("UF_Cat", QVariant.String),
                                                QgsField("UF_SubCat", QVariant.String),
                                                QgsField("UF_SSx", QVariant.String),
                                                QgsField("UF_NLUD", QVariant.String),
                                                QgsField("UF_TCPA", QVariant.String),
                                                QgsField("UF_Descrip", QVariant.String)])
                        self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                    null_attr = []

                    if self.ludlg.LUincGFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincLFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincUFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincUFcheckBox.checkState() and self.ludlg.LUincUFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    new_feat_list =[]
                    for feat in vl.getFeatures():
                        new_feat = QgsFeature()
                        new_feat.setAttributes([feat[idcolumn]]+ null_attr)
                        new_feat.setGeometry(feat.geometry())
                        new_feat_list.append(new_feat)

                    nl.updateFields()
                    provider.addFeatures(new_feat_list)

                    features = nl.getFeatures()
                    i = 1
                    nl.startEditing()
                    for feat in features:
                        feat['LU_ID'] = i
                        i += 1
                        nl.updateFeature(feat)
                    nl.commitChanges()
                    nl.startEditing()
                    QgsVectorFileWriter.writeAsVectorFormat(nl, location, "ogr", None, "ESRI Shapefile")

                    QgsMapLayerRegistry.instance().removeMapLayers([nl.id()])

                    input2 = self.iface.addVectorLayer(location, filename, "ogr")
                    QgsMapLayerRegistry.instance().addMapLayer(input2)

                    if not input2:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'Layer failed to load!' + location)
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

                    else:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'New Land Use Layer Created:' + location)
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)
                        input2.startEditing()

                else:
                    # Save to memory, no base land use layer
                    destCRS = self.canvas.mapRenderer().destinationCrs()
                    vl = self.getSelectedLULayer()

                    nl = QgsVectorLayer("Polygon?crs=" + destCRS.toWkt(), "memory:Land use", "memory")
                    provider = nl.dataProvider()

                    QgsMapLayerRegistry.instance().addMapLayer(nl)

                    if self.ludlg.LUincGFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("Build_ID", QVariant.Int),
                             QgsField("LU_ID", QVariant.Int),
                             QgsField("Floors", QVariant.Int),
                             QgsField("Area", QVariant.Double),
                             QgsField("GF_Cat", QVariant.String),
                             QgsField("GF_SubCat", QVariant.String),
                             QgsField("GF_SSx", QVariant.String),
                             QgsField("GF_NLUD", QVariant.String),
                             QgsField("GF_TCPA", QVariant.String),
                             QgsField("GF_Descrip", QVariant.String)])
                        self.dockwidget.LUGroundfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincLFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("LF_Cat", QVariant.String),
                             QgsField("LF_SubCat", QVariant.String),
                             QgsField("LF_SSx", QVariant.String),
                             QgsField("LF_NLUD", QVariant.String),
                             QgsField("LF_TCPA", QVariant.String),
                             QgsField("LF_Descrip", QVariant.String)])
                        self.dockwidget.LULowerfloorradioButton.setEnabled(1)

                    if self.ludlg.LUincUFcheckBox.checkState() == 2:
                        provider.addAttributes([QgsField("UF_Cat", QVariant.String),
                             QgsField("UF_SubCat", QVariant.String),
                             QgsField("UF_SSx", QVariant.String),
                             QgsField("UF_NLUD", QVariant.String),
                             QgsField("UF_TCPA", QVariant.String),
                             QgsField("UF_Descrip", QVariant.String)])
                        self.dockwidget.LUUpperfloorradioButton.setEnabled(1)

                    null_attr = []
                    if self.ludlg.LUincGFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincLFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                                     NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincUFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                                     NULL]

                    if self.ludlg.LUincGFcheckBox.checkState() == 2 and self.ludlg.LUincUFcheckBox.checkState() and self.ludlg.LUincUFcheckBox.checkState() == 2:
                        null_attr = [NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                                     NULL, NULL, NULL, NULL, NULL, NULL, NULL]

                    new_feat_list = []
                    for feat in vl.getFeatures():
                        new_feat = QgsFeature()
                        new_feat.setAttributes([feat[idcolumn]] + null_attr)
                        new_feat.setGeometry(feat.geometry())
                        new_feat_list.append(new_feat)

                    nl.updateFields()
                    nl.startEditing()
                    provider.addFeatures(new_feat_list)

                    features = nl.getFeatures()
                    i = 1
                    nl.startEditing()
                    for feat in features:
                        feat['LU_ID'] = i
                        i += 1
                        nl.updateFeature(feat)
                    nl.commitChanges()

                    if not nl:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'Layer failed to load!')
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)
                    else:
                        msgBar = self.iface.messageBar()
                        msg = msgBar.createMessage(u'New Land Use Layer Created:')
                        msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)
                        nl.startEditing()

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

        updateID = data.fieldNameIndex("LU_ID")
        updatefloors = data.fieldNameIndex("Floors")
        updatearea = data.fieldNameIndex("Area")

        GFupdate1 = data.fieldNameIndex("GF_Cat")
        GFupdate2 = data.fieldNameIndex("GF_SubCat")
        GFupdate3 = data.fieldNameIndex("GF_SSx")
        GFupdate4 = data.fieldNameIndex("GF_NLUD")
        GFupdate5 = data.fieldNameIndex("GF_TCPA")
        GFupdate6 = data.fieldNameIndex("GF_Descrip")

        LFupdate1 = data.fieldNameIndex("LF_Cat")
        LFupdate2 = data.fieldNameIndex("LF_SubCat")
        LFupdate3 = data.fieldNameIndex("LF_SSx")
        LFupdate4 = data.fieldNameIndex("LF_NLUD")
        LFupdate5 = data.fieldNameIndex("LF_TCPA")
        LFupdate6 = data.fieldNameIndex("LF_Descrip")

        UFupdate1 = data.fieldNameIndex("UF_Cat")
        UFupdate2 = data.fieldNameIndex("UF_SubCat")
        UFupdate3 = data.fieldNameIndex("UF_SSx")
        UFupdate4 = data.fieldNameIndex("UF_NLUD")
        UFupdate5 = data.fieldNameIndex("UF_TCPA")
        UFupdate6 = data.fieldNameIndex("UF_Descrip")

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
        request = QgsFeatureRequest().setFilterExpression(u'"LU_ID" = %s' % inputid)
        features = v_layer.getFeatures(request)
        for feat in features:
            geom = feat.geometry()
            luarea = geom.area()
        v_layer.changeAttributeValue(fid, updatearea, luarea, True)

        v_layer.updateFields()
        # lets let the user decide when to change these fields
        #self.dockwidget.setLuFloors(0)
        #self.dockwidget.LUtextedit.clear()

# Update Feature
    def updateSelectedLUAttribute(self):
        #QtGui.QApplication.beep()
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
                feat["Floors"] = floortext
            geom = feat.geometry()
            feat["Area"] = geom.area()
            layer.updateFeature(feat)
            if self.dockwidget.LUGroundfloorradioButton.isChecked():
                feat["GF_Cat"] = categorytext
                feat["GF_SubCat"] = subcategorytext
                feat["GF_SSx"] = ssxcode
                feat["GF_NLUD"] = nludcode
                feat["GF_TCPA"] = tcpacode
                feat["GF_Descrip"] = description
                layer.updateFeature(feat)
            if self.dockwidget.LULowerfloorradioButton.isChecked():
                feat["LF_Cat"] = categorytext
                feat["LF_SubCat"] = subcategorytext
                feat["LF_SSx"] = ssxcode
                feat["LF_NLUD"] = nludcode
                feat["LF_TCPA"] = tcpacode
                feat["LF_Descrip"] = description
                layer.updateFeature(feat)
            if self.dockwidget.LUUpperfloorradioButton.isChecked():
                feat["UF_Cat"] = categorytext
                feat["UF_SubCat"] = subcategorytext
                feat["UF_SSx"] = ssxcode
                feat["UF_NLUD"] = nludcode
                feat["UF_TCPA"] = tcpacode
                feat["UF_Descrip"] = description
                layer.updateFeature(feat)

        self.dockwidget.addLUDataFields()
        # lets let the user decide when to change these fields
        #self.dockwidget.setLuFloors(0)
        #self.dockwidget.LUtextedit.clear()
