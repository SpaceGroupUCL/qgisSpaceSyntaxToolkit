from __future__ import absolute_import
from __future__ import print_function

import itertools
import traceback
from builtins import range
from builtins import zip

from qgis.PyQt.QtCore import QObject, pyqtSignal, QVariant
from qgis.core import QgsSpatialIndex, QgsGeometry, QgsDistanceArea, QgsFeature, QgsField, QgsFields, NULL, QgsWkbTypes

try:
    from .utilityFunctions import prototype_feature
except ImportError:
    pass


# read graph - as feat
class segmentor(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, str)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self, layer, unlinks, stub_ratio, buffer, errors):
        QObject.__init__(self)
        self.layer, self.unlinks, self.stub_ratio, self.buffer, self.errors = layer, unlinks, stub_ratio, buffer, errors

        # internal
        self.spIndex = QgsSpatialIndex()
        self.feats = {}
        self.cross_points = []
        self.connectivity = {}
        self.invalid_unlinks = []
        self.stubs_points = []

        self.cross_p_list = []

        self.id = -1

        fields = QgsFields()
        fields.append(QgsField('type', QVariant.String))
        self.break_f = prototype_feature(['break point'], fields)
        self.invalid_unlink_f = prototype_feature(['invalid unlink'], fields)
        self.stub_f = prototype_feature(['stub'], fields)

        self.step = 1
        self.total_progress = 0
        self.unlinks_points = None

    def load_graph(self):

        # load graph
        res = [self.spIndex.addFeature(feat) for feat in self.feat_iter(self.layer)]
        if len(res) == 0:
            raise BaseException("No valid lines found to segment")
        self.step = 80 / float(len(res))

        # feats need to be created - after iter
        self.unlinks_points = {ml_id: [] for ml_id in list(self.feats.keys())}

        # unlink validity
        if self.unlinks:
            res = [self.load_unlink(unlink) for unlink in
                   [u for u in self.unlinks.getFeatures() if u.geometry() is not NULL and u.geometry()]]
        del res
        return

    def load_unlink(self, unlink):  # TODO buffer not allowed in polygons

        unlink_geom = unlink.geometry()
        if self.buffer != 0 and self.buffer:
            unlink_geom = unlink_geom.buffer(self.buffer, 36)
        lines = [i for i in self.spIndex.intersects(unlink_geom.boundingBox()) if
                 unlink_geom.intersects(self.feats[i].geometry())]
        lines = list(set(lines))
        if len(lines) != 2:
            self.invalid_unlinks.append(unlink_geom.centroid().asPoint())
        else:

            line1_geom = self.feats[lines[0]].geometry()
            line2_geom = self.feats[lines[1]].geometry()
            unlink_geom = line1_geom.intersection(line2_geom)
            unlink_geom_p = unlink_geom.centroid().asPoint()
            if unlink_geom_p in line1_geom.asPolyline():
                # what if unlink on polyline vertices
                self.invalid_unlinks.append(unlink_geom_p)
            elif unlink_geom_p in line2_geom.asPolyline():
                self.invalid_unlinks.append(unlink_geom_p)
            else:
                # save point and not line - if line unlinked by one line in two points
                self.unlinks_points[lines[0]].append(unlink_geom.centroid().asPoint())
                self.unlinks_points[lines[1]].append(unlink_geom.centroid().asPoint())
        return True

    # for every line explode and crossings
    def point_iter(self, interlines, ml_geom):
        for line in interlines:
            inter = ml_geom.intersection(self.feats[line].geometry())
            if inter.type() == QgsWkbTypes.PointGeometry:
                if not inter.isMultipart():
                    yield ml_geom.lineLocatePoint(inter), inter.asPoint()
                else:
                    for i in inter.asMultiPoint():
                        yield ml_geom.lineLocatePoint(QgsGeometry.fromPointXY(i)), i
            elif self.feats[line].geometry().type() == QgsWkbTypes.LineGeometry:
                inter_line_geom_pl = self.feats[line].geometry().asPolyline()
                sh_line = (ml_geom.shortestLine(self.feats[line].geometry())).asPolyline()
                if sh_line[0] in inter_line_geom_pl:
                    if sh_line[0] == inter_line_geom_pl[0]:
                        line_geometry = self.feats[line].geometry()
                        line_geometry.moveVertex(sh_line[-1].x(), sh_line[-1].y(), 0)
                        self.feats[line].setGeometry(line_geometry)
                    if sh_line[0] == inter_line_geom_pl[-1]:
                        line_geometry = self.feats[line].geometry()
                        line_geometry.moveVertex(sh_line[-1].x(), sh_line[-1].y(),
                                                 len(inter_line_geom_pl) - 1)
                        self.feats[line].setGeometry(line_geometry)

                    yield ml_geom.lineLocatePoint(QgsGeometry.fromPointXY(sh_line[-1])), sh_line[-1]
                else:
                    if sh_line[-1] == inter_line_geom_pl[0]:
                        line_geometry = self.feats[line].geometry()
                        line_geometry.moveVertex(sh_line[0].x(), sh_line[0].y(), 0)
                        self.feats[line].setGeometry(line_geometry)
                    if sh_line[-1] == inter_line_geom_pl[-1]:
                        line_geometry = self.feats[line].geometry()
                        line_geometry.moveVertex(sh_line[0].x(), sh_line[0].y(),
                                                 len(inter_line_geom_pl) - 1)
                        self.feats[line].setGeometry(line_geometry)
                    yield ml_geom.lineLocatePoint(QgsGeometry.fromPointXY(sh_line[0])), sh_line[0]
        ml_pl = ml_geom.asPolyline()
        pl_len = 0  # executed first time
        yield pl_len, ml_pl[0]
        for p1, p2 in zip(ml_pl[: -1], ml_pl[1:]):
            # unlinks in vertices not allowed
            # if closed polyline return last point/ if self intersection
            segm_len = QgsDistanceArea().measureLine(p1, p2)
            if segm_len != 0:
                pl_len += segm_len
                yield pl_len, p2

    def break_segm(self, feat):

        f_geom = feat.geometry()
        inter_lines = [line for line in self.spIndex.intersects(f_geom.boundingBox()) if
                       feat.geometry().distance(self.feats[line].geometry()) <= 0.00001]
        # TODO: group by factor because some times slightly different points are returned
        # TODO: keep order
        cross_p = {factor: p for (factor, p) in sorted(set(self.point_iter(inter_lines, f_geom))) if
                   p not in self.unlinks_points[feat.id()]}
        cross_p = sorted(cross_p.items())
        cross_p = [p for (factor, p) in cross_p]

        if self.stub_ratio:
            cross_p = [p for p in self.stubs_clean_iter(cross_p, f_geom.asPolyline())]

        return cross_p

    def break_feats_iter(self, cross_p_list):
        self.total_progress = 80
        for idx, cross_p in enumerate(cross_p_list):
            if self.killed is True:
                break
            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            for pair in zip(cross_p[:-1], cross_p[1:]):
                feat = self.feats[idx]
                self.id += 1
                yield feat, QgsGeometry.fromPolylineXY(list(pair)), self.id

    def list_iter(self, any_list):
        self.total_progress = 10
        for item in any_list:
            if self.killed is True:
                break
            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            yield item

    def segment(self):

        break_point_feats, invalid_unlink_point_feats, stubs_point_feats, segmented_feats = [], [], [], []

        try:
            # TODO: if postgis - run function
            self.step = 10 / float(self.layer.featureCount())
            self.load_graph()
            # self.step specified in load_graph
            # progress emitted by break_segm & break_feats_iter
            cross_p_list = [self.break_segm(feat) for feat in self.list_iter(list(self.feats.values()))]
            self.step = 20 / float(len(cross_p_list))
            segmented_feats = [self.copy_feat(feat_geom_fid[0], feat_geom_fid[1], feat_geom_fid[2]) for feat_geom_fid in
                               self.break_feats_iter(cross_p_list)]

            if self.errors:
                cross_p_list = set(list(itertools.chain.from_iterable(cross_p_list)))

                ids1 = [i for i in range(0, len(cross_p_list))]
                break_point_feats = [self.copy_feat(self.break_f, QgsGeometry.fromPointXY(p_fid[0]), p_fid[1]) for p_fid
                                     in (list(zip(cross_p_list, ids1)))]
                ids2 = [i for i in range(max(ids1) + 1, max(ids1) + 1 + len(self.invalid_unlinks))]
                invalid_unlink_point_feats = [
                    self.copy_feat(self.invalid_unlink_f, QgsGeometry.fromPointXY(p_fid1[0]), p_fid1[1]) for p_fid1 in
                    (list(zip(self.invalid_unlinks, ids2)))]
                ids = [i for i in range(max(ids1 + ids2) + 1, max(ids1 + ids2) + 1 + len(self.stubs_points))]
                stubs_point_feats = [self.copy_feat(self.stub_f, QgsGeometry.fromPointXY(p_fid2[0]), p_fid2[1]) for
                                     p_fid2 in (list(zip(self.stubs_points, ids)))]

        except Exception as exc:
            print(exc, traceback.format_exc())
            # TODO: self.error.emit(exc, traceback.format_exc())

        return segmented_feats, break_point_feats + invalid_unlink_point_feats + stubs_point_feats

    def stubs_clean_iter(self, cross_p, f_pl):
        for pnt in cross_p[:1]:

            if QgsDistanceArea().measureLine(pnt, cross_p[1]) >= self.stub_ratio * QgsDistanceArea().measureLine(pnt,
                                                                                                                 f_pl[
                                                                                                                     1]):
                yield pnt

            # elif self.connectivity[(pnt.x(), pnt.y())] == 1:
            elif self.get_no_inter_lines(pnt) == 1:
                self.stubs_points.append(pnt)
                pass
            else:
                yield pnt
        for pnt in cross_p[1:-1]:
            yield pnt
        for pnt in cross_p[-1:]:
            if QgsDistanceArea().measureLine(pnt, cross_p[-2]) >= self.stub_ratio * QgsDistanceArea().measureLine(pnt,
                                                                                                                  f_pl[
                                                                                                                      -2]):
                yield pnt
            elif self.get_no_inter_lines(pnt) == 1:

                # elif self.connectivity[(pnt.x(), pnt.y())] == 1:
                self.stubs_points.append(pnt)
                pass
            else:
                yield pnt

    def get_no_inter_lines(self, point):
        point_geom = QgsGeometry.fromPointXY(point)
        lines = self.spIndex.intersects(point_geom.boundingBox())
        filtered_lines = [l for l in lines if self.feats[l].geometry().intersects(point_geom)]
        return len(set(filtered_lines))

    def copy_feat(self, f, geom, feat_id):
        copy_feat = QgsFeature(f)
        copy_feat.setGeometry(geom)
        copy_feat.setId(feat_id)
        return copy_feat

    # only 1 time execution permitted
    def feat_iter(self, layer):
        id = 0
        self.total_progress = 0

        for f in layer.getFeatures():

            self.total_progress += self.step
            self.progress.emit(self.total_progress)

            f_geom = f.geometry()
            if self.killed is True:
                break
            elif f.geometry() is NULL:
                pass
            elif not f.geometry():  # NULL geometries
                pass
            elif f_geom.length() == 0:
                pass
            elif f_geom.type() == QgsWkbTypes.LineGeometry:
                if f_geom.isMultipart():
                    ml_segms = f_geom.asMultiPolyline()
                    for ml in ml_segms:
                        ml_geom = QgsGeometry.fromPolylineXY(ml)
                        ml_feat = self.copy_feat(f, ml_geom, id)
                        self.feats[id] = ml_feat
                        id += 1
                        yield ml_feat
                else:
                    f.setId(id)
                    self.feats[id] = f
                    id += 1
                    yield f

    def kill(self):
        self.killed = True
