# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2016-05-19
# copyright            : (C) 2016 by Space Syntax Limited
# author               : Laurens Versluis
# email                : l.versluis@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import print_function

import ntpath

import psycopg2
from psycopg2.extensions import AsIs
from qgis.core import (QgsProject, QgsMapLayer, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsVectorFileWriter,
                       NULL, QgsWkbTypes, QgsCoordinateTransformContext)


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


def check_for_NULL_geom(layer):
    has_null = False
    for f in layer.getFeatures():
        if f.geometry() is None or f.geometry() is NULL:
            has_null = True
            break
    return has_null


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


# WRITE -----------------------------------------------------------------

# geom_type allowed: 'Point', 'Linestring', 'Polygon'
def to_layer(fields, crs, encoding, geom_type, layer_type, path):
    layer = None
    if layer_type == 'memory':
        layer = QgsVectorLayer(geom_type + '?crs=' + crs.authid(), path, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields.toList())
        layer.updateFields()

    elif layer_type == 'shapefile':

        wkbTypes = {'Point': QgsWkbTypes.Point, 'Linestring': QgsWkbTypes.LineString, 'Polygon': QgsWkbTypes.Polygon}
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = encoding
        file_writer = QgsVectorFileWriter.create(path, fields, wkbTypes[geom_type], crs,
                                                 QgsCoordinateTransformContext(), options)
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ", file_writer.errorMessage())
        del file_writer
        layer = QgsVectorLayer(path, ntpath.basename(path)[:-4], "ogr")

    elif layer_type == 'postgis':

        # this is needed to load the table later
        # uri = connstring + """ type=""" + geom_types[geom_type] + """ table=\"""" + schema_name + """\".\"""" + table_name + """\" (geom) """

        connstring, schema_name, table_name = path
        uri = connstring + """ type=""" + geom_type + """ table=\"""" + schema_name + """\".\"""" + table_name + """\" (geom) """
        crs_id = crs.postgisSrid()
        try:
            con = psycopg2.connect(connstring)
            cur = con.cursor()
            create_query = cur.mogrify(
                """DROP TABLE IF EXISTS "%s"."%s"; CREATE TABLE "%s"."%s"( geom geometry(%s, %s))""", (
                    AsIs(schema_name), AsIs(table_name), AsIs(schema_name), AsIs(table_name), geom_type, AsIs(crs_id)))
            cur.execute(create_query)
            con.commit()
            post_q_flds = {2: 'bigint', 6: 'numeric', 1: 'bool', 'else': 'text', 4: 'numeric'}
            for f in fields:
                f_type = f.type()
                if f_type not in [2, 6, 1]:
                    f_type = 'else'
                attr_query = cur.mogrify("""ALTER TABLE "%s"."%s" ADD COLUMN "%s" %s""", (
                AsIs(schema_name), AsIs(table_name), AsIs(f.name()), AsIs(post_q_flds[f_type])))
                cur.execute(attr_query)
                con.commit()
            layer = QgsVectorLayer(uri, table_name, 'postgres')
        except psycopg2.DatabaseError as e:
            print(e)
    return layer


def has_unique_values(column, layer):
    if column:
        values = [f[column] for f in layer.getFeatures()]
        if NULL in values:  # len(values) > len(set(values)) or
            return False
        else:
            return True
    else:
        return True
