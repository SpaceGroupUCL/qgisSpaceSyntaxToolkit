# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2017-06-12
# copyright            : (C) 2017 by Space Syntax Ltd
# author               : Ioanna Kolovou
# email                : i.kolovou@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" This is to load the postgis db settings
"""

from __future__ import absolute_import
from __future__ import print_function

import os
from builtins import str

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal

from esstoolkit.utilities import db_helpers as dbh

# from qgis.core import QgsDataSourceURI

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DbSettings_dialog_base.ui'))


class DbSettingsDialog(QtWidgets.QDialog, FORM_CLASS):
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

        self.available_dbs = available_dbs
        self.connstring = None
        self.popDbs()
        self.okButton.clicked.connect(self.close)
        self.dbCombo.currentIndexChanged.connect(self.popSchemas)

    def popDbs(self):
        self.dbCombo.clear()
        self.dbCombo.addItems(['select db'] + sorted(self.available_dbs.keys()))
        return

    def getSelectedDb(self):
        return self.dbCombo.currentText()

    def getDbSettings(self):
        connection = self.dbCombo.currentText()
        if connection in list(self.available_dbs.keys()):
            return {'dbname': connection,
                    'schema': self.schemaCombo.currentText(),
                    'table_name': self.nameLineEdit.text()}
        else:
            return {}

    def popSchemas(self):
        idx = self.dbCombo.findText('select db')
        if idx != -1:
            self.dbCombo.removeItem(idx)
        self.schemaCombo.clear()
        schemas = []
        selected_db = self.getSelectedDb()
        if len(self.getSelectedDb()) > 1:
            self.get_connstring(selected_db)
            schemas = dbh.getPostgisSchemas(self.connstring)
            # fix_print_with_import
            # fix_print_with_import
            print('connstring', self.connstring)
        self.schemaCombo.addItems(schemas)

    def get_connstring(self, selected_db):
        db_info = self.available_dbs[selected_db]
        # fix_print_with_import
        # fix_print_with_import
        print('tries', db_info, selected_db)
        self.connstring = ''
        try:
            db_info['user'] = db_info['username']
            del db_info['username']
        except KeyError:
            pass
        try:
            db_info['dbname'] = db_info['database']
            del db_info['database']
        except KeyError:
            pass
        for k, v in list(db_info.items()):
            self.connstring += str(k) + '=' + str(v) + ' '
        return

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
