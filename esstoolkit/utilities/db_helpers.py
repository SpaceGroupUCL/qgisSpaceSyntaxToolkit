# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2014-04-01
# copyright            : (C) 2015 by Jorge Gil, UCL
# author               : Jorge Gil
# email                : jorge.gil@ucl.ac.uk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from __future__ import print_function

import itertools
import operator
from builtins import str
from sqlite3 import dbapi2 as sqlite

import psycopg2 as pgsql
from qgis.PyQt.QtCore import (QVariant, QSettings)
from qgis.core import (QgsProject, QgsDataSourceUri, QgsVectorLayer, QgsCredentials, NULL)

from . import gui_helpers as gh


# ------------------------------
# General database functions
# ------------------------------
def getDBLayerConnection(layer):
    provider = layer.providerType()
    uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
    if provider == 'spatialite':
        path = uri.database()
        connection_object = getSpatialiteConnection(path)
    elif provider == 'postgres':
        connection_object = pgsql.connect(uri.connectionInfo().encode('utf-8'))
    else:
        connection_object = None
    return connection_object


def testSameDatabase(layers):
    # check if the layers are in the same database
    if len(layers) > 1:
        database = []
        for layer in layers:
            database.append(QgsDataSourceUri(layer.dataProvider().dataSourceUri()).database())
        if len(list(set(database))) > 1:
            return False
        else:
            return True
    return True


def getDBLayerTableName(layer):
    uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
    return uri.table()


def getDBLayerGeometryColumn(layer):
    uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
    return uri.geometryColumn()


def getDBLayerPrimaryKey(layer):
    uri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
    return uri.key()


# ---------------------------------------------
# Spatialite database specific functions
#
# adapted from the QSpatiaLite plugin for QGIS by Romain Riviere
# see: https://github.com/romain974/qspatialite
# ----------------------------------------------
# spatialite geometry types
# 1 point; 2 line; 3 polygon; 4 multipoint; 5 multiline; 6 multipolygon

def listSpatialiteConnections():
    """List SpatiaLite connections stored in QGIS settings, and return dict with keys:
    path (list),name(list) and index (int) of last used DB (index) (-1 by default)"""
    res = dict()
    res['idx'] = 0
    settings = QSettings()
    settings.beginGroup('/SpatiaLite/connections')
    res['name'] = [str(item) for item in settings.childGroups()]
    res['path'] = [str(settings.value(u'%s/sqlitepath' % str(item))) for item in settings.childGroups()]
    settings.endGroup()
    # case: no connection available
    if len(res['name']) > 0:
        # case: connections available
        # try to select directly last opened dataBase ()
        try:
            last_db = settings.value(u'/SpatiaLite/connections/selected')
            last_db = last_db.split('@', 1)[1]
            # get last connexion index
            res['idx'] = res['name'].index(last_db)
        except:
            res['idx'] = 0
    # return the result even if empty
    return res


def createSpatialiteConnection(name, path):
    try:
        settings = QSettings()
        settings.beginGroup('/SpatiaLite/connections')
        settings.setValue(u'%s/sqlitepath' % name, '%s' % path)
        settings.endGroup()
    except sqlite.OperationalError as error:
        gh.pop_up_error("Unable to create connection to selected database: \n %s" % error)


def getSpatialiteConnection(path):
    try:
        connection = sqlite.connect(path)
    except sqlite.OperationalError as error:
        # pop_up_error("Unable to connect to selected database: \n %s" % error)
        connection = None
    return connection


def createSpatialiteDatabase(path):
    connection = getSpatialiteConnection(path)
    executeSpatialiteQuery(connection, "SELECT initspatialmetadata()")


def getSpatialiteDatabaseName(layer):
    pass


