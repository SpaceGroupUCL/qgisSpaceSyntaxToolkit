# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essTools
                                 A QGIS plugin
 Set of tools for space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2014 by Jorge Gil, UCL
        email                : jorge.gil@ucl.ac.uk
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from pyspatialite import dbapi2 as sqlite
import psycopg2 as pgsql

import os.path
import math
from itertools import izip_longest


#------------------------------
# QGIS layer and field handling functions
#------------------------------
# QGIS enum types reference
# geometry types:
# 0 point; 1 line; 2 polygon; 3 multipoint; 4 multiline; 5 multipolygon
# providers:
# 'ogr'; 'spatialite'; 'postgis'


#------------------------------
# Layer functions
#------------------------------
def getVectorLayers(geom='all', provider='all'):
    """Return list of valid QgsVectorLayer in QgsMapLayerRegistry, with specific geometry type and/or data provider"""
    layers_list = []
    for layer in QgsMapLayerRegistry.instance().mapLayers().values():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.hasGeometryType() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list


def getLegendLayers(iface, geom='all', provider='all'):
    """Return list of valid QgsVectorLayer in QgsLegendInterface, with specific geometry type and/or data provider"""
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


def getCanvasLayers(iface, geom='all', provider='all'):
    """Return list of valid QgsVectorLayer in QgsMapCanvas, with specific geometry type and/or data provider"""
    layers_list = []
    for layer in iface.mapCanvas().layers():
        add_layer = False
        if layer.isValid() and layer.type() == QgsMapLayer.VectorLayer:
            if layer.hasGeometryType() and (geom is 'all' or layer.geometryType() in geom):
                if provider is 'all' or layer.dataProvider().name() in provider:
                    add_layer = True
        if add_layer:
            layers_list.append(layer)
    return layers_list


def isLayerProjected(layer):
    projected = False
    if layer:
        projected = not layer.crs().geographicFlag()
    return projected


def getLayerByName(name):
    layer = None
    for i in QgsMapLayerRegistry.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer


def getLegendLayerByName(iface, name):
    layer = None
    for i in iface.legendInterface().layers():
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
    if provider_type in ('spatialite','postgres'):
        uri = QgsDataSourceURI(provider.dataSourceUri())
        path = uri.database()
    elif provider_type == 'ogr':
        uri = provider.dataSourceUri()
        path = os.path.dirname(uri)
    return path


def getLayersListNames(layerslist):
    layer_names = [layer.name() for layer in layerslist]
    return layer_names


def reloadLayer(layer):
    layer_name = layer.name()
    layer_provider = layer.dataProvider().name()
    new_layer = None
    if layer_provider in ('spatialite','postgres'):
        uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
        new_layer = QgsVectorLayer(uri.uri(),layer_name,layer_provider)
    elif layer_provider == 'ogr':
        uri = layer.dataProvider().dataSourceUri()
        new_layer = QgsVectorLayer(uri.split("|")[0],layer_name,layer_provider)
    QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
    if new_layer:
        QgsMapLayerRegistry.instance().addMapLayer(new_layer)
    return new_layer


#------------------------------
# Field functions
#------------------------------
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
        types = (type)
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
        types = (QVariant.Int, QVariant.LongLong, QVariant.Double, QVariant.UInt, QVariant.ULongLong, QVariant.String, QVariant.Char)
    else:
        types = (type)
    if layer and layer.dataProvider():
        for index, field in enumerate(layer.dataProvider().fields()):
            if field.type() in types:
                vals = layer.uniqueValues(index,2)
                # exclude layers that only have NULL values
                if null == 'all':
                    if (len(vals) == 1 and vals[0] != NULL) or len(vals) > 1:
                        field_names[field.name()] = index
                # exclude layers with any NULL values
                elif null == 'any':
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
        vals = layer.uniqueValues(idx,2)
        # depending on the provider list is empty or has single NULL value
        if len(vals) == 0 or (len(vals) == 1 and vals[0] == NULL):
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
    # exclude fields that have some NULL values
        idx = getFieldIndex(layer, name)
        vals = layer.uniqueValues(idx,1)
        # depending on the provider list is empty or has NULL value in first position
        if len(vals) == 0 or (len(vals) == 1 and vals[0] == NULL):
            return True
        else:
            return False


def getFieldValues(layer, name, null=True):
    attributes = []
    ids = []
    if fieldExists(layer, name):
        request = QgsFeatureRequest().setSubsetOfAttributes([getFieldIndex(layer, name)])
        features = layer.getFeatures(request)
        for feature in features:
            val = feature.attribute(name)
            if null:
                attributes.append(val)
                ids.append(feature.id())
            else:
                if val != NULL:
                    attributes.append(val)
                    ids.append(feature.id())
    return attributes, ids


