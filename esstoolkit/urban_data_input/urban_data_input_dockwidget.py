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

from __future__ import absolute_import

import os
from builtins import str

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (QDockWidget, QTableWidgetItem, QHeaderView)
from qgis.PyQt.uic import loadUiType
from qgis.core import QgsProject

from .CreateNew_Entrance_dialog import CreateNew_EntranceDialog
from .CreateNew_LU_dialog import CreateNew_LUDialog
from .CreateNew_dialog import CreatenewDialog
from esstoolkit.utilities import layer_field_helpers as lfh

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'urban_data_input_dockwidget_base.ui'))


class UrbanDataInputDockWidget(QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()
    loadFrontageLayer = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(UrbanDataInputDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.legend = QgsProject.instance().mapLayers()

        # create sub dialogs for new layers
        self.frontagedlg = CreatenewDialog()
        self.entrancedlg = CreateNew_EntranceDialog()
        self.ludlg = CreateNew_LUDialog()

        # define globals
        self.frontage_layer = None
        self.entrance_layer = None
        self.LU_layer = None

        # customise the dockwidget
        self.tableWidgetFrontage.verticalHeader().hide()
        self.tableWidgetEntrance.verticalHeader().hide()
        self.tableWidgetlanduse.verticalHeader().hide()

        # initialisation
        self.updateFrontageTypes()
        self.pushIDlistWidget.hide()
        self.pushIDcomboBox.hide()
        self.updateIDPushButton.hide()
        self.frontagescatlistWidget.setCurrentRow(0)
        self.updateFrontageSubTypes()

        self.updateEntranceTypes()
        self.ecategorylistWidget.setCurrentRow(0)
        self.eaccesscategorylistWidget.setCurrentRow(0)
        self.updateSubCategory()

        self.updateLUTypes()
        self.LUGroundfloorradioButton.setChecked(1)
        self.lineEdit_luSSx.hide()
        self.lineEdit_luNLUD.hide()
        self.lineEdit_luTCPA.hide()
        self.LUGroundfloorradioButton.setEnabled(0)
        self.LULowerfloorradioButton.setEnabled(0)
        self.LUUpperfloorradioButton.setEnabled(0)
        self.lucategorylistWidget.setCurrentRow(0)
        self.lusubcategorylistWidget.setCurrentRow(0)

        # setup dockwidget signals
        # frontages
        self.frontagescatlistWidget.currentRowChanged.connect(self.updateFrontageSubTypes)
        self.useExistingcomboBox.currentIndexChanged.connect(self.clearDataFields)
        self.useExistingcomboBox.currentIndexChanged.connect(self.loadFrontageLayer)
        self.pushButtonNewFile.clicked.connect(self.newFileDialog)
        # entrances
        self.ecategorylistWidget.currentRowChanged.connect(self.updateSubCategory)
        self.pushButtonNewEntrancesFile.clicked.connect(self.newFileDialogEntrance)
        self.useExistingEntrancescomboBox.currentIndexChanged.connect(self.clearEntranceDataFields)
        # landuse
        self.useExistingLUcomboBox.currentIndexChanged.connect(self.clearLUDataFields)
        self.lucategorylistWidget.currentRowChanged.connect(self.updateLUsubcat)
        self.lucategorylistWidget.currentRowChanged.connect(self.updateLUCodes)
        self.LUGroundfloorradioButton.toggled.connect(self.addLUDataFields)
        self.LULowerfloorradioButton.toggled.connect(self.addLUDataFields)
        self.LUUpperfloorradioButton.toggled.connect(self.addLUDataFields)
        self.lusubcategorylistWidget.currentRowChanged.connect(self.updateLUCodes)
        self.pushButtonNewLUFile.clicked.connect(self.newFileDialogLU)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def newFileDialog(self):
        """Run method that performs all the real work"""
        self.frontagedlg.lineEditFrontages.clear()
        # show the dialog
        self.frontagedlg.show()
        # Run the dialog event loop
        result = self.frontagedlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def newFileDialogEntrance(self):
        """Run method that performs all the real work"""
        self.entrancedlg.lineEditEntrances.clear()
        # show the dialog
        self.entrancedlg.show()
        # Run the dialog event loop
        result = self.entrancedlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def newFileDialogLU(self):
        """Run method that performs all the real work"""
        self.ludlg.lineEditLU.clear()
        # show the dialog
        self.ludlg.show()
        # Run the dialog event loop
        result = self.ludlg.exec_()
        # See if OK was pressed
        if result:
            pass

    #######
    #   Frontages
    #######

    # Update frontage types
    def updateFrontageTypes(self):
        self.frontagescatlistWidget.clear()
        frontage_list_cat = ['Building', 'Fences']
        self.frontagescatlistWidget.addItems(frontage_list_cat)

    def updateFrontageSubTypes(self):
        frontage_sub_category_list_Building = ['Transparent', 'Semi Transparent', 'Blank']
        frontage_sub_category_list_Fences = ['High Opaque Fence', 'High See Through Fence', 'Low Fence']
        self.frontagessubcatlistWidget.clear()
        self.frontagessubcatlistWidget.addItems(frontage_sub_category_list_Building)
        self.frontagessubcatlistWidget.setCurrentRow(0)

        if self.frontagescatlistWidget.currentRow() == 0:
            self.frontagessubcatlistWidget.clear()
            self.frontagessubcatlistWidget.addItems(frontage_sub_category_list_Building)
            self.frontagessubcatlistWidget.setCurrentRow(0)

        elif self.frontagescatlistWidget.currentRow() == 1:
            self.frontagessubcatlistWidget.clear()
            self.frontagessubcatlistWidget.addItems(frontage_sub_category_list_Fences)
            self.frontagessubcatlistWidget.setCurrentRow(0)

    # Set universal Frontage layer if conditions are satisfied
    def setFrontageLayer(self):
        # get the new layer
        index = self.useExistingcomboBox.currentIndex()
        self.frontage_layer = self.useExistingcomboBox.itemData(index)
        return self.frontage_layer

    # Get building layer based on name
    def getSelectedLayerPushID(self):
        layer_name = self.pushIDcomboBox.currentText()
        layer = lfh.getLegendLayerByName(self.iface, layer_name)
        return layer

    def clearDataFields(self):
        self.tableWidgetFrontage.setColumnCount(4)
        headers = ["F-ID", "Group", "Type", "Length"]
        self.tableWidgetFrontage.setHorizontalHeaderLabels(headers)
        self.tableWidgetFrontage.setRowCount(0)

    def addDataFields(self):
        self.tableClear()
        layer = self.setFrontageLayer()
        if layer:
            features = layer.selectedFeatures()
            attrs = []
            for feat in features:
                attr = feat.attributes()
                attrs.append(attr)

            fields = layer.fields()
            field_names = [field.name() for field in fields]

            field_length = len(field_names)
            A1 = field_length - 4
            A2 = field_length - 3
            A3 = field_length - 2
            A4 = field_length - 1

            self.tableWidgetFrontage.setColumnCount(4)
            headers = ["F-ID", "Group", "Type", "Length"]
            self.tableWidgetFrontage.setHorizontalHeaderLabels(headers)
            self.tableWidgetFrontage.setRowCount(len(attrs))

            for i, item in enumerate(attrs):
                self.tableWidgetFrontage.setItem(i, 0, QTableWidgetItem(str(item[A1])))
                self.tableWidgetFrontage.setItem(i, 1, QTableWidgetItem(str(item[A2])))
                self.tableWidgetFrontage.setItem(i, 2, QTableWidgetItem(str(item[A3])))
                self.tableWidgetFrontage.setItem(i, 3, QTableWidgetItem(str(item[A4])))

            self.tableWidgetFrontage.resizeRowsToContents()
            self.tableWidgetFrontage.resizeColumnsToContents()
            self.tableWidgetFrontage.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)

    def tableClear(self):
        self.tableWidgetFrontage.clear()

    #######
    #   Entrances
    #######

    def updateEntranceTypes(self):
        self.ecategorylistWidget.clear()
        entrance_category_list = ['Controlled', 'Uncontrolled']

        entrance_access_level_list = ["Lower Floor", "Ground Floor", "Upper Floor"]

        self.ecategorylistWidget.addItems(entrance_category_list)
        self.eaccesscategorylistWidget.addItems(entrance_access_level_list)

    def updateSubCategory(self):
        entrance_sub_category_list_Controlled = ['Default', 'Fire Exit', 'Service Entrance', 'Unused']
        entrance_sub_category_list_Uncontrolled = ['Default']
        self.esubcategorylistWidget.addItems(entrance_sub_category_list_Controlled)

        if self.ecategorylistWidget.currentRow() == 0:
            self.esubcategorylistWidget.clear()
            self.esubcategorylistWidget.addItems(entrance_sub_category_list_Controlled)
            self.esubcategorylistWidget.setCurrentRow(0)

        elif self.ecategorylistWidget.currentRow() == 1:
            self.esubcategorylistWidget.clear()
            self.esubcategorylistWidget.addItems(entrance_sub_category_list_Uncontrolled)
            self.esubcategorylistWidget.setCurrentRow(0)

    # Set universal Entrance layer if conditions are satisfied
    def setEntranceLayer(self):
        index = self.useExistingEntrancescomboBox.currentIndex()
        self.entrance_layer = self.useExistingEntrancescomboBox.itemData(index)
        return self.entrance_layer

    def clearEntranceDataFields(self):
        self.entrancetableClear()
        self.tableWidgetEntrance.setColumnCount(4)
        headers = ["E-ID", "Category", "Sub Category", "Access Level"]
        self.tableWidgetEntrance.setHorizontalHeaderLabels(headers)
        self.tableWidgetEntrance.setRowCount(0)

    def addEntranceDataFields(self):
        self.entrancetableClear()
        layer = self.setEntranceLayer()
        if layer:
            features = layer.selectedFeatures()
            attrs = []
            for feat in features:
                attr = feat.attributes()
                attrs.append(attr)

            fields = layer.fields()
            field_names = [field.name() for field in fields]

            field_length = len(field_names)
            A1 = field_length - 4
            A2 = field_length - 3
            A3 = field_length - 2
            A4 = field_length - 1

            self.tableWidgetEntrance.setColumnCount(4)
            headers = ["E-ID", "Category", "Sub Category", "Access Level"]
            self.tableWidgetEntrance.setHorizontalHeaderLabels(headers)
            self.tableWidgetEntrance.setRowCount(len(attrs))

            for i, item in enumerate(attrs):
                self.tableWidgetEntrance.setItem(i, 0, QTableWidgetItem(str(item[A1])))
                self.tableWidgetEntrance.setItem(i, 1, QTableWidgetItem(str(item[A2])))
                self.tableWidgetEntrance.setItem(i, 2, QTableWidgetItem(str(item[A3])))
                self.tableWidgetEntrance.setItem(i, 3, QTableWidgetItem(str(item[A4])))

            self.tableWidgetEntrance.resizeRowsToContents()
            self.tableWidgetEntrance.resizeColumnsToContents()
            self.tableWidgetEntrance.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)

    def entrancetableClear(self):
        self.tableWidgetEntrance.clear()

        #######
        #   Land Use
        #######

    def updateLUTypes(self):
        self.lucategorylistWidget.clear()
        lu_category_list = ["Agriculture", "Community", "Catering",
                            "Education", "Government", "Hotels",
                            "Industry", "Leisure", "Medical",
                            "Offices", "Parking", "Retail",
                            "Residential", "Services", "Storage",
                            "Transport", "Utilities", "Under Construction",
                            "Under Developed", "Unknown/Undefined", "Vacant Building"]
        lu_sub_category_list_empty = ["-"]

        self.lucategorylistWidget.addItems(lu_category_list)
        self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)

    def updateLUsubcat(self):

        lu_sub_category_list_catering = ["Restaurant and Cafes", "Drinking Establishments",
                                         "Hot Food Takeaways"]
        lu_sub_category_list_leisure = ["Art and Culture", "Amusement or Sports"]
        lu_sub_category_list_medical = ["Hospitals", "Health centres"]
        lu_sub_category_list_parking = ["Car Parks", "Other Vehicles"]
        lu_sub_category_list_residential = ["Institutions", "Dwellings"]
        lu_sub_category_list_services = ["Commercial", "Financial"]
        lu_sub_category_list_transport = ["Transport Terminals", "Goods Terminals"]
        lu_sub_category_list_empty = ["-"]

        if self.lucategorylistWidget.currentRow() == 0:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 1:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 2:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_catering)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 3:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 4:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 5:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 6:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 7:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_leisure)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 8:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_medical)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 9:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 10:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_parking)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 11:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 12:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_residential)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 13:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_services)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 14:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 15:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_transport)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 16:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 17:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 18:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 19:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
            self.lusubcategorylistWidget.setCurrentRow(0)

        elif self.lucategorylistWidget.currentRow() == 20:
            self.lusubcategorylistWidget.clear()
            self.lusubcategorylistWidget.addItems(lu_sub_category_list_empty)
        self.lusubcategorylistWidget.setCurrentRow(0)

    # Set universal Entrance layer if conditions are satisfied

    def setLULayer(self):
        index = self.useExistingLUcomboBox.currentIndex()
        self.LU_layer = self.useExistingLUcomboBox.itemData(index)
        return self.LU_layer

    def clearLUDataFields(self):
        self.LUtableClear()

        if self.LUGroundfloorradioButton.isChecked():
            self.tableWidgetlanduse.setColumnCount(5)
            headers = ["LU-ID", "Floors", "Area", "GF Category", "GF Sub Category"]
            self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)
            self.tableWidgetlanduse.setRowCount(0)

        if self.LULowerfloorradioButton.isChecked():
            self.tableWidgetlanduse.setColumnCount(5)
            headers = ["LU-ID", "Floors", "Area", "LF Category", "LF Sub Category"]
            self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)
            self.tableWidgetlanduse.setRowCount(0)

        if self.LUUpperfloorradioButton.isChecked():
            self.tableWidgetlanduse.setColumnCount(5)
            headers = ["LU-ID", "Floors", "Area", "UF Category", "UF Sub Category"]
            self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)
            self.tableWidgetlanduse.setRowCount(0)

    def addLUDataFields(self):
        self.LUtableClear()
        layer = self.setLULayer()
        if layer:
            dp = layer.dataProvider()
            fieldlist = lfh.getFieldNames(layer)
            features = layer.selectedFeatures()
            attrs = []
            for feat in features:
                attr = feat.attributes()
                attrs.append(attr)

            idfieldindex = dp.fieldNameIndex('LU_ID')
            floorfieldindex = dp.fieldNameIndex('Floors')
            areafieldindex = dp.fieldNameIndex('Area')
            gfcatfieldindex = dp.fieldNameIndex('GF_Cat')
            gfsubcatfieldindex = dp.fieldNameIndex('GF_SubCat')
            lfcatfieldindex = dp.fieldNameIndex('LF_Cat')
            lfsubcatfieldindex = dp.fieldNameIndex('LF_SubCat')
            ufcatfieldindex = dp.fieldNameIndex('UF_Cat')
            ufsubcatfieldindex = dp.fieldNameIndex('UF_SubCat')

            self.tableWidgetlanduse.setColumnCount(5)
            self.tableWidgetlanduse.setRowCount(len(attrs))
            if self.LUGroundfloorradioButton.isChecked():

                headers = ["LU-ID", "Floors", "Area", "GF Category", "GF Sub Category"]
                self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)

                for i, item in enumerate(attrs):
                    self.tableWidgetlanduse.setItem(i, 0, QTableWidgetItem(str(item[idfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 1, QTableWidgetItem(str(item[floorfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 2, QTableWidgetItem(str(item[areafieldindex])))
                    self.tableWidgetlanduse.setItem(i, 3, QTableWidgetItem(str(item[gfcatfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 4, QTableWidgetItem(str(item[gfsubcatfieldindex])))

            elif self.LULowerfloorradioButton.isChecked():

                headers = ["LU-ID", "Floors", "Area", "LF Category", "LF Sub Category"]
                self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)

                for i, item in enumerate(attrs):
                    self.tableWidgetlanduse.setItem(i, 0, QTableWidgetItem(str(item[idfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 1, QTableWidgetItem(str(item[floorfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 2, QTableWidgetItem(str(item[areafieldindex])))
                    self.tableWidgetlanduse.setItem(i, 3, QTableWidgetItem(str(item[lfcatfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 4, QTableWidgetItem(str(item[lfsubcatfieldindex])))

            elif self.LUUpperfloorradioButton.isChecked():

                headers = ["LU-ID", "Floors", "Area", "UF Category", "UF Sub Category"]
                self.tableWidgetlanduse.setHorizontalHeaderLabels(headers)

                for i, item in enumerate(attrs):
                    self.tableWidgetlanduse.setItem(i, 0, QTableWidgetItem(str(item[idfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 1, QTableWidgetItem(str(item[floorfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 2, QTableWidgetItem(str(item[areafieldindex])))
                    self.tableWidgetlanduse.setItem(i, 3, QTableWidgetItem(str(item[ufcatfieldindex])))
                    self.tableWidgetlanduse.setItem(i, 4, QTableWidgetItem(str(item[ufsubcatfieldindex])))

            self.tableWidgetlanduse.resizeRowsToContents()
            self.tableWidgetlanduse.resizeColumnsToContents()
            self.tableWidgetlanduse.horizontalHeader().setResizeMode(5, QHeaderView.Stretch)

    def LUtableClear(self):
        self.tableWidgetlanduse.clear()
        self.tableWidgetlanduse.clearContents()

    def clearLuTabledel(self):
        layer = self.dockwidget.setLULayer()
        # layer.featureDeleted.connect(self.dockwidget.clearLUDataFields)

    def setLuFloors(self, value):
        self.spinBoxlufloors.setValue(int(value))

    def updateLUCodes(self):
        if self.lucategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("AG")
            self.lineEdit_luNLUD.setText("U010")
            self.lineEdit_luTCPA.setText("B2")

        if self.lucategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("C")
            self.lineEdit_luNLUD.setText("U082")
            self.lineEdit_luTCPA.setText("D1")

        if self.lucategorylistWidget.currentRow() == 2 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("CA")
            self.lineEdit_luNLUD.setText("U093")
            self.lineEdit_luTCPA.setText("A3")

        elif self.lucategorylistWidget.currentRow() == 2 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.clear()
            self.lineEdit_luNLUD.clear()
            self.lineEdit_luTCPA.clear()

            self.lineEdit_luSSx.setText("CA")
            self.lineEdit_luNLUD.setText("U094")
            self.lineEdit_luTCPA.setText("A4")

        elif self.lucategorylistWidget.currentRow() == 2 and self.lusubcategorylistWidget.currentRow() == 2:
            self.lineEdit_luSSx.clear()
            self.lineEdit_luNLUD.clear()
            self.lineEdit_luTCPA.clear()

            self.lineEdit_luSSx.setText("CA")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("A5")

        if self.lucategorylistWidget.currentRow() == 3:
            self.lineEdit_luSSx.setText("ED")
            self.lineEdit_luNLUD.setText("U083")
            self.lineEdit_luTCPA.setText("D1")

        if self.lucategorylistWidget.currentRow() == 4:
            self.lineEdit_luSSx.setText("GOV")
            self.lineEdit_luNLUD.setText("U120")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 5:
            self.lineEdit_luSSx.setText("H")
            self.lineEdit_luNLUD.setText("U072")
            self.lineEdit_luTCPA.setText("C1")

        if self.lucategorylistWidget.currentRow() == 6:
            self.lineEdit_luSSx.setText("I")
            self.lineEdit_luNLUD.setText("U101")
            self.lineEdit_luTCPA.setText("B2")

        if self.lucategorylistWidget.currentRow() == 7 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("LE")
            self.lineEdit_luNLUD.setText("U040")
            self.lineEdit_luTCPA.setText("D1")

        elif self.lucategorylistWidget.currentRow() == 7 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("LE")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("D2")

        if self.lucategorylistWidget.currentRow() == 8 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("M")
            self.lineEdit_luNLUD.setText("U081")
            self.lineEdit_luTCPA.setText("C2")

        elif self.lucategorylistWidget.currentRow() == 8 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("M")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("D1")

        if self.lucategorylistWidget.currentRow() == 9:
            self.lineEdit_luSSx.setText("O")
            self.lineEdit_luNLUD.setText("U102")
            self.lineEdit_luTCPA.setText("B1")

        if self.lucategorylistWidget.currentRow() == 10 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("P")
            self.lineEdit_luNLUD.setText("U053")
            self.lineEdit_luTCPA.setText("")

        elif self.lucategorylistWidget.currentRow() == 10 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("P")
            self.lineEdit_luNLUD.setText("U053")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 11:
            self.lineEdit_luSSx.setText("R")
            self.lineEdit_luNLUD.setText("U091")
            self.lineEdit_luTCPA.setText("A1")

        if self.lucategorylistWidget.currentRow() == 12 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("RE")
            self.lineEdit_luNLUD.setText("U071")
            self.lineEdit_luTCPA.setText("C2")

        elif self.lucategorylistWidget.currentRow() == 12 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("RE")
            self.lineEdit_luNLUD.setText("U073")
            self.lineEdit_luTCPA.setText("C2")

        if self.lucategorylistWidget.currentRow() == 13 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("S")
            self.lineEdit_luNLUD.setText("U092")
            self.lineEdit_luTCPA.setText("A1")

        elif self.lucategorylistWidget.currentRow() == 13 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("S")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("A2")

        if self.lucategorylistWidget.currentRow() == 14:
            self.lineEdit_luSSx.setText("ST")
            self.lineEdit_luNLUD.setText("U103")
            self.lineEdit_luTCPA.setText("B8")

        if self.lucategorylistWidget.currentRow() == 15 and self.lusubcategorylistWidget.currentRow() == 0:
            self.lineEdit_luSSx.setText("TR")
            self.lineEdit_luNLUD.setText("U052")
            self.lineEdit_luTCPA.setText("")

        elif self.lucategorylistWidget.currentRow() == 15 and self.lusubcategorylistWidget.currentRow() == 1:
            self.lineEdit_luSSx.setText("TR")
            self.lineEdit_luNLUD.setText("U055")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 16:
            self.lineEdit_luSSx.setText("U")
            self.lineEdit_luNLUD.setText("U060")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 17:
            self.lineEdit_luSSx.setText("UC")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 18:
            self.lineEdit_luSSx.setText("UD")
            self.lineEdit_luNLUD.setText("U130")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 19:
            self.lineEdit_luSSx.setText("UN")
            self.lineEdit_luNLUD.setText("")
            self.lineEdit_luTCPA.setText("")

        if self.lucategorylistWidget.currentRow() == 20:
            self.lineEdit_luSSx.setText("V")
            self.lineEdit_luNLUD.setText("U110")
            self.lineEdit_luTCPA.setText("")
