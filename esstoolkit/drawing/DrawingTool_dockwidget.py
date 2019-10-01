# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrawingToolDockWidget
                                 A QGIS plugin
 Drawing tool for axial lines, segment lines and unlinks.
                             -------------------
        begin                : 2019-06-16
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Space Syntax Limited
        email                : i.kolovou@spaceyntax.com
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

from PyQt4.QtCore import QThread, QSettings, pyqtSignal, Qt, QSize
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

from PyQt4 import QtGui, uic
from utility_functions import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'DrawingTool_dockwidget_base.ui'))


class DrawingToolDockWidget(QtGui.QDockWidget, FORM_CLASS):

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
        axial_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/axial_disabled.png")
        segment_icon = QtGui.QPixmap(os.path.dirname(__file__) +"/custom_icons/segment_disabled.png")
        unlink_icon = QtGui.QPixmap(os.path.dirname(__file__) +"/custom_icons/unlink_disabled.png")
        self.axialButton.setIcon(QtGui.QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40,40))
        self.segmentButton.setIcon(QtGui.QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))
        self.unlinksButton.setIcon(QtGui.QIcon(unlink_icon))
        self.unlinksButton.setIconSize(QSize(40, 40))
        self.unlinksButton.setFixedHeight(60)
        self.unlinksButton.setFixedWidth(60)
        self.segmentButton.setFixedHeight(60)
        self.segmentButton.setFixedWidth(60)
        self.axialButton.setFixedHeight(60)
        self.axialButton.setFixedWidth(60)

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
        print 'network upd', self.settings
        return

    def update_unlinks(self):
        if self.settings[1]:
            self.resetSnapping()
        self.settings[1] = self.unlinksCombo.currentText()
        print 'unlinks upd', self.settings
        return

    def update_tolerance(self):
        if self.settings[0]:
            self.resetSnapping()
        self.settings[2] = self.toleranceSpin.value()
        print 'tolerance upd', self.settings
        return

    def setAxialSnapping(self):
        # keep button pressed

        # un press other buttons

        # disable previous snapping setting
        self.resetSnapping()

        #self.axialButton.setCheckable(True)
        self.resetIcons()
        axial_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/axial.png")
        self.axialButton.setIcon(QtGui.QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40, 40))

        # snap to nothing
        if self.settings[0] != '':
            proj = QgsProject.instance()
            print proj, 'ax'
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = getLayerByName(self.settings[0])
            self.iface.setActiveLayer(layer)
            #if layer.isEditable():
            #    layer.commitChanges()
            #else:
            #    layer.startEditing()
            proj.setSnapSettingsForLayer(layer.id(), False, 0, 0, self.settings[2], True)
            proj.setTopologicalEditing(False)
        else:
            self.iface.messageBar().pushMessage("Network layer not specified!", QgsMessageBar.CRITICAL, duration=5)
        return

    def setSegmentSnapping(self):
        # disable previous snapping setting
        self.resetSnapping()
        self.resetIcons()
        segment_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/segment.png")
        self.segmentButton.setIcon(QtGui.QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))

        # snap to vertex
        if self.settings[0] != '':
            proj = QgsProject.instance()
            print proj, 'seg'
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = getLayerByName(self.settings[0])
            self.iface.setActiveLayer(layer)
            #if layer.isEditable():
            #    layer.commitChanges()
            #else:
            #    layer.startEditing()
            proj.setSnapSettingsForLayer(layer.id(), True, 0, 0, self.settings[2], True)
            proj.setTopologicalEditing(True)
            self.iface.mapCanvas().snappingUtils().setSnapOnIntersections(False)
        else:
            self.iface.messageBar().pushMessage("Network layer not specified!", QgsMessageBar.CRITICAL, duration=5)
        return

    def setUnlinkSnapping(self):
        # disable previous snapping setting if segment
        self.resetSnapping()

        # snap to vertex
        if self.settings[1] != 'no unlinks':
            self.resetIcons()
            unlink_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/unlink.png")
            self.unlinksButton.setIcon(QtGui.QIcon(unlink_icon))
            self.unlinksButton.setIconSize(QSize(40, 40))
            proj = QgsProject.instance()
            print proj, 'un'
            proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = getLayerByName(self.settings[0])
            unlinks_layer = getLayerByName(self.settings[1])
            #if unlinks_layer.isEditable():
            #    unlinks_layer.commitChanges()
            #else:
            #    unlinks_layer.startEditing()
            self.iface.setActiveLayer(unlinks_layer)
            proj.setSnapSettingsForLayer(layer.id(), True, 0, 0, self.settings[2], True)
            proj.setTopologicalEditing(False)
            self.iface.mapCanvas().snappingUtils().setSnapOnIntersections(True)
        else:
            self.iface.messageBar().pushMessage("Unlinks layer not specified!", QgsMessageBar.CRITICAL, duration=5)
        return

    def resetSnapping(self):
        # disable previous snapping setting
        if self.settings[0] != '' and self.settings[0]:
            proj = QgsProject.instance()
            #proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = getLayerByName(self.settings[0])
            if layer: # layer might have been removed
                proj.setSnapSettingsForLayer(layer.id(), False, 0, 0, self.settings[2], True)
        if self.settings[1] != 'no unlinks' and self.settings[1]:
            proj = QgsProject.instance()
            #proj.writeEntry('Digitizing', 'SnappingMode', 'advanced')
            layer = getLayerByName(self.settings[1])
            if layer:
                proj.setSnapSettingsForLayer(layer.id(), False, 0, 0, self.settings[2], False)
        self.iface.mapCanvas().snappingUtils().setSnapOnIntersections(False)
        return

    def resetIcons(self):
        axial_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/axial_disabled.png")
        self.axialButton.setIcon(QtGui.QIcon(axial_icon))
        self.axialButton.setIconSize(QSize(40, 40))
        segment_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/segment_disabled.png")
        self.segmentButton.setIcon(QtGui.QIcon(segment_icon))
        self.segmentButton.setIconSize(QSize(40, 40))
        unlink_icon = QtGui.QPixmap(os.path.dirname(__file__) + "/custom_icons/unlink_disabled.png")
        self.unlinksButton.setIcon(QtGui.QIcon(unlink_icon))
        self.unlinksButton.setIconSize(QSize(40, 40))
        return

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


