# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# copyright            : (C) 2020 Petros Koutsolampros, Space Syntax Ltd.
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import print_function

import os.path
from builtins import str
from builtins import zip

from qgis.PyQt.QtCore import (QVariant)
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsProject, QgsMapLayer, QgsDataSourceUri, QgsVectorLayer, QgsVectorDataProvider, QgsField,
                       QgsPoint, QgsGeometry, QgsFeature, QgsFeatureRequest, QgsSpatialIndex, NULL, QgsWkbTypes)


# from pyspatialite import dbapi2 as sqlite


# ------------------------------
# QGIS layer and field handling functions
# ------------------------------
# QGIS enum types reference
# geometry types:
# 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon
# providers:
# 'ogr'; 'spatialite'; 'postgis'


# ------------------------------
# Layer functions
# ------------------------------
def getVectorLayers(geom='all', provider='all'):
    """Return list of valid QgsVectorLayer in QgsProject, with specific geometry type and/or data provider"""
    layers_list = []
    for layer in list(QgsProject.instance().mapLayers().values()):
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list


def getLegendLayers(iface, geom='all', provider='all'):
    """
    Return list of layer objects in the legend, with specific geometry type and/or data provider
    :param iface: QgsInterface
    :param geom: string ('point', 'linestring', 'polygon')
    :param provider: string
    :return: list QgsVectorLayer
    """
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


def getCanvasLayers(iface, geom='all', provider='all'):
    """Return list of valid QgsVectorLayer in QgsMapCanvas, with specific geometry type and/or data provider"""
    layers_list = []
    for layer in iface.mapCanvas().layers():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list


def getLineLayers():
    """Get a list of QgsVectorLayer that are of Line geometry"""
    layers_list = []
    for layer in QgsProject.instance().mapLayers().values():
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (layer.geometryType() == QgsWkbTypes.LineGeometry):
                layers_list.append(layer.name())
    return layers_list


def getPointPolygonLayers():
    """Get a list of QgsVectorLayer that are of Point or Polygon geometry"""
    layers_list = []
    for layer in QgsProject.instance().mapLayers().values():
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.isSpatial() and (layer.geometryType() in [QgsWkbTypes.PointGeometry,
                                                               QgsWkbTypes.PolygonGeometry]):
                layers_list.append(layer.name())
    return layers_list


def isLayerProjected(layer):
    projected = False
    if layer:
        projected = not layer.crs().isGeographic()
    return projected


def getLayerByName(name):
    layer = None
    for i in list(QgsProject.instance().mapLayers().values()):
        if i.name() == name:
            layer = i
    return layer


def getLegendLayerByName(iface, name):
    layer = None
    for i in QgsProject.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer


def getCanvasLayerByName(iface, name):
    layer = None
    for i in iface.mapCanvas().layers():
        if i.name() == name:
            layer = i
    return layer


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
    if layer_provider in ('spatialite', 'postgres'):
        uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        new_layer = QgsVectorLayer(uri.uri(), layer_name, layer_provider)
    elif layer_provider == 'ogr':
        uri = layer.dataProvider().dataSourceUri()
        new_layer = QgsVectorLayer(uri.split("|")[0], layer_name, layer_provider)
    QgsProject.instance().removeMapLayer(layer.id())
    if new_layer:
        QgsProject.instance().addMapLayer(new_layer)
    return new_layer


def layerHasFields(layer, fields):
    return set(fields).issubset(getFieldNames(layer))


# ------------------------------
# Field functions
# ------------------------------
def fieldExists(layer, name):
    fields = getFieldNames(layer)
    if name in fields:
        return True
    else:
        return False


def getFieldNames(layer):
    fields_list = []
    if layer and layer.dataProvider():
        fields_list = [field.name() for field in layer.dataProvider().fields()]
    return fields_list


def getNumericFields(layer, type='all'):
    fields = []
    if type == 'all':
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong)
    else:
        types = type
    if layer and layer.dataProvider():
        for field in layer.dataProvider().fields():
            if field.type() in types:
                fields.append(field)
    return fields


def getNumericFieldNames(layer, type='all'):
    field_names = []
    field_indices = []
    if type == 'all':
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong)
    else:
        types = [type]
    if layer and layer.dataProvider():
        for index, field in enumerate(layer.dataProvider().fields()):
            if field.type() in types:
                field_names.append(field.name())
                field_indices.append(index)
    return field_names, field_indices


def getValidFieldNames(layer, type='all', null='any'):
    field_names = {}
    if type == 'all':
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong, QVariant.String,
                 QVariant.Char)
    else:
        types = type
    if layer and layer.dataProvider():
        for index, field in enumerate(layer.dataProvider().fields()):
            if field.type() in types:
                # exclude layers that only have NULL values
                if null == 'all':
                    maxval = layer.maximumValue(index)
                    minval = layer.minimumValue(index)
                    if maxval != NULL and minval != NULL:
                        field_names[field.name()] = index
                # exclude layers with any NULL values
                elif null == 'any':
                    vals = layer.uniqueValues(index, 2)
                    if len(vals) > 0 and vals[0] != NULL:
                        field_names[field.name()] = index
    return field_names


