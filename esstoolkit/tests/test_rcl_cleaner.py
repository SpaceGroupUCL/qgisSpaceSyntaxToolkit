# -*- coding: utf-8 -*-

# Space Syntax Toolkit
# Set of tools for essential space syntax network analysis and results exploration
# -------------------
# begin                : 2020-09-10
# copyright            : (C) 2020 by Petros Koutsolampros / Space Syntax Ltd.
# author               : Petros Koutsolampros
# email                : p.koutsolampros@spacesyntax.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import unittest

from qgis.core import (QgsApplication, QgsVectorLayer, QgsFeature, QgsLineString, QgsPoint)

from esstoolkit.network_segmenter.segment_tools import segmentor
from esstoolkit.rcl_cleaner.road_network_cleaner_dialog import RoadNetworkCleanerDialog
from esstoolkit.rcl_cleaner.sGraph.sGraph import sGraph
from esstoolkit.rcl_cleaner.sGraph.utilityFunctions import clean_features_iter

qgs = QgsApplication([], False)
qgs.initQgis()


class TestRCLCleaner(unittest.TestCase):

    @staticmethod
    def make_geometry_feature_layer(layertype: str, geometries):
        vl = QgsVectorLayer(layertype, 'temp', "memory")
        pr = vl.dataProvider()
        for geometry in geometries:
            f = QgsFeature()
            f.setGeometry(geometry)
            pr.addFeature(f)
        vl.updateExtents()
        return vl

    def test_merge_nodes(self):

        error_tolerance = 0.0001

        axial_lines = TestRCLCleaner.make_geometry_feature_layer(
            "LineString",
            [QgsLineString([QgsPoint(535088.141198, 185892.128181),
                            QgsPoint(535037.617992, 186342.145327)]),
             QgsLineString([QgsPoint(534931.347277, 186103.472964),
                            QgsPoint(535285.548630, 186203.990233)]),
             QgsLineString([QgsPoint(534952.224080, 186285.463215),
                            QgsPoint(535248.881516, 185907.343107)])])

        unlinks = TestRCLCleaner.make_geometry_feature_layer(
            "Point", [])

        # segment the axial lines without removing stubs
        stub_ratio = 0
        buffer = 1
        errors = True

        my_segmentor = segmentor(axial_lines, unlinks, stub_ratio, buffer, errors)

        my_segmentor.step = 10 / float(my_segmentor.layer.featureCount())
        my_segmentor.load_graph()
        # self.step specified in load_graph
        # progress emitted by break_segm & break_feats_iter
        cross_p_list = [my_segmentor.break_segm(feat) for feat in
                        my_segmentor.list_iter(list(my_segmentor.feats.values()))]
        my_segmentor.step = 20 / float(len(cross_p_list))
        segmented_feats = [my_segmentor.copy_feat(feat_geom_fid[0], feat_geom_fid[1], feat_geom_fid[2]) for
                           feat_geom_fid in my_segmentor.break_feats_iter(cross_p_list)]

        segmented_geometry = [segmented_feat.geometry() for segmented_feat in segmented_feats]
        segment_layer = TestRCLCleaner.make_geometry_feature_layer(
            "LineString", segmented_geometry)

        # segment the axial lines without removing stubs
        self.assertEqual(segment_layer.featureCount(), 9)

        # cleaning settings
        snap_threshold = 10  # TODO: Test
        break_at_vertices = True  # TODO: Test
        merge_type = 'intersections'  # TODO: Test
        # merge_type = 'colinear'  # TODO: Test
        collinear_threshold = 0  # TODO: Test
        angle_threshold = 10  # TODO: Test
        fix_unlinks = True  # TODO: Test
        orphans = True  # TODO: Test
        get_unlinks = True  # TODO: Test

        [load_range, cl1_range, cl2_range, cl3_range, break_range, merge_range, snap_range, unlinks_range,
         fix_range] = RoadNetworkCleanerDialog.get_progress_ranges(break_at_vertices, merge_type, snap_threshold,
                                                                   get_unlinks, fix_unlinks)

        points = []
        multiparts = []
        pseudo_graph = sGraph({}, {})

        if break_at_vertices:

            pseudo_graph.step = load_range / float(segment_layer.featureCount())
            graph = sGraph({}, {})
            graph.total_progress = load_range
            pseudo_graph.load_edges_w_o_topology(clean_features_iter(segment_layer.getFeatures()))
            # QgsMessageLog.logMessage('pseudo_graph edges added %s' % load_range, level=Qgis.Critical)
            pseudo_graph.step = break_range / float(len(pseudo_graph.sEdges))
            graph.load_edges(
                pseudo_graph.break_features_iter(get_unlinks, angle_threshold, fix_unlinks),
                angle_threshold)
            # QgsMessageLog.logMessage('pseudo_graph edges broken %s' % break_range, level=Qgis.Critical)

        else:
            graph = sGraph({}, {})
            graph.step = load_range / float(segment_layer.featureCount())
            graph.load_edges(clean_features_iter(segment_layer.getFeatures()), angle_threshold)
            # QgsMessageLog.logMessage('graph edges added %s' % load_range, level=Qgis.Critical)

        graph.step = cl1_range / (float(len(graph.sEdges)) * 2.0)
        if orphans:
            graph.clean(True, False, snap_threshold, True)
        else:
            graph.clean(True, False, snap_threshold, False)
        # QgsMessageLog.logMessage('graph clean parallel and closed pl %s' % cl1_range, level=Qgis.Critical)

        if fix_unlinks:
            graph.step = fix_range / float(len(graph.sEdges))
            graph.fix_unlinks()
            # QgsMessageLog.logMessage('unlinks added  %s' % fix_range, level=Qgis.Critical)

        if snap_threshold != 0:

            graph.step = snap_range / float(len(graph.sNodes))
            graph.snap_endpoints(snap_threshold)
            # QgsMessageLog.logMessage('snap  %s' % snap_range, level=Qgis.Critical)
            graph.step = cl2_range / (float(len(graph.sEdges)) * 2.0)

            if orphans:
                graph.clean(True, False, snap_threshold, True)
            else:
                graph.clean(True, False, snap_threshold, False)
            # QgsMessageLog.logMessage('clean   %s' % cl2_range, level=Qgis.Critical)

        if merge_type == 'intersections':

            graph.step = merge_range / float(len(graph.sNodes))
            graph.merge_b_intersections(angle_threshold)
            # QgsMessageLog.logMessage('merge %s %s angle_threshold ' % (merge_range, angle_threshold),
            #                          level=Qgis.Critical)

        elif merge_type == 'collinear':

            graph.step = merge_range / float(len(graph.sEdges))
            graph.merge_collinear(collinear_threshold, angle_threshold)
            # QgsMessageLog.logMessage('merge  %s' % merge_range, level=Qgis.Critical)

        # cleaned multiparts so that unlinks are generated properly
        if orphans:
            graph.step = cl3_range / (float(len(graph.sEdges)) * 2.0)
            graph.clean(True, orphans, snap_threshold, False, True)
        else:
            graph.step = cl3_range / (float(len(graph.sEdges)) * 2.0)
            graph.clean(True, False, snap_threshold, False, True)

        if get_unlinks:
            graph.step = unlinks_range / float(len(graph.sEdges))
            graph.generate_unlinks()
            unlinks = graph.unlinks
        else:
            unlinks = []

        cleaned_features = [e.feature for e in list(graph.sEdges.values())]
        # add to errors multiparts and points
        graph.errors += multiparts
        graph.errors += points

        expected_segments = [
            QgsLineString([QgsPoint(535088.141198, 185892.128181), QgsPoint(535061.604423, 186143.502228)]),
            QgsLineString([QgsPoint(535061.604423, 186143.502228), QgsPoint(535037.617992, 186342.145327)]),
            QgsLineString([QgsPoint(534931.347277, 186103.472964), QgsPoint(535061.604423, 186143.502228)]),
            QgsLineString([QgsPoint(535061.604423, 186143.502228), QgsPoint(535285.548630, 186203.990233)]),
            QgsLineString([QgsPoint(534952.224080, 186285.463215), QgsPoint(535061.604423, 186143.502228)]),
            QgsLineString([QgsPoint(535061.604423, 186143.502228), QgsPoint(535248.881516, 185907.343107)])
        ]

        self.assertEqual(len(cleaned_features), len(expected_segments))

        for cleaned_feature in cleaned_features:
            cleaned_line = cleaned_feature.geometry().asPolyline()
            for expected_segment in expected_segments:
                x1eq = abs(cleaned_line[0].x() - expected_segment[0].x()) < error_tolerance
                y1eq = abs(cleaned_line[0].y() - expected_segment[0].y()) < error_tolerance
                x2eq = abs(cleaned_line[1].x() - expected_segment[1].x()) < error_tolerance
                y2eq = abs(cleaned_line[1].y() - expected_segment[1].y()) < error_tolerance
                if x1eq and y1eq and x2eq and y2eq:
                    expected_segments.remove(expected_segment)
                    break

        # all the expected features should have been found and removed
        self.assertEqual(len(expected_segments), 0)

        expected_errors = [
            QgsPoint(535060.304968, 186140.069309),
            QgsPoint(535059.304801, 186148.977932),
            QgsPoint(535065.203499, 186141.459442)
        ]

        self.assertEqual(len(graph.errors), len(expected_errors))

        for break_point_feat in graph.errors:
            break_point = break_point_feat.geometry().asPoint()
            for expected_break_point in expected_errors:
                xeq = abs(break_point.x() - expected_break_point.x()) < error_tolerance
                yeq = abs(break_point.y() - expected_break_point.y()) < error_tolerance
                if xeq and yeq:
                    expected_errors.remove(expected_break_point)
                    break

        # all the expected errors should have been found and removed
        self.assertEqual(len(expected_errors), 0)


if __name__ == '__main__':
    unittest.main()

qgs.exitQgis()