def executeSpatialiteQuery(connection, query, params=(), commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db) and return result set [header,data]
    or [error] error"""
    query = str(query)
    header = []
    data = []
    error = ''
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        if cursor.description is not None:
            header = [item[0] for item in cursor.description]
        data = [row for row in cursor]
        if commit:
            connection.commit()
    except sqlite.Error as error:
        connection.rollback()
        gh.pop_up_error("The SQL query seems to be invalid. \n %s" % query)
    cursor.close()
    # return the result even if empty
    return header, data, error


def listSpatialiteColumns(connection, name):
    columns = {}
    # query to extract the names and data types of the columns in a table of the database
    query = """PRAGMA TABLE_INFO("%s")""" % name
    header, data, error = executeSpatialiteQuery(connection, query)
    if header != [] and data != []:
        for col in data:
            columns[col[1]] = col[2]
    # return the result even if empty
    return columns


def loadSpatialiteTable(connection, path, name):
    """Load table (spatial or non-spatial) in QGIS"""
    uri = QgsDataSourceUri()
    uri.setDatabase(path)
    geometry = ''
    query = """SELECT f_geometry_column FROM geometry_columns WHERE f_table_name = '%s'""" % name
    header, data, error = executeSpatialiteQuery(connection, query)
    if data:
        geometry = data[0][0]
    uri.setDataSource('', "%s" % name, "%s" % geometry, '', "ROWID")
    layer = QgsVectorLayer(uri.uri(), '%s' % name, 'spatialite')
    # add layer to canvas
    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
    else:
        # newfeature: write error message?
        return False
    return True


def getSpatialiteLayer(connection, path, name):
    """Load table (spatial or non-spatial)in QGIS"""
    uri = QgsDataSourceUri()
    uri.setDatabase(path)
    geometry = ''
    tablename = name.lower()
    query = """SELECT f_geometry_column FROM geometry_columns WHERE f_table_name = '%s'""" % tablename
    header, data, error = executeSpatialiteQuery(connection, query)
    if data:
        geometry = data[0][0]
    if geometry != '':
        uri.setDataSource('', "%s" % tablename, "%s" % geometry)
        layer = QgsVectorLayer(uri.uri(), "%s" % tablename, 'spatialite')
    else:
        layer = None
    return layer


def getSpatialiteGeometryColumn(connection, name):
    geomname = ''
    query = """SELECT f_geometry_column, spatial_index_enabled FROM geometry_columns WHERE f_table_name = '%s'""" % (
        name)
    header, data, error = executeSpatialiteQuery(connection, query)
    if data:
        geomname = data[0][0]
    # ensure that it has a spatial index
    if data[0][1] == 0:
        query = """SELECT CreateSpatialIndex('%s', '%s')""" % (name, geomname)
        executeSpatialiteQuery(connection, query, commit=True)
    return geomname


def testSpatialiteTableExists(connection, name):
    """check if name already exists in the database
    """
    tablename = name.lower()  # .replace(" ","_")
    query = """SELECT name FROM sqlite_master WHERE type='table' AND lower(name) = '%s' """ % tablename
    header, data, error = executePostgisQuery(connection, query)
    if data:
        return True
    return False


def createSpatialiteTable(connection, path, name, srid, attributes, types, geometrytype):
    res = True
    # Drop table
    executeSpatialiteQuery(connection, """DROP TABLE IF EXISTS '%s' """ % name)
    # Get the database uri
    uri = QgsDataSourceUri()
    uri.setDatabase(path)
    # Get the fields
    fields = []
    for i, type in enumerate(types):
        field_type = ''
        if type in (QVariant.Char, QVariant.String):  # field type is TEXT
            field_type = 'TEXT'
        elif type in (
                QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt,
                QVariant.ULongLong):  # field type is INTEGER
            field_type = 'INTEGER'
        elif type == QVariant.Double:  # field type is DOUBLE
            field_type = 'REAL'
        fields.append('"%s" %s' % (attributes[i], field_type))  # .lower()
    # Get the geometry
    geometry = False
    if geometrytype != '':
        if 'point' in geometrytype.lower():
            geometry = 'MULTIPOINT'
        elif 'line' in geometrytype.lower():
            geometry = 'MULTILINESTRING'
        elif 'polygon' in geometrytype.lower():
            geometry = 'MULTIPOLYGON'
    if geometry:
        fields.insert(0, '"geometry" %s' % geometry)
    # Create new table
    fields = ','.join(fields)
    if len(fields) > 0:
        fields = ', %s' % fields
    header, data, error = executeSpatialiteQuery(connection,
                                                 """CREATE TABLE "%s" ( pk_id INTEGER PRIMARY KEY AUTOINCREMENT %s )""" % (
                                                     name, fields))
    if error:
        res = False
    else:
        # Recover Geometry Column:
        if geometry:
            executeSpatialiteQuery(connection,
                                   """SELECT RecoverGeometryColumn("%s","geometry",%s,'%s',2)""" % (
                                       name, srid, geometry))
            executeSpatialiteQuery(connection, """SELECT CreateSpatialIndex("%s", "%s") """ % (
                name, 'geometry'))
        if error:
            res = False
    if res:
        connection.commit()
    return res


def insertSpatialiteValues(connection, name, attributes, values, coords=None):
    # get table srid and geometry column info
    geometry_attr = ''
    srid = ''
    geometry_type = ''
    tablename = name.lower()
    query = """SELECT f_geometry_column, geometry_type, srid FROM geometry_columns WHERE f_table_name = '%s'""" % (
        tablename)
    header, data, error = executeSpatialiteQuery(connection, query)
    if data:
        geometry_attr = data[0][0]
        geometry_type = data[0][1]
        srid = data[0][2]

    # iterate through values to populate geometry and attributes
    if values:
        res = True
        if geometry_type in (1, 4) and len(coords) == 2:
            for val in values:
                WKT = "POINT(%s %s)" % (val[coords[0]], val[coords[1]])
                geometry_values = "CastToMulti(GeomFromText('%s', %s))" % (WKT, srid)
                # Create line in DB table
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s" ("%s","%s") VALUES (%s,%s)""" % (
                    tablename, geometry_attr, '","'.join(attributes), geometry_values, attr_values)
                header, data, error = executeSpatialiteQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
                # cursor.execute()
        elif geometry_type in (2, 5) and len(coords) == 4:
            for val in values:
                WKT = "LINESTRING(%s %s, %s %s)" % (val[coords[0]], val[coords[1]], val[coords[2]], val[coords[3]])
                geometry_values = "CastToMulti(GeomFromText('%s',%s))" % (WKT, srid)
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s" ("%s","%s") VALUES (%s,%s)""" % (
                    tablename, geometry_attr, '","'.join(attributes), geometry_values, attr_values)
                header, data, error = executeSpatialiteQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
        else:
            for val in values:
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s" ("%s") VALUES (%s)""" % (tablename, '","'.join(attributes), attr_values)
                header, data, error = executeSpatialiteQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
    else:
        res = False
    if res:
        # Commit changes to connection:
        connection.commit()
        # create spatial index
        executeSpatialiteQuery(connection, """SELECT CreateSpatialIndex("%s", '%s') """ % (
            tablename, 'geometry'))
    else:
        connection.rollback()
    return res