def getFieldIndex(layer, name):
    idx = layer.dataProvider().fields().indexFromName(name)
    return idx


def fieldHasValues(layer, name):
    if layer and fieldExists(layer, name):
        # find fields that only have NULL values
        idx = getFieldIndex(layer, name)
        maxval = layer.maximumValue(idx)
        minval = layer.minimumValue(idx)
        if maxval == NULL and minval == NULL:
            return False
        else:
            return True


def getUniqueValuesNumber(layer, name):
    total = 0
    if layer and fieldExists(layer, name):
        idx = layer.dataProvider().fields().indexFromName(name)
        unique = layer.uniqueValues(idx)
        total = len(unique)
    return total


def fieldHasNullValues(layer, name):
    if layer and fieldExists(layer, name):
        idx = getFieldIndex(layer, name)
        vals = layer.uniqueValues(idx, 1)
        # depending on the provider list is empty or has NULL value in first position
        if len(vals) == 0 or (len(vals) == 1 and next(iter(vals)) == NULL):
            return True
        else:
            return False


def getFieldValues(layer, fieldname, null=True, selection=False):
    attributes = []
    ids = []
    # field_values = {}
    if fieldExists(layer, fieldname):
        if selection:
            features = layer.selectedFeatures()
        else:
            request = QgsFeatureRequest().setSubsetOfAttributes([getFieldIndex(layer, fieldname)])
            features = layer.getFeatures(request)
        if null:
            for feature in features:
                # field_values[str(feature.id())] = feature.attribute(fieldname)
                attributes.append(feature.attribute(fieldname))
                ids.append(feature.id())
        else:
            for feature in features:
                val = feature.attribute(fieldname)
                if val != NULL:
                    # field_values[str(feature.id())] = val
                    attributes.append(val)
                    ids.append(feature.id())
        # field_values['id'] = ids
        # field_values[fieldname] = attributes
    return attributes, ids


def getFieldsListValues(layer, fieldnames, null=True, selection=False):
    attributes = []
    ids = []
    field_values = {}
    fields = [field for field in fieldnames if fieldExists(layer, field)]
    idx = [getFieldIndex(layer, field) for field in fields]
    if selection:
        features = layer.selectedFeatures()
    else:
        request = QgsFeatureRequest().setSubsetOfAttributes(idx)
        features = layer.getFeatures(request)
    if features:
        if null:
            for feature in features:
                val = [feature.attributes()[i] for i in idx]
                attributes.append(val)
                ids.append(feature.id())
        else:
            for feature in features:
                val = [feature.attributes()[i] for i in idx]
                if False not in [False for x in val if x == NULL]:
                    attributes.append(val)
                    ids.append(feature.id())
        field_values['id'] = ids
        values = list(zip(*attributes))
        for seq, field in enumerate(fields):
            field_values[str(field)] = values[seq]
    else:
        field_values['id'] = []
        for field in fields:
            field_values[str(field)] = []
    return field_values


def getIdField(layer):
    pk = layer.dataProvider().pkAttributeIndexes()
    if len(pk) > 0:
        user_id = layer.dataProvider().fields().field(pk[0]).name()
    else:
        names, idxs = getNumericFieldNames(layer)
        user_id = ''
        standard_id = ("pk", "pkuid", "pkid", "pk_id", "pk id", "sid", "uid", "fid", "id", "ref")
        # look for user defined ID, take first found
        for field in names:
            if field.lower() in standard_id:
                if isValidIdField(layer, field):
                    user_id = field
                    break
    return user_id


def getIdFieldNames(layer):
    user_ids = []
    # first id will be the primary key
    pk = layer.dataProvider().pkAttributeIndexes()
    if len(pk) > 0:
        user_ids.append(layer.dataProvider().fields().field(pk[0]).name())
    # followed by other ids
    names, idxs = getNumericFieldNames(layer)
    standard_id = ("pk", "pkuid", "pkid", "pk_id", "pk id", "sid", "uid", "fid", "id", "ref")
    # look for user defined ID, take first found
    for field in names:
        if field.lower() in standard_id and field.lower() not in user_ids:
            user_ids.append(field)
    return user_ids


def isValidIdField(layer, name):
    count = layer.featureCount()
    unique = getUniqueValuesNumber(layer, name)
    if count == unique and not fieldHasNullValues(layer, name):
        return True
    else:
        return False


def addFields(layer, names, types):
    res = False
    if layer:
        provider = layer.dataProvider()
        caps = provider.capabilities()
        if caps & QgsVectorDataProvider.AddAttributes:
            fields = provider.fields()
            for i, name in enumerate(names):
                # add new field if it doesn't exist
                if fields.indexFromName(name) == -1:
                    res = provider.addAttributes([QgsField(name, types[i])])
        # apply changes if any made
        if res:
            layer.updateFields()
    return res


