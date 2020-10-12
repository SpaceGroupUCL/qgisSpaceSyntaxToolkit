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

import time
# Import the PyQt and QGIS libraries
from builtins import str
from builtins import zip

from qgis.PyQt.QtCore import (QThread, QVariant, pyqtSignal)
from qgis.core import (QgsFeatureRequest, NULL, QgsWkbTypes)

from esstoolkit.utilities import db_helpers as dbh, layer_field_helpers as lfh

# Import the debug library
is_debug = False
try:
    import pydevd_pycharm as pydevd

    has_pydevd = True
except ImportError:
    has_pydevd = False


class UnlinksVerification(QThread):
    verificationFinished = pyqtSignal(dict, list)
    verificationProgress = pyqtSignal(int)
    verificationError = pyqtSignal(str)

    def __init__(self, parentThread, parentObject, settings, axial, axial_id, unlinks, id):
        QThread.__init__(self, parentThread)
        self.parent = parentObject
        self.running = False
        self.verification_settings = settings
        self.axial_layer = axial
        self.unlinks_layer = unlinks
        self.unlink_type = unlinks.geometryType()
        self.user_id = id
        self.axial_id = axial_id

        # verification globals
        self.problem_nodes = []
        # error types to identify:
        self.unlink_errors = {'duplicate geometry': [], 'invalid geometry': [], 'multiple lines': [], 'single line': [],
                              'no lines': [],
                              'no line id': [], 'unmatched line id': [], 'same line id': []}

    def run(self):
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
        self.running = True
        # reset all the errors
        self.problem_nodes = []
        for k, v in self.unlink_errors.items():
            self.unlink_errors[k] = []
        datastore = self.unlinks_layer.storageType().lower()
        if 'spatialite' in datastore or 'postgresql' in datastore:
            # get the relevant layers names
            start_time = time.time()
            unlinkname = dbh.getDBLayerTableName(self.unlinks_layer)
            axialname = dbh.getDBLayerTableName(self.axial_layer)
            if not dbh.testSameDatabase([self.unlinks_layer, self.axial_layer]):
                self.verificationError.emit("The map layer must be in the same database as the unlinks layer.")
                return
            connection = dbh.getDBLayerConnection(self.unlinks_layer)
            # get the geometry column name and other properties
            if 'spatialite' in datastore:
                unlinkgeom = dbh.getSpatialiteGeometryColumn(connection, unlinkname)
                axialgeom = dbh.getSpatialiteGeometryColumn(connection, axialname)
            else:
                unlinkinfo = dbh.getPostgisLayerInfo(self.unlinks_layer)
                unlinkgeom = dbh.getPostgisGeometryColumn(connection, unlinkinfo['schema'], unlinkname)
                axialinfo = dbh.getPostgisLayerInfo(self.axial_layer)
                axialgeom = dbh.getPostgisGeometryColumn(connection, axialinfo['schema'], axialname)
                # todo: ensure that it has a spatial index
                # dbh.createPostgisSpatialIndex(self.connection, unlinkinfo['schema'], unlinkname, unlinkgeom)
            print("Preparing the map: %s" % str(time.time() - start_time))
            self.verificationProgress.emit(5)
            # update the unlinks
            start_time = time.time()
            if 'spatialite' in datastore:
                added = dbh.addSpatialiteColumns(connection, unlinkname, ['line1', 'line2'],
                                                [QVariant.Int, QVariant.Int])
            else:
                added = dbh.addPostgisColumns(connection, unlinkinfo['schema'], unlinkname, ['line1', 'line2'],
                                             [QVariant.Int, QVariant.Int])
            print("Updating unlinks: %s" % str(time.time() - start_time))
            self.verificationProgress.emit(10)
            # analyse the unlinks
            start_time = time.time()
            if 'spatialite' in datastore:
                self.spatialiteTestUnlinks(connection, unlinkname, unlinkgeom, axialname, axialgeom)
            else:
                self.postgisTestUnlinks(connection, unlinkinfo['schema'], unlinkname, unlinkgeom, axialinfo['schema'],
                                        axialname, axialgeom)
            print("Analysing unlinks: %s" % str(time.time() - start_time))
            self.verificationProgress.emit(100)
            connection.close()
        else:
            # add attributes if necessary
            lfh.addFields(self.unlinks_layer, ['line1', 'line2'], [QVariant.Int, QVariant.Int])
            # analyse the unlinks
            start_time = time.time()
            self.qgisTestUnlinks()
            print("Analysing unlinks: %s" % str(time.time() - start_time))
        self.verificationProgress.emit(100)
        # return the results
        self.problem_nodes = list(set(self.problem_nodes))
        self.verificationFinished.emit(self.unlink_errors, self.problem_nodes)
        return

    def stop(self):
        self.running = False
        self.terminate()

    def spatialiteTestUnlinks(self, connection, unlinkname, unlinkgeom, axialname, axialgeom):
        # this function checks the geometric validity of geometry using spatialite
        threshold = self.verification_settings['unlink_dist']
        if self.user_id == '':
            unlinkid = 'ROWID'
        else:
            unlinkid = self.user_id
        if self.axial_id == '':
            axialid = 'ROWID'
        else:
            axialid = self.axial_id
        steps = 90.0 / 9.0
        progress = 10.0
        # geometry is valid (generally)
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s" WHERE NOT ST_IsSimple(%s) OR NOT ST_IsValid(%s)""" % (
            unlinkid, unlinkname, unlinkgeom, unlinkgeom)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['invalid geometry'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse valid: %s" % str(time.time() - start_time))
        # duplicate geometry
        start_time = time.time()
        query = 'SELECT a."%s", a.line1, a.line2 FROM "%s" a, "%s" b WHERE a."%s" <> b."%s" AND ST_Equals(a."%s",b."%s") ' \
                'AND a.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name="%s" AND search_frame=b."%s")' \
                % (unlinkid, unlinkname, unlinkname, unlinkid, unlinkid, unlinkgeom, unlinkgeom, unlinkname, unlinkgeom)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['duplicate geometry'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse duplicate: %s" % str(time.time() - start_time))
        # no line id
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s" WHERE line1 IS NULL OR line2 IS NULL""" % (unlinkid, unlinkname)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['no line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse no id: %s" % str(time.time() - start_time))
        # same line id
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s" WHERE line1 = line2""" % (unlinkid, unlinkname)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['same line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse no id: %s" % str(time.time() - start_time))
        # create temp table for intersection results
        if self.unlink_type in (QgsWkbTypes.PolygonGeometry, QgsWkbTypes.LineGeometry):
            operat_a = 'ST_Intersects'
            operat_b = ''
        else:
            operat_a = 'PtDistWithin'
            operat_b = ',%s' % threshold
        start_time = time.time()
        query = """CREATE TEMP TABLE "temp_unlinks_result" AS SELECT a."%s" unlinkid, b."%s" lineid FROM "%s" a, "%s" b WHERE %s(a."%s",b."%s"%s)""" \
                % (unlinkid, axialid, unlinkname, axialname, operat_a, unlinkgeom, axialgeom, operat_b)
        header, data, error = dbh.executeSpatialiteQuery(connection, query, commit=True)
        progress += steps
        self.verificationProgress.emit(progress)
        print("temp unlinks result: %s" % str(time.time() - start_time))
        # 'multiple lines'
        start_time = time.time()
        query = 'SELECT "%s", line1, line2 FROM "%s" WHERE "%s" IN (SELECT unlinkid FROM (SELECT unlinkid, count(unlinkid) freq ' \
                'FROM temp_unlinks_result GROUP BY unlinkid) WHERE freq > 2)' % (unlinkid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['multiple lines'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse multiple lines: %s" % str(time.time() - start_time))
        # 'single line'
        start_time = time.time()
        query = 'SELECT "%s", line1, line2 FROM "%s" WHERE "%s" IN (SELECT unlinkid FROM (SELECT unlinkid, count(unlinkid) freq ' \
                'FROM temp_unlinks_result GROUP BY unlinkid) WHERE freq = 1)' % (unlinkid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['single line'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse single lines: %s" % str(time.time() - start_time))
        # 'no lines'
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s" WHERE "%s" NOT IN (SELECT unlinkid FROM temp_unlinks_result GROUP BY unlinkid)""" \
                % (unlinkid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['no lines'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse no lines: %s" % str(time.time() - start_time))
        # 'unmatched line id'
        start_time = time.time()
        query = """SELECT b."%s", b.line1, b.line2 FROM temp_unlinks_result a, "%s" b WHERE a.unlinkid = b."%s" AND (a.lineid <> b.line1 AND a.lineid <> b.line2)""" \
                % (unlinkid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['unmatched line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse unmatched id: %s" % str(time.time() - start_time))

    def postgisTestUnlinks(self, connection, unlinkschema, unlinkname, unlinkgeom, axialschema, axialname, axialgeom):
        # this function checks the geometric validity of geometry using spatialite
        threshold = self.verification_settings['unlink_dist']
        # in postgis we need a unique id because it doesn't have rowid
        if self.user_id == '' or self.axial_id == '':
            return
        else:
            unlinkid = self.user_id
            axialid = self.axial_id
        steps = 90.0 / 9.0
        progress = 10.0
        # geometry is valid (generally)
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s"."%s" WHERE NOT ST_IsSimple("%s") OR NOT ST_IsValid("%s")""" \
                % (unlinkid, unlinkschema, unlinkname, unlinkgeom, unlinkgeom)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['invalid geometry'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse valid: %s" % str(time.time() - start_time))
        # duplicate geometry
        start_time = time.time()
        query = """SELECT a."%s", a.line1, a.line2 FROM "%s"."%s" a, "%s".""%s" b WHERE a."%s" <> b."%s" AND ST_Equals(a."%s",b."%s")""" \
                % (unlinkid, unlinkschema, unlinkname, unlinkschema, unlinkname, unlinkid, unlinkid, unlinkgeom,
                   unlinkgeom)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['duplicate geometry'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse duplicate: %s" % str(time.time() - start_time))
        # no line id
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s"."%s" WHERE line1 IS NULL OR line2 IS NULL""" % (
            unlinkid, unlinkschema, unlinkname)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['no line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse no id: %s" % str(time.time() - start_time))
        # same line id
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s"."%s" WHERE line1 = line2""" % (
            unlinkid, unlinkschema, unlinkname)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['same line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse same id: %s" % str(time.time() - start_time))
        # create temp table for intersection results
        if self.unlink_type in (QgsWkbTypes.PolygonGeometry, QgsWkbTypes.LineGeometry):
            operat_a = 'ST_Intersects'
            operat_b = ''
        else:
            operat_a = 'ST_DWithin'
            operat_b = ',%s' % threshold
        start_time = time.time()
        query = """CREATE TEMP TABLE "temp_unlinks_result" AS SELECT a."%s" unlinkid, b."%s" lineid FROM "%s"."%s" a, "%s"."%s" b WHERE %s(a."%s",b."%s"%s)""" \
                % (unlinkid, axialid, unlinkschema, unlinkname, axialschema, axialname, operat_a, unlinkgeom, axialgeom,
                   operat_b)
        header, data, error = dbh.executePostgisQuery(connection, query, commit=True)
        progress += steps
        self.verificationProgress.emit(progress)
        print("temp unlinks result: %s" % str(time.time() - start_time))
        # 'multiple lines'
        start_time = time.time()
        query = 'SELECT "%s", line1, line2 FROM "%s"."%s" WHERE "%s" IN (SELECT unlinkid FROM (SELECT unlinkid, count(*) freq ' \
                'FROM temp_unlinks_result GROUP BY unlinkid) a WHERE freq > 2)' % (
                    unlinkid, unlinkschema, unlinkname, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['multiple lines'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse multiple lines: %s" % str(time.time() - start_time))
        # 'single line'
        start_time = time.time()
        query = 'SELECT "%s", line1, line2 FROM "%s"."%s" WHERE "%s" IN (SELECT unlinkid FROM (SELECT unlinkid, count(*) freq ' \
                'FROM temp_unlinks_result GROUP BY unlinkid) a WHERE freq = 1)' % (
                    unlinkid, unlinkschema, unlinkname, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['single line'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse single lines: %s" % str(time.time() - start_time))
        # 'no lines'
        start_time = time.time()
        query = """SELECT "%s", line1, line2 FROM "%s"."%s" WHERE "%s" NOT IN (SELECT unlinkid FROM temp_unlinks_result GROUP BY unlinkid)""" \
                % (unlinkid, unlinkschema, unlinkname, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['no lines'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse no lines: %s" % str(time.time() - start_time))
        # 'unmatched line id'
        start_time = time.time()
        query = """SELECT b."%s", b.line1, b.line2 FROM temp_unlinks_result a, "%s"."%s" b WHERE a.unlinkid = b."%s" AND (a.lineid <> b.line1 AND a.lineid <> b.line2)""" \
                % (unlinkid, unlinkschema, unlinkname, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(data)
            self.unlink_errors['unmatched line id'] = nodes
        progress += steps
        self.verificationProgress.emit(progress)
        print("analyse unmatched id: %s" % str(time.time() - start_time))

    def qgisTestUnlinks(self):
        # this function checks the validity of unlinks using QGIS
        start_time = time.time()
        lfh.addFields(self.unlinks_layer, ['line1', 'line2'], [QVariant.LongLong, QVariant.LongLong])
        line1 = lfh.getFieldIndex(self.unlinks_layer, 'line1')
        line2 = lfh.getFieldIndex(self.unlinks_layer, 'line2')
        # unlinksindex = createIndex(self.unlinks_layer)
        axialindex = lfh.createIndex(self.axial_layer)
        print("Preparing the map: %s" % str(time.time() - start_time))
        # prepare unlinks to test
        self.verificationProgress.emit(5)
        threshold = self.verification_settings['unlink_dist']
        chunk = 100.0 / float(self.unlinks_layer.featureCount())
        steps = chunk / 6.0
        progress = 0.0
        if self.user_id == '':
            features = self.unlinks_layer.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([line1, line2]))
        else:
            field = lfh.getFieldIndex(self.unlinks_layer, self.user_id)
            features = self.unlinks_layer.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([field, line1, line2]))
        # run unlinks tests
        for feature in features:
            has_problem = False
            geom = feature.geometry()
            id1 = feature.attribute('line1')
            id2 = feature.attribute('line2')
            if self.user_id == '':
                id = feature.id()
            else:
                id = feature.attribute(self.user_id)
            # geometry is valid (generally)
            if not geom.isGeosValid() or geom.isEmpty():
                has_problem = True
                self.axial_errors['invalid geometry'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            # no line id
            if id1 is NULL or id2 is NULL:
                has_problem = True
                self.unlink_errors['no line id'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            # same line id
            if id1 == id2 and id1 is not NULL:
                has_problem = True
                self.unlink_errors['same line id'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            # duplicate geometry with other unlinks
            if self.user_id == '':
                request = QgsFeatureRequest().setSubsetOfAttributes([])
            else:
                field = lfh.getFieldIndex(self.unlinks_layer, self.user_id)
                request = QgsFeatureRequest().setSubsetOfAttributes([field])
            targets = self.unlinks_layer.getFeatures(request)
            for target in targets:
                if self.user_id == '':
                    tid = target.id()
                else:
                    tid = target.attribute(self.user_id)
                if tid != id and geom.isGeosEqual(target.geometry()):
                    has_problem = True
                    self.unlink_errors['duplicate geometry'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            # get intersection results
            if self.unlink_type == QgsWkbTypes.PointGeometry and threshold > 0:
                buff = geom.buffer(threshold, 4)
            else:
                buff = geom
            box = buff.boundingBox()
            request = QgsFeatureRequest()
            if axialindex:
                # should be faster to retrieve from index (if available)
                ints = axialindex.intersects(box)
                request.setFilterFids(ints)
            else:
                # can retrieve objects using bounding box
                request.setFilterRect(box)
            if self.axial_id == '':
                request.setSubsetOfAttributes([])
            else:
                field = lfh.getFieldIndex(self.axial_layer, self.axial_id)
                request.setSubsetOfAttributes([field])
            axiallines = self.axial_layer.getFeatures(request)
            intersects = []
            for line in axiallines:
                if self.axial_id == '':
                    id_b = line.id()
                else:
                    id_b = line.attribute(self.axial_id)
                if line.geometry().intersects(buff):
                    intersects.append(id_b)
                    # 'unmatched line id'
                    if id_b != id1 and id_b != id2:
                        has_problem = True
                        self.unlink_errors['unmatched line id'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            # 'multiple lines'
            if len(intersects) > 2:
                has_problem = True
                self.unlink_errors['multiple lines'].append(id)
            # 'single line'
            elif len(intersects) == 1:
                has_problem = True
                self.unlink_errors['single line'].append(id)
            # 'no lines'
            elif len(intersects) == 0:
                has_problem = True
                self.unlink_errors['no lines'].append(id)
            progress += steps
            self.verificationProgress.emit(progress)
            if has_problem:
                self.problem_nodes.append((id, id1, id2))


class UnlinksIdUpdate(QThread):
    verificationFinished = pyqtSignal()
    verificationProgress = pyqtSignal(int)
    verificationError = pyqtSignal(str)

    def __init__(self, parentThread, parentObject, unlinks, id, axial, axial_id, threshold):
        QThread.__init__(self, parentThread)
        self.parent = parentObject
        self.running = False
        self.threshold = threshold
        self.axial_layer = axial
        self.unlinks_layer = unlinks
        self.unlink_type = unlinks.geometryType()
        self.user_id = id
        self.axial_id = axial_id

    def run(self):
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
        self.running = True
        # get line ids (to match the object ids in the map)
        unlinktype = self.unlinks_layer.geometryType()
        datastore = self.unlinks_layer.storageType().lower()
        if 'spatialite' in datastore or 'postgresql' in datastore:
            # test the relevant layers
            if not dbh.testSameDatabase([self.unlinks_layer, self.axial_layer]):
                self.verificationError.emit("The map layer must be in the same database as the unlinks layer.")
                return
            connection = dbh.getDBLayerConnection(self.unlinks_layer)
            if 'spatialite' in datastore:
                self.spatialiteUpdateIDs(connection, unlinktype)
            else:
                # get the layer id columns, required in postgis
                if self.user_id == '' or self.axial_id == '':
                    self.verificationError.emit("The unlinks layer needs an id attribute or primary key.")
                else:
                    self.postgisUpdateIDs(connection, unlinktype)
            connection.close()
        else:
            self.qgisUpdateIDs(unlinktype)
        self.verificationProgress.emit(100)
        self.verificationFinished.emit()
        return

    def stop(self):
        self.running = False
        # self.terminate()

    def spatialiteUpdateIDs(self, connection, unlinktype):
        # get the relevant layers names
        unlinkname = dbh.getDBLayerTableName(self.unlinks_layer)
        axialname = dbh.getDBLayerTableName(self.axial_layer)
        # get the geometry column name and other properties
        unlinkgeom = dbh.getSpatialiteGeometryColumn(connection, unlinkname)
        axialgeom = dbh.getSpatialiteGeometryColumn(connection, axialname)
        # add line id columns
        added = dbh.addSpatialiteColumns(connection, unlinkname, ['line1', 'line2'], [QVariant.Int, QVariant.Int])
        self.verificationProgress.emit(22)
        # prepare variables for update query
        if self.user_id == '':
            unlinkid = 'ROWID'
        else:
            unlinkid = self.user_id
            if not lfh.isValidIdField(self.unlinks_layer, unlinkid):
                # update unlink id column
                query = 'UPDATE %s SET %s = ROWID' % (unlinkname, unlinkid)
                header, data, error = dbh.executeSpatialiteQuery(connection, query, commit=True)
        if self.axial_id == '':
            axialid = 'ROWID'
        else:
            axialid = self.axial_id
        if unlinktype in (QgsWkbTypes.PolygonGeometry, QgsWkbTypes.LineGeometry):
            operat_a = 'ST_Intersects'
            operat_b = ''
        else:
            operat_a = 'PtDistWithin'
            operat_b = ',%s' % self.threshold
        self.verificationProgress.emit(33)
        # update line id columns
        query = 'UPDATE %s SET line1 = (SELECT c.line FROM (SELECT b.%s unlink, a.%s line FROM ' \
                '%s a, %s b WHERE %s(a.%s,b.%s%s) ORDER BY b.%s, a.%s ASC)' \
                ' c WHERE c.unlink = %s.%s)' \
                % (unlinkname, unlinkid, axialid, axialname, unlinkname, operat_a, axialgeom, unlinkgeom, operat_b,
                   unlinkid, axialid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query, commit=True)
        self.verificationProgress.emit(66)
        query = 'UPDATE %s SET line2 = (SELECT c.line FROM (SELECT b.%s unlink, a.%s line FROM ' \
                '%s a, %s b WHERE %s(a.%s,b.%s%s) ORDER BY b.%s, a.%s DESC)' \
                ' c WHERE c.unlink = %s.%s)' \
                % (unlinkname, unlinkid, axialid, axialname, unlinkname, operat_a, axialgeom, unlinkgeom, operat_b,
                   unlinkid, axialid, unlinkname, unlinkid)
        header, data, error = dbh.executeSpatialiteQuery(connection, query, commit=True)
        query = """SELECT UpdateLayerStatistics("%s")""" % unlinkname
        header, data, error = dbh.executeSpatialiteQuery(connection, query)
        self.verificationProgress.emit(99)

    def postgisUpdateIDs(self, connection, unlinktype):
        unlinkid = self.user_id
        axialid = self.axial_id
        # get the geometry column name and other properties
        unlinkinfo = dbh.getPostgisLayerInfo(self.unlinks_layer)
        unlinkname = unlinkinfo['table']
        unlinkschema = unlinkinfo['schema']
        unlinkgeom = dbh.getPostgisGeometryColumn(connection, unlinkschema, unlinkname)
        # todo: ensure that it has a spatial index
        # dbh.createPostgisSpatialIndex(connection, unlinkschema, unlinkname, unlinkgeom)
        axialinfo = dbh.getPostgisLayerInfo(self.axial_layer)
        axialname = axialinfo['table']
        axialschema = axialinfo['schema']
        axialgeom = dbh.getPostgisGeometryColumn(connection, axialschema, axialname)
        # todo: ensure that it has a spatial index
        # dbh.createPostgisSpatialIndex(connection, axialschema, axialname, axialgeom)
        # add line id columns
        added = dbh.addPostgisColumns(connection, unlinkschema, unlinkname, ['line1', 'line2'],
                                     [QVariant.Int, QVariant.Int])
        self.verificationProgress.emit(33)
        # prepare variables for update query
        if unlinktype in (QgsWkbTypes.PolygonGeometry, QgsWkbTypes.LineGeometry):
            operat_a = 'ST_Intersects'
            operat_b = ''
        else:
            operat_a = 'ST_DWithin'
            operat_b = ',%s' % self.threshold
        # update line id columns
        query = 'UPDATE "%s"."%s" ul SET line1 = ax.line FROM (SELECT b."%s" unlink, a."%s" line FROM ' \
                '"%s"."%s" a, "%s"."%s" b WHERE %s(a."%s",b."%s"%s) ORDER BY b."%s", a."%s" ASC) ax ' \
                'WHERE ax.unlink = ul."%s"' \
                % (unlinkschema, unlinkname, unlinkid, axialid, axialschema, axialname, unlinkschema, unlinkname,
                   operat_a, axialgeom, unlinkgeom, operat_b, unlinkid, axialid, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query, commit=True)
        self.verificationProgress.emit(66)
        query = 'UPDATE "%s"."%s" ul SET line2 = ax.line FROM (SELECT b."%s" unlink, a."%s" line FROM ' \
                '"%s"."%s" a, "%s"."%s" b WHERE %s(a."%s",b."%s"%s) ORDER BY b."%s", a."%s" DESC) ax ' \
                'WHERE ax.unlink = ul."%s"' \
                % (unlinkschema, unlinkname, unlinkid, axialid, axialschema, axialname, unlinkschema, unlinkname,
                   operat_a, axialgeom, unlinkgeom, operat_b, unlinkid, axialid, unlinkid)
        header, data, error = dbh.executePostgisQuery(connection, query, commit=True)
        connection.close()
        self.verificationProgress.emit(99)

    def qgisUpdateIDs(self, unlinktype):
        # create spatial index
        unlinksindex = lfh.createIndex(self.unlinks_layer)
        axialindex = lfh.createIndex(self.axial_layer)
        # add line id columns if necessary
        lfh.addFields(self.unlinks_layer, ['line1', 'line2'], [QVariant.Int, QVariant.Int])
        line1 = lfh.getFieldIndex(self.unlinks_layer, 'line1')
        line2 = lfh.getFieldIndex(self.unlinks_layer, 'line2')
        update_id = False
        if self.user_id == '':
            features = self.unlinks_layer.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([line1, line2]))
        else:
            update_id = not lfh.isValidIdField(self.unlinks_layer, self.user_id)
            field = lfh.getFieldIndex(self.unlinks_layer, self.user_id)
            features = self.unlinks_layer.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([field, line1, line2]))
        # run unlinks tests
        chunk = 100.0 / float(self.unlinks_layer.featureCount())
        steps = chunk / 3.0
        progress = 0.0
        for feature in features:
            geom = feature.geometry()
            # get intersection results
            if unlinktype == QgsWkbTypes.PointGeometry and self.threshold > 0.0:
                buff = geom.buffer(self.threshold, 4)
            else:
                buff = geom
            box = buff.boundingBox()
            request = QgsFeatureRequest()
            if axialindex:
                # should be faster to retrieve from index (if available)
                ints = axialindex.intersects(box)
                request.setFilterFids(ints)
            else:
                # can retrieve objects using bounding box
                request.setFilterRect(box)
            if self.axial_id == '':
                request.setSubsetOfAttributes([])
            else:
                ax_field = lfh.getFieldIndex(self.axial_layer, self.axial_id)
                request.setSubsetOfAttributes([ax_field])
            axiallines = self.axial_layer.getFeatures(request)
            progress += steps
            self.verificationProgress.emit(progress)
            # parse intersection results
            intersects = []
            for line in axiallines:
                if self.axial_id == '':
                    id_b = line.id()
                else:
                    id_b = line.attribute(self.axial_id)
                if buff.intersects(line.geometry()):
                    intersects.append(id_b)
            progress += steps
            self.verificationProgress.emit(progress)
            # update line ids in unlinks table
            attrs = {line1: NULL, line2: NULL}
            if len(intersects) == 1:
                attrs = {line1: intersects[0]}
            elif len(intersects) > 1:
                attrs = {line1: intersects[0], line2: intersects[1]}
            if update_id and field:
                attrs[field] = feature.id()
            self.unlinks_layer.dataProvider().changeAttributeValues({feature.id(): attrs})
            progress += steps
            self.verificationProgress.emit(progress)
        self.unlinks_layer.updateFields()
