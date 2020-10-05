# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os.path
# Import the PyQt and QGIS libraries
from builtins import str

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsProject

from esstoolkit.utilities import db_helpers as dbh, shapefile_helpers as shph
# import project settings dialog
from .ui_Project import Ui_ProjectDialog


class ProjectManager(QtCore.QObject):
    settingsUpdated = QtCore.pyqtSignal()

    def __init__(self, iface, settings):
        QtCore.QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        # self.connection = None
        self.proj = QgsProject.instance()
        self.proj_settings = dict()
        self.datastore = {'name': '', 'type': 0, 'path': '', 'schema': '', 'crs': ''}
        self.__loadSettings()

        self.dlg = ProjectDialog(self.iface, self.proj_settings, self.settings)

        # set up GUI signals
        # for the buttonbox we must use old style connections, or else use simple buttons
        self.dlg.saveDatastoreSettings.connect(self.writeSettings)
        self.settingsUpdated.connect(self.updateDatastore)
        self.iface.projectRead.connect(self.__loadSettings)
        self.iface.newProjectCreated.connect(self.__loadDefaults)

    def unload(self):
        self.iface.projectRead.disconnect(self.__loadSettings)
        self.iface.newProjectCreated.disconnect(self.__loadDefaults)

    def showDialog(self):
        self.dlg.loadSettings(self.proj_settings)
        self.dlg.show()

    def getProject(self):
        return self.proj

    def getProjectName(self):
        return self.proj.title()

    def readSettings(self, settings, group=''):
        if group != '':
            position = str(group) + '/'
        else:
            position = ''
        for key in settings.keys():
            this_type = type(settings[key]).__name__
            if this_type in ('int', 'long'):
                entry = self.proj.readNumEntry('esst', position + str(key))
            elif this_type == 'float':
                entry = self.proj.readDoubleEntry('esst', position + str(key))
            elif this_type == 'bool':
                entry = self.proj.readBoolEntry('esst', position + str(key))
            elif this_type == 'list':
                entry = self.proj.readListEntry('esst', position + str(key))
            else:
                entry = self.proj.readEntry('esst', position + str(key))
            if entry[1]:
                settings[key] = entry[0]

    def readSetting(self, key, group='', type=''):
        if group != '':
            position = str(group) + '/'
        else:
            position = ''
        if type in ('int', 'long'):
            entry = self.proj.readNumEntry('esst', position + str(key))
        elif type == 'float':
            entry = self.proj.readDoubleEntry('esst', position + str(key))
        elif type == 'bool':
            entry = self.proj.readBoolEntry('esst', position + str(key))
        elif type == 'list':
            entry = self.proj.readListEntry('esst', position + str(key))
        else:
            entry = self.proj.readEntry('esst', position + str(key))
        if entry[1]:
            setting = entry[0]
        else:
            setting = None
        return setting

    def getGroupSettings(self, group=''):
        # this function returns all settings as strings.
        # impossible to get type from value as read function is always true.
        settings = dict()
        keys = self.proj.entryList('esst', str(group))
        if group != '':
            position = str(group) + '/'
        else:
            position = ''
        for key in keys:
            entry = self.proj.readEntry('esst', position + str(key))
            if entry[1]:
                settings[key] = entry[0]
            else:
                settings[key] = self.proj.readListEntry('esst', position + str(key))[0]
        return settings

    def getAllSettings(self):
        # this function returns all settings as strings.
        # it's impossible to get type from value as read function is always true.
        settings = dict()
        # retrieve ungrouped keys
        base = self.proj.entryList('esst', '')
        if len(base) > 0:
            for key in base:
                settings[key] = self.proj.readEntry('esst', str(key))[0]
        # retrieve grouped keys (1 level only)
        groups = self.proj.subkeyList('esst', '')
        if len(groups) > 0:
            for group in groups:
                keys = self.proj.entryList('esst', str(group))
                if len(keys) > 0:
                    for key in keys:
                        entry = self.proj.readEntry('esst', str(group) + "/" + str(key))
                        if entry[1]:
                            setting = entry[0]
                        else:
                            setting = self.proj.readListEntry('esst', str(group) + "/" + str(key))[0]
                        settings[str(group) + "/" + str(key)] = setting
        return settings

    def __loadDefaults(self):
        self.proj_settings = dict()
        self.settingsUpdated.emit()

    def __loadSettings(self):
        self.proj_settings = self.getAllSettings()
        self.settingsUpdated.emit()

    def writeSettings(self, settings, group=''):
        if group != '':
            position = str(group) + '/'
        else:
            position = ''
        try:
            for key in settings.keys():
                val = settings[key]
                self.proj.writeEntry('esst', position + str(key), val)
            self.settingsUpdated.emit()
            return True
        except:
            return False

    def writeSetting(self, key, value, group):
        position = ''
        if group != '':
            position = str(group) + '/'
        try:
            self.proj.writeEntry('esst', position + str(key), value)
            self.settingsUpdated.emit()
            return True
        except:
            return False

    def __saveSettings(self):
        for key in self.proj_settings.keys():
            self.proj.writeEntry('esst', key, self.proj_settings[key])
        self.settingsUpdated.emit()
        # self.__loadSettings()

    def updateDatastore(self):
        # update data store object:
        if "datastore/type" in self.proj_settings:
            self.datastore["type"] = int(self.proj_settings["datastore/type"])
        else:
            self.datastore["type"] = 0
        if "datastore/name" in self.proj_settings:
            self.datastore["name"] = self.proj_settings["datastore/name"]
        else:
            self.datastore["name"] = ''
        if "datastore/path" in self.proj_settings:
            self.datastore["path"] = self.proj_settings["datastore/path"]
        else:
            self.datastore["path"] = ''
        if "datastore/schema" in self.proj_settings:
            self.datastore["schema"] = self.proj_settings["datastore/schema"]
        else:
            self.datastore["schema"] = ''
        if "datastore/crs" in self.proj_settings:
            self.datastore["crs"] = self.proj_settings["datastore/crs"]
        else:
            self.datastore["crs"] = ''