# ------------------------------
# Feature functions
# ------------------------------
def getFeaturesListValues(layer, name, values=list):
    features = {}
    if layer:
        if fieldExists(layer, name):
            request = QgsFeatureRequest().setSubsetOfAttributes([getFieldIndex(layer, name)])
            iterator = layer.getFeatures(request)
            for feature in iterator:
                att = feature.attribute(name)
                if att in values:
                    features[feature.id()] = att
    return features


def getFeaturesRangeValues(layer, name, min, max):
    features = {}
    if layer:
        if fieldExists(layer, name):
            request = QgsFeatureRequest().setSubsetOfAttributes([getFieldIndex(layer, name)])
            iterator = layer.getFeatures(request)
            for feature in iterator:
                att = feature.attribute(name)
                if min <= att <= max:
                    features[feature.id()] = att
    return features


def getAllFeatures(layer):
    allfeatures = {}
    if layer:
        features = layer.getFeatures()
        allfeatures = {feature.id(): feature for feature in features}
    return allfeatures


def getAllFeatureIds(layer):
    ids = []
    if layer:
        features = layer.getFeatures()
        ids = [feature.id() for feature in features]
    return ids


def getAllFeatureSymbols(layer):
    symbols = {}
    if layer:
        renderer = layer.renderer()
        features = layer.getFeatures()
        for feature in features:
            symb = renderer.symbolsForFeature(feature)
            if len(symb) > 0:
                symbols = {feature.id(): symb[0].color()}
            else:
                symbols = {feature.id(): QColor(200, 200, 200, 255)}
    return symbols


def getAllFeatureData(layer):
    data = {}
    symbols = {}
    if layer:
        renderer = layer.renderer()
        features = layer.getFeatures()
        for feature in features:
            data = {feature.id(): feature}
            symb = renderer.symbolsForFeature(feature)
            if len(symb) > 0:
                symbols = {feature.id(): symb[0].color()}
            else:
                symbols = {feature.id(): QColor(200, 200, 200, 255)}
    return data, symbols


# ------------------------------
# Creation functions
# ------------------------------
def createTempLayer(name, srid, attributes, types, values, coords):
    # create an instance of a memory vector layer
    type = ''
    if len(coords) == 2:
        type = 'Point'
    elif len(coords) == 4:
        type = 'LineString'
    vlayer = QgsVectorLayer('%s?crs=EPSG:%s' % (type, srid), name, "memory")
    provider = vlayer.dataProvider()
    # create the required fields
    fields = []
    for i, name in enumerate(attributes):
        fields.append(QgsField(name, types[i]))
    # add the fields to the layer
    vlayer.startEditing()
    try:
        provider.addAttributes(fields)
    except:
        return None
    # add features by iterating the values
    features = []
    for i, val in enumerate(values):
        feat = QgsFeature()
        # add geometry
        try:
            if type == 'Point':
                feat.setGeometry(QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]), float(val[coords[1]]))]))
            elif type == 'LineString':
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]), float(val[coords[1]])),
                                                           QgsPoint(float(val[coords[2]]), float(val[coords[3]]))]))
        except:
            pass
        # add attribute values
        feat.setAttributes(list(val))
        features.append(feat)
    # add the features to the layer
    try:
        provider.addFeatures(features)
    except:
        return None

    vlayer.commitChanges()
    vlayer.updateExtents()
    if not vlayer.isValid():
        print("Layer failed to load!")
        return None
    return vlayer


# Function to create a spatial index for QgsVectorDataProvider
def createIndex(layer):
    provider = layer.dataProvider()
    caps = provider.capabilities()
    if caps & QgsVectorDataProvider.CreateSpatialIndex:
        feat = QgsFeature()
        index = QgsSpatialIndex()
        fit = provider.getFeatures()
        while fit.nextFeature(feat):
            index.addFeature(feat)
        return index
    else:
        return None


# Function to build a topology from line layer
def buildTopology(self, axial, unlinks, links):
    index = createIndex(axial)
    axial_links = []
    unlinks_list = []
    links_list = []
    # get unlinks pairs
    if unlinks:
        features = unlinks.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1', 'line2'], unlinks.fields()))
        for feature in features:
            unlinks_list.append((feature.attribute('line1'), feature.attribute('line2')))
    # get links pairs
    if links:
        features = links.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1', 'line2'], links.fields()))
        for feature in features:
            links_list.append((feature.attribute('line1'), feature.attribute('line2')))
    # get axial intersections
    features = axial.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([]))
    for feature in features:
        geom = feature.geometry()
        id = feature.id()
        box = geom.boundingBox()
        request = QgsFeatureRequest()
        if index:
            # should be faster to retrieve from index (if available)
            ints = index.intersects(box)
            request.setFilterFids(ints)
        else:
            # can retrieve objects using bounding box
            request.setFilterRect(box)
        request.setSubsetOfAttributes([])
        targets = axial.getFeatures(request)
        for target in targets:
            geom_b = target.geometry()
            id_b = target.id()
            if not id_b == id and geom.intersects(geom_b):
                # check if in the unlinks
                if (id, id_b) not in unlinks_list and (id, id_b) not in unlinks_list:
                    axial_links.append((id, id_b))
    return axial_links
