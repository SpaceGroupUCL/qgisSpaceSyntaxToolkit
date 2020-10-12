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

""" Network based catchment analysis
"""

from __future__ import absolute_import

from builtins import range
from builtins import str

from qgis.PyQt.QtCore import (QObject, pyqtSignal, QVariant)
from qgis.analysis import (QgsVectorLayerDirector, QgsNetworkDistanceStrategy, QgsGraphBuilder, QgsGraphAnalyzer)
from qgis.core import (QgsSpatialIndex, QgsGeometry, QgsFeature, QgsFields, QgsField, NULL, QgsWkbTypes)

try:
    from . import analysis_tools as ct
except ImportError:
    pass
try:
    from . import utility_functions as uf
except ImportError:
    pass

is_debug = False
try:
    import pydevd

    has_pydevd = True
except ImportError:
    has_pydevd = False

import traceback


class CatchmentAnalysis(QObject):
    # Setup signals
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, str)
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
                if self.killed: return

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
                if self.killed: return

                # Run the analysis
                catchment_network, catchment_points = self.graph_analysis(
                    graph,
                    tied_origins,
                    self.settings['distances']
                )
                self.progress.emit(40)
                if self.killed: return

                # Create output signal
                output = {'output network features': None,
                          'output polygon features': None,
                          'distances': self.settings['distances']}

                network = self.settings['network']

                # Write and render the catchment polygons

                if self.settings['output polygon check']:
                    new_fields = QgsFields()
                    new_fields.append(QgsField('id', QVariant.Int))
                    new_fields.append(QgsField('origin', QVariant.String))
                    new_fields.append(QgsField('distance', QVariant.Int))

                    output_polygon_features = self.polygon_writer(
                        catchment_points,
                        self.settings['distances'],
                        new_fields,
                        self.settings['polygon tolerance'],
                    )
                    output['output polygon features'] = output_polygon_features

                self.progress.emit(70)
                if self.killed: return

                # get fields

                new_fields = self.get_fields(origins, self.settings['name'])

                # Write and render the catchment network
                output_network_features = self.network_writer(
                    catchment_network,
                    new_fields,
                    self.settings['name']
                )

                output['output network features'] = output_network_features

                if self.killed is False:
                    self.progress.emit(100)
                    self.finished.emit(output)

            except Exception as e:
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
                origin_name = i  # "origin_" + "%s" % (i+1)

            origins.append({'name': origin_name, 'geom': f.geometry().centroid()})

        return origins

    def graph_builder(self, network, cost_field, origins, tolerance, crs, epsg):

        # Settings
        otf = False

        # Get index of cost field
        network_fields = network.fields()
        network_cost_index = network_fields.indexFromName(cost_field)

        # Setting up graph build director
        director = QgsVectorLayerDirector(network, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)

        # Determining cost calculation
        if cost_field != 'length':
            strategy = ct.CustomCost(network_cost_index, 0.01)
        else:
            strategy = QgsNetworkDistanceStrategy()

        # Creating graph builder
        director.addStrategy(strategy)
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

        self.spIndex = QgsSpatialIndex()
        self.indices = {}
        self.attributes_dict = {}
        self.centroids = {}
        i = 0
        for f in network.getFeatures():
            if f.geometry().type() == QgsWkbTypes.LineGeometry:
                if not f.geometry().isMultipart():
                    self.attributes_dict[f.id()] = f.attributes()
                    polyline = f.geometry().asPolyline()
                    for idx, p in enumerate(polyline[1:]):
                        ml = QgsGeometry.fromPolylineXY([polyline[idx], p])
                        new_f = QgsFeature()
                        new_f.setGeometry(ml.centroid())
                        new_f.setAttributes([f.id()])
                        new_f.setId(i)
                        self.spIndex.addFeature(new_f)
                        self.centroids[i] = f.id()
                        i += 1
                else:
                    self.attributes_dict[f.id()] = f.attributes()
                    for pl in f.geometry().asMultiPolyline():
                        for idx, p in enumerate(pl[1:]):
                            ml = QgsGeometry.fromPolylineXY([pl[idx], p])
                            new_f = QgsFeature()
                            new_f.setGeometry(ml.centroid())
                            new_f.setAttributes([f.id()])
                            new_f.setId(i)
                            self.spIndex.addFeature(new_f)
                            self.centroids[i] = f.id()
                            i += 1

        self.network_fields = network_fields
        return graph, tied_origins

    def graph_analysis(self, graph, tied_origins, distances):
        # Settings
        catchment_threshold = max(distances)

        # Variables
        catchment_network = {}
        catchment_points = {}

        # Loop through graph and get geometry and write to catchment network
        for index in range(graph.edgeCount()):
            inVertexId = graph.edge(index).fromVertex()
            outVertexId = graph.edge(index).toVertex()
            inVertexGeom = graph.vertex(inVertexId).point()
            outVertexGeom = graph.vertex(outVertexId).point()
            # only include one of the two possible arcs
            if inVertexId < outVertexId:
                arcGeom = QgsGeometry.fromPolylineXY([inVertexGeom, outVertexGeom])
                catchment_network[index] = {'geom': arcGeom, 'start': inVertexId, 'end': outVertexId, 'cost': {}}

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
            for index in catchment_network.keys():
                if self.killed: break
                # Define the arc properties
                inVertexId = catchment_network[index]['start']
                outVertexId = catchment_network[index]['end']
                inVertexCost = cost[inVertexId]
                outVertexCost = cost[outVertexId]
                # this is the permissive option gives cost to the arc based on the closest point,
                # it just needs to be reach by one node
                arcCost = min(inVertexCost, outVertexCost)
                # this is the restrictive option, gives cost to the arc based on the furtherst point,
                # it needs to be entirely within distance
                # arcCost = max(inVertexCost, outVertexCost)

                # If arc is the origin set cost to 0
                if outVertexId == originVertexId or inVertexId == originVertexId:
                    catchment_network[index]['cost'][origin_name] = 0

                # If arc is connected and within the maximum radius set cost
                elif arcCost <= catchment_threshold and tree[inVertexId] != -1:
                    if origin_name in catchment_network[index]['cost']:
                        if catchment_network[index]['cost'][origin_name] > int(arcCost):
                            catchment_network[index]['cost'][origin_name] = int(arcCost)
                    else:
                        catchment_network[index]['cost'][origin_name] = int(arcCost)

                    # Add catchment points for each given radius
                    inVertexGeom = graph.vertex(inVertexId).point()
                    outVertexGeom = graph.vertex(outVertexId).point()
                    seg_length = catchment_network[index][
                        'geom'].length()  # math.sqrt(inVertexGeom.sqrDist(outVertexGeom))
                    for distance in distances:
                        if self.killed: break
                        # this option includes both nodes as long as arc is within distance
                        # the polygon is the same as the network output
                        # if arcCost <= distance:
                        #    catchment_points[tied_point][distance].extend([inVertexGeom, outVertexGeom])
                        # this option only includes nodes within distance
                        # it does linear interpolation for extra points
                        if inVertexCost <= distance:
                            catchment_points[tied_point][distance].append(inVertexGeom)
                            # add an extra point with linear referencing
                            if outVertexCost > distance:
                                target_dist = distance - inVertexCost
                                midVertexGeom = catchment_network[index]['geom'].interpolate(target_dist).asPoint()
                                catchment_points[tied_point][distance].append(midVertexGeom)
                        if outVertexCost <= distance:
                            catchment_points[tied_point][distance].append(outVertexGeom)
                            # add an extra point with linear referencing
                            if inVertexCost > distance:
                                target_dist = distance - outVertexCost
                                midVertexGeom = catchment_network[index]['geom'].interpolate(
                                    seg_length - target_dist).asPoint()
                                catchment_points[tied_point][distance].append(midVertexGeom)

            i += 1
        return catchment_network, catchment_points

    def get_fields(self, origins, use_name):
        # fields: self.network_fields
        # Setup all unique origin columns and minimum origin distance column

        # add origin field names
        if use_name:
            self.names = set([str(origin['name']) for origin in origins])
            for n in self.names:
                self.network_fields.append(QgsField(n, QVariant.Int))
        else:
            self.names = list(range(0, len(origins)))

        self.network_fields.append(QgsField('min_dist', QVariant.Int))

        return self.network_fields

    def network_writer(self, catchment_network, new_fields, use_name):

        # Loop through arcs in catchment network and write geometry and costs
        i = 0
        features = []

        for k, v in catchment_network.items():

            self.progress.emit(70 + int(30 * i / len(catchment_network)))

            if self.killed is True:
                break

            # Get arc properties
            arc_geom = v['geom']
            arc_cost_dict = {str(key): value for key, value in list(v['cost'].items())}

            i += 1
            # Ignore arc if not connected or outside of catchment
            if len(arc_cost_dict) > 0:
                # Create feature and write id and geom
                f = QgsFeature()
                # get original feature attributes
                centroid_match = self.spIndex.nearestNeighbor(arc_geom.centroid().asPoint(), 1).pop()
                original_feature_id = self.centroids[centroid_match]
                f_attrs = self.attributes_dict[original_feature_id]
                arc_cost_list = []
                for name in self.names:
                    try:
                        arc_cost_list.append(arc_cost_dict[str(name)])
                    except KeyError:
                        arc_cost_list.append(NULL)

                f.setFields(new_fields)
                if use_name:
                    f.setAttributes(f_attrs + arc_cost_list + [min(arc_cost_list)])
                else:
                    f.setAttributes(f_attrs + [min(arc_cost_list)])

                f.setGeometry(arc_geom)

                # Write feature to output network layer
                features.append(f)

            i += 1

        return features

    def polygon_writer(self, catchment_points, distances, new_fields, polygon_tolerance):

        # Setup unique origin dictionary containing all distances
        unique_origins_list = []
        polygon_dict = {}
        output_polygon_features = []
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
                for hull in polygon_dict[name][distance]:  # Later add combine functionality
                    if self.killed: break
                    # Check if hull is a actual polygon
                    try:
                        polygon_geom = QgsGeometry.fromPolygonXY([hull, ])
                    except TypeError:
                        hull_validity = False
                        continue
                    if polygon_geom:
                        p = QgsFeature()
                        p.setFields(new_fields)
                        p.setAttribute('id', index)
                        p.setAttribute('origin', name)
                        p.setAttribute('distance', distance)
                        p.setGeometry(polygon_geom)
                        output_polygon_features.append(p)
                        index += 1
        if not hull_validity:
            self.warning.emit('Polygon tolerance too high for small cost bands.')
        return output_polygon_features

    def kill(self):
        self.killed = True
