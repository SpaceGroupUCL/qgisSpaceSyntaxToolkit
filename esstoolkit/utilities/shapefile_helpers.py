# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015, UCL
# author               : Jorge Gil, Petros Koutsolampros
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

""" Helper functions for dealing with ESRI Shapefiles
"""

from __future__ import print_function

import os.path

from qgis.core import (QgsVectorLayer, QgsVectorDataProvider, QgsFields, QgsField, QgsPoint, QgsGeometry, QgsFeature,
                       QgsVectorFileWriter, QgsCoordinateTransformContext, QgsWkbTypes)

from . import layer_field_helpers as lfh


# from pyspatialite import dbapi2 as sqlite

# ---------------------------------------------
# Shape file specific functions
# ---------------------------------------------
def listShapeFolders():
    # get folder name and path of open layers
    res = dict()
    res['idx'] = 0
    res['name'] = []
    res['path'] = []
    layers = lfh.getVectorLayers('all', 'ogr')
    for layer in layers:
        provider = layer.dataProvider()
        if layer.storageType() == 'ESRI Shapefile':
            path = os.path.dirname(layer.dataProvider().dataSourceUri())
            try:
                idx = res['path'].index(path)
            except:
                res['name'].append(os.path.basename(os.path.normpath(path)))  # layer.name()
                res['path'].append(path)
            # for the file name: os.path.basename(uri).split('|')[0]
    # case: no folders available
    if len(res['name']) < 1:
        res = None
    # return the result even if empty
    return res


def testShapeFileExists(path, name):
    filename = path + "/" + name + ".shp"
    exists = os.path.isfile(filename)
    return exists


def copyLayerToShapeFile(layer, path, name):
    # Get layer provider
    provider = layer.dataProvider()
    filename = path + "/" + name + ".shp"
    fields = provider.fields()
    if layer.isSpatial():
        geometry = layer.wkbType()
    else:
        geometry = None
    srid = layer.crs()
    # create an instance of vector file writer, which will create the vector file.
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = 'utf-8'
    writer = QgsVectorFileWriter.create(filename, fields, geometry, srid, QgsCoordinateTransformContext(), options)
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print("Error when creating shapefile: ", writer.hasError())
        return None
    # add features by iterating the values
    for feat in layer.getFeatures():
        writer.addFeature(feat)
    # delete the writer to flush features to disk
    del writer
    # open the newly created file
    vlayer = QgsVectorLayer(filename, name, "ogr")
    if not vlayer.isValid():
        print("Layer failed to load!")
        return None
    return vlayer


def create_shapefile_full_layer_data_provider(path, name, srid, attributes, types, values, coords):
    """
    Creates a shapefile using the Shapefile Data Provider

    Parameters
    ----------
    path : `str`
        folder where the shapefile is to be saved
    name : `str`
        name of the shapefile
    srid : `str`
        CRS of the newly created shapefile
    attributes: array_like
        list of attribute (field) names
    types : array_like
        list of types (field) types, in sync with the `attributes` parameter
    values : array_like
        coordinates and attribute data, one array for each feature (F, C + A),
        F for features, C for coordinates and A for attribute data
    coords : array_like
        indices of the coordinate values within the `values` array

    Returns
    -------
    vl : `QgsVectorLayer`
        the newly-created layer

    """
    # create new layer with given attributes
    filename = path + "/" + name + ".shp"

    # create an instance of vector file writer, which will create the vector file.
    writer = None
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = 'utf-8'
    if len(coords) == 2:
        type = 'point'
        writer = QgsVectorFileWriter.create(filename, QgsFields(), QgsWkbTypes.Point, srid,
                                            QgsCoordinateTransformContext(), options)
    elif len(coords) == 4:
        type = 'line'
        writer = QgsVectorFileWriter.create(filename, QgsFields(), QgsWkbTypes.LineString, srid,
                                            QgsCoordinateTransformContext(), options)
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print("Error when creating shapefile: ", writer.hasError())
        return None
    del writer
    # open the newly created file
    vl = QgsVectorLayer(filename, name, "ogr")

    pr = vl.dataProvider()

    # create the required fields
    for i, attr in enumerate(attributes):
        pr.addAttributes([QgsField(attr, types[i])])
    vl.commitChanges()
    # add features by iterating the values
    feat = QgsFeature()
    for i, val in enumerate(values):
        # add geometry
        try:
            if type == 'point':
                geometry = QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]),
                                                           float(val[coords[1]]))])
            elif type == 'line':
                geometry = QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]),
                                                              float(val[coords[1]])),
                                                     QgsPoint(float(val[coords[2]]),
                                                              float(val[coords[3]]))])
            feat.setGeometry(geometry)
        except:
            pass
        # add attributes
        attrs = []
        for j, attr in enumerate(attributes):
            attrs.append(val[j])
        feat.setAttributes(attrs)
        pr.addFeature(feat)
    vl.updateExtents()

    vl = QgsVectorLayer(filename, name, "ogr")

    if not vl.isValid():
        raise IOError("Layer could not be created")
        return None
    return vl