def getSelectionValues(layer, name, null=True, id=False):
    attributes = []
    ids = []
    if fieldExists(layer, name):
        features = layer.selectedFeatures()
        for feature in features:
            val = feature.attribute(name)
            if null:
                attributes.append(val)
                ids.append(feature.id())
            else:
                if val != NULL:
                    attributes.append(val)
                    ids.append(feature.id())
    return attributes, ids


def fieldExists(layer, name):
    fields = getFieldNames(layer)
    if name in fields:
        return True
    else:
        return False


def getIdField(layer):
    pk = layer.dataProvider().pkAttributeIndexes()
    if len(pk) > 0:
        user_id = layer.dataProvider().fields().field(pk[0]).name()
    else:
        names, idxs = getNumericFieldNames(layer)
        user_id = ''
        standard_id = ("pk","pkuid","pkid","sid","fid","id","ref")
        # look for user defined ID
        #for field in getNumericFields(layer):
        for field in names:
            if field.lower() in standard_id:
                if isValidIdField(layer, field):
                    user_id = field
                    break
    return user_id


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
                #add new field if it doesn't exist
                if fields.indexFromName(name) == -1:
                    res = provider.addAttributes([QgsField(name, types[i])])
                else:
                    res = True
        #apply changes if any made
        if res:
            layer.updateFields()
    return res


#------------------------------
# Feature functions
#------------------------------
def getFeatureListIds(layer, name, values=list):
    features = {}
    if layer:
        if fieldExists(layer, name):
            request = QgsFeatureRequest().setSubsetOfAttributes([getFieldIndex(layer, name)])
            iterator = layer.getFeatures(request)
            for feature in iterator:
                att = feature.attribute(name)
                if att in values:
                    features[att] = feature.id()
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
        renderer = layer.rendererV2()
        features = layer.getFeatures()
        for feature in features:
            symb = renderer.symbolsForFeature(feature)
            if len(symb) > 0:
                symbols = {feature.id(): symb[0].color()}
            else:
                symbols = {feature.id(): QColor(200,200,200,255)}
    return symbols


def getAllFeatureData(layer):
    data = {}
    symbols = {}
    if layer:
        renderer = layer.rendererV2()
        features = layer.getFeatures()
        for feature in features:
            data = {feature.id(): feature}
            symb = renderer.symbolsForFeature(feature)
            if len(symb) > 0:
                symbols = {feature.id(): symb[0].color()}
            else:
                symbols = {feature.id(): QColor(200,200,200,255)}
    return data, symbols

#------------------------------
# Canvas functions
#------------------------------
# Display a message in the QGIS canvas
def showMessage(iface, msg, type='Info', lev=1, dur=2):
    iface.messageBar().pushMessage(type,msg,level=lev,duration=dur)


def getCanvasColour(iface):
    colour = iface.mapCanvas().canvasColor()
    return colour


#------------------------------
# General functions
#------------------------------
# Display an error message via Qt message box
def pop_up_error(msg=''):
    # newfeature: make this work with the new messageBar
    QMessageBox.warning(None, 'error', '%s' % msg)


# Return iterator with items of iterable grouped by n
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


# check if a text string is of numeric type
def isNumericOld(txt):
    try:
        int(txt)
        return True
    except ValueError:
        try:
            long(txt)
            return True
        except ValueError:
            try:
                float(txt)
                return True
            except ValueError:
                return False


# function found here http://www.power-quant.com/?q=node/85
def isNumeric(x):
    """Checks to see if x represents a numeric value by converting
    into unicode and utilizing the isnumeric() method."""
    # first convert the number into a string
    strRep = str(x)
    # then make a unicode version so we can ensure we're dealing with
    # something that represents a numeric value:
    uRep = unicode(strRep)
    if ('.' in uRep) and all([x.isnumeric() for x in uRep.split('.')]):
        return True # there's a decimal and everything to the right
                    # and left of it is numeric
    else:
        return uRep.isnumeric()


# convert a text string to a numeric value, if possible
def convertNumeric(txt):
    try:
        value = int(txt)
    except ValueError:
        try:
            value = long(txt)
        except ValueError:
            try:
                value = float(txt)
            except ValueError:
                value = ''#txt
    return value


# by Ben Hoyt
# http://code.activestate.com/recipes/578114-round-number-to-specified-number-of-significant-di/
# round a number to specified significant digits
def roundSigFigs(num, sig_figs):
    """Round to specified number of sigfigs.
    round_sigfigs(0, sig_figs=4)
    >> 0
    int(round_sigfigs(12345, sig_figs=2))
    >> 12000
    int(round_sigfigs(-12345, sig_figs=2))
    >> -12000
    int(round_sigfigs(1, sig_figs=2))
    >> 1
    '{0:.3}'.format(round_sigfigs(3.1415, sig_figs=2))
    >> '3.1'
    '{0:.3}'.format(round_sigfigs(-3.1415, sig_figs=2))
    >> '-3.1'
    '{0:.5}'.format(round_sigfigs(0.00098765, sig_figs=2))
    >> '0.00099'
    '{0:.6}'.format(round_sigfigs(0.00098765, sig_figs=3))
    >> '0.000988'
    """
    if num != 0:
        return round(num, -int(math.floor(math.log10(abs(num))) - (sig_figs - 1)))
    else:
        return 0  # Can't take the log of 0


