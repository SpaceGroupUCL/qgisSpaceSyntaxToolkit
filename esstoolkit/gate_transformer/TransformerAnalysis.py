# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GateTransformer
                                 A QGIS plugin
 This plugin performs basic transformation on a line in qgis.
                              -------------------
        begin                : 2016-02-29
        author               : Stephen Law
        copyright            : (C) 2016 by Space Syntax Limited
        email                : s.law@spacesyntax.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from PyQt4.QtCore import *
from qgis.core import *
import math

from .network_transformer_dialog import NetworkTransformerDialog

# analysis class
class GateTransformer(QObject):

    # initialise class with self and iface
    def __init__(self,iface):
        QObject.__init__(self)

        self.iface=iface

        # create the dialog object
        self.dlg = NetworkTransformerDialog()
        # setup signals with the transformation method
        self.dlg.run_button.clicked.connect(self.run_method)
        self.dlg.close_button.clicked.connect(self.close_method)

    # prepare the dialog
    def load_gui(self):
        # put current layers into comboBox
        self.dlg.update_layer(self.get_layers())
        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        #result = self.dlg.exec_()

    def unload_gui(self):
        if self.dlg:
            self.dlg.run_button.clicked.disconnect(self.run_method)
            self.dlg.close_button.clicked.disconnect(self.close_method)

    def get_layers(self):
        layers = list(QgsMapLayerRegistry.instance().mapLayers().values())
        layer_objects = []
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Line:
                layer_objects.append((layer.name(), layer))

        return layer_objects

    ################################# run and close methods #############################
    def run_method(self):
        layer = self.dlg.get_layer()
        transformation, value = self.dlg.get_transformation()

        if transformation == 1:
            self.rotate_line02(layer, value)
            #self.close_method()

        elif transformation == 2:
            self.resize_line02(layer, value)
            #self.close_method()

        elif transformation == 3:
            self.rescale_line02(layer, value)
            #self.close_method()

        # self.close_method()

    def close_method(self):
        self.dlg.close()


    ########################### transformation block ########################
    # rotate_line_scripts
    def rotate_line02(self,layer,value):

        layer.startEditing()
        layer.selectAll()
        set_angle = value

        for i in layer.selectedFeatures():
            geom=i.geometry()
            geom.rotate(set_angle,QgsPoint(geom.centroid().asPoint()))
            layer.changeGeometry(i.id(),geom)

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()

    # resize_line_scripts
    def resize_line02(self,layer,value):

        layer.startEditing()
        layer.selectAll()

        set_length=value

        for i in layer.selectedFeatures():
            geom=i.geometry()
            pt=geom.asPolyline()
            dy=pt[1][1] - pt[0][1]
            dx=pt[1][0] - pt[0][0]
            angle = math.atan2(dy,dx)
            length=geom.length()
            startx=geom.centroid().asPoint()[0]+((0.5*length*set_length/length)*math.cos(angle))
            starty=geom.centroid().asPoint()[1]+((0.5*length*set_length/length)*math.sin(angle))
            endx=geom.centroid().asPoint()[0]-((0.5*length*set_length/length)*math.cos(angle))
            endy=geom.centroid().asPoint()[1]-((0.5*length*set_length/length)*math.sin(angle))
            n_geom=QgsFeature()
            n_geom.setGeometry(QgsGeometry.fromPolyline([QgsPoint(startx,starty),QgsPoint(endx,endy)]))
            layer.changeGeometry(i.id(),n_geom.geometry())

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()

    # rescale_line_scripts
    def rescale_line02(self,layer,value):

        layer.startEditing()
        layer.selectAll()

        set_scale=value

        for i in layer.selectedFeatures():
            geom=i.geometry()
            pt=geom.asPolyline()
            dy=pt[1][1] - pt[0][1]
            dx=pt[1][0] - pt[0][0]
            angle = math.atan2(dy,dx)
            length=geom.length()
            startx=geom.centroid().asPoint()[0]+((0.5*length*set_scale)*math.cos(angle))
            starty=geom.centroid().asPoint()[1]+((0.5*length*set_scale)*math.sin(angle))
            endx=geom.centroid().asPoint()[0]-((0.5*length*set_scale)*math.cos(angle))
            endy=geom.centroid().asPoint()[1]-((0.5*length*set_scale)*math.sin(angle))
            new_geom=QgsFeature()
            new_geom.setGeometry(QgsGeometry.fromPolyline([QgsPoint(startx,starty),QgsPoint(endx,endy)]))
            layer.changeGeometry(i.id(),new_geom.geometry())

        layer.updateExtents()
        layer.reload()
        layer.removeSelection()
