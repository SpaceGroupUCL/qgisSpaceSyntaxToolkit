# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UrbanDataInputDockWidget
                                 A QGIS plugin
 Urban Data Input Tool for QGIS
                             -------------------
        begin                : 2016-06-03
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Abhimanyu Acharya/ Space Syntax Limited
        email                : a.acharya@spacesyntax.com
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
from qgis.core import (QgsMapLayer, QgsDataSourceUri, QgsVectorLayer, QgsProject)
import os.path

def getLegendLayers(iface, geom='all', provider='all'):
    """
    Return list of layer objects in the legend, with specific geometry type and/or data provider
    :param iface: QgsInterface
    :param geom: string ('point', 'linestring', 'polygon')
    :param provider: string
    :return: list QgsVectorLayer
    """
    layers_list = []
    for layer in iface.legendInterface().layers():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.hasGeometryType() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list

def getLayersListNames(layerslist):
    layer_names = [layer.name() for layer in layerslist]
    return layer_names

def getLegendLayerByName(iface, name):
    layer = None
    for i in iface.legendInterface().layers():
        if i.name() == name:
            layer = i
    return layer

def getfieldByName(iface, name, layer):
    field = None
    for i in layer.dataProvider().fields():
        if i.name() == name:
            field = i
    return field

def getLegendLayerByIndex(iface, index):
    layer = None
    for i in iface.legendInterface().layers():
        if i.index() == index:
            layer = i
    return layer

def getFieldNames(layer):
    field_names = []
    if layer and layer.dataProvider():
        field_names = [field.name() for field in layer.dataProvider().fields()]
    return field_names

def getLayerPath(layer):
    path = ''
    provider = layer.dataProvider()
    provider_type = provider.name()
    if provider_type == 'spatialite':
        uri = QgsDataSourceUri(provider.dataSourceUri())
        path = uri.database()
    elif provider_type == 'ogr':
        uri = provider.dataSourceUri()
        path = os.path.dirname(uri)
    return path

def reloadLayer(layer):
    layer_name = layer.name()
    layer_provider = layer.dataProvider().name()
    new_layer = None
    if layer_provider in ('spatialite','postgres'):
        uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        new_layer = QgsVectorLayer(uri.uri(), layer_name, layer_provider)
    elif layer_provider == 'ogr':
        uri = layer.dataProvider().dataSourceUri()
        new_layer = QgsVectorLayer(uri.split("|")[0], layer_name, layer_provider)
    QgsProject.instance().removeMapLayer(layer.id())
    if new_layer:
        QgsProject.instance().addMapLayer(new_layer)
    return new_layer

def isRequiredLayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = getFieldNames(layer)
        if 'F_Group' in fieldlist and 'F_Type' in fieldlist:
            return True

    return False

def isRequiredEntranceLayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = getFieldNames(layer)
        if 'E_Category' in fieldlist and 'E_SubCat' in fieldlist:
            return True

    return False

def isRequiredLULayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = getFieldNames(layer)
        if 'GF_Cat' in fieldlist and 'GF_SubCat' in fieldlist:
            return True

    return False