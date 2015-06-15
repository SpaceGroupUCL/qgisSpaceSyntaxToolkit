# -*- coding: utf-8 -*-
"""
/***************************************************************************
 essToolkit
                            Space Syntax Toolkit
 Set of tools for essential space syntax network analysis and results exploration
                              -------------------
        begin                : 2014-04-01
        copyright            : (C) 2015, UCL
        author               : Jorge Gil
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from .. import utility_functions as uf

import time

try:
    import igraph as ig
    has_igraph = False
except (ImportError, NameError), e:
    has_igraph = False

# try to import installed networx, if not available use the one shipped with the esstoolkit
try:
    import networkx as nx
    has_networkx = True
except ImportError, e:
    has_networkx = False

# Import the debug library
try:
    import pydevd
    has_pydevd = True
except ImportError, e:
    has_pydevd = False
is_debug = False


class AxialVerification(QThread):
    verificationFinished = pyqtSignal(dict, list)
    verificationProgress = pyqtSignal(int)
    verificationError = pyqtSignal(str)

    def __init__( self, parentThread, parentObject, settings, axial, id, unlinks, links):
        QThread.__init__( self, parentThread)
        self.parent = parentObject
        self.running = False
        self.verification_settings = settings
        self.axial_layer = axial
        self.unlinks_layer = unlinks
        self.links_layer = links
        self.user_id = id

        # verification globals
        self.problem_nodes = []
        # error types to identify:
        self.axial_errors = {'orphan':[],'island':[],'short line':[],'invalid geometry':[],'polyline':[],\
                            'coinciding points':[],'small line':[],'duplicate geometry':[],'overlap':[]}

    def run(self):
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
        self.running = True
        # reset all the errors
        self.problem_nodes = []
        for k, v in self.axial_errors.iteritems():
            self.axial_errors[k]=[]
        provider = self.axial_layer.storageType()
        #caps = self.axial_layer.dataProvider().capabilities()
        graph_links = []
        datastore = provider.lower()
        if 'spatialite' in datastore or 'postgis' in datastore:
            # get the relevant layers
            unlinkname = ''
            unlinkschema = ''
            if self.unlinks_layer:
                unlinkname = uf.getDBLayerTableName(self.unlinks_layer)
                if not uf.testSameDatabase([self.unlinks_layer, self.axial_layer]):
                    self.verificationError.emit("The map layer must be in the same database as the unlinks layer.")
                    return
                if 'postgresql' in datastore:
                    unlinkschema = uf.getPostgisLayerInfo(self.unlinks_layer)['schema']
            linkname = ''
            linkschema = ''
            if self.links_layer:
                linkname = uf.getDBLayerTableName(self.links_layer)
                if not uf.testSameDatabase([self.links_layer, self.axial_layer]):
                    self.verificationError.emit("The map layer must be in the same database as the links layer.")
                    return
                if 'postgresql' in datastore:
                    linkschema = uf.getPostgisLayerInfo(self.links_layer)['schema']
            axialname = uf.getDBLayerTableName(self.axial_layer)
            if self.user_id == '':
                self.user_id = uf.getDBLayerPrimaryKey(self.axial_layer)
            # get the geometry column name and other properties
            # always check if the operation has been cancelled before proceeding.
            # this would come up only once if the thread was based on a loop, to break it.
            if not self.running: return
            start_time = time.time()
            geomname = ''
            # could use this generic but I want to force a spatial index
            #geomname = uf.getDBLayerGeometryColumn(self.axial_layer)
            connection = uf.getDBLayerConnection(self.axial_layer)
            if 'spatialite' in datastore:
                geomname = uf.getSpatialiteGeometryColumn(connection, axialname)
            else:
                layerinfo = uf.getPostgisLayerInfo(self.axial_layer)
                geomname = uf.getPostgisGeometryColumn(connection, layerinfo['schema'], axialname)
                # todo: ensure that it has a spatial index
                #uf.createPostgisSpatialIndex(onnection, layerinfo['schema'], axialname, geomname)
            if is_debug: print "Preparing the map: %s"%str(time.time()-start_time)
            self.verificationProgress.emit(5)
            # analyse the geometry
            if not self.running or not geomname:
                return
            start_time = time.time()
            if 'spatialite' in datastore:
                self.spatialiteTestGeometry(connection, axialname, geomname)
            else:
                self.postgisTestGeometry(connection, layerinfo['schema'], axialname, geomname)
            if is_debug: print "Analysing geometry: %s"%str(time.time()-start_time)
            self.verificationProgress.emit(80)
            # build the topology
            if not self.running: return
            if has_igraph or has_networkx:
                start_time = time.time()
                if 'spatialite' in datastore:
                    graph_links = self.spatialiteBuildTopology(connection, axialname, geomname, unlinkname, linkname)
                else:
                    graph_links = self.postgisBuildTopology(connection, layerinfo['schema'], axialname, geomname, unlinkschema, unlinkname, linkschema, linkname)
                if is_debug: print "Building topology: %s"%str(time.time()-start_time)
            self.verificationProgress.emit(90)
            connection.close()
        else:
            # create spatial index
            if not self.running: return
            start_time = time.time()
            index = uf.createIndex(self.axial_layer)
            if is_debug: print "Creating spatial index: %s"%str(time.time()-start_time)
            self.verificationProgress.emit(5)
            # analyse the geometry and topology
            if not self.running: return
            start_time = time.time()
            graph_links = self.qgisGeometryTopologyTest(self.axial_layer, index, self.unlinks_layer, self.links_layer)
            if is_debug: print "Analysing geometry and topology: %s"%str(time.time()-start_time)
        # analyse the topology with igraph or networkx
        if not self.running: return
        if len(graph_links) > 0 and (has_igraph or has_networkx):
            start_time = time.time()
            # get axial node ids
            if self.user_id == '':
                axialids = self.axial_layer.allFeatureIds()
            else:
                axialids, ids = uf.getFieldValues(self.axial_layer, self.user_id)
            # uses igraph to test islands. looks for orphans with the geometry test
            if has_igraph:
                self.igraphTestTopology(graph_links, axialids)
            elif has_networkx:
                self.networkxTestTopology(graph_links, axialids)
            if is_debug: print "Analysing topology: %s"%str(time.time()-start_time)
        self.verificationProgress.emit(100)
        # return the results
        self.problem_nodes = list(set(self.problem_nodes))
        self.verificationFinished.emit(self.axial_errors, self.problem_nodes)
        return

    def stop(self):
        self.running = False
        self.exit()

    def igraphTestTopology(self, graph_links, graph_nodes):
        # create an igraph graph object and store the axial links
        try:
            g = ig.Graph(graph_links)
        except:
            return False
        # ideally g would be created with a list of edges based on 0 indexed and continuous vertices
        # but sqlite rowid is 1 indexed and might have gaps as it is a unique and persistent numbering
        # igraph adds 0 and other missing vertices, these must be identified and removed
        to_delete = []
        for v in g.vs:
            if v.index not in graph_nodes:
                to_delete.append(v.index)
        g.delete_vertices(to_delete)
        # deleting 0 reassigns all the indices, and creates a new 0.
        # the vertex reference to use to identify features must be a fid attribute
        g.vs["fid"] = graph_nodes
        if not g.is_connected():
            start_time = time.time()
            components = g.components()
            if components.__len__ > 1:
                giant = components.giant().vcount()
                islands = []
                # get vertex ids
                for i, cluster in enumerate(components):
                    # identify orphans
                    if len(cluster) == 1:
                        node = g.vs[cluster]['fid'][0]
                        self.axial_errors['orphan'].append(node)
                        self.problem_nodes.append(node)
                    # identify islands
                    elif len(cluster) > 1 and len(cluster) != giant:
                        nodes = g.vs[cluster]['fid']
                        islands.append(nodes)
                        self.problem_nodes.extend(nodes)
                # add results to the list of problems
                if islands:
                    self.axial_errors['island'] = islands
            if is_debug: print "analyse orphans/islands: %s"%str(time.time()-start_time)
        return True

    def networkxTestTopology(self, graph_links, graph_nodes):
        # create a networkx graph object and store the axial links
        try:
            g = nx.Graph(graph_links)
        except:
            return False
        # networkx just accepts all sorts of node ids... no need to fix
        if not nx.is_connected(g):
            start_time = time.time()
            components = sorted(nx.connected_components(g), key=len, reverse=True)
            if len(components) > 1:
                islands = []
                # get vertex ids
                for cluster in components[1:len(components)]:
                    # identify orphans
                    if len(cluster) == 1:
                        node = cluster[0]
                        self.axial_errors['orphan'].append(node)
                        self.problem_nodes.append(node)
                    # identify islands
                    elif len(cluster) > 1:
                        nodes = cluster
                        islands.append(nodes)
                        self.problem_nodes.extend(nodes)
                # add results to the list of problems
                if islands:
                    self.axial_errors['island'] = islands
            if is_debug: print "analyse orphans/islands: %s"%str(time.time()-start_time)
        return True

    # spatialite based functions
    #
    def spatialiteTestGeometry(self, connection, axialname, geomname):
        # this function checks the geometric validity of geometry using spatialite
        length = self.verification_settings['ax_min']
        threshold = self.verification_settings['ax_dist']
        if self.user_id == '':
            idcol = 'ROWID'
        else:
            idcol = self.user_id
        # geometry is valid (generally)
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s" WHERE NOT ST_IsSimple("%s") OR NOT ST_IsValid("%s")"""%(idcol, axialname, geomname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['invalid geometry'] = nodes
        self.verificationProgress.emit(10)
        if is_debug: print "analyse valid: %s"%str(time.time()-start_time)
        # geometry is polyline
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s" WHERE ST_NPoints("%s") <> 2 """%(idcol, axialname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['polyline'] = nodes
        self.verificationProgress.emit(15)
        if is_debug: print "analyse polyline: %s"%str(time.time()-start_time)
        # has two coinciding points
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s" WHERE ST_Equals(ST_StartPoint("%s"),ST_EndPoint("%s"))"""%(idcol, axialname, geomname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['coinciding points'] = nodes
        self.verificationProgress.emit(20)
        if is_debug: print "analyse coinciding: %s"%str(time.time()-start_time)
        # small lines, with small length
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s" WHERE ST_Length("%s")<%s"""%(idcol, axialname, geomname,length)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['small line'] = nodes
        self.verificationProgress.emit(25)
        if is_debug: print "analyse small: %s"%str(time.time()-start_time)
        # short lines, just about touch without intersecting
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s" a, "%s" b WHERE a."%s" <> b."%s" AND NOT ST_Intersects(a."%s",b."%s") AND ' \
                '(PtDistWithin(ST_StartPoint(a."%s"),b."%s",%s) OR PtDistWithin(ST_EndPoint(a."%s"),b."%s",%s)) ' \
                'AND a.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name="%s" AND search_frame=b."%s")' \
                %(idcol, axialname, axialname, idcol, idcol, geomname, geomname, geomname, geomname, threshold,
                  geomname, geomname, threshold, axialname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['short line'] = nodes
        self.verificationProgress.emit(40)
        if is_debug: print "analyse short: %s"%str(time.time()-start_time)
        # duplicate geometry
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s" a, "%s" b WHERE a."%s" <> b."%s" AND ST_Equals(a."%s",b."%s") ' \
                'AND a.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name="%s" AND search_frame=b."%s")' \
                %(idcol, axialname, axialname, idcol, idcol, geomname, geomname, axialname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['duplicate geometry'] = nodes
        self.verificationProgress.emit(60)
        if is_debug: print "analyse duplicate: %s"%str(time.time()-start_time)
        # geometry overlaps
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s" a, "%s" b WHERE a."%s" <> b."%s" AND NOT ST_Equals(a."%s",b."%s") AND ST_Overlaps(a."%s",b."%s") ' \
            'AND a.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name="%s" AND search_frame=b."%s")' \
            %(idcol, axialname, axialname, idcol, idcol, geomname, geomname, geomname, geomname, axialname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['overlap'] = nodes
        self.verificationProgress.emit(80)
        if is_debug: print "analyse overlap: %s"%str(time.time()-start_time)
        # the overlap function is very accurate and rare in GIS
        # an alternative function with buffer is too slow

    def spatialiteBuildTopology(self, connection, axialname, geomname, unlinkname, linkname):
        # this function builds the axial map topology using spatialite. it's much faster.
        if self.user_id == '':
            idcol = 'ROWID'
        else:
            idcol = self.user_id
        # remove temporary table if already exists
        graphname = "temp_axial_topology"
        header, data, error = uf.executeSpatialiteQuery(connection,"""DROP TABLE IF EXISTS "%s" """ % graphname)
        start_time = time.time()
        # create a new temporary table
        query = """CREATE TEMP TABLE %s (pk_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, a_fid INTEGER, b_fid INTEGER)"""%(graphname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        # calculate edges from intersecting feature pairs
        query = 'INSERT INTO %s (a_fid, b_fid) SELECT DISTINCT CASE WHEN a."%s" < b."%s" THEN a."%s" ELSE b."%s" END AS least_col, ' \
                'CASE WHEN a."%s" > b."%s" THEN a."%s" ELSE b."%s" END AS greatest_col ' \
                'FROM "%s" a, "%s" b WHERE a."%s" <> b."%s" AND Intersects(a."%s",b."%s") ' \
                'AND a.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name="%s" AND search_frame=b."%s")' \
                %(graphname, idcol, idcol, idcol, idcol, idcol, idcol, idcol, idcol, axialname, axialname, idcol, idcol,
                  geomname, geomname, axialname, geomname)
        header, data, error = uf.executeSpatialiteQuery(connection, query, commit=True)
        if is_debug: print "Building the graph: %s"%str(time.time()-start_time)
        # eliminate unlinks
        if unlinkname:
            if uf.fieldExists(uf.getLayerByName(unlinkname),'line1') and uf.fieldExists(uf.getLayerByName(unlinkname),'line2'):
                start_time = time.time()
                query = 'DELETE FROM %s WHERE cast(a_fid as text)||"_"||cast(b_fid as text) in (SELECT cast(line1 as text)||"_"||cast(line2 as text) FROM "%s") ' \
                        'OR cast(b_fid as text)||"_"||cast(a_fid as text) in (SELECT cast(line1 as text)||"_"||cast(line2 as text) FROM "%s")' \
                        %(graphname, unlinkname, unlinkname)
                header, data, error = uf.executeSpatialiteQuery(connection, query, commit=True)
                if is_debug: print "Unlinking the graph: %s"%str(time.time()-start_time)
        # newfeature: implement inserting links
        # return all the links to build the graph
        query = """SELECT a_fid, b_fid FROM "%s";"""%(graphname)
        header, data, error = uf.executeSpatialiteQuery(connection, query)
        return data

    # Postgis based functions
    #
    def postgisTestGeometry(self, connection, schema, axialname, geomname):
        # this function checks the geometric validity of geometry using spatialite
        length = self.verification_settings['ax_min']
        threshold = self.verification_settings['ax_dist']
        idcol = self.user_id
        # in postgis we need a unique id because it doesn't have rowid
        if idcol == '':
            return
        # geometry is valid (generally)
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s"."%s" WHERE NOT ST_IsSimple("%s") OR NOT ST_IsValid("%s")""" % (idcol, schema, axialname, geomname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['invalid geometry'] = nodes
        self.verificationProgress.emit(10)
        if is_debug: print "analyse valid: %s" % str(time.time()-start_time)
        # geometry is polyline
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s"."%s" WHERE ST_NPoints("%s") <> 2 """ % (idcol, schema, axialname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['polyline'] = nodes
        self.verificationProgress.emit(15)
        if is_debug: print "analyse polyline: %s" % str(time.time()-start_time)
        # has two coinciding points
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s"."%s" WHERE ST_Equals(ST_StartPoint("%s"),ST_EndPoint("%s"))""" % (idcol, schema, axialname, geomname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['coinciding points'] = nodes
        self.verificationProgress.emit(20)
        if is_debug: print "analyse coinciding: %s" % str(time.time()-start_time)
        # small lines, with small length
        if not self.running: return
        start_time = time.time()
        query = """SELECT "%s" FROM "%s"."%s" WHERE ST_Length("%s")<%s""" % (idcol, schema, axialname, geomname,length)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['small line'] = nodes
        self.verificationProgress.emit(25)
        if is_debug: print "analyse small: %s" % str(time.time()-start_time)
        # short lines, just about touch without intersecting
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s"."%s" a, "%s"."%s" b WHERE a."%s" <> b."%s" AND NOT ST_Intersects(a."%s",b."%s") AND ' \
                '(ST_DWithin(ST_StartPoint(a."%s"),b."%s",%s) OR ST_DWithin(ST_EndPoint(a."%s"),b."%s",%s))'\
                % (idcol, schema, axialname, schema, axialname, idcol, idcol, geomname, geomname, geomname, geomname, threshold,
                  geomname, geomname, threshold)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['short line'] = nodes
        self.verificationProgress.emit(40)
        if is_debug: print "analyse short: %s" % str(time.time()-start_time)
        # duplicate geometry
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s"."%s" a, "%s"."%s" b WHERE a."%s" <> b."%s" AND ST_Equals(a."%s",b."%s")' \
                % (idcol, schema, axialname, schema, axialname, idcol, idcol, geomname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['duplicate geometry'] = nodes
        self.verificationProgress.emit(60)
        if is_debug: print "analyse duplicate: %s" % str(time.time()-start_time)
        # geometry overlaps
        if not self.running: return
        start_time = time.time()
        query = 'SELECT a."%s" FROM "%s"."%s" a, "%s"."%s" b WHERE a."%s" <> b."%s" AND NOT ST_Equals(a."%s",b."%s") AND ST_Overlaps(a."%s",b."%s")' \
            % (idcol, schema, axialname, schema, axialname, idcol, idcol, geomname, geomname, geomname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query)
        if data:
            nodes = list(zip(*data)[0])
            self.problem_nodes.extend(nodes)
            self.axial_errors['overlap'] = nodes
        self.verificationProgress.emit(80)
        if is_debug: print "analyse overlap: %s" % str(time.time()-start_time)
        # the overlap function is very accurate and rare in GIS
        # an alternative function with buffer is too slow

    def postgisBuildTopology(self, connection, schema, axialname, geomname, unlinkschema, unlinkname, linkschema, linkname):
        # this function builds the axial map topology using spatialite. it's much faster.
        idcol = self.user_id
        if idcol == '':
            return
        # remove temporary table if already exists
        graphname = "temp_axial_topology"
        header, data, error = uf.executePostgisQuery(connection,"""DROP TABLE IF EXISTS %s CASCADE """ % graphname)
        start_time = time.time()
        # create a new temporary table
        query = """CREATE TEMP TABLE %s (pk_id serial NOT NULL PRIMARY KEY, a_fid integer, b_fid integer)""" % graphname
        header, data, error = uf.executePostgisQuery(connection, query)
        # calculate edges from intersecting feature pairs
        query = 'INSERT INTO %s (a_fid, b_fid) SELECT DISTINCT CASE WHEN a."%s" < b."%s" THEN a."%s" ELSE b."%s" END AS least_col, ' \
                'CASE WHEN a."%s" > b."%s" THEN a."%s" ELSE b."%s" END AS greatest_col '\
                'FROM "%s"."%s" a, "%s"."%s" b WHERE a."%s" <> b."%s" AND ST_Intersects(a."%s",b."%s") '\
                % (graphname, idcol, idcol, idcol, idcol, idcol, idcol, idcol, idcol, schema, axialname, schema, axialname,
                  idcol, idcol, geomname, geomname)
        header, data, error = uf.executePostgisQuery(connection, query, commit=True)
        if is_debug: print "Building the graph: %s" % str(time.time()-start_time)
        # eliminate unlinks
        if unlinkname:
            if uf.fieldExists(uf.getLayerByName(unlinkname),'line1') and uf.fieldExists(uf.getLayerByName(unlinkname),'line2'):
                start_time = time.time()
                query = 'DELETE FROM %s WHERE a_fid::text||"_"||b_fid::text in (SELECT line1::||"_"||line2::text FROM "%s"."%s") ' \
                        'OR b_fid::text||"_"||a_fid::text in (SELECT line1::text)||"_"||line2::text FROM "%s"."%s")' \
                        % (graphname, unlinkschema, unlinkname, unlinkschema, unlinkname)
                header, data, error = uf.executePostgisQuery(connection, query, commit=True)
                if is_debug: print "Unlinking the graph: %s" % str(time.time()-start_time)
        # newfeature: implement inserting links
        # return all the links to build the graph
        query = """SELECT a_fid, b_fid FROM %s""" % graphname
        header, data, error = uf.executePostgisQuery(connection, query)
        return data

    # QGIS based functions
    #
    def qgisGeometryTopologyTest(self, axial, index, unlinks, links):
        # this function checks the geometric validity of geometry using QGIS
        length = self.verification_settings['ax_min']
        threshold = self.verification_settings['ax_dist']
        axial_links = []
        unlinks_list = []
        links_list = []
        # get unlinks pairs
        if not self.running: return
        if unlinks:
            if uf.fieldExists(unlinks,'line1') and uf.fieldExists(unlinks,'line2'):
                features = unlinks.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1','line2'],unlinks.pendingFields()))
                for feature in features:
                    unlinks_list.append((feature.attribute('line1'),feature.attribute('line2')))
        # get links pairs
        if not self.running: return
        if links:
            features = links.getFeatures(QgsFeatureRequest().setSubsetOfAttributes(['line1','line2'],links.pendingFields()))
            for feature in features:
                links_list.append((feature.attribute('line1'),feature.attribute('line2')))
        if not self.running: return
        if self.user_id == '':
            features = axial.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([]))
        else:
            field = uf.getFieldIndex(axial, self.user_id)
            features = axial.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([field]))
        steps = 85.0/float(axial.featureCount())
        progress = 5.0
        start_buff = QgsGeometry()
        end_buff = QgsGeometry()
        for i, feature in enumerate(features):
            if not self.running: break
            has_problem = False
            geom = feature.geometry()
            if self.user_id == '':
                id = feature.id()
            else:
                id = feature.attribute(self.user_id)
            # geometry is valid (generally)
            if not geom.isGeosValid() or geom.isGeosEmpty():
                has_problem = True
                self.axial_errors['invalid geometry'].append(id)
            # geometry is polyline
            if len(geom.asPolyline()) > 2:
                has_problem = True
                self.axial_errors['polyline'].append(id)
            # has two coinciding points
            if geom.length() == 0:
                has_problem = True
                self.axial_errors['coinciding points'].append(id)
            # small lines, with small length
            if geom.length() < length:
                has_problem = True
                self.axial_errors['small line'].append(id)
            # testing against other lines in the layer
            buff = None
            if threshold > 0:
                start_buff = QgsGeometry.fromPoint(geom.asPolyline()[0]).buffer(threshold,4)
                end_buff = QgsGeometry.fromPoint(geom.asPolyline()[1]).buffer(threshold,4)
                buff = geom.buffer(threshold,4)
                box = buff.boundingBox()
            else:
                box = geom.boundingBox()
            request = QgsFeatureRequest()
            if index:
                # should be faster to retrieve from index (if available)
                ints = index.intersects(box)
                request.setFilterFids(ints)
            else:
                # can retrieve objects using bounding box
                request.setFilterRect(box)
            if self.user_id == '':
                request.setSubsetOfAttributes([])
            else:
                field = uf.getFieldIndex(axial, self.user_id)
                request.setSubsetOfAttributes([field])
            targets = axial.getFeatures(request)
            orphan = True
            for target in targets:
                if not self.running: break
                geom_b = target.geometry()
                if self.user_id == '':
                    id_b = target.id()
                else:
                    id_b = target.attribute(self.user_id)
                if not id_b == id:
                    # duplicate geometry
                    if geom.isGeosEqual(geom_b):
                        has_problem = True
                        self.axial_errors['duplicate geometry'].append(id)
                    # geometry overlaps
                    if geom.overlaps(geom_b):
                        has_problem = True
                        self.axial_errors['overlap'].append(id)
                    # short lines, just about touch without intersecting
                    if (geom_b.intersects(start_buff) or geom_b.intersects(end_buff)) and not geom_b.intersects(geom):
                        has_problem = True
                        self.axial_errors['short line'].append(id)
                    if geom.intersects(geom_b):
                        # check if in the unlinks
                        if (id,id_b) not in unlinks_list and (id_b,id) not in unlinks_list:
                            # build the topology
                            if has_igraph or has_networkx:
                                #axial_links.append((uf.convertNumeric(id),uf.convertNumeric(id_b)))
                                axial_links.append((id,id_b))
                            # test orphans
                            if orphan:
                                orphan = False
            if orphan:
                has_problem = True
                self.axial_errors['orphan'].append(id)
            if has_problem:
                self.problem_nodes.append(id)
            progress += steps
            self.verificationProgress.emit(int(progress))
        return axial_links