def calcGini(values):
    """
    Calculate gini coefficient, using transformed formula, like R code in 'ineq'
    :param values: list of numeric values
    :return: gini coefficient
    """
    S = sorted(values)
    N = len(values)
    T = sum(values)
    P = sum(xi * (i+1) for i,xi in enumerate(S))
    G = 2.0 * P/(N * T)
    gini = G - 1 - (1./N)
    return gini


# fixme: this calculates pearson correlation, not p value!
def calcPvalue(x, y):
    n = len(x)
    if not n == len(y) or not n > 0:
        pearson = None
    else:
        avg_x = float(sum(x)) / n
        avg_y = float(sum(y)) / n
        diffprod = 0
        xdiff2 = 0
        ydiff2 = 0
        for idx in range(n):
            xdiff = x[idx] - avg_x
            ydiff = y[idx] - avg_y
            diffprod += xdiff * ydiff
            xdiff2 += xdiff * xdiff
            ydiff2 += ydiff * ydiff
        pearson = diffprod / math.sqrt(xdiff2 * ydiff2)
    return pearson


#------------------------------
# Creation functions
#------------------------------
def createTempLayer(name, srid, attributes, types, values, coords):
    # create an instance of a memory vector layer
    type = ''
    if len(coords) == 2: type = 'Point'
    elif len(coords) == 4: type = 'LineString'
    vlayer = QgsVectorLayer('%s?crs=EPSG:%s'% (type, srid), name, "memory")
    provider = vlayer.dataProvider()
    #create the required fields
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
                feat.setGeometry(QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]),float(val[coords[1]]))]))
            elif type == 'LineString':
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]),float(val[coords[1]])), \
                                                           QgsPoint(float(val[coords[2]]),float(val[coords[3]]))]))
        except:
            pass
        # add attribute values
        feat.setAttributes(val)
        features.append(feat)
    # add the features to the layer
    try:
        provider.addFeatures(features)
    except:
        return None

    vlayer.commitChanges()
    vlayer.updateExtents()
    if not vlayer.isValid():
        print "Layer failed to load!"
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
            index.insertFeature(feat)
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
        features = unlinks.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1','line2'],unlinks.pendingFields()))
        for feature in features:
            unlinks_list.append((feature.attribute('line1'),feature.attribute('line2')))
    # get links pairs
    if links:
        features = links.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1','line2'],links.pendingFields()))
        for feature in features:
            links_list.append((feature.attribute('line1'),feature.attribute('line2')))
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
                if (id,id_b) not in unlinks_list and (id,id_b) not in unlinks_list:
                    axial_links.append((id,id_b))
    return axial_links


#------------------------------
# General database functions
#------------------------------
def getLayerConnection(layer):
    provider = layer.providerType()
    uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
    if provider == 'spatialite':
        path = uri.database()
        connection_object = getSpatialiteConnection(path)
    elif provider == 'postgres':
        connection_object = pgsql.connect(uri.connectionInfo().encode('utf-8'))
    else:
        connection_object = None
    return connection_object


def testSameDatabase(layers):
    #check if the layers are in the same database
    if len(layers) > 1:
        database = []
        for layer in layers:
            database.append(QgsDataSourceURI(layer.dataProvider().dataSourceUri()).database())
        if len(list(set(database))) > 1:
            return False
        else:
            return True
    return True


def getLayerTableName(layer):
    uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
    return uri.table ()


#---------------------------------------------
# spatialite database specific functions
# some were adapted from the QSpatiaLite plugin for QGIS
#----------------------------------------------
# spatialite geometry types
# 1 point; 2 line; 3 polygon; 4 multipoint; 5 multiline; 6 multipolygon

def listSpatialiteConnections():
    """List SpatiaLite connexions stored in QGIS settings, and return dict with keys:
    path (list),name(list) and index (int) of last used DB (index) (-1 by default)"""
    res = dict()
    res['idx'] = 0
    settings = QSettings()
    settings.beginGroup('/SpatiaLite/connections')
    res['name'] = [unicode(item) for item in settings.childGroups()]
    res['path'] = [unicode(settings.value(u'%s/sqlitepath' % unicode(item))) for item in settings.childGroups()]
    settings.endGroup()
    #case: no connection available
    if len(res['name']) < 1:
        res = None
    else:
        #case: connections available
        #try to select directly last opened dataBase ()
        try:
            last_db = settings.value(u'/SpatiaLite/connections/selected')
            last_db = last_db.split('@', 1)[1]
            #get last connexion index
            res['idx'] = res['name'].index(last_db)
        except:
            res['idx'] = 0
    #return the result even if empty
    return res


