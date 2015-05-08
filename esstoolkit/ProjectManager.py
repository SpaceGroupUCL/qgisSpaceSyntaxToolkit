# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015 UCL, Jorge Gil
        email                : jorge.gil@ucl.ac.uk
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
from PyQt4 import QtCore, QtGui
from qgis.core import *

import os.path

from . import utility_functions as uf

# import project settings dialog
from ui_Project import Ui_ProjectDialog

class ProjectManager(QtCore.QObject):
    settingsUpdated = QtCore.pyqtSignal()

    def __init__(self, iface, settings):
        QtCore.QObject.__init__(self)

        self.iface = iface
        self.settings = settings
        #self.connection = None
        self.proj = QgsProject.instance()
        self.proj_settings = dict()
        self.datastore = {'name':'','type':0,'path':'','schema':'','crs':''}
        self.__loadSettings()

        self.dlg = ProjectDialog(self.proj_settings, self.settings)

        # set up GUI signals
        #for the buttonbox we must use old style connections, or else use simple buttons
        self.dlg.saveDatastoreSettings.connect(self.writeSettings)
        self.settingsUpdated.connect(self.updateDatastore)
        self.iface.projectRead.connect(self.__loadSettings)
        self.iface.newProjectCreated.connect(self.__loadDefaults)

    def unload(self):
        self.iface.projectRead.disconnect(self.__loadSettings)
        self.iface.newProjectCreated.disconnect(self.__loadDefaults)

    def showDialog(self):
        self.__loadSettings()
        self.dlg.loadSettings(self.proj_settings)
        self.dlg.show()

    def getProject(self):
        return self.proj

    def getProjectName(self):
        return self.proj.title()

    def readSettings(self, settings, group=''):
        if group != '':
            position = str(group)+'/'
        else:
            position = ''
        for key in settings.iterkeys():
            this_type = type(settings[key]).__name__
            if this_type in ('int','long'):
                entry = self.proj.readNumEntry('esst',position+str(key))
            elif this_type == 'float':
                entry = self.proj.readDoubleEntry('esst',position+str(key))
            elif this_type == 'bool':
                entry = self.proj.readBoolEntry('esst',position+str(key))
            elif this_type == 'list':
                entry = self.proj.readListEntry('esst',position+str(key))
            else:
                entry = self.proj.readEntry('esst',position+str(key))
            if entry[1]:
                settings[key] = entry[0]

    def readSetting(self, key, group='', type=''):
        if group != '':
            position = str(group)+'/'
        else:
            position = ''
        if type in ('int','long'):
            entry = self.proj.readNumEntry('esst',position+str(key))
        elif type == 'float':
            entry = self.proj.readDoubleEntry('esst',position+str(key))
        elif type == 'bool':
            entry = self.proj.readBoolEntry('esst',position+str(key))
        elif type == 'list':
            entry = self.proj.readListEntry('esst',position+str(key))
        else:
            entry = self.proj.readEntry('esst',position+str(key))
        if entry[1]:
            setting = entry[0]
        else:
            setting = None
        return setting

    def getGroupSettings(self, group=''):
        # this function returns all settings as strings.
        # impossible to get type from value as read function is always true.
        settings = dict()
        keys = self.proj.entryList('esst',str(group))
        if group != '':
            position = str(group)+'/'
        else:
            position = ''
        for key in keys:
            entry = self.proj.readEntry('esst',position+str(key))
            if entry[1] == True:
                settings[key] = entry[0]
            else:
                settings[key] = self.proj.readListEntry('esst',position+str(key))[0]
        return settings

    def getAllSettings(self):
        # this function returns all settings as strings.
        # it's impossible to get type from value as read function is always true.
        settings = dict()
        # retrieve ungrouped keys
        base = self.proj.entryList('esst','')
        if len(base) > 0:
            for key in base:
                settings[key] = self.proj.readEntry('esst',str(key))[0]
        # retrieve grouped keys (1 level only)
        groups = self.proj.subkeyList('esst','')
        if len(groups) > 0:
            for group in groups:
                keys = self.proj.entryList('esst',str(group))
                if len(keys) > 0:
                    for key in keys:
                        entry = self.proj.readEntry('esst',str(group)+"/"+str(key))
                        if entry[1] == True:
                            setting = entry[0]
                        else:
                            setting = self.proj.readListEntry('esst',str(group)+"/"+str(key))[0]
                        settings[str(group)+"/"+str(key)] = setting
        return settings

    def __loadDefaults(self):
        self.proj_settings = dict()
        self.settingsUpdated.emit()

    def __loadSettings(self):
        self.proj_settings = self.getAllSettings()
        self.settingsUpdated.emit()

    def writeSettings(self, settings, group=''):
        if group != '':
            position = str(group)+'/'
        else:
            position = ''
        try:
            for key in settings.iterkeys():
                val = settings[key]
                self.proj.writeEntry('esst', position+str(key), str(val))
            self.settingsUpdated.emit()
            return True
        except:
            return False

    def writeSetting(self, key, value, group):
        position = ''
        if group != '':
            position = str(group)+'/'
        try:
            self.proj.writeEntry('esst', position+str(key), value)
            self.settingsUpdated.emit()
            return True
        except:
            return False

    def __saveSettings(self):
        for key in self.proj_settings.iterkeys():
            self.proj.writeEntry('esst', key, self.proj_settings[key])
        self.settingsUpdated.emit()
        #self.__loadSettings()

    def updateDatastore(self):
        #update data store object:
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
        #self.datastoreUpdated.emit(self.datastore)


