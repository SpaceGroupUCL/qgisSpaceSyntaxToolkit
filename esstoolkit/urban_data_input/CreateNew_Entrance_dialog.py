# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-08-16
# copyright            : (C) 2016 by Abhimanyu Acharya/(C) 2016 by Space Syntax Limited’.
# author               : Abhimanyu Acharya
# email                : a.acharya@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import absolute_import
from __future__ import print_function

import os

from qgis.PyQt import QtCore, QtWidgets, uic

from .DbSettings_dialog import DbSettingsDialog
from esstoolkit.utilities import db_helpers as dbh

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'CreateNew_Entrance_dialog_base.ui'))


class CreateNew_EntranceDialog(QtWidgets.QDialog, FORM_CLASS):
    create_new_layer = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(CreateNew_EntranceDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # setup signals
        self.pushButtonSelectLocationEntrance.clicked.connect(self.selectSaveLocationEntrance)
        self.pushButtonEntrancesNewFileDLG.clicked.connect(self.newEntranceLayer)
        self.closePopUpEntrancesButton.clicked.connect(self.closePopUpEntrances)

        available_dbs = dbh.getQGISDbs()
        self.dbsettings_dlg = DbSettingsDialog(available_dbs)
        self.dbsettings_dlg.nameLineEdit.setText('entrances')

        self.e_memory_radioButton.setChecked(True)
        self.lineEditEntrances.setPlaceholderText('Specify temporary layer name')
        self.lineEditEntrances.setDisabled(False)
        self.e_shp_radioButton.setChecked(False)
        self.e_postgis_radioButton.setChecked(False)

        self.e_shp_radioButton.clicked.connect(self.setOutput)
        self.e_postgis_radioButton.clicked.connect(self.setOutput)
        self.e_memory_radioButton.clicked.connect(self.setOutput)
        self.pushButtonSelectLocationEntrance.setDisabled(True)

        # self.dbsettings_dlg.setDbOutput.connect(self.setOutput)
        self.dbsettings_dlg.dbCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.schemaCombo.currentIndexChanged.connect(self.setDbPath)
        self.dbsettings_dlg.nameLineEdit.textChanged.connect(self.setDbPath)

    def closePopUpEntrances(self):
        self.close()

    # Open Save file dialogue and set location in text edit
    def selectSaveLocationEntrance(self):
        if self.e_shp_radioButton.isChecked():
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Specify Output Location ", "", '*.shp')
            self.lineEditEntrances.clear()
            self.lineEditEntrances.setText(filename)
        elif self.e_postgis_radioButton.isChecked():
            self.lineEditEntrances.clear()
            self.setOutput()
            self.dbsettings_dlg.show()
            self.dbsettings = self.dbsettings_dlg.getDbSettings()
            if self.dbsettings:
                db_layer_name = "%s:%s:%s" % (
                    self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                print('db_layer_name')
                self.lineEditEntrances.setText(db_layer_name)
        elif self.e_memory_radioButton.isChecked():
            self.lineEditEntrances.clear()
            pass

    def setDbPath(self):
        if self.e_postgis_radioButton.isChecked():
            try:
                self.dbsettings = self.dbsettings_dlg.getDbSettings()
                db_layer_name = "%s:%s:%s" % (
                    self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                self.lineEditEntrances.setText(db_layer_name)
            except:
                self.lineEditEntrances.clear()
        return

    def newEntranceLayer(self):
        self.create_new_layer.emit()

    def setOutput(self):
        if self.e_shp_radioButton.isChecked():
            self.lineEditEntrances.clear()
            self.lineEditEntrances.setPlaceholderText('Specify output location')
            self.lineEditEntrances.setDisabled(True)
            self.pushButtonSelectLocationEntrance.setDisabled(False)
        elif self.e_postgis_radioButton.isChecked():
            self.lineEditEntrances.clear()
            self.dbsettings = self.dbsettings_dlg.getDbSettings()
            self.pushButtonSelectLocationEntrance.setDisabled(False)
            print('dbs1', self.dbsettings)
            if self.dbsettings != {}:
                db_layer_name = "%s:%s:%s" % (
                    self.dbsettings['dbname'], self.dbsettings['schema'], self.dbsettings['table_name'])
                self.lineEditEntrances.setText(db_layer_name)
                self.lineEditEntrances.setDisabled(False)
            else:
                self.lineEditEntrances.setPlaceholderText('Specify as database:schema:table name')
                self.lineEditEntrances.setDisabled(True)
        elif self.e_memory_radioButton.isChecked():
            self.lineEditEntrances.clear()
            self.lineEditEntrances.setDisabled(False)
            self.lineEditEntrances.setPlaceholderText('Specify temporary layer name')
            self.pushButtonSelectLocationEntrance.setDisabled(True)