def createSpatialiteConnection(name, path):
    #connection = None
    try:
        settings=QSettings()
        settings.beginGroup('/SpatiaLite/connections')
        settings.setValue(u'%s/sqlitepath'%name,'%s'%path)
        settings.endGroup()

        #connection=getSpatialiteConnection(path)
    except sqlite.OperationalError, error:
        pop_up_error("Unable to create connection to selected database: \n %s" % error)
    #return connection


def getSpatialiteConnection(path):
    try:
        connection=sqlite.connect(path)
    except sqlite.OperationalError, error:
        #pop_up_error("Unable to connect to selected database: \n %s" % error)
        connection = None
    return connection


def createSpatialiteDatabase(path):
    connection = getSpatialiteConnection(path)
    executeSpatialiteQuery(connection,"SELECT initspatialmetadata()")


def getSpatialiteDatabaseName(layer):
    pass


def executeSpatialiteQuery(connection, query, params=(), commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionnaly perform commit to save Db) and return result set [header,data]
    or [error] error"""
    query = unicode(query)
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
    except sqlite.OperationalError, error:
        connection.rollback()
        pop_up_error("The SQL query seems to be invalid. \n %s" % error)
    cursor.close()
    #return the result even if empty
    return header, data, error


def listSpatialiteGeomTables(connection):
    tables = []
    #query to read information about tables from the database
    #each value returned is an element in the data list
    query = """SELECT * FROM geometry_columns ORDER BY lower(f_table_name)"""
    header, data, error = executeSpatialiteQuery(connection, query)
    #extract information from query
    #info per table (array): name (0),geometry_column (1), geometry_column_type (2),
    # geometry_dimension (3), srid (4), spatial_index_enabled (5)
    if header != [] and data != []:
        tables = data
    #return the result even if empty
    return tables


def listSpatialiteSeqTables(connection):
    tables = []
    #query to read information about tables from the database
    #each value returned is an element in the data list
    query = """SELECT * FROM sqlite_sequence ORDER BY lower(name)"""
    header, data, error = executeSpatialiteQuery(connection, query)
    #extract information from query
    #info per table (array): name (0),seq (1)
    if header != [] and data != []:
        tables = data
    #return the result even if empty
    return tables


def listSpatialiteColumns(connection, name):
    columns = {}
    #query to extract the names and data types of the columns in a table of the database
    query = """PRAGMA TABLE_INFO("%s")""" % name
    header, data, error = executeSpatialiteQuery(connection, query)
    if header != [] and data != []:
        for col in data:
            columns[col[1]] = col[2]
    #return the result even if empty
    return columns


def loadSpatialiteTable(connection, path, name):
    """Load table (spatial or non-spatial)in QGIS"""
    uri = QgsDataSourceURI()
    uri.setDatabase(path)
    geometry = ''
    for table in listSpatialiteGeomTables(connection):
        if table[0] == name:
            geometry = table[1]
    uri.setDataSource('', "%s" %name, "%s"%geometry, '',"ROWID")
    layer=QgsVectorLayer(uri.uri(), '%s'%name, 'spatialite')
    #add layer to canvas
    if layer.isValid():
        QgsMapLayerRegistry.instance().addMapLayer(layer)
    else:
        # newfeature: write error message?
        return False
    return True


def getSpatialiteLayer(connection, path, name):
    """Load table (spatial or non-spatial)in QGIS"""
    uri = QgsDataSourceURI()
    uri.setDatabase(path)
    geometry = ''
    for table in listSpatialiteGeomTables(connection):
        if table[0] == name.lower():
            geometry = table[1]
            break
    if geometry != '':
        uri.setDataSource('', "%s" % name, "%s" % geometry)
        layer = QgsVectorLayer(uri.uri(), "%s" %  name, 'spatialite')
    else:
        layer = None
    return layer


def getSpatialiteGeometryColumn(connection, name):
    # table preparation
    query = """SELECT f_geometry_column, spatial_index_enabled FROM geometry_columns WHERE f_table_name = '%s'"""%(name)
    header, data, error = executeSpatialiteQuery(connection, query)
    geomname = data[0][0]
    # ensure that it has a spatial index
    if data[0][1] == 0:
        query = """SELECT CreateSpatialIndex('%s', '%s')"""%(name,geomname)
        header, data, error = executeSpatialiteQuery(connection, query, commit=True)
    return geomname


def testSpatialiteTableExists(connection, name):
    #check if name already exists in the database
    existing_names = [table[0].lower() for table in listSpatialiteGeomTables(connection)]
    tablename = name.lower()
    if tablename in existing_names:
        return True
    return False


def createSpatialiteTable(connection, path, name, srid, attributes, types, geometrytype):
    #Drop table
    header, data, error = executeSpatialiteQuery(connection,"""DROP TABLE IF EXISTS '%s' """ % name)
    #Get the database uri
    uri = QgsDataSourceURI()
    uri.setDatabase(path)
    # Get the fields
    fields = []
    for i, type in enumerate(types):
        field_type = ''
        if type in (QVariant.Char,QVariant.String): # field type is TEXT
            field_type = 'TEXT'
        elif type in (QVariant.Bool,QVariant.Int,QVariant.LongLong,QVariant.UInt,QVariant.ULongLong): # field type is INTEGER
            field_type = 'INTEGER'
        elif type==QVariant.Double: # field type is DOUBLE
            field_type = 'REAL'
        fields.append('"%s" %s'% (attributes[i],field_type)) #.lower()
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
        fields.insert(0,'"geometry" %s'%geometry)
    #Create new table
    fields=','.join(fields)
    if len(fields)>0:
        fields=', %s'%fields
    header, data, error = executeSpatialiteQuery(connection,"""CREATE TABLE "%s" ( pk_id INTEGER PRIMARY KEY AUTOINCREMENT %s )""" % (name, fields))
    #Recover Geometry Column:
    if geometry:
        header, data, error = executeSpatialiteQuery(connection,"""SELECT RecoverGeometryColumn("%s","geometry",%s,'%s',2)""" % (name,srid,geometry))
        header,data, error = executeSpatialiteQuery(connection,"""SELECT CreateSpatialIndex("%s", "%s") """%(name,'geometry'))
    if error != '':
        return False
    return True


def insertSpatialiteValues(connection, name, attributes, values, coords=None):
    # get table srid and geometry column info
    geometry_attr = ''
    srid = ''
    geometry_type = ''
    for table in listSpatialiteGeomTables(connection):
        if table[0] == name.lower():
            geometry_attr = table[1]
            geometry_type = table[2]
            srid = table[4]
            break
    if geometry_attr == '':
        return False
    # iterate through values to populate geometry and attributes
    if values:
        for val in values:
            geometry_values = ""
            if geometry_type in (1,4) and len(coords) == 2:
                WKT = "POINT(%s %s)" % (val[coords[0]],val[coords[1]])
                geometry_values = 'CastToMulti(GeomFromText("%s",%s))'%(WKT,srid)
            elif geometry_type in (2,5) and len(coords) == 4:
                WKT = "LINESTRING(%s %s, %s %s)" % (val[coords[0]],val[coords[1]],val[coords[2]],val[coords[3]])
                geometry_values = 'CastToMulti(GeomFromText("%s",%s))'%(WKT,srid)
            #Create line in DB table
            attr_values = ','.join(tuple([unicode(value) for value in val]))
            if geometry_values == "":
                header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" ("%s") VALUES (%s)""" % (name, '","'.join(attributes), attr_values), commit=True)
            else:
                header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" ("%s","%s") VALUES (%s,%s)""" % (name, geometry_attr, '","'.join(attributes), geometry_values, attr_values), commit=True)
    else:
        return False
    #Commit changes to connection:
    connection.commit()
    #create spatial index
    header, data, error = executeSpatialiteQuery(connection,"""SELECT CreateSpatialIndex("%s", '%s') """ % (name,'geometry'))
    return True