class ProjectDialog(QDialog, Ui_ProjectDialog):
    saveDatastoreSettings = QtCore.pyqtSignal(dict)

    def __init__(self, iface, proj_settings, settings):

        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.iface = iface
        self.settings = settings
        self.proj_settings = proj_settings
        self.datastores = dict()
        self.datastore_type = 0
        self.datastore_idx = None
        self.datastore_name = None
        self.datastore_path = None
        self.datastore_schema = None
        self.default_data_type = 0

        self.dataTypeCombo.clear()
        self.dataTypeCombo.addItems(['Shape files folder', 'Personal geodatabase', 'PostGIS database'])

        # set up internal GUI signals
        self.closeButtonBox.rejected.connect(self.close)
        self.closeButtonBox.accepted.connect(self.updateSettings)
        self.dataTypeCombo.currentIndexChanged.connect(self.selectDatastoreType)
        self.dataSelectCombo.currentIndexChanged.connect(self.selectDatastore)
        self.schemaCombo.currentIndexChanged.connect(self.selectSchema)
        self.dataOpenButton.clicked.connect(self.openDatastore)
        self.dataNewButton.clicked.connect(self.newDatastore)

    def loadSettings(self, proj_settings):
        self.proj_settings = proj_settings
        # set up current settings, otherwise default
        if "datastore/type" in self.proj_settings:
            try:
                data_type = int(self.proj_settings["datastore/type"])
                self.dataTypeCombo.setCurrentIndex(data_type)
            except:
                self.dataTypeCombo.setCurrentIndex(self.default_data_type)
        else:
            self.dataTypeCombo.setCurrentIndex(self.default_data_type)
        self.selectDatastoreType()

    def selectDatastoreType(self):
        self.datastore_type = self.dataTypeCombo.currentIndex()
        # type 0 - shape file folder
        if self.datastore_type == 0:
            self.dataNewButton.setDisabled(False)
            self.dataOpenButton.setDisabled(False)
            self.clearDatastoreSelect()
            self.clearSchemaSelect()
        # type 0 - spatialite personal geodatabase # the default
        elif self.datastore_type == 1:
            self.dataNewButton.setDisabled(False)
            self.dataOpenButton.setDisabled(False)
            self.clearDatastoreSelect()
            self.clearSchemaSelect()
        # type 2 - PostGIS geodatabase
        elif self.datastore_type == 2:
            self.dataNewButton.setDisabled(True)
            self.dataOpenButton.setDisabled(True)

        # update datastores according to type
        self.loadDatastoreList()

    def loadDatastoreList(self):
        # get list of datastores from loaded layers or existing database connections
        if self.datastore_type == 0:
            self.datastores = shph.listShapeFolders()
        elif self.datastore_type == 1:
            self.datastores = dbh.listSpatialiteConnections()
        elif self.datastore_type == 2:
            con_settings = dbh.getPostgisConnectionSettings()
            if len(con_settings) > 0:
                self.datastores = dict()
                self.datastores['name'] = [con['name'] for con in con_settings]
                self.datastores['idx'] = self.datastores['name'].index(dbh.getPostgisSelectedConnection())
                path = []
                for con in con_settings:
                    if con['database'] != 'NULL':
                        path.append(con['database'])
                    elif con['service'] != 'NULL':
                        path.append(con['service'])
                self.datastores['path'] = path
        # identify datastore from settings
        try:
            data_type = int(self.proj_settings["datastore/type"])
        except:
            data_type = None
        if self.datastore_type and data_type and (self.datastore_type == data_type):
            # for shape files, append the folder if existing and not yet in the list
            if self.datastore_type == 0 and os.path.exists(self.proj_settings["datastore/path"]):
                self.appendDatastoreList(self.proj_settings["datastore/name"], self.proj_settings["datastore/path"])
            # select the datastore if in the list
            try:
                self.datastores['idx'] = self.datastores['path'].index(self.proj_settings["datastore/path"])
            except:
                pass
        # populate list and select default datastore
        if self.datastores and len(self.datastores['name']) > 0:
            self.setDatastore()
        else:
            self.clearDatastoreSelect()
            self.clearSchemaSelect()

    def clearDatastoreSelect(self):
        self.datastore_name = None
        self.datastore_path = None
        self.datastore_idx = None
        self.dataSelectCombo.clear()
        self.dataSelectCombo.setDisabled(True)
        self.dataSelectLabel.setDisabled(True)

    def clearSchemaSelect(self):
        self.datastore_schema = None
        self.schemaCombo.clear()
        self.schemaCombo.setDisabled(True)
        self.schemaLabel.setDisabled(True)

    def appendDatastoreList(self, name, path):
        if self.datastores:
            # only append if unique in the list
            if path not in self.datastores['path']:
                self.datastores['name'].append(name)
                self.datastores['path'].append(path)
                self.datastores['idx'] = len(self.datastores['path']) - 1
        else:
            self.datastores = dict()
            self.datastores['name'] = [name]
            self.datastores['path'] = [path]
            self.datastores['idx'] = 0

    def setDatastore(self):
        # update the combo box
        self.dataSelectCombo.blockSignals(True)
        self.dataSelectCombo.clear()
        self.dataSelectCombo.addItems(self.datastores['name'])
        self.dataSelectCombo.blockSignals(False)
        self.dataSelectCombo.setDisabled(False)
        self.dataSelectLabel.setDisabled(False)
        # set the previous datastore
        self.dataSelectCombo.setCurrentIndex(self.datastores['idx'])
        self.selectDatastore()

    def selectDatastore(self):
        if self.datastores:
            self.datastore_idx = self.dataSelectCombo.currentIndex()
            self.datastore_name = self.datastores['name'][self.datastore_idx]
            self.datastore_path = self.datastores['path'][self.datastore_idx]
            self.dataSelectCombo.setToolTip(self.datastores['path'][self.datastore_idx])
            # update schemas accordingly
            if self.datastore_type == 2:
                self.schemaCombo.setDisabled(False)
                self.schemaLabel.setDisabled(False)
                self.loadSchemaList(self.datastore_name)

    def loadSchemaList(self, name):
        if name:
            # get schemas for selected database
            connection = dbh.getPostgisConnection(name)
            self.datastores['schema'] = dbh.listPostgisSchemas(connection)
            connection.close()
            #
            self.schemaCombo.blockSignals(True)
            self.schemaCombo.clear()
            self.schemaCombo.addItems(self.datastores['schema'])
            self.schemaCombo.blockSignals(False)
            self.schemaCombo.setDisabled(False)
            self.schemaLabel.setDisabled(False)
            try:
                idx = self.datastores['schema'].index(self.proj_settings['datastore/schema'])
                self.schemaCombo.setCurrentIndex(idx)
            except:
                self.schemaCombo.setCurrentIndex(0)
            self.selectSchema()

    def selectSchema(self):
        if self.datastores:
            self.datastore_schema = self.schemaCombo.currentText()

    def openDatastore(self):
        lastDir = self.settings.getLastDir()
        if not lastDir:
            lastDir = ""
        path = ""
        name = ""
        append = True
        if self.datastore_type == 0:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select shape files folder", lastDir)
            if path.strip() != "":
                path = str(path)
                name = os.path.basename(path)
        elif self.datastore_type == 1:
            path = QtWidgets.QFileDialog.getOpenFileName(self, "Open Spatialite data base", lastDir,
                                                         "Spatialite (*.sqlite *.db)")
            if path.strip() != "":
                path = str(path)
                name = os.path.basename(path)
                # check if datastore with same name exists
                if self.datastores and name in self.datastores['name']:
                    self.iface.messageBar().pushMessage("Error", "A database already exists with the same name.",
                                                        level=1, duration=5)
                    append = False
                # if not, create new connection in registry
                else:
                    dbh.createSpatialiteConnection(name, path)
        if path != "" and name != "":
            # store the path used
            self.settings.setLastDir(path)
            if append:
                self.appendDatastoreList(name, path)
                self.setDatastore()

    def newDatastore(self):
        lastDir = self.settings.getLastDir()
        if not lastDir:
            lastDir = ""
        path = ""
        name = ""
        append = True
        if self.datastore_type == 0:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select shape files folder ", lastDir)
            if path.strip() != "":
                path = str(path)
                name = os.path.basename(path)
        elif self.datastore_type == 1:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Create Spatialite data base", lastDir,
                                                            "Spatialite (*.sqlite *.db)")
            if path.strip() != "":
                path = str(path)
                name = os.path.basename(path)
                # check if datastore with same name exists
                if self.datastores and name in self.datastores['name']:
                    self.iface.messageBar().pushMessage("Error", "A database already exists with the same name.",
                                                        level=1, duration=5)
                # if not, create new connection in registry
                else:
                    dbh.createSpatialiteConnection(name, path)
                    dbh.createSpatialiteDatabase(path)
        if path != "" and name != "":
            # store the path used
            self.settings.setLastDir(path)
            if append:
                self.appendDatastoreList(name, path)
                self.setDatastore()

    def updateSettings(self):
        # this is just a quick hack for now... not clean, will revise for a more generic project manager
        self.proj_settings['datastore/type'] = self.datastore_type
        self.proj_settings['datastore/idx'] = self.datastore_idx
        self.proj_settings['datastore/name'] = self.datastore_name
        self.proj_settings['datastore/path'] = self.datastore_path
        self.proj_settings['datastore/schema'] = self.datastore_schema
        self.saveDatastoreSettings.emit(self.proj_settings)