def addSpatialiteColumns(connection, name, columns, types):
    # add new columns to the layer
    res = False
    fields = listSpatialiteColumns(connection, name)
    for i, attr in enumerate(columns):
        # add new field if it doesn't exist
        if attr not in list(fields.keys()):
            field_type = ''
            if types[i] in (QVariant.Char, QVariant.String):  # field type is TEXT
                field_type = 'TEXT'
            elif types[i] in (
                    QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt,
                    QVariant.ULongLong):  # field type is INTEGER
                field_type = 'INTEGER'
            elif types[i] == QVariant.Double:  # field type is DOUBLE
                field_type = 'REAL'
            if field_type != '':
                query = """ALTER TABLE "%s" ADD COLUMN "%s" %s""" % (name, attr, field_type)
                header, data, error = executeSpatialiteQuery(connection, query)
                if error:
                    res = False
                    break
                else:
                    res = True
    if res:
        # Commit changes to connection:
        connection.commit()
        query = """SELECT UpdateLayerStatistics("%s")""" % name
        executeSpatialiteQuery(connection, query, commit=True)
    else:
        connection.rollback()
    return res


def dropSpatialiteColumns(connection, name, columns):
    # emulate a drop columns command, not available in SQLite
    res = True
    fields = listSpatialiteColumns(connection, name)
    new_cols = []
    for attr in list(fields.keys()):
        # drop column if it exists
        if attr not in columns:
            new_cols.append(attr)
    query = """ALTER TABLE "%s" RENAME TO to_drop""" % name
    executeSpatialiteQuery(connection, query)
    query = """CREATE TABLE "%s" AS SELECT "%s" FROM to_drop""" % (name, '","'.join(new_cols))
    executeSpatialiteQuery(connection, query)
    query = """SELECT UpdateLayerStatistics("%s")""" % name
    executeSpatialiteQuery(connection, query, commit=True)
    executeSpatialiteQuery(connection, "DROP TABLE to_drop", commit=True)
    executeSpatialiteQuery(connection, "VACUUM")
    return res