class ProjectDialog(QtGui.QDialog, Ui_ProjectDialog):
    saveDatastoreSettings = QtCore.pyqtSignal(dict)

    def __init__(self, proj_settings, settings):

        QtGui.QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.settings = settings
        self.proj_settings = proj_settings
        self.datastores = dict()
        self.datastore_type = None
        self.datastore_idx = None
        self.datastore_name = None
        self.datastore_path = None
        self.datastore_schema = None

        # set up internal GUI signals
        QtCore.QObject.connect(self.closeButtonBox,QtCore.SIGNAL("rejected()"),self.close)
        QtCore.QObject.connect(self.closeButtonBox,QtCore.SIGNAL("accepted()"),self.updateSettings)
        self.dataTypeCombo.currentIndexChanged.connect(self.selectDatastoreType)
        self.dataSelectCombo.currentIndexChanged.connect(self.selectDatastore)
        self.schemaCombo.currentIndexChanged.connect(self.selectSchema)
        self.dataOpenButton.clicked.connect(self.openDatastore)
        self.dataNewButton.clicked.connect(self.newDatastore)

        # Hide schema setting for now. It's only relevant in PostGIS
        self.schemaLabel.hide()
        self.schemaCombo.hide()


    def loadSettings(self,proj_settings):
        self.proj_settings = proj_settings
        # set up current settings, otherwise default
        if "datastore/type" in self.proj_settings:
            try:
                idx = int(self.proj_settings["datastore/type"])
                self.dataTypeCombo.setCurrentIndex(idx)
            except:
                return
        else:
            self.dataTypeCombo.setCurrentIndex(0)
        self.selectDatastoreType()

    def selectDatastoreType(self):
        self.datastore_type = self.dataTypeCombo.currentIndex()
        # type 0 - spatialite personal geodatabase # the default
        if self.datastore_type == 0:
            self.dataNewButton.setDisabled(False)
            self.dataOpenButton.setDisabled(False)
            self.schemaCombo.setDisabled(True)
            self.schemaLabel.setDisabled(True)
        # type 1 - shape file folder
        elif self.datastore_type == 1:
            self.dataNewButton.setDisabled(False)
            self.dataOpenButton.setDisabled(False)
            self.schemaCombo.setDisabled(True)
            self.schemaLabel.setDisabled(True)
        # type 2 - PostGIS geodatabase # not available for now...
        elif self.datastore_type == 2:
            self.dataNewButton.setDisabled(True)
            self.dataOpenButton.setDisabled(True)
            self.schemaCombo.setDisabled(False)
            self.schemaLabel.setDisabled(False)

        # update datastores according to type
        self.loadDatastoreList()

    def loadDatastoreList(self):
        # get list of datastores from loaded layers
        if self.datastore_type == 0:
            self.datastores = uf.listSpatialiteConnections()
        elif self.datastore_type == 1:
            self.datastores = uf.listShapeFolders()
        elif self.datastore_type == 2:
            #newfeature: get list of PostGIS connections
            pass
        # identify datastore from settings
        try:
            idx = int(self.proj_settings["datastore/type"])
        except:
            idx = 0
        if self.datastore_type == idx:
            if self.datastore_type == 1 and os.path.exists(self.proj_settings["datastore/path"]):
                self.appendDatastoreList(self.proj_settings["datastore/name"],self.proj_settings["datastore/path"])
            try:
                self.datastores['idx'] = self.datastores['path'].index(self.proj_settings["datastore/path"])
            except:
                pass
        # populate list and select default datastore
        if self.datastores:
            self.setDatastore()
        else:
            self.dataSelectCombo.clear()
            self.dataSelectCombo.setDisabled(True)
            self.dataSelectLabel.setDisabled(True)

    def appendDatastoreList(self, name, path):
        if self.datastores:
            #only append if unique in the list
            if path not in self.datastores['path']:
                self.datastores['name'].append(name)
                self.datastores['path'].append(path)
                self.datastores['idx'] = len(self.datastores['path'])-1
        else:
            self.datastores = dict()
            self.datastores['name'] = [name]
            self.datastores['path'] = [path]
            self.datastores['idx'] = 0
        self.dataSelectCombo.setDisabled(False)
        self.dataSelectLabel.setDisabled(False)

    def setDatastore(self):
        self.dataSelectCombo.clear()
        self.dataSelectCombo.addItems(self.datastores['name'])
        self.dataSelectCombo.setCurrentIndex(self.datastores['idx'])
        self.dataSelectCombo.setToolTip(self.datastores['path'][self.datastores['idx']])
        self.dataSelectCombo.setDisabled(False)
        self.dataSelectLabel.setDisabled(False)

    def selectDatastore(self):
        if self.datastores:
            self.datastore_idx = self.dataSelectCombo.currentIndex()
            self.datastore_name = self.datastores['name'][self.datastore_idx]
            self.datastore_path = self.datastores['path'][self.datastore_idx]

        #update schemas accordingly
        if self.datastore_type == 2:
            self.loadSchemaList(self.settings["datastore/name"])
            self.setSchema(self.settings["datastore/schema"])

    def loadSchemaList(self, name):
        # newfeature: get list of schemas in PostGIS database
        pass

    def setSchema(self, name):
        idx = self.datastores["schema"].index(name)
        if idx:
            self.schemaCombo.setCurrentIndex(idx)
        else:
            self.schemaCombo.setCurrentIndex(0)

    def selectSchema(self):
        txt = self.schemaCombo.currentText()
        self.datastore_schema = txt

    def openDatastore(self):
        lastDir = self.settings.getLastDir()
        if not lastDir:
            lastDir = ""
        path = ""
        name = ""
        if self.datastore_type == 0:
            path = QtGui.QFileDialog.getOpenFileName(self, "Open Spatialite data base", lastDir, "Spatialite (*.sqlite *.db)")
            if path.strip()!="":
                path = unicode(path)
                name = os.path.basename(path)
                #check if datastore with same name exists
                if self.datastores:
                    if name in self.datastores['name']:
                        self.iface.messageBar().pushMessage("Error","A database already exists with the same name.",level = 1,duration = 5)
                    #if not, create new connection in registry
                    else:
                        uf.createSpatialiteConnection(name, path)
                else:
                    uf.createSpatialiteConnection(name, path)
        elif self.datastore_type == 1:
            path = QtGui.QFileDialog.getExistingDirectory(self, "Select shape files folder", lastDir)
            if path.strip()!="":
                path = unicode(path)
                name = os.path.basename(path)
        if name != "" and path != "":
            self.appendDatastoreList(name,path)
            self.setDatastore()
            #store the path used
            self.settings.setLastDir(path)

    def newDatastore(self):
        lastDir = self.settings.getLastDir()
        if not lastDir:
            lastDir = ""
        path = ""
        name = ""
        if self.datastore_type == 0:
            path = QtGui.QFileDialog.getSaveFileName(self, "Create Spatialite data base", lastDir, "Spatialite (*.sqlite *.db)")
            if path.strip()!="":
                path = unicode(path)
                name = os.path.basename(path)
                #check if datastore with same name exists
                if self.datastores and name in self.datastores['name']:
                    self.iface.messageBar().pushMessage("Error","A database already exists with the same name.",level = 1,duration = 5)
                #if not, create new connection in registry
                else:
                    uf.createSpatialiteConnection(name, path)
                    uf.createSpatialiteDatabase(path)
        if self.datastore_type == 1:
            path = QtGui.QFileDialog.getExistingDirectory(self, "Select shape files folder ", lastDir)
            if path.strip()!="":
                path = unicode(path)
                name = os.path.basename(path)
        if path != "" and name != "":
            self.appendDatastoreList(name,path)
            self.setDatastore()
            #store the path used
            self.settings.setLastDir(path)

    def updateSettings(self):
        # this is just a quick hack for now... not clean, will revise for a more generic project manager
        self.proj_settings['datastore/type'] = self.datastore_type
        self.proj_settings['datastore/idx'] = self.datastore_idx
        self.proj_settings['datastore/name'] = self.datastore_name
        self.proj_settings['datastore/path'] = self.datastore_path
        self.proj_settings['datastore/schema'] = self.datastore_schema
        self.saveDatastoreSettings.emit(self.proj_settings)