def insertSpatialiteGeometry(connection, name, geometry, attributes=None, values=None):
    # get table srid and geometry column
    geometry_attr = ''
    srid = ''
    geometry_type = ''
    for table in listSpatialiteGeomTables(connection):
        if table[0] == name:
            geometry_attr = table[1]
            geometry_type = table[2]
            srid = table[4]
    if geometry_attr == '':
        return False
    #
    if geometry:
        for i, geom in enumerate(geometry):
            WKT = ""
            if geometry_type in (1,4) and len(geom) == 2:
                WKT = "POINT (%s %s)" % (geom[0],geom[1])
            elif len(geom) > 2:
                coords = []
                for pair in grouper(geom,2):
                    coords.append(pair)
                if geometry_type in (2,5):
                    WKT = "LINESTRING (%s)" % ','.join(coords)
                else:
                    WKT = "POLYGON ((%s))" % ','.join(coords)
            else:
                return False
            geometry_values = 'CastToMulti(GeomFromText("%s",%s))'%(WKT,srid)
            #Create line in DB table
            if attributes:
                attr_values = ','.join(tuple([unicode(value) for value in values[i]]))
                header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" ("%s","%s") VALUES (%s,%s)""" % (name, geometry_attr, '","'.join(attributes), geometry_values, attr_values))
            else: #no attribute data, only geometry
                header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" ("%s") VALUES (%s)""" % (name, geometry_attr, geometry_values))
    else:
        return False
    #Commit changes to connection:
    connection.commit()
    #create spatial index
    header, data, error = executeSpatialiteQuery(connection,"""SELECT CreateSpatialIndex("%s", '%s') """ % (name,'geometry'))
    return True