def addSpatialiteAttributes(connection, name, id, attributes, types, values):
    # add attributes with values to the layer
    res = addSpatialiteColumns(connection, name, attributes, types)
    # update attribute values iterating over values
    if res:
        # identify attributes to update
        fields = listSpatialiteColumns(connection, name)
        attr_index = {}
        attr_id = 0
        for j, attr in enumerate(attributes):
            if attr in list(fields.keys()) and attr != id:
                attr_index[attr] = j
            # the id attribute is identified but kept separate, not updated
            elif attr == id:
                attr_id = j
        # get values for attributes
        for val in values:
            new_values = []
            for attr in attr_index.keys():
                # add quotes if inserting a text value
                if types[attr_index[attr]] in (QVariant.Char, QVariant.String):
                    new_values.append("""'%s' = '%s'""" % (attr, val[attr_index[attr]]))
                else:
                    new_values.append("""'%s' = %s""" % (attr, val[attr_index[attr]]))
            if len(new_values) > 0:
                query = """UPDATE "%s" SET %s WHERE %s = %s""" % (name, ', '.join(new_values), id, val[attr_id])
                header, data, error = executeSpatialiteQuery(connection, query)
                if error:
                    res = False
                    break
        if res:
            # Commit changes to connection:
            connection.commit()
            query = """SELECT UpdateLayerStatistics("%s")""" % name
            executeSpatialiteQuery(connection, query, commit=True)
        else:
            connection.rollback()
    return res


def copyLayerToSpatialite(connection, layer, path, name):
    # Drop table
    executeSpatialiteQuery(connection, """DROP TABLE IF EXISTS "%s" """ % name)
    # Get layer provider
    provider = layer.dataProvider()
    # Get the database uri
    uri = QgsDataSourceUri()
    uri.setDatabase(path)
    # Get fields with corresponding types
    fields = []
    fieldsNames = []
    mapinfoDate = []
    for id, field in enumerate(provider.fields().toList()):
        fldName = str(field.name()).replace("'", " ").replace('"', " ")
        # Avoid two columns with same name:
        while fldName.upper() in fieldsNames:
            fldName = '%s_2' % fldName
        fldType = field.type()
        fldTypeName = str(field.typeName()).upper()
        if fldTypeName == 'DATE' and str(
                provider.storageType()).lower() == u'mapinfo file':  # Mapinfo DATE compatibility
            fldType = 'DATE'
            mapinfoDate.append([id, fldName])  # stock id and name of DATE field for MAPINFO layers
        elif fldType in (QVariant.Char, QVariant.String):  # field type is TEXT
            fldLength = field.length()
            fldType = 'TEXT(%s)' % fldLength  # Add field Length Information
        elif fldType in (
                QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt,
                QVariant.ULongLong):  # field type is INTEGER
            fldType = 'INTEGER'
        elif fldType == QVariant.Double:  # field type is DOUBLE
            fldType = 'REAL'
        else:  # field type is not recognized by SQLITE
            fldType = fldTypeName
        fields.append(""" "%s" %s """ % (fldName, fldType))
        fieldsNames.append(fldName.upper())
    # Get the geometry type
    geometry = False
    if layer.isSpatial():
        # Get geometry type
        geom = ['MULTIPOINT', 'MULTILINESTRING', 'MULTIPOLYGON', 'UnknownGeometry']
        geometry = geom[layer.geometryType()]
        # set SRID
        srid = layer.crs().postgisSrid()
    # select attributes to import (remove Pkuid if already exists):
    allAttrs = provider.attributeIndexes()
    fldDesc = provider.fieldNameIndex("pk_id")
    if fldDesc != -1:
        # print "pk_id already exists and will be replaced!"
        del allAttrs[fldDesc]  # remove pk_id Field
        del fields[fldDesc]  # remove pk_id Field
    if geometry:
        fields.insert(0, "geometry %s" % geometry)
    # Create new table
    fields = ','.join(fields)
    if len(fields) > 0:
        fields = ', %s' % fields
    executeSpatialiteQuery(connection,
                           """CREATE TABLE "%s" ( pk_id INTEGER PRIMARY KEY AUTOINCREMENT %s )""" % (
                               name, fields))
    # Recover Geometry Column:
    if geometry:
        executeSpatialiteQuery(connection,
                               """SELECT RecoverGeometryColumn("%s",'geometry',%s,'%s',2)""" % (
                                   name, srid, geometry,))
    # Retrieve every feature
    for feat in layer.getFeatures():
        # PKUID and Geometry
        values_auto = ['NULL']  # PKUID value
        if geometry:
            geom = feat.geometry()
            WKT = geom.asWkt()
            values_auto.append('CastToMulti(GeomFromText("%s",%s))' % (WKT, srid))
        # show all attributes and their values
        values = []
        for val in allAttrs:  # All except PKUID
            values.append(feat[val])
        # Create line in DB table
        if len(fields) > 0:
            executeSpatialiteQuery(connection, """INSERT INTO "%s" VALUES (%s,%s)""" % (
                name, ','.join([str(value).encode('utf-8') for value in values_auto]), ','.join('?' * len(values))),
                                   tuple([str(value) for value in values]))
        else:  # no attribute data
            executeSpatialiteQuery(connection, """INSERT INTO "%s" VALUES (%s)""" % (
                name, ','.join([str(value).encode('utf-8') for value in values_auto])))
    for date in mapinfoDate:  # mapinfo compatibility: convert date in SQLITE format (2010/02/11 -> 2010-02-11 ) or rollback if any error
        executeSpatialiteQuery(connection,
                               """UPDATE OR ROLLBACK "%s" set '%s'=replace( "%s", '/' , '-' )  """ % (
                                   name, date[1], date[1]))
    # Commit changes to connection:
    connection.commit()
    # create spatial index
    executeSpatialiteQuery(connection,
                           """SELECT CreateSpatialIndex("%s", "%s") """ % (name, 'geometry'))
    return True


