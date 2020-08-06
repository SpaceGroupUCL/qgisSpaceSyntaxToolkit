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
from __future__ import print_function
from builtins import str
from qgis.core import *
import os.path
import psycopg2

import traceback
from qgis.PyQt.QtCore import QSettings
import operator
import itertools

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

def getLayersListNames(layerslist):
    layer_names = [layer.name() for layer in layerslist]
    return layer_names

def getLegendLayerByName(iface, name):
    layer = None
    for i in QgsProject.instance().mapLayers().values():
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
    for i in QgsProject.instance().mapLayers().values():
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
        uri = QgsDataSourceURI(provider.dataSourceUri())
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
        uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
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
        if 'f_group' in fieldlist and 'f_type' in fieldlist:
            return True

    return False

def isRequiredEntranceLayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = getFieldNames(layer)
        if 'e_category' in fieldlist and 'e_subcat' in fieldlist:
            return True

    return False

def isRequiredLULayer(self, layer, type):
    if layer.type() == QgsMapLayer.VectorLayer \
            and layer.geometryType() == type:
        fieldlist = getFieldNames(layer)
        if 'gf_cat' in fieldlist and 'gf_subcat' in fieldlist:
            return True

    return False



# POSTGIS -----------------------------------------------------------------

def getPostgisSchemas(connstring, commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """

    try:
        connection = psycopg2.connect(connstring)
    except psycopg2.Error as e:
        print(e.pgerror)
        connection = None

    schemas = []
    data = []
    if connection:
        query = str("""SELECT schema_name from information_schema.schemata;""")
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            if cursor.description is not None:
                data = cursor.fetchall()
            if commit:
                connection.commit()
        except psycopg2.Error as e:
            connection.rollback()
        cursor.close()

    # only extract user schemas
    for schema in data:
        if schema[0] not in ('topology', 'information_schema') and schema[0][:3] != 'pg_':
            schemas.append(schema[0])
    #return the result even if empty
    return sorted(schemas)


def getQGISDbs():
    """Return all PostGIS connection settings stored in QGIS
    :return: connection dict() with name and other settings
    """
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections')
    named_dbs = settings.childGroups()
    all_info = [i.split("/") + [str(settings.value(i))] for i in settings.allKeys() if
                settings.value(i) != NULL and settings.value(i) != '']
    all_info = [i for i in all_info if
                i[0] in named_dbs and i[2] != NULL and i[1] in ['name', 'host', 'service', 'password', 'username',
                                                                'database',
                                                                'port']]
    dbs = dict(
        [k, dict([i[1:] for i in list(g)])] for k, g in itertools.groupby(sorted(all_info), operator.itemgetter(0)))
    QgsMessageLog.logMessage('dbs %s' % str(dbs), level = Qgis.Critical)
    settings.endGroup()

    return dbs