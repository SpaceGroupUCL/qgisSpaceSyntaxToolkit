import itertools
import unittest

from qgis.core import (QgsApplication, QgsVectorLayer, QgsFeature, QgsLineString, QgsPoint, QgsGeometry)

from esstoolkit.network_segmenter.segment_tools import segmentor

qgs = QgsApplication([], False)
qgs.initQgis()


class TestGateTransformer(unittest.TestCase):

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

        vl = TestGateTransformer.make_geometry_feature_layer(
            "LineString",
            [QgsLineString([QgsPoint(535088.141198, 185892.128181),
                            QgsPoint(535037.617992, 186342.145327)]),
             QgsLineString([QgsPoint(535012.560937, 186126.546603),
                            QgsPoint(535285.548630, 186203.990233)]),
             QgsLineString([QgsPoint(534952.224080, 186285.463215),
                            QgsPoint(535248.881516, 185907.343107)])])

        ul = TestGateTransformer.make_geometry_feature_layer(
            "Point", [
                QgsPoint(535067.772756, 186147.054373),  # invalid unlink
                QgsPoint(535059.304801, 186148.977932)  # valid unlink
            ])

        self.assertEqual(vl.featureCount(), 3)

        # segment the axial lines without removing stubs
        stub_ratio = 0.3
        buffer = 1
        errors = True

        self.my_segmentor = segmentor(vl, ul, stub_ratio, buffer, errors)

        break_point_feats, invalid_unlink_point_feats, stubs_point_feats, segmented_feats = [], [], [], []

        self.my_segmentor.step = 10 / float(self.my_segmentor.layer.featureCount())
        self.my_segmentor.load_graph()
        # self.step specified in load_graph
        # progress emitted by break_segm & break_feats_iter
        cross_p_list = [self.my_segmentor.break_segm(feat) for feat in
                        self.my_segmentor.list_iter(list(self.my_segmentor.feats.values()))]
        self.my_segmentor.step = 20 / float(len(cross_p_list))
        segmented_feats = [self.my_segmentor.copy_feat(feat_geom_fid[0], feat_geom_fid[1], feat_geom_fid[2]) for
                           feat_geom_fid in self.my_segmentor.break_feats_iter(cross_p_list)]

        if errors:
            cross_p_list = set(list(itertools.chain.from_iterable(cross_p_list)))

            ids1 = [i for i in range(0, len(cross_p_list))]
            break_point_feats = [
                self.my_segmentor.copy_feat(self.my_segmentor.break_f, QgsGeometry.fromPointXY(p_fid[0]),
                                            p_fid[1]) for p_fid in (list(zip(cross_p_list, ids1)))]
            ids2 = [i for i in range(max(ids1) + 1, max(ids1) + 1 + len(self.my_segmentor.invalid_unlinks))]
            invalid_unlink_point_feats = [self.my_segmentor.copy_feat(self.my_segmentor.invalid_unlink_f,
                                                                      QgsGeometry.fromPointXY(p_fid1[0]),
                                                                      p_fid1[1]) for p_fid1 in
                                          (list(zip(self.my_segmentor.invalid_unlinks, ids2)))]
            ids = [i for i in
                   range(max(ids1 + ids2) + 1, max(ids1 + ids2) + 1 + len(self.my_segmentor.stubs_points))]
            stubs_point_feats = [
                self.my_segmentor.copy_feat(self.my_segmentor.stub_f, QgsGeometry.fromPointXY(p_fid2[0]),
                                            p_fid2[1]) for p_fid2 in
                (list(zip(self.my_segmentor.stubs_points, ids)))]

        expected_segments = [
            QgsLineString([QgsPoint(535088.141198, 185892.128181), QgsPoint(535060.302601, 186140.090392)]),
            QgsLineString([QgsPoint(535060.302601, 186140.090392), QgsPoint(535037.617991, 186342.145327)]),
            QgsLineString([QgsPoint(535060.302601, 186140.090392), QgsPoint(535065.189841, 186141.476849)]),
            QgsLineString([QgsPoint(535065.189841, 186141.476849), QgsPoint(535285.548629, 186203.990232)]),
            QgsLineString([QgsPoint(534952.224079, 186285.463214), QgsPoint(535065.189841, 186141.476849)]),
            QgsLineString([QgsPoint(535065.189841, 186141.476849), QgsPoint(535248.881516, 185907.343106)]),

        ]

        self.assertEqual(len(segmented_feats), len(expected_segments))

        for segmented_feat in segmented_feats:
            segmented_line = segmented_feat.geometry().asPolyline()
            for expected_segment in expected_segments:
                x1eq = abs(segmented_line[0].x() - expected_segment[0].x()) < error_tolerance
                y1eq = abs(segmented_line[0].y() - expected_segment[0].y()) < error_tolerance
                x2eq = abs(segmented_line[1].x() - expected_segment[1].x()) < error_tolerance
                y2eq = abs(segmented_line[1].y() - expected_segment[1].y()) < error_tolerance
                if x1eq and y1eq and x2eq and y2eq:
                    expected_segments.remove(expected_segment)
                    break

        # all the expected features should have been found and removed
        self.assertEqual(len(expected_segments), 0)

        expected_break_points = [
            QgsPoint(535285.548629, 186203.990232),
            QgsPoint(535065.189841, 186141.476849),
            QgsPoint(535060.302601, 186140.090392),
            QgsPoint(535037.617991, 186342.145327),
            QgsPoint(534952.224079, 186285.463214),
            QgsPoint(535248.881516, 185907.343106),
            QgsPoint(535088.141198, 185892.128181)
        ]

        self.assertEqual(len(break_point_feats), len(expected_break_points))

        for break_point_feat in break_point_feats:
            break_point = break_point_feat.geometry().asPoint()
            for expected_break_point in expected_break_points:
                xeq = abs(break_point.x() - expected_break_point.x()) < error_tolerance
                yeq = abs(break_point.y() - expected_break_point.y()) < error_tolerance
                if xeq and yeq:
                    expected_break_points.remove(expected_break_point)
                    break

        # all the expected break points should have been found and removed
        self.assertEqual(len(expected_segments), 0)

        # only one stub removed
        self.assertEqual(len(stubs_point_feats), 1)
        self.assertAlmostEqual(stubs_point_feats[0].geometry().asPoint().x(), 535012.560936, places=3)
        self.assertAlmostEqual(stubs_point_feats[0].geometry().asPoint().y(), 186126.546602, places=3)

        # first unlink is invalid
        self.assertEqual(len(invalid_unlink_point_feats), 1)
        self.assertAlmostEqual(invalid_unlink_point_feats[0].geometry().asPoint().x(),
                               next(ul.getFeatures()).geometry().asPoint().x(), places=3)
        self.assertAlmostEqual(invalid_unlink_point_feats[0].geometry().asPoint().y(),
                               next(ul.getFeatures()).geometry().asPoint().y(), places=3)


if __name__ == '__main__':
    unittest.main()

qgs.exitQgis()