# ---------------------------------------------
# PostGIS database specific functions
# ---------------------------------------------
# postgis geometry types
# 1 point; 2 line; 3 polygon; 4 multipoint; 5 multiline; 6 multipolygon

def listPostgisConnectionNames():
    """ Retrieve a list of PostgreSQL connection names
    :return: connections - list of strings
    """
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections')
    connection_names = [str(item) for item in settings.childGroups()]
    return connection_names


def getPostgisSelectedConnection():
    """

    :return:
    """
    # try to select directly the last opened dataBase
    try:
        settings = QSettings()
        last_db = settings.value(u'/PostgreSQL/connections/selected')
    except:
        last_db = ''
    return last_db


def getPostgisConnectionSettings():
    """Return all PostGIS connection settings stored in QGIS
    :return: connection dict() with name and other settings
    """
    con_settings = []
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections')
    for item in settings.childGroups():
        con = dict()
        con['name'] = str(item)
        con['service'] = str(settings.value(u'%s/service' % str(item)))
        con['host'] = str(settings.value(u'%s/host' % str(item)))
        con['port'] = str(settings.value(u'%s/port' % str(item)))
        con['database'] = str(settings.value(u'%s/database' % str(item)))
        con['username'] = str(settings.value(u'%s/username' % str(item)))
        con['password'] = str(settings.value(u'%s/password' % str(item)))
        con_settings.append(con)
    settings.endGroup()
    if len(con_settings) < 1:
        con_settings = None
    return con_settings


def createPostgisConnectionSetting(name, connection=None):
    """

    :param name:
    :param connection:
    :return:
    """
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections')
    if connection and isinstance(connection, dict):
        if 'service' in connection:
            settings.setValue(u'%s/service' % name, u'%s' % connection['service'])
        if 'host' in connection:
            settings.setValue(u'%s/host' % name, u'%s' % connection['host'])
        if 'port' in connection:
            settings.setValue(u'%s/port' % name, u'%s' % connection['port'])
        if 'dbname' in connection:
            settings.setValue(u'%s/database' % name, u'%s' % connection['dbname'])
        if 'user' in connection:
            settings.setValue(u'%s/saveUsername' % name, u'%s' % "true")
            settings.setValue(u'%s/username' % name, u'%s' % connection['user'])
        if 'password' in connection:
            settings.setValue(u'%s/savePassword' % name, u'%s' % "true")
            settings.setValue(u'%s/password' % name, u'%s' % connection['password'])
    settings.endGroup()


def getPostgisConnection(name):
    """

    :param name:
    :return:
    """
    con_str = getPostgisConnectionString(name)
    try:
        connection = pgsql.connect(con_str)
    except pgsql.Error as e:
        print(e.pgerror)
        connection = None
    return connection


def getPostgisConnectionString(name):
    """

    :param name:
    :return:
    """
    connstring = ''
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections/%s' % name)
    for item in settings.allKeys():
        if item in ('host', 'port', 'password', 'service'):
            if settings.value(item):
                connstring += "%s='%s' " % (item, settings.value(item))
        elif item == 'database':
            if settings.value(item):
                connstring += "dbname='%s' " % settings.value(item)
        elif item == 'username':
            if settings.value(item):
                connstring += "user='%s' " % settings.value(item)
    return connstring