def create_shapefile_full_layer_writer(path, name, srid, attributes, types, values, coords):
    """
    Creates a shapefile using the QGIS QgsVectorFileWriter

    Parameters
    ----------
    path : `str`
        folder where the shapefile is to be saved
    name : `str`
        name of the shapefile
    srid : `str`
        CRS of the newly created shapefile
    attributes: array_like
        list of attribute (field) names
    types : array_like
        list of types (field) types, in sync with the `attributes` parameter
    values : array_like
        coordinates and attribute data, one array for each feature (F, C + A),
        F for features, C for coordinates and A for attribute data
    coords : array_like
        indices of the coordinate values within the `values` array

    Returns
    -------
    vl : `QgsVectorLayer`
        the newly-created layer

    """
    # create new layer with given attributes
    filename = path + "/" + name + ".shp"
    # create the required fields
    fields = QgsFields()
    for i, attr in enumerate(attributes):
        fields.append(QgsField(attr, types[i]))
    # create an instance of vector file writer, which will create the vector file.
    writer = None
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = 'utf-8'
    if len(coords) == 2:
        type = 'point'
        writer = QgsVectorFileWriter.create(filename, fields, QgsWkbTypes.Point, srid,
                                            QgsCoordinateTransformContext(), options)
    elif len(coords) == 4:
        type = 'line'
        writer = QgsVectorFileWriter.create(filename, fields, QgsWkbTypes.LineString, srid,
                                            QgsCoordinateTransformContext(), options)
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print("Error when creating shapefile: ", writer.hasError())
        return None
    # add features by iterating the values
    feat = QgsFeature()
    for i, val in enumerate(values):
        # add geometry
        try:
            if type == 'point':
                geometry = QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]),
                                                           float(val[coords[1]]))])
            elif type == 'line':
                geometry = QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]),
                                                              float(val[coords[1]])),
                                                     QgsPoint(float(val[coords[2]]),
                                                              float(val[coords[3]]))])
            feat.setGeometry(geometry)
        except:
            pass
        # add attributes
        attrs = []
        for j, attr in enumerate(attributes):
            attrs.append(val[j])
        feat.setAttributes(attrs)
        writer.addFeature(feat)
    # delete the writer to flush features to disk (optional)
    del writer
    # open the newly created file
    vlayer = QgsVectorLayer(filename, name, "ogr")
    if not vlayer.isValid():
        print("Layer failed to load!")
        return None
    return vlayer


def createShapeFileLayer(path, name, srid, attributes, types, geometrytype):
    # create new layer with given attributes
    # todo: created table has no attributes. not used
    # use createShapeFileFullLayer instead
    filename = path + "/" + name + ".shp"
    # create the required fields
    fields = QgsFields()
    for i, attr in enumerate(attributes):
        fields.append(QgsField(attr, types[i]))
    # create an instance of vector file writer, which will create the vector file.
    writer = None
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = 'utf-8'
    if 'point' in geometrytype.lower():
        writer = QgsVectorFileWriter.create(filename, fields, QgsWkbTypes.Point, srid, QgsCoordinateTransformContext(),
                                            options)
    elif 'line' in geometrytype.lower():
        writer = QgsVectorFileWriter.create(filename, fields, QgsWkbTypes.LineString, srid,
                                            QgsCoordinateTransformContext(), options)
    elif 'polygon' in geometrytype.lower():
        writer = QgsVectorFileWriter.create(filename, fields, QgsWkbTypes.Polygon, srid,
                                            QgsCoordinateTransformContext(), options)
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print("Error when creating shapefile: ", writer.hasError())
        return None
    # delete the writer to flush features to disk (optional)
    del writer
    # open the newly created file
    vlayer = QgsVectorLayer(filename, name, "ogr")
    if not vlayer.isValid():
        print("Layer failed to open!")
        return None
    return vlayer


def insertShapeFileValues(layer, attributes, values, coords):
    # get the geometry type
    # todo: not working yet. attribute ids must match those from table.
    # use createShapeFileFullLayer instead
    res = False
    if layer:
        geom_type = layer.geometryType()
        provider = layer.dataProvider()
        caps = provider.capabilities()
        if caps & QgsVectorDataProvider.AddFeatures:
            # add features by iterating the values
            features = []
            for val in values:
                feat = QgsFeature()
                # add geometry
                try:
                    if geom_type in (0, 3):
                        feat.setGeometry(
                            QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]), float(val[coords[1]]))]))
                    elif geom_type in (1, 4):
                        feat.setGeometry(
                            QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]), float(val[coords[1]])),
                                                      QgsPoint(float(val[coords[2]]), float(val[coords[3]]))]))
                except:
                    pass
                # add attributes
                for i, x in enumerate(val):
                    feat.addAttribute(i, x)
                features.append(feat)
            res, outFeats = provider.addFeatures(features)
            layer.updateFields()
        else:
            res = False
    else:
        res = False
    return res


def insertShapeFileGeometry(path, name, srid, geometry, attributes=None, values=None):
    # newfeature: function to insert new geometry features (and attributes) in shapefile
    pass


def addShapeFileAttributes(layer, attributes, types, values):
    # add attributes to the layer
    attributes_pos = dict()
    res = False
    if layer:
        provider = layer.dataProvider()
        caps = provider.capabilities()
        res = False
        if caps & QgsVectorDataProvider.AddAttributes:
            fields = provider.fields()
            count = fields.count()
            for i, name in enumerate(attributes):
                # add new field if it doesn't exist
                if fields.indexFromName(name) == -1:
                    res = provider.addAttributes([QgsField(name, types[i])])
                    # keep position of attributes that are added, since name can change
                    attributes_pos[i] = count
                    count += 1
            # apply changes if any made
            if res:
                layer.updateFields()
        # update attribute values by iterating the layer's features
        res = False
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            # fields = provider.fields() #the fields must be retrieved again after the updateFields() method
            iter = layer.getFeatures()
            for i, feature in enumerate(iter):
                fid = feature.id()
                # to update the features the attribute/value pairs must be converted to a dictionary for each feature
                attrs = {}
                for j in attributes_pos.keys():
                    field_id = attributes_pos[j]
                    val = values[i][j]
                    attrs.update({field_id: val})
                # update the layer with the corresponding dictionary
                res = provider.changeAttributeValues({fid: attrs})
            # apply changes if any made
            if res:
                layer.updateFields()
    return res
