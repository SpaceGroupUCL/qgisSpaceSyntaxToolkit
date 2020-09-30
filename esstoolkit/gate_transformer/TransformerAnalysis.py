# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-02-29
# copyright            : (C) 2016 by Space Syntax Limited
# author               : Stephen Law
# email                : s.law@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" This plugin performs basic transformation on a line in qgis.
"""

from __future__ import absolute_import

import math

from qgis.PyQt.QtCore import QObject
from qgis.core import (QgsProject, QgsMapLayer, QgsWkbTypes, QgsFeature, QgsGeometry, QgsPoint)

from esstoolkit.utilities import gui_helpers as guih
from esstoolkit.utilities.exceptions import BadInputError
from .network_transformer_dialog import NetworkTransformerDialog


# analysis class
class GateTransformer(QObject):

    # initialise class with self and iface
    def __init__(self, iface):
        QObject.__init__(self)

        self.iface = iface

        # create the dialog object
        self.dlg = NetworkTransformerDialog()
        # setup signals with the transformation method
        self.dlg.run_button.clicked.connect(self.run_method)
        self.dlg.close_button.clicked.connect(self.close_method)

    # prepare the dialog
    def load_gui(self):
        # put current layers into comboBox
        self.dlg.update_layer(GateTransformer.get_layers())
        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        # result = self.dlg.exec_()

    def unload_gui(self):
        if self.dlg:
            self.dlg.run_button.clicked.disconnect(self.run_method)
            self.dlg.close_button.clicked.disconnect(self.close_method)

    @staticmethod
    def get_layers():
        layers = list(QgsProject.instance().mapLayers().values())
        layer_objects = []
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QgsWkbTypes.LineGeometry:
                layer_objects.append((layer.name(), layer))

        return layer_objects

    def run_method(self):
        layer = self.dlg.get_layer()
        transformation, value = self.dlg.get_transformation()

        try:
            if transformation == 1:
                self.rotate_line(layer, value)

            elif transformation == 2:
                self.resize_line(layer, value)

            elif transformation == 3:
                self.rescale_line(layer, value)
        except BadInputError as e:
            guih.showMessage(self.iface, str(e))

        # self.close_method()

    def close_method(self):
        self.dlg.close()

    @staticmethod
    def check_singlepart_lines(layer):

        # do not allow non-line layers
        if layer.geometryType() != QgsWkbTypes.LineGeometry:
            raise BadInputError("Only line layers can be resized")

        # QGis 3 imports shapefiles as MultiLineStrings by default so this check only fails if there are actually
        # multi-part features or if a linestring contains more than two vertices
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if geom.isMultipart():  # line is multi-part, pick first part
                polys = geom.asMultiPolyline()
                if len(polys) == 0:
                    raise BadInputError(
                        "Feature with id " + str(feature.id()) + " has no line geometry, please correct")
                if len(polys) > 1:
                    raise BadInputError(
                        "Feature with id " + str(feature.id()) +
                        " contains more than 1 line, please correct")
                pt = polys[0]
            else:
                pt = geom.asPolyline()
            if len(pt) < 2:
                raise BadInputError(
                    "Line with id " + str(feature.id()) + " has fewer than 2 vertices, please correct")
            if len(pt) > 2:
                raise BadInputError(
                    "Line with id " + str(feature.id()) + " has more than 2 vertices, please correct")

    @staticmethod
    def rotate_line(layer, value):

        layer.startEditing()
        layer.selectAll()
        set_angle = value

        for i in layer.selectedFeatures():
            geom = i.geometry()
            geom.rotate(set_angle, geom.centroid().asPoint())
            layer.changeGeometry(i.id(), geom)

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()

    @staticmethod
    def resize_line(layer, value):

        GateTransformer.check_singlepart_lines(layer)

        layer.startEditing()
        layer.selectAll()

        set_length = value

        for feature in layer.selectedFeatures():
            geom = feature.geometry()
            if geom.isMultipart():  # line is multi-part, pick first part
                pt = geom.asMultiPolyline()[0]
            else:
                pt = geom.asPolyline()
            dy = pt[1][1] - pt[0][1]
            dx = pt[1][0] - pt[0][0]
            angle = math.atan2(dy, dx)
            length = geom.length()
            startx = geom.centroid().asPoint()[0] + ((0.5 * length * set_length / length) * math.cos(angle))
            starty = geom.centroid().asPoint()[1] + ((0.5 * length * set_length / length) * math.sin(angle))
            endx = geom.centroid().asPoint()[0] - ((0.5 * length * set_length / length) * math.cos(angle))
            endy = geom.centroid().asPoint()[1] - ((0.5 * length * set_length / length) * math.sin(angle))
            n_geom = QgsFeature()
            n_geom.setGeometry(QgsGeometry.fromPolyline([QgsPoint(startx, starty), QgsPoint(endx, endy)]))
            layer.changeGeometry(feature.id(), n_geom.geometry())

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()

    @staticmethod
    def rescale_line(layer, value):

        GateTransformer.check_singlepart_lines(layer)

        layer.startEditing()
        layer.selectAll()

        set_scale = value

        for feature in layer.selectedFeatures():
            geom = feature.geometry()
            if geom.isMultipart():  # line is multi-part, pick first part
                pt = geom.asMultiPolyline()[0]
            else:
                pt = geom.asPolyline()
            dy = pt[1][1] - pt[0][1]
            dx = pt[1][0] - pt[0][0]
            angle = math.atan2(dy, dx)
            length = geom.length()
            startx = geom.centroid().asPoint()[0] + ((0.5 * length * set_scale) * math.cos(angle))
            starty = geom.centroid().asPoint()[1] + ((0.5 * length * set_scale) * math.sin(angle))
            endx = geom.centroid().asPoint()[0] - ((0.5 * length * set_scale) * math.cos(angle))
            endy = geom.centroid().asPoint()[1] - ((0.5 * length * set_scale) * math.sin(angle))
            new_geom = QgsFeature()
            new_geom.setGeometry(QgsGeometry.fromPolyline([QgsPoint(startx, starty), QgsPoint(endx, endy)]))
            layer.changeGeometry(feature.id(), new_geom.geometry())

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()
