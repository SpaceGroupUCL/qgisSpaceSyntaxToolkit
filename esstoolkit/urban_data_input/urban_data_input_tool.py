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

from qgis.PyQt.QtCore import (QObject, QSettings, Qt)
from qgis.core import QgsProject

from .entrances import EntranceTool
from .frontages import FrontageTool
from .landuse import LanduseTool
from .urban_data_input_dockwidget import UrbanDataInputDockWidget


class UrbanDataInputTool(QObject):
    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # create the dialog objects
        self.dockwidget = UrbanDataInputDockWidget(self.iface)
        self.frontage_tool = FrontageTool(self.iface, self.dockwidget)
        self.entrance_tool = EntranceTool(self.iface, self.dockwidget)
        self.lu_tool = LanduseTool(self.iface, self.dockwidget)

        # connect to provide cleanup on closing of dockwidget
        self.dockwidget.closingPlugin.connect(self.unload_gui)

        # get current user settings
        self.user_settings = {}
        self.user_settings['crs'] = QSettings().value('/qgis/crs/use_project_crs')
        self.user_settings['attrib_dialog'] = QSettings().value(
            '/qgis/digitizing/disable_enter_attribute_values_dialog')

    def load_gui(self):
        # Overide existing QGIS settings
        if not self.user_settings['attrib_dialog']:
            QSettings().setValue('/qgis/digitizing/disable_enter_attribute_values_dialog', True)
        if not self.user_settings['crs']:
            QSettings().setValue('/qgis/crs/use_project_crs', True)

        # show the dockwidget
        # TODO: fix to allow choice of dock location
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

        # set up GUI operation signals
        # legend change connections
        self.iface.projectRead.connect(self.updateLayers)
        self.iface.newProjectCreated.connect(self.updateLayers)
        QgsProject.instance().layersRemoved.connect(self.updateLayers)
        QgsProject.instance().layersAdded.connect(self.updateLayers)
        # Frontages
        self.iface.mapCanvas().selectionChanged.connect(self.dockwidget.addDataFields)
        # Entrances
        self.iface.mapCanvas().selectionChanged.connect(self.dockwidget.addEntranceDataFields)
        # Landuse
        self.iface.mapCanvas().selectionChanged.connect(self.dockwidget.addLUDataFields)
        # Initialisation
        self.updateLayers()

    def unload_gui(self):
        # self.dockwidget.close()
        # disconnect interface signals
        try:
            # restore user settings
            QSettings().setValue('/qgis/digitizing/disable_enter_attribute_values_dialog',
                                 self.user_settings['attrib_dialog'])
            QSettings().setValue('/qgis/crs/use_project_crs', self.user_settings['crs'])

            # legend change connections
            self.iface.projectRead.disconnect(self.updateLayers)
            self.iface.newProjectCreated.disconnect(self.updateLayers)
            QgsProject.instance().layersRemoved.disconnect(self.updateLayers)
            QgsProject.instance().layersAdded.disconnect(self.updateLayers)
            # Frontages
            self.iface.mapCanvas().selectionChanged.disconnect(self.dockwidget.addDataFields)
            self.dockwidget.disconnectFrontageLayer()
            # Entrances
            self.iface.mapCanvas().selectionChanged.disconnect(self.dockwidget.addEntranceDataFields)
            self.dockwidget.disconnectEnranceLayer()
            # Landuse
            self.iface.mapCanvas().selectionChanged.disconnect(self.dockwidget.addLUDataFields)
            self.dockwidget.disconnectLULayer()
        except:
            pass

    def updateLayers(self):
        # frontages
        self.frontage_tool.updateLayers()
        self.frontage_tool.updateFrontageLayer()
        # this is not being used at the moment
        # self.frontage_tool.updateLayersPushID
        # entrances
        self.entrance_tool.updateEntranceLayer()
        # land use
        self.lu_tool.loadLULayer()
        self.lu_tool.updatebuildingLayers()
        self.lu_tool.updateLULayer()