def executePostgisQuery(connection, query, params='', commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """
    query = str(query)
    header = []
    data = []
    error = ''
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        if cursor.description is not None:
            header = [item[0] for item in cursor.description]
            data = cursor.fetchall()
        if commit:
            connection.commit()
    except pgsql.Error as e:
        error = e.pgerror
        connection.rollback()
    cursor.close()
    # return the result even if empty
    return header, data, error


def listPostgisSchemas(connection):
    schemas = []
    query = """SELECT schema_name from information_schema.schemata;"""
    header, data, error = executePostgisQuery(connection, query)
    if data:
        # only extract user schemas
        for schema in data:
            if schema[0] not in ('topology', 'information_schema') and schema[0][:3] != 'pg_':
                schemas.append(schema[0])
    return schemas


def getPostgisConnectionInfo(layer):
    info = dict()
    if layer:
        provider = layer.dataProvider()
        if provider.name() == 'postgres':
            uri = QgsDataSourceUri(provider.dataSourceUri())
            info['service'] = uri.service()
            info['host'] = uri.host()
            info['port'] = uri.port()
            info['dbname'] = uri.database()
            (success, username, passwd) = QgsCredentials.instance().get(uri.connectionInfo(), None, None)
            if success:
                info['user'] = username  # uri.username()
                info['password'] = passwd  # uri.password()
            connection_settings = getPostgisConnectionSettings()
            for connection in connection_settings:
                if (connection['database'] == info['dbname']) \
                        and (connection['host'] == info['host']) \
                        and (connection['port'] == info['port']) \
                        and (connection['service'] == info['service']):
                    info['name'] = connection['name']
                    break
    return info


def getPostgisLayerInfo(layer):
    info = dict()
    if layer:
        provider = layer.dataProvider()
        if provider.name() == 'postgres':
            uri = QgsDataSourceUri(provider.dataSourceUri())
            info['service'] = uri.service()
            info['database'] = uri.database()
            info['schema'] = uri.schema()
            info['table'] = uri.table()
            info['key'] = uri.keyColumn()
            info['geom'] = uri.geometryColumn()
            info['geomtype'] = uri.wkbType()
            info['srid'] = uri.srid()
            info['filter'] = uri.sql()
            info['service'] = uri.service()
            connection_settings = getPostgisConnectionSettings()
            for connection in connection_settings:
                if connection['database'] == info['database'] or connection['service'] == info['service']:
                    info['connection'] = connection['name']
                    break
    return info


def listPostgisGeomTables(connection):
    """query to read information about tables from the database
    each value returned is an element in the data list"""
    tables = []
    query = """SELECT * FROM geometry_columns ORDER BY lower(f_table_name)"""
    header, data, error = executePostgisQuery(connection, query)
    # extract information from query
    # info per table (array): name (0),geometry_column (1), geometry_column_type (2),
    # geometry_dimension (3), srid (4), spatial_index_enabled (5)
    if header != [] and data != []:
        tables = data
    # return the result even if empty
    return tables


def listPostgisColumns(connection, schema, name):
    """query to extract the names and data types of the columns in a table of the database
    """
    columns = {}
    query = """SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '%s' AND table_name = '%s';""" % (
        schema, name)
    header, data, error = executePostgisQuery(connection, query)
    if data:
        for col in data:
            columns[col[0]] = col[1]
    # return the result even if empty
    return columns


def loadPostgisTable(connection, name, schema, table):
    """Load table (spatial or non-spatial) in QGIS
    """
    uri = QgsDataSourceUri()
    dsn = None
    for con in getPostgisConnectionSettings():
        if con['name'] == name:
            dsn = con
            break
    if dsn:
        if dsn['service'] != 'NULL' and dsn['service'] != '':
            uri.setConnection(dsn['service'], '', '', '')
        elif dsn['username'] == 'NULL' or dsn['password'] == 'NULL':
            uri.setConnection(dsn['host'], dsn['port'], dsn['database'], '', '')
        else:
            uri.setConnection(dsn['host'], dsn['port'], dsn['database'], dsn['username'], dsn['password'])
        geometry = getPostgisGeometryColumn(connection, schema, table)
        if geometry:
            uri.setDataSource("%s" % schema, "%s" % table, "%s" % geometry)
            layer = QgsVectorLayer(uri, "%s" % table, 'postgres')
            # add layer to canvas
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                # newfeature: write error message?
                return False
        else:
            return False
    else:
        return False
    return True


def getPostgisLayer(connection, name, schema, table):
    """Load table in QGIS"""
    uri = QgsDataSourceUri()
    dsn = None
    for con in getPostgisConnectionSettings():
        if con['name'] == name:
            dsn = con
            break
    if dsn:
        if dsn['service'] != 'NULL' and dsn['service'] != '':
            uri.setConnection(dsn['service'], '', '', '')
        elif dsn['username'] == 'NULL' or dsn['password'] == 'NULL':
            uri.setConnection(dsn['host'], dsn['port'], dsn['database'], '', '')
        else:
            uri.setConnection(dsn['host'], dsn['port'], dsn['database'], dsn['username'], dsn['password'])
        query = """SELECT f_geometry_column FROM geometry_columns WHERE f_table_schema = '%s' AND f_table_name = '%s'""" % (
            schema, table)
        header, data, error = executePostgisQuery(connection, query)
        if data:
            geometry = data[0][0]
            uri.setDataSource("%s" % schema, "%s" % table, "%s" % geometry)
            layer = QgsVectorLayer(uri.uri(), "%s" % table, 'postgres')
        else:
            layer = None
    else:
        layer = None
    return layer


def getPostgisGeometryColumn(connection, schema, table):
    geomname = ''
    query = """SELECT f_geometry_column FROM geometry_columns WHERE f_table_schema = '%s' AND f_table_name = '%s'""" % (
        schema, table)
    header, data, error = executePostgisQuery(connection, query)
    if data:
        geomname = data[0][0]
    return geomname


def createPostgisSpatialIndex(connection, schema, table, geomname):
    # create a spatial index if not present, it makes subsequent queries much faster
    index = table.lower().replace(" ", "_")
    query = """CREATE INDEX %s_gidx ON "%s"."%s" USING GIST ("%s")""" % (index, schema, table, geomname)
    try:
        executePostgisQuery(connection, query)
    except:
        pass
    return


def testPostgisTableExists(connection, schema, name):
    """
    :param connection:
    :param schema:
    :param name:
    :return:
    """
    query = """SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = '%s' AND table_name = '%s' """ % (
        schema, name)
    header, data, error = executePostgisQuery(connection, query)
    if data:
        return True
    return False


def createPostgisTable(connection, schema, name, srid, attributes, types, geometrytype):
    res = True
    # Drop table
    executePostgisQuery(connection,
                        """DROP TABLE IF EXISTS "%s"."%s" CASCADE """ % (schema, name))
    # Get the fields
    fields = []
    for i, type in enumerate(types):
        field_type = ''
        if type in (QVariant.Char, QVariant.String):  # field type is TEXT
            field_type = 'character varying'
        elif type in (
                QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt,
                QVariant.ULongLong):  # field type is INTEGER
            field_type = 'integer'
        elif type == QVariant.Double:  # field type is DOUBLE
            field_type = 'double precision'
        fields.append('"%s" %s' % (attributes[i], field_type))
    # Get the geometry
    geometry = False
    if geometrytype != '':
        if 'point' in geometrytype.lower():
            geometry = 'MULTIPOINT'
        elif 'line' in geometrytype.lower():
            geometry = 'MULTILINESTRING'
        elif 'polygon' in geometrytype.lower():
            geometry = 'MULTIPOLYGON'
    # Create new table
    fields = ','.join(fields)
    if len(fields) > 0:
        fields = ', %s' % fields
    header, data, error = executePostgisQuery(connection,
                                              """CREATE TABLE "%s"."%s" ( sid SERIAL NOT NULL PRIMARY KEY %s ) """ % (
                                                  schema, name, fields))
    if error:
        res = False
    else:
        # Add the geometry column:
        if geometry:
            executePostgisQuery(connection,
                                """ALTER TABLE "%s"."%s" ADD COLUMN geom geometry('%s', %s) """ % (
                                    schema, name, geometry, srid))
            idx_name = name.lower().replace(" ", "_")
            header, data, error = executePostgisQuery(connection,
                                                      """CREATE INDEX %s_gix ON "%s"."%s" USING GIST (geom) """ % (
                                                          idx_name, schema, name))
        if error:
            res = False
    if res:
        # Commit changes to connection:
        connection.commit()
    return res


def insertPostgisValues(connection, schema, name, attributes, values, coords=None):
    # get table srid and geometry column info
    query = """SELECT f_geometry_column,  type, srid FROM geometry_columns WHERE f_table_schema = '%s' AND f_table_name = '%s'""" % (
        schema, name)
    header, data, error = executePostgisQuery(connection, query)
    if data:
        geometry_attr = data[0][0]
        geometry_type = data[0][1]
        srid = data[0][2]

    # iterate through values to populate geometry and attributes
    if values:
        res = True
        if geometry_type in ('POINT', 'MULTIPOINT') and len(coords) == 2:
            for val in values:
                WKT = "POINT(%s %s)" % (val[coords[0]], val[coords[1]])
                geometry_values = "ST_Multi(ST_GeomFromText('%s',%s))" % (WKT, srid)
                # Create line in DB table
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s"."%s" ("%s","%s") VALUES (%s,%s)""" % (
                    schema, name, geometry_attr, '","'.join(attributes), geometry_values, attr_values)
                header, data, error = executePostgisQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
        elif geometry_type in ('LINESTRING', 'MULTILINESTRING') and len(coords) == 4:
            for val in values:
                WKT = "LINESTRING(%s %s, %s %s)" % (val[coords[0]], val[coords[1]], val[coords[2]], val[coords[3]])
                geometry_values = "ST_Multi(ST_GeomFromText('%s',%s))" % (WKT, srid)
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s"."%s" ("%s","%s") VALUES (%s,%s)""" % (
                    schema, name, geometry_attr, '","'.join(attributes), geometry_values, attr_values)
                header, data, error = executePostgisQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
        else:
            for val in values:
                attr_values = ','.join(tuple([str(value) for value in val]))
                query = """INSERT INTO "%s"."%s" ("%s") VALUES (%s)""" % (
                    schema, name, '","'.join(attributes), attr_values)
                header, data, error = executePostgisQuery(connection, query, commit=False)
                if error:
                    res = False
                    break
    else:
        res = False
    if res:
        # Commit changes to connection:
        connection.commit()
    return res


def addPostgisColumns(connection, schema, name, columns, types):
    # add new columns to the layer
    res = False
    fields = listPostgisColumns(connection, schema, name)
    for i, attr in enumerate(columns):
        # add new field if it doesn't exist
        if attr not in list(fields.keys()):
            res = True
            field_type = ''
            if types[i] in (QVariant.Char, QVariant.String):  # field type is TEXT
                field_type = 'character varying'
            elif types[i] in (
                    QVariant.Bool, QVariant.Int, QVariant.LongLong, QVariant.UInt,
                    QVariant.ULongLong):  # field type is INTEGER
                field_type = 'integer'
            elif types[i] == QVariant.Double:  # field type is DOUBLE
                field_type = 'double precision'
            if field_type != '':
                query = """ALTER TABLE "%s"."%s" ADD COLUMN "%s" %s""" % (schema, name, attr, field_type)
                header, data, error = executePostgisQuery(connection, query)
                if error:
                    res = False
                    break
    # Commit changes to connection:
    connection.commit()
    return res


def addPostgisAttributes(connection, schema, name, id, attributes, types, values):
    # add attributes with values to the layer
    res = addPostgisColumns(connection, schema, name, attributes, types)
    # update attribute values iterating over values
    if res:
        # identify attributes to update
        fields = listPostgisColumns(connection, schema, name)
        attr_index = {}
        attr_id = 0
        for j, attr in enumerate(attributes):
            if attr in list(fields.keys()) and attr != id:
                attr_index[attr] = j
            elif attr == id:
                attr_id = j
        # get values for attributes
        for val in values:
            new_values = []
            for attr in attr_index.keys():
                # add quotes if inserting a text value
                if types[attr_index[attr]] in (QVariant.Char, QVariant.String):
                    new_values.append(""" "%s" = '%s'""" % (attr, val[attr_index[attr]]))
                else:
                    new_values.append(""" "%s" = %s""" % (attr, val[attr_index[attr]]))
            if len(new_values) > 0:
                query = """UPDATE "%s"."%s" SET %s WHERE "%s" = %s""" % (
                    schema, name, ', '.join(new_values), id, val[attr_id])
                header, data, error = executePostgisQuery(connection, query)
                if error:
                    res = False
                    break
        if res:
            connection.commit()
        else:
            connection.rollback()
    return res


def getPostgisSchemas(connstring, commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """

    try:
        connection = pgsql.connect(connstring)
    except pgsql.Error as e:
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
        except pgsql.Error as e:
            connection.rollback()
        cursor.close()

    # only extract user schemas
    for schema in data:
        if schema[0] not in ('topology', 'information_schema') and schema[0][:3] != 'pg_':
            schemas.append(schema[0])
    # return the result even if empty
    return sorted(schemas)


def getQGISDbs(portlast=False):
    """Return all PostGIS connection settings stored in QGIS
    :return: connection dict() with name and other settings
            """
    settings = QSettings()
    settings.beginGroup('/PostgreSQL/connections')
    named_dbs = settings.childGroups()
    all_info = [i.split("/") + [str(settings.value(i))] for i in settings.allKeys() if
                settings.value(i) != NULL and settings.value(i) != '']

    query_columns = ['name', 'host', 'service', 'password', 'username', 'port', 'database']
    if portlast:
        query_columns = ['name', 'host', 'service', 'password', 'username', 'database', 'port']

    all_info = [i for i in all_info if
                i[0] in named_dbs and i[2] != NULL and i[1] in query_columns]
    dbs = dict(
        [k, dict([i[1:] for i in list(g)])] for k, g in itertools.groupby(sorted(all_info), operator.itemgetter(0)))
    settings.endGroup()
    return dbs
