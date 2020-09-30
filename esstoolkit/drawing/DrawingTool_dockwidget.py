# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2019-06-16
# copyright            : (C) 2019 by Space Syntax Limited
# author               : Ioanna Kolovou
# email                : i.kolovou@spaceyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" Drawing tool for axial lines, segment lines and unlinks.
"""

from __future__ import absolute_import
from __future__ import print_function

import os
from builtins import range

from qgis.PyQt import (QtWidgets, uic)
from qgis.PyQt.QtCore import (pyqtSignal, QSize)
from qgis.PyQt.QtGui import (QPixmap, QIcon)
from qgis.core import (QgsProject, QgsSnappingConfig, QgsTolerance, Qgis)

from esstoolkit.utilities import layer_field_helpers as lfh

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DrawingTool_dockwidget_base.ui'))


class DrawingToolDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(DrawingToolDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        axial_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/axial_disabled.png")
        segment_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/segment_disabled.png")
        unlink_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/unlink_disabled.png")
        self.axialButton.setIcon(QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40, 40))
        self.segmentButton.setIcon(QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))
        self.unlinksButton.setIcon(QIcon(unlink_icon))
        self.unlinksButton.setIconSize(QSize(40, 40))
        self.unlinksButton.setFixedHeight(60)
        self.unlinksButton.setFixedWidth(60)
        self.segmentButton.setFixedHeight(60)
        self.segmentButton.setFixedWidth(60)
        self.axialButton.setFixedHeight(60)
        self.axialButton.setFixedWidth(60)
        self.activatedUnlinks = 'no unlinks'
        self.unlink_mode = False
        self.axial_mode = False
        self.segment_mode = False
        self.activatedNetwork = None

        # get settings

        # if axial button checked - update snapping
        self.axialButton.clicked.connect(self.setAxialSnapping)

        # if segment button checked - update snapping
        self.segmentButton.clicked.connect(self.setSegmentSnapping)

        # if unlinks button checked - update snapping
        self.unlinksButton.clicked.connect(self.setUnlinkSnapping)

        self.toleranceSpin.setRange(1, 30)
        self.toleranceSpin.setSingleStep(1)
        self.toleranceSpin.setValue(10)

        self.settings = [None, None, 10]

        self.iface = iface

    def update_network(self):
        if self.settings[0]:
            self.resetSnapping()
        self.settings[0] = self.networkCombo.currentText()
        self.activatedNetwork = self.settings[0]
        # fix_print_with_import
        # fix_print_with_import
        print('user selected network', self.settings[0])
        combo_items = [self.networkCombo.itemText(i) for i in range(self.networkCombo.count())]
        if combo_items.count(self.settings[0]) > 1:
            self.iface.messageBar().pushMessage(
                "Drawing Tool: ",
                "Rename layers in the layers panel that have the same names!",
                level=Qgis.Warning,
                duration=5)
        if self.segment_mode:
            self.setSegmentSnapping()
        elif self.axial_mode:
            self.setAxialSnapping()
        return

    def update_unlinks(self):
        if self.settings[1]:
            self.resetSnapping()
        self.settings[1] = self.unlinksCombo.currentText()
        self.activatedUnlinks = self.settings[1]
        # fix_print_with_import
        # fix_print_with_import
        print('user selected unlinks', self.settings[1])
        combo_items = [self.unlinksCombo.itemText(i) for i in range(self.unlinksCombo.count())]
        if combo_items.count(self.settings[1]) > 1:
            self.iface.messageBar().pushMessage(
                "Drawing Tool: ",
                "Rename layers in the layers panel that have the same names!",
                level=Qgis.Warning,
                duration=5)
        if self.unlink_mode:
            self.setUnlinkSnapping()
        return

    def update_tolerance(self):
        if self.settings[0]:
            self.resetSnapping()
        self.settings[2] = self.toleranceSpin.value()
        # fix_print_with_import
        # fix_print_with_import
        print('tolerance upd', self.settings)
        return

    def setAxialSnapping(self):
        # keep button pressed

        # un press other buttons

        # disable previous snapping setting
        self.resetSnapping()

        # self.axialButton.setCheckable(True)
        self.resetIcons()
        axial_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/axial.png")
        self.axialButton.setIcon(QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40, 40))

        # snap to nothing
        if self.settings[0] != '':
            proj = QgsProject.instance()
            # fix_print_with_import
            # fix_print_with_import
            print(proj, 'ax')
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = lfh.getLayerByName(self.settings[0])
            self.iface.setActiveLayer(layer)
            # if layer.isEditable():
            #    layer.commitChanges()
            # else:
            #    layer.startEditing()
            snapConfig = QgsSnappingConfig()
            snapConfig.setMode(QgsSnappingConfig.AdvancedConfiguration)
            layerSnapConfig = QgsSnappingConfig.IndividualLayerSettings(False, QgsSnappingConfig.Vertex,
                                                                        self.settings[2], QgsTolerance.LayerUnits)
            snapConfig.setIndividualLayerSettings(layer, layerSnapConfig)
            snapConfig.setEnabled(False)
            proj.setAvoidIntersectionsLayers([layer])
            proj.setSnappingConfig(snapConfig)
            proj.setTopologicalEditing(False)
            self.axial_mode = True
        else:
            self.iface.messageBar().pushMessage("Network layer not specified!", Qgis.Critical, duration=5)
            self.axial_mode = False
        return

    def setSegmentSnapping(self):
        # disable previous snapping setting
        self.resetSnapping()
        self.resetIcons()
        segment_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/segment.png")
        self.segmentButton.setIcon(QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))

        # snap to vertex
        if self.settings[0] != '':
            proj = QgsProject.instance()
            # fix_print_with_import
            # fix_print_with_import
            print(proj, 'seg')
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = lfh.getLayerByName(self.settings[0])
            self.iface.setActiveLayer(layer)
            # if layer.isEditable():
            #    layer.commitChanges()
            # else:
            #    layer.startEditing()
            snapConfig = QgsSnappingConfig()
            snapConfig.setMode(QgsSnappingConfig.AdvancedConfiguration)
            layerSnapConfig = QgsSnappingConfig.IndividualLayerSettings(True, QgsSnappingConfig.Vertex,
                                                                        self.settings[2], QgsTolerance.LayerUnits)
            snapConfig.setIndividualLayerSettings(layer, layerSnapConfig)
            proj.setAvoidIntersectionsLayers([layer])
            snapConfig.setIntersectionSnapping(False)
            snapConfig.setEnabled(True)
            proj.setSnappingConfig(snapConfig)
            proj.setTopologicalEditing(True)
            self.segment_mode = True
        else:
            self.iface.messageBar().pushMessage("Network layer not specified!", Qgis.Critical, duration=5)
            self.segment_mode = False
        return

    def setUnlinkSnapping(self):
        # disable previous snapping setting if segment
        self.resetSnapping()

        # snap to vertex
        if self.settings[1] != 'no unlinks':
            self.resetIcons()
            unlink_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/unlink.png")
            self.unlinksButton.setIcon(QIcon(unlink_icon))
            self.unlinksButton.setIconSize(QSize(40, 40))
            proj = QgsProject.instance()
            # fix_print_with_import
            # fix_print_with_import
            print(proj, 'un')
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = lfh.getLayerByName(self.settings[0])
            unlinks_layer = lfh.getLayerByName(self.settings[1])
            # if unlinks_layer.isEditable():
            #    unlinks_layer.commitChanges()
            # else:
            #    unlinks_layer.startEditing()
            self.iface.setActiveLayer(unlinks_layer)
            snapConfig = QgsSnappingConfig()
            snapConfig.setMode(QgsSnappingConfig.AdvancedConfiguration)
            layerSnapConfig = QgsSnappingConfig.IndividualLayerSettings(True, QgsSnappingConfig.Vertex,
                                                                        self.settings[2], QgsTolerance.LayerUnits)
            snapConfig.setIndividualLayerSettings(layer, layerSnapConfig)
            proj.setAvoidIntersectionsLayers([layer])
            snapConfig.setIntersectionSnapping(True)
            snapConfig.setEnabled(True)
            QgsProject.instance().setSnappingConfig(snapConfig)
            proj.setTopologicalEditing(False)
            self.unlink_mode = True
        else:
            self.iface.messageBar().pushMessage("Unlinks layer not specified!", Qgis.Critical, duration=5)
            self.unlink_mode = False
        return

    def resetSnapping(self):
        self.unlink_mode = False
        # disable previous snapping setting
        proj = QgsProject.instance()
        snapConfig = QgsSnappingConfig()
        if self.settings[0] != '' and self.settings[0]:
            # proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = lfh.getLayerByName(self.settings[0])
            if layer:  # layer might have been removed
                snapConfig.setMode(QgsSnappingConfig.AdvancedConfiguration)
                layerSnapConfig = QgsSnappingConfig.IndividualLayerSettings(False, QgsSnappingConfig.Vertex,
                                                                            self.settings[2], QgsTolerance.LayerUnits)
                snapConfig.setIndividualLayerSettings(layer, layerSnapConfig)
                proj.setAvoidIntersectionsLayers([layer])
        if self.settings[1] != 'no unlinks' and self.settings[1]:
            # proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = lfh.getLayerByName(self.settings[1])
            if layer:
                snapConfig.setMode(QgsSnappingConfig.AdvancedConfiguration)
                layerSnapConfig = QgsSnappingConfig.IndividualLayerSettings(False, QgsSnappingConfig.Vertex,
                                                                            self.settings[2], QgsTolerance.LayerUnits)
                snapConfig.setIndividualLayerSettings(layer, layerSnapConfig)
                proj.setAvoidIntersectionsLayers([])
        snapConfig.setIntersectionSnapping(False)
        proj.setSnappingConfig(snapConfig)
        return

    def resetIcons(self):
        axial_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/axial_disabled.png")
        self.axialButton.setIcon(QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40, 40))
        segment_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/segment_disabled.png")
        self.segmentButton.setIcon(QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))
        unlink_icon = QPixmap(os.path.dirname(__file__) + "/custom_icons/unlink_disabled.png")
        self.unlinksButton.setIcon(QIcon(unlink_icon))
        self.unlinksButton.setIconSize(QSize(40, 40))
        return

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