def addSpatialiteColumns(connection, name, columns, types):
    # add new columns to the layer
    res = False
    fields = listSpatialiteColumns(connection, name)
    for i, attr in enumerate(columns):
        #add new field if it doesn't exist
        if attr not in fields.keys():
            res = True
            field_type = ''
            if types[i] in (QVariant.Char,QVariant.String): # field type is TEXT
                field_type = 'TEXT'
            elif types[i] in (QVariant.Bool,QVariant.Int,QVariant.LongLong,QVariant.UInt,QVariant.ULongLong): # field type is INTEGER
                field_type = 'INTEGER'
            elif types[i] == QVariant.Double: # field type is DOUBLE
                field_type = 'REAL'
            if field_type != '':
                query = """ALTER TABLE "%s" ADD COLUMN "%s" %s""" % (name, attr, field_type)
                header, data, error = executeSpatialiteQuery(connection,query)
    query = """SELECT UpdateLayerStatistics("%s")""" % name
    header, data, error = executeSpatialiteQuery(connection,query, commit=True)
    #Commit changes to connection:
    connection.commit()
    return res


def dropSpatialiteColumns(connection, name, columns):
    # emulate a drop columns command, not available in SQLite
    res = True
    fields = listSpatialiteColumns(connection, name)
    new_cols = []
    for attr in fields.keys():
        #drop column if it exists
        if attr not in columns:
            new_cols.append(attr)
    query = """ALTER TABLE "%s" RENAME TO to_drop""" % name
    header, data, error = executeSpatialiteQuery(connection,query)
    query = """CREATE TABLE "%s" AS SELECT "%s" FROM to_drop""" % (name, '","'.join(new_cols))
    header, data, error = executeSpatialiteQuery(connection,query)
    query = """SELECT UpdateLayerStatistics("%s")""" % name
    header, data, error = executeSpatialiteQuery(connection,query, commit=True)
    header, data, error = executeSpatialiteQuery(connection,"DROP TABLE to_drop", commit=True)
    header, data, error = executeSpatialiteQuery(connection,"VACUUM")
    return res


def addSpatialiteAttributes(connection, name, attributes, types, values):
    # add attributes with values to the layer
    fields = listSpatialiteColumns(connection, name)
    for i, attr in enumerate(attributes):
        #add new field if it doesn't exist
        if attr not in fields.keys():
            field_type = ''
            if types[i] in (QVariant.Char,QVariant.String): # field type is TEXT
                field_type = 'TEXT'
            elif types[i] in (QVariant.Bool,QVariant.Int,QVariant.LongLong,QVariant.UInt,QVariant.ULongLong): # field type is INTEGER
                field_type = 'INTEGER'
            elif types[i] == QVariant.Double: # field type is DOUBLE
                field_type = 'REAL'
            if field_type != '':
                query = """ALTER TABLE "%s" ADD COLUMN '%s' %s""" % (name, attr, field_type)
                header, data, error = executeSpatialiteQuery(connection,query)
    # update attribute values iterating over values
    fields = listSpatialiteColumns(connection, name)
    for i, val in enumerate(values):
        new_values = []
        for j, attr in enumerate(attributes):
            if attr in fields.keys():
                if types[j] in (QVariant.Char,QVariant.String):
                    new_values.append("""'%s' = '%s'""" % (attr,val[j]))
                else:
                    new_values.append("""'%s' = %s""" % (attr,val[j]))
        if len(new_values) > 0:
            query = """UPDATE "%s" SET %s WHERE rowid = %s""" % (name, ', '.join(new_values), i+1)
            header, data, error = executeSpatialiteQuery(connection,query)
            if error:
                return False
    query = """SELECT UpdateLayerStatistics("%s")""" % name
    header, data, error = executeSpatialiteQuery(connection,query)
    #Commit changes to connection:
    connection.commit()
    return True


