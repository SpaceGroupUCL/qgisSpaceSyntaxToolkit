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

from PyQt4.QtCore import *

from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
from qgis.utils import *

import analysis_tools as ct
import utility_functions as uf

is_debug = False
try:
    import pydevd
    has_pydevd = True
except ImportError, e:
    has_pydevd = False

import traceback


class CatchmentAnalysis(QObject):

    # Setup signals
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)

    def __init__(self, iface, settings):
        QObject.__init__(self)
        self.concave_hull = ct.ConcaveHull()
        self.iface = iface
        self.settings = settings
        self.killed = False

    def analysis(self):
        if has_pydevd and is_debug:
            pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True, suspend=False)
        if self.settings:
            try:
                # Prepare the origins
                origins = self.origin_preparation(
                    self.settings['origins'],
                    self.settings['name']
                )
                self.progress.emit(10)
                if self.killed == True: return

                # Build the graph
                graph, tied_origins = self.graph_builder(
                    self.settings['network'],
                    self.settings['cost'],
                    origins,
                    self.settings['network tolerance'],
                    self.settings['crs'],
                    self.settings['epsg']
                )
                self.progress.emit(20)
                if self.killed == True: return

                # Run the analysis
                catchment_network, catchment_points = self.graph_analysis(
                    graph,
                    tied_origins,
                    self.settings['distances']
                )
                self.progress.emit(40)
                if self.killed == True: return

                # Create output signal
                output = {'output network': None,
                          'output polygon': None,
                          'distances': self.settings['distances']}

                # Write and render the catchment polygons
                if self.settings['output polygon check']:
                    output_polygon = self.polygon_writer(
                        catchment_points,
                        self.settings['distances'],
                        self.settings['temp polygon'],
                        self.settings['polygon tolerance']
                    )
                    if self.settings['output polygon']:
                        uf.createShapeFile(output_polygon, self.settings['output polygon'], self.settings['crs'])
                        output_polygon = QgsVectorLayer(self.settings['output polygon'], 'catchment_areas', 'ogr')
                    output['output polygon'] = output_polygon

                self.progress.emit(70)
                if self.killed == True: return

                # Write and render the catchment network
                if self.settings['output network check']:
                    output_network = self.network_writer(
                        origins,
                        catchment_network,
                        self.settings['temp network']
                    )
                    if self.settings['output network']:
                        uf.createShapeFile(output_network, self.settings['output network'], self.settings['crs'])
                        output_network = QgsVectorLayer(self.settings['output network'], 'catchment_network', 'ogr')
                    output['output network'] = output_network

                if self.killed is False:
                    self.progress.emit(100)
                    self.finished.emit(output)

            except Exception, e:
                self.error.emit(e, traceback.format_exc())

    def origin_preparation(self, origin_vector, origin_name_field):

        # Create a dictionary of origin point dictionaries containing name and geometry
        origins = []

        # Loop through origin and get or create points
        for i, f in enumerate(origin_vector.getFeatures()):

            # Get origin name
            if origin_name_field:
                origin_name = f[origin_name_field]
            else:
                origin_name = "origin_" + "%s" % (i+1)

            origins.append({'name': origin_name, 'geom': f.geometry().centroid()})

        return origins

    def graph_builder(self, network, cost_field, origins, tolerance, crs, epsg):

        # Settings
        otf = False

        # Get index of cost field
        network_fields = network.pendingFields()
        network_cost_index = network_fields.indexFromName(cost_field)

        # Setting up graph build director
        director = QgsLineVectorLayerDirector(network, -1, '', '', '', 3)

        # Determining cost calculation
        if cost_field:
            properter = ct.CustomCost(network_cost_index, 0.01)
        else:
            properter = QgsDistanceArcProperter()

        # Creating graph builder
        director.addProperter(properter)
        builder = QgsGraphBuilder(crs, otf, tolerance, epsg)

        # Reading origins and making list of coordinates
        graph_origin_points = []

        # Loop through the origin points and add graph vertex indices
        for index, origin in enumerate(origins):
            graph_origin_points.append(origins[index]['geom'].asPoint())

        # Get origin graph vertex index
        tied_origin_vertices = director.makeGraph(builder, graph_origin_points)

        # Build the graph
        graph = builder.graph()

        # Create dictionary of origin names and tied origins
        tied_origins = {}

        # Combine origin names and tied point vertices
        for index, tied_origin in enumerate(tied_origin_vertices):
            tied_origins[index] = {'name': origins[index]['name'], 'vertex': tied_origin}

        return graph, tied_origins

    def graph_analysis(self, graph, tied_origins, distances):
        # Settings
        catchment_threshold = max(distances)

        # Variables
        catchment_network = {}
        catchment_points = {}

        # Loop through graph and get geometry and write to catchment network
        for index in range(graph.arcCount()):
            inVertexId = graph.arc(index).inVertex()
            outVertexId = graph.arc(index).outVertex()
            inVertexGeom = graph.vertex(inVertexId).point()
            outVertexGeom = graph.vertex(outVertexId).point()
            arcGeom = QgsGeometry.fromPolyline([outVertexGeom,inVertexGeom])
            if inVertexId < outVertexId:
                catchment_network[index] = {'geom': arcGeom, 'start':inVertexId, 'end':outVertexId, 'cost': {}}

        # Loop through tied origins and write origin names
        for tied_point, origin in enumerate(tied_origins):
            origin_name = tied_origins[tied_point]['name']
            catchment_points[tied_point] = {'name': origin_name}
            catchment_points[tied_point].update({distance: [] for distance in distances})

        # Loop through tied origins and write costs and polygon points
        i = 1
        for tied_point, origin in enumerate(tied_origins):
            self.progress.emit(20 + int(20 * i / len(tied_origins)))
            origin_name = tied_origins[tied_point]['name']
            originVertexId = graph.findVertex(tied_origins[tied_point]['vertex'])

            # Run dijkstra and get tree and cost
            (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, originVertexId, 0)

            # Loop through graph arcs
            for index in catchment_network.iterkeys():
                if self.killed == True: break
                # Define the arc properties
                inVertexId = catchment_network[index]['start']
                outVertexId = catchment_network[index]['end']
                arcCost = max(cost[outVertexId], cost[inVertexId])

                # If arc is the origin set cost to 0
                if outVertexId == originVertexId or inVertexId == originVertexId:
                    catchment_network[index]['cost'][origin_name] = 0

                # If arc is connected and within the maximum radius set cost
                elif arcCost < catchment_threshold and tree[inVertexId] != -1:
                    if origin_name in catchment_network[index]['cost']:
                        if catchment_network[index]['cost'][origin_name] > int(arcCost):
                            catchment_network[index]['cost'][origin_name] = int(arcCost)
                    else:
                        catchment_network[index]['cost'][origin_name] = int(arcCost)

                    # Add catchment points for each given radius
                    for distance in distances:
                        if self.killed == True: break
                        if arcCost < distance:
                            inVertexGeom = graph.vertex(inVertexId).point()
                            outVertexGeom = graph.vertex(outVertexId).point()
                            catchment_points[tied_point][distance].extend([inVertexGeom, outVertexGeom])
            i += 1
        return catchment_network, catchment_points

    def network_writer(self, origins, catchment_network, output_network):

        # Setup all unique origin columns and minimum origin distance column
        unique_origin_list = []
        for origin in origins:
            name = origin['name']
            if not name in unique_origin_list:
                output_network.dataProvider().addAttributes([QgsField("%s" % name, QVariant.Int)])
                unique_origin_list.append(name)
        output_network.dataProvider().addAttributes([QgsField('min_dist', QVariant.Int)])
        output_network.updateFields()

        # Loop through arcs in catchment network and write geometry and costs
        i = 1
        for k, v in catchment_network.iteritems():
            self.progress.emit(70 + int(30 * i / len(catchment_network)))
            if self.killed == True: break

            # Get arc properties
            arc_geom = v['geom']
            arc_cost_dict = v['cost']
            arc_cost_list = []

            # Ignore arc if not connected or outside of catchment
            if len(arc_cost_dict) > 0:
                # Create feature and write id and geom
                f = QgsFeature(output_network.pendingFields())
                f.setAttribute("id", k)
                f.setGeometry(arc_geom)
                # Read the list of costs and write them to output network
                for name, cost in arc_cost_dict.iteritems():
                    arc_cost_list.append(cost)
                    f.setAttribute("%s" % name, cost)

                # Set minimum cost
                if len(arc_cost_list) > 0:
                    f.setAttribute('min_dist', min(arc_cost_list))

                # Write feature to output network layer
                output_network.dataProvider().addFeatures([f])
            i += 1

        return output_network

    def polygon_writer(self, catchment_points, distances, output_polygon, polygon_tolerance):

        # Setup unique origin dictionary containing all distances
        unique_origins_list = []
        polygon_dict = {}
        i = 1
        for tied_point in catchment_points:
            if self.killed: break
            self.progress.emit(40 + int(30 * i / len(catchment_points)))
            name = catchment_points[tied_point]['name']
            if name not in unique_origins_list:
                polygon_dict[name] = {distance: [] for distance in distances}
                unique_origins_list.append(name)
            # Creating hull for each distance and if applicable in a list
            for distance in distances:
                if self.killed: break
                points = catchment_points[tied_point][distance]
                if len(points) > 2:  # Only three points can create a polygon
                    hull = self.concave_hull.concave_hull(points, polygon_tolerance)
                    polygon_dict[name][distance].append(hull)
            i += 1
        # Generate the polygons
        index = 1
        hull_validity = True
        for name in polygon_dict:
            for distance in distances:
                for hull in polygon_dict[name][distance]: # Later add combine functionality
                    if self.killed: break
                    # Check if hull is a actual polygon
                    try:
                        polygon_geom = QgsGeometry.fromPolygon([hull,])
                    except TypeError:
                        hull_validity = False
                        continue
                    if polygon_geom:
                        p = QgsFeature(output_polygon.pendingFields())
                        p.setAttribute('id', index)
                        p.setAttribute('origin', name)
                        p.setAttribute('distance', distance)
                        p.setGeometry(polygon_geom)
                        output_polygon.dataProvider().addFeatures([p])
                        index += 1
        if hull_validity == False:
            self.warning.emit('Polygon tolerance too high for small cost bands.')
        return output_polygon

    def kill(self):
        self.killed = True

