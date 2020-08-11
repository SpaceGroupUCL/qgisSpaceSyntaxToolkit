# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CatchmentAnalyser
                             Catchment Analyser
 Network based catchment analysis
                              -------------------
        begin                : 2016-05-19
        author               : Laurens Versluis
        copyright            : (C) 2016 by Space Syntax Limited
        email                : l.versluis@spacesyntax.com
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

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsProject, QgsMapLayer, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsVectorFileWriter)

def getLegendLayers(iface, geom='all', provider='all'):
    """geometry types: 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon"""
    layers_list = []
    for layer in QgsProject.instance().mapLayers().values():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list

def getLegendLayersNames(iface, geom='all', provider='all'):
    """geometry types: 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon"""
    layers_list = []
    for layer in QgsProject.instance().mapLayers().values():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer.name())
    return layers_list


def getLegendLayerByName(iface, name):
    layer = None
    for i in QgsProject.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer

def getNumericFieldNames(layer, type='all'):
    field_names = []
    if type == 'all':
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong)
    else:
        types = [type]
    if layer and layer.dataProvider():
        for field in layer.dataProvider().fields():
            if field.type() in types:
                field_names.append(field.name())
    return field_names

def getFieldNames(layer):
    field_names = []
    if layer and layer.dataProvider():
        for field in layer.dataProvider().fields():
            field_names.append(field.name())
    return field_names


def createTempLayer(name, geometry, srid, attributes, types):
    # Geometry can be 'POINT', 'LINESTRING' or 'POLYGON' or the 'MULTI' version of the previous
    vlayer = QgsVectorLayer('%s?crs=EPSG:%s' % (geometry, srid), name, "memory")
    provider = vlayer.dataProvider()

    # Create the required fields
    if attributes:
        vlayer.startEditing()
        fields = []
        for i, att in enumerate(attributes):
            fields.append(QgsField(att, types[i]))

        # add the fields to the layer
        try:
            provider.addAttributes(fields)
        except:
            return None
        vlayer.commitChanges()

    return vlayer


def insertTempFeatures(layer, geometry, attributes):
    provider = layer.dataProvider()
    geometry_type = provider.geometryType()
    for i, geom in enumerate(geometry):
        fet = QgsFeature()
        if geometry_type in (1, 4):
            fet.setGeometry(QgsGeometry.fromPoint(geom))
        elif geometry_type in (2, 5):
            fet.setGeometry(QgsGeometry.fromPolyline(geom))
        elif geometry_type in (3, 6):
            fet.setGeometry(QgsGeometry.fromPolygon(geom))
        if attributes:
            fet.setAttributes(attributes[i])
        provider.addFeatures([fet])
    provider.updateExtents()


def createShapeFile(layer, path, crs):
    shapefile = QgsVectorFileWriter.writeAsVectorFormat(
        layer,
        r"%s" % path,
        "utf-8",
        crs,
        "ESRI Shapefile"
    )
    return shapefile