def copyLayerToSpatialite(connection, layer, path, name):
    #Drop table
    header,data, error = executeSpatialiteQuery(connection,"""DROP TABLE IF EXISTS "%s" """ % name)
    #Get layer provider
    provider = layer.dataProvider()
    #Get the database uri
    uri = QgsDataSourceURI()
    uri.setDatabase(path)
    #Get fields with corresponding types
    fields=[]
    fieldsNames=[]
    mapinfoDate=[]
    for id,field in enumerate(provider.fields().toList()):
        fldName=unicode(field.name()).replace("'"," ").replace('"'," ")
        #Avoid two columns with same name:
        while fldName.upper() in fieldsNames:
            fldName='%s_2'%fldName
        fldType=field.type()
        fldTypeName=unicode(field.typeName()).upper()
        if fldTypeName=='DATE' and unicode(provider.storageType()).lower()==u'mapinfo file': # Mapinfo DATE compatibility
            fldType='DATE'
            mapinfoDate.append([id,fldName]) #stock id and name of DATE field for MAPINFO layers
        elif fldType in (QVariant.Char,QVariant.String): # field type is TEXT
            fldLength=field.length()
            fldType='TEXT(%s)'%fldLength  #Add field Length Information
        elif fldType in (QVariant.Bool,QVariant.Int,QVariant.LongLong,QVariant.UInt,QVariant.ULongLong): # field type is INTEGER
            fldType='INTEGER'
        elif fldType==QVariant.Double: # field type is DOUBLE
            fldType='REAL'
        else: # field type is not recognized by SQLITE
            fldType=fldTypeName
        fields.append(""" "%s" %s """%(fldName,fldType))
        fieldsNames.append(fldName.upper())
    #Get the geometry type
    geometry=False
    if layer.hasGeometryType():
        #Get geometry type
        geom=['MULTIPOINT','MULTILINESTRING','MULTIPOLYGON','UnknownGeometry']
        geometry=geom[layer.geometryType()]
        #set SRID
        srid=layer.crs().postgisSrid()
    #select attributes to import (remove Pkuid if already exists):
    allAttrs = provider.attributeIndexes()
    fldDesc = provider.fieldNameIndex("pk_id")
    if fldDesc != -1:
        #print "pk_id already exists and will be replaced!"
        del allAttrs[fldDesc] #remove pk_id Field
        del fields[fldDesc] #remove pk_id Field
    if geometry:
        fields.insert(0,"geometry %s"%geometry)
    #Create new table
    fields=','.join(fields)
    if len(fields)>0:
        fields=', %s'%fields
    header, data, error = executeSpatialiteQuery(connection,"""CREATE TABLE "%s" ( pk_id INTEGER PRIMARY KEY AUTOINCREMENT %s )"""%(name, fields))
    #Recover Geometry Column:
    if geometry:
        header, data, error=executeSpatialiteQuery(connection,"""SELECT RecoverGeometryColumn("%s",'geometry',%s,'%s',2)"""%(name,srid,geometry,))
    # Retrieve every feature
    for feat in layer.getFeatures():
        #PKUID and Geometry
        values_auto=['NULL'] #PKUID value
        if geometry:
            geom = feat.geometry()
            WKT=geom.exportToWkt()
            values_auto.append('CastToMulti(GeomFromText("%s",%s))'%(WKT,srid))
        # show all attributes and their values
        values=[]
        for val in allAttrs: # All except PKUID
            values.append(feat[val])
        #Create line in DB table
        if len(fields)>0:
            header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" VALUES (%s,%s)""" % (name,','.join([unicode(value).encode('utf-8') for value in values_auto]), ','.join('?'*len(values))), tuple([unicode(value) for value in values]))
        else: #no attribute data
            header, data, error = executeSpatialiteQuery(connection,"""INSERT INTO "%s" VALUES (%s)""" % (name,','.join([unicode(value).encode('utf-8') for value in values_auto])))
    for date in mapinfoDate: #mapinfo compatibility: convert date in SQLITE format (2010/02/11 -> 2010-02-11 ) or rollback if any error
        header, data, error = executeSpatialiteQuery(connection,"""UPDATE OR ROLLBACK "%s" set '%s'=replace( "%s", '/' , '-' )  """%(name,date[1],date[1]))
    #Commit changes to connection:
    connection.commit()
    #create spatial index
    header, data, error = executeSpatialiteQuery(connection,"""SELECT CreateSpatialIndex("%s", "%s") """%(name,'geometry'))
    return True



#---------------------------------------------
# Shape file specific functions
#---------------------------------------------
def listShapeFolders():
    # get folder name and path of open layers
    res = dict()
    res['idx'] = 0
    res['name'] = []
    res['path'] = []
    layers = getVectorLayers('all', 'ogr')
    for layer in layers:
        provider = layer.dataProvider()
        if layer.storageType() == 'ESRI Shapefile':
            path = os.path.dirname(layer.dataProvider().dataSourceUri())
            try:
                idx = res['path'].index(path)
            except:
                res['name'].append(os.path.basename(os.path.normpath(path))) #layer.name()
                res['path'].append(path)
            #for the file name: os.path.basename(uri).split('|')[0]
    #case: no folders available
    if len(res['name']) < 1:
        res = None
    #return the result even if empty
    return res


def testShapeFileExists(path, name):
    filename = path+"/"+name+".shp"
    exists = os.path.isfile(filename)
    return exists


