# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DbSettingsDialog
                                 A QGIS plugin
 This is to load the postgis db settings
                             -------------------
        begin                : 2017-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Ioanna Kolovou
        email                : i.kolovou@spacesyntax.com
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

import os

from PyQt4.QtCore import pyqtSignal
from PyQt4 import QtGui, uic

from qgis.core import QgsDataSourceURI
from sGraph.utilityFunctions import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DbSettings_dialog_base.ui'))


class DbSettingsDialog(QtGui.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()
    setDbOutput = pyqtSignal()

    def __init__(self, available_dbs, parent=None):
        """Constructor."""
        super(DbSettingsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.nameLineEdit.setText("cleaned")
        self.available_dbs = available_dbs

        self.okButton.clicked.connect(self.close)
        self.dbCombo.currentIndexChanged.connect(self.popSchemas)
        self.dbCombo.currentIndexChanged.connect(self.setDbOutput)
        self.schemaCombo.currentIndexChanged.connect(self.setDbOutput)
        self.nameLineEdit.textChanged.connect(self.setDbOutput)


        self.popDbs()
        if self.dbCombo.currentText() in self.available_dbs.keys():
            self.popSchemas()

    def popDbs(self):
        self.dbCombo.clear()
        self.dbCombo.addItems(sorted(self.available_dbs.keys()))
        return

    def getSelectedDb(self):
        return self.dbCombo.currentText()

    def getDbSettings(self):
        connection = self.dbCombo.currentText()
        if connection in self.available_dbs.keys():
            return {'dbname': self.available_dbs[connection]['name'],
        'user': self.available_dbs[connection]['username'],
        'host': self.available_dbs[connection]['host'],
        'port': self.available_dbs[connection]['port'],
        'password': self.available_dbs[connection]['password'],
        'schema': self.schemaCombo.currentText(),
        'table_name': self.nameLineEdit.text()}
        else:
            return {}

    def popSchemas(self):
        self.schemaCombo.clear()
        schemas = []
        selected_db = self.getSelectedDb()
        if len(self.getSelectedDb()) > 1:
            try:
                print 'tries'
                uri = QgsDataSourceURI()
                db_info = self.available_dbs[selected_db]
                print db_info, selected_db
                conname = selected_db
                dbname = db_info['database']
                user = db_info['username']
                host = db_info['host']
                port = db_info['port']
                password = db_info['password']
                uri.setConnection(host, port, dbname, user, password)
                connstring = "dbname=%s user=%s host=%s port=%s password=%s" % (dbname, user, host, port, password)
                schemas = getPostgisSchemas(connstring)
            except:
                print 'error'
                pass
        self.schemaCombo.addItems(schemas)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()