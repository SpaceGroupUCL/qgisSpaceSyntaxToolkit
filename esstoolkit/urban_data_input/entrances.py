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
from PyQt4.QtCore import *
from PyQt4 import QtGui

from qgis.core import *
from qgis.gui import *

from . import utility_functions as uf

import os


class EntranceTool(QObject):

    def __init__(self, iface, dockwidget):
        QObject.__init__(self)
        self.iface = iface
        self.legend = self.iface.legendInterface()
        self.canvas = self.iface.mapCanvas()

        self.dockwidget = dockwidget
        self.entrancedlg = self.dockwidget.entrancedlg

        self.plugin_path = os.path.dirname(os.path.dirname(__file__))

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
            feat['E_ID'] = i
            i += 1
            layer.updateFeature(feat)

        layer.commitChanges()
        layer.startEditing()

    # Add Frontage layer to combobox if conditions are satisfied
    def updateEntranceLayer(self):
        # disconnect any current entrance layer
        self.disconnectEntranceLayer()
        self.dockwidget.useExistingEntrancescomboBox.clear()
        self.dockwidget.useExistingEntrancescomboBox.setEnabled(False)
        layers = self.legend.layers()
        type = 0
        for lyr in layers:
            if uf.isRequiredEntranceLayer(self.iface, lyr, type):
                self.dockwidget.useExistingEntrancescomboBox.addItem(lyr.name(), lyr)

        if self.dockwidget.useExistingEntrancescomboBox.count() > 0:
            self.dockwidget.useExistingEntrancescomboBox.setEnabled(True)
            self.entrance_layer = self.dockwidget.setEntranceLayer()
            self.connectEntranceLayer()

    # Create New Layer
    def newEntranceLayer(self):
        # Save to file
        if self.entrancedlg.lineEditEntrances.text() != "":
            path = self.entrancedlg.lineEditEntrances.text()
            filename = os.path.basename(path)
            location = os.path.abspath(path)

            destCRS = self.canvas.mapRenderer().destinationCrs()
            vl = QgsVectorLayer("Point?crs=" + destCRS.toWkt(), "memory:Entrances", "memory")


            provider = vl.dataProvider()
            provider.addAttributes([QgsField("E_ID", QVariant.Int),
                                 QgsField("E_Category", QVariant.String),
                                 QgsField("E_SubCat", QVariant.String),
                                 QgsField("E_Level", QVariant.Double)])

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
                msg = msgBar.createMessage(u'New Frontages Layer Created:' + location)
                msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)
                input2.startEditing()
        else:
            # Save to memory, no base land use layer
            destCRS = self.canvas.mapRenderer().destinationCrs()
            vl = QgsVectorLayer("Point?crs=" + destCRS.toWkt(), "memory:Entrances", "memory")
            QgsMapLayerRegistry.instance().addMapLayer(vl)

            if not vl:
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'Layer failed to load!')
                msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

            else:
                msgBar = self.iface.messageBar()
                msg = msgBar.createMessage(u'New Frontages Layer Create:')
                msgBar.pushWidget(msg, QgsMessageBar.INFO, 10)

                vl.startEditing()
                edit1 = vl.dataProvider()
                edit1.addAttributes([QgsField("E_ID", QVariant.Int),
                                     QgsField("E_Category", QVariant.String),
                                     QgsField("E_SubCat", QVariant.String),
                                     QgsField("E_Level", QVariant.Double)])
                vl.commitChanges()
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
        update1 = data.fieldNameIndex("E_Category")
        update2 = data.fieldNameIndex("E_SubCat")
        update3 = data.fieldNameIndex("E_ID")
        update4 = data.fieldNameIndex("E_Level")

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
        #QtGui.QApplication.beep()
        mc = self.canvas
        layer = self.dockwidget.setEntranceLayer()
        features = layer.selectedFeatures()

        categorytext = self.dockwidget.ecategorylistWidget.currentItem().text()
        subcategorytext = self.dockwidget.esubcategorylistWidget.currentItem().text()
        accessleveltext = self.dockwidget.eaccesscategorylistWidget.currentItem().text()

        for feat in features:
            feat['E_Category'] = categorytext
            feat['E_SubCat'] = subcategorytext
            feat['E_Level'] = accessleveltext
            layer.updateFeature(feat)
        self.dockwidget.addEntranceDataFields()