def copyLayerToShapeFile(layer, path, name):
    #Get layer provider
    provider = layer.dataProvider()
    filename = path+"/"+name+".shp"
    fields = provider.fields()
    if layer.hasGeometryType():
        geometry = layer.wkbType()
    else:
        geometry = None
    srid = layer.crs()
    # create an instance of vector file writer, which will create the vector file.
    writer = QgsVectorFileWriter(filename, "CP1250", fields, geometry, srid, "ESRI Shapefile")
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", writer.hasError()
        return None
    # add features by iterating the values
    for feat in layer.getFeatures():
        writer.addFeature(feat)
    # delete the writer to flush features to disk
    del writer
    # open the newly created file
    vlayer = QgsVectorLayer(filename, name, "ogr")
    if not vlayer.isValid():
        print "Layer failed to load!"
        return None
    return vlayer


def createShapeFileFullLayer(path, name, srid, attributes, types, values, coords):
    # create new layer with given attributes
    filename = path+"/"+name+".shp"
    #create the required fields
    fields = QgsFields()
    for i, attr in enumerate(attributes):
        fields.append(QgsField(attr, types[i]))
    # create an instance of vector file writer, which will create the vector file.
    writer = None
    if len(coords) == 2:
        type = 'point'
        writer = QgsVectorFileWriter(filename, "CP1250", fields, QGis.WKBPoint, srid, "ESRI Shapefile")
    elif len(coords) == 4:
        type = 'line'
        writer = QgsVectorFileWriter(filename, "CP1250", fields, QGis.WKBLineString, srid, "ESRI Shapefile")
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", writer.hasError()
        return None
    # add features by iterating the values
    feat = QgsFeature()
    for i, val in enumerate(values):
        # add geometry
        try:
            if type == 'point':
                feat.setGeometry(QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]),float(val[coords[1]]))]))
            elif type == 'line':
                feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]),float(val[coords[1]])), \
                                                           QgsPoint(float(val[coords[2]]),float(val[coords[3]]))]))
        except: pass
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
        print "Layer failed to load!"
        return None
    return vlayer


def createShapeFileLayer(path, name, srid, attributes, types, geometrytype):
    # create new layer with given attributes
    # fixme: created table has no attributes.
    # use createShapeFileFullLayer instead
    filename = path+"/"+name+".shp"
    #create the required fields
    fields = QgsFields()
    for i, attr in enumerate(attributes):
        fields.append(QgsField(attr, types[i]))
    # create an instance of vector file writer, which will create the vector file.
    writer = None
    if 'point' in geometrytype.lower():
        writer = QgsVectorFileWriter(filename, "CP1250", fields, QGis.WKBPoint, srid, "ESRI Shapefile")
    elif 'line' in geometrytype.lower():
        writer = QgsVectorFileWriter(filename, "CP1250", fields, QGis.WKBLineString, srid, "ESRI Shapefile")
    elif 'polygon' in geometrytype.lower():
        writer = QgsVectorFileWriter(filename, "CP1250", fields, QGis.WKBPolygon, srid, "ESRI Shapefile")
    if writer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", writer.hasError()
        return None
    # delete the writer to flush features to disk (optional)
    del writer
    # open the newly created file
    vlayer = QgsVectorLayer(filename, name, "ogr")
    if not vlayer.isValid():
        print "Layer failed to open!"
        return None
    return vlayer


def insertShapeFileValues(layer, attributes, values, coords):
    # get the geometry type
    # fixme: not working yet. attribute ids must match those from table.
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
                    if geom_type in (0,3):
                        feat.setGeometry(QgsGeometry.fromPoint([QgsPoint(float(val[coords[0]]),float(val[coords[1]]))]))
                    elif geom_type in (1,4):
                        feat.setGeometry(QgsGeometry.fromPolyline([QgsPoint(float(val[coords[0]]),float(val[coords[1]])), \
                                                                   QgsPoint(float(val[coords[2]]),float(val[coords[3]]))]))
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
                #add new field if it doesn't exist
                if fields.indexFromName(name) == -1:
                    res = provider.addAttributes([QgsField(name, types[i])])
                    # keep position of attributes that are added, since name can change
                    attributes_pos[i] = count
                    count += 1
            #apply changes if any made
            if res:
                layer.updateFields()
        # update attribute values by iterating the layer's features
        res = False
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            #fields = provider.fields() #the fields must be retrieved again after the updateFields() method
            iter = layer.getFeatures()
            for i, feature in enumerate(iter):
                fid = feature.id()
                #to update the features the attribute/value pairs must be converted to a dictionary for each feature
                attrs = {}
                for j in attributes_pos.iterkeys():
                    field_id = attributes_pos[j]
                    val = values[i][j]
                    attrs.update({field_id: val})
                #update the layer with the corresponding dictionary
                res = provider.changeAttributeValues({fid: attrs})
            #apply changes if any made
            if res:
                layer.updateFields()
    return res


#---------------------------------------------
# PostGIS database specific functions
#---------------------------------------------

# newfeature: create all PostGIS functions
def listPostgisConnections():
    pass