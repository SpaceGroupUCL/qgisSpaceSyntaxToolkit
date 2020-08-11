from __future__ import absolute_import

# general imports
from builtins import range
from qgis.core import (QgsFeature, QgsGeometry, QgsSpatialIndex, QgsPoint, QgsVectorFileWriter, QgsField)
from qgis.PyQt.QtCore import (QObject, pyqtSignal, QVariant)


# plugin module imports
try:
    from .utilityFunctions import *
except ImportError:
    pass

class breakTool(QObject):

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, str)
    progress = pyqtSignal(float)
    warning = pyqtSignal(str)
    killed = pyqtSignal(bool)

    def __init__(self,layer, tolerance, uid, errors, unlinks):
        QObject.__init__(self)

        self.layer = layer
        self.feat_count = self.layer.featureCount()
        self.tolerance = tolerance
        self.uid = uid

        self.errors = errors
        self.errors_features = {}
        self.unlinks = unlinks
        self.unlinked_features = []
        self.unlinks_count = 0
        self.ml_keys = {}
        self.br_keys = {}

        self.features = []
        self.attributes = {}
        self.geometries = {}
        self.geometries_wkt = {}
        self.geometries_vertices = {}
        # create spatial index object
        self.spIndex = QgsSpatialIndex()
        self.layer_fields = [QgsField(i.name(), i.type()) for i in self.layer.dataProvider().fields()]

    def add_edges(self):

        new_key_count = 0
        f_count = 1

        for f in self.layer.getFeatures():

            self.progress.emit(3 * f_count / self.feat_count)
            f_count += 1

            if self.killed is True:
                break

            geom_type = f.geometry().wkbType()

            if geom_type not in [5,2,1] and f.geometry().geometry().is3D():
                f.geometry().geometry().dropZValue()
                geom_type = f.geometry().wkbType()

            if geom_type == 5:
                if self.errors:
                    self.errors_features[f.id()] = ('multipart', f.geometry().exportToWkt())
                for multipart in f.geometry().asGeometryCollection():
                    new_key_count += 1
                    attr = f.attributes()
                    new_feat = QgsFeature()
                    new_feat.setAttributes(attr)
                    new_feat.setFeatureId(new_key_count)
                    if self.tolerance:
                        snapped_wkt = make_snapped_wkt(multipart.exportToWkt(), self.tolerance)
                    else:
                        snapped_wkt = multipart.exportToWkt()
                    snapped_geom = QgsGeometry.fromWkt(snapped_wkt)
                    new_feat.setGeometry(snapped_geom)
                    self.features.append(new_feat)
                    self.attributes[new_key_count] = attr
                    self.geometries[new_key_count] = new_feat.geometryAndOwnership()
                    self.geometries_wkt[new_key_count] = snapped_wkt
                    self.geometries_vertices[new_key_count] = [vertex for vertex in vertices_from_wkt_2(snapped_wkt)]
                    # insert features to index
                    self.spIndex.insertFeature(new_feat)
                    self.ml_keys[new_key_count] = f.id()
            elif geom_type == 1:
                if self.errors:
                    self.errors_features[f.id()] = ('point', QgsGeometry().exportToWkt())
            elif not f.geometry().isGeosValid():
                if self.errors:
                    self.errors_features[f.id()] = ('invalid', QgsGeometry().exportToWkt())
            elif geom_type == 2:
                attr = f.attributes()
                if self.tolerance:
                    snapped_wkt = make_snapped_wkt(f.geometry().exportToWkt(), self.tolerance)
                else:
                    snapped_wkt = f.geometry().exportToWkt()
                snapped_geom = QgsGeometry.fromWkt(snapped_wkt)
                f.setGeometry(snapped_geom)
                new_key_count += 1
                f.setFeatureId(new_key_count)
                self.features.append(f)
                self.attributes[f.id()] = attr
                self.geometries[f.id()] = f.geometryAndOwnership()
                self.geometries_wkt[f.id()] = snapped_wkt
                self.geometries_vertices[f.id()] = [vertex for vertex in vertices_from_wkt_2(snapped_wkt)]
                # insert features to index
                self.spIndex.insertFeature(f)
                self.ml_keys[new_key_count] = f.id()

    def break_features(self):

        broken_features = []
        f_count = 1

        for fid in list(self.geometries.keys()):

            if self.killed is True:
                break

            f_geom = self.geometries[fid]
            f_attrs = self.attributes[fid]

            # intersecting lines
            gids = self.spIndex.intersects(f_geom.boundingBox())

            self.progress.emit((45 * f_count / self.feat_count) + 5)
            f_count += 1

            f_errors, vertices = self.find_breakages(fid, gids)

            if self.errors and f_errors:
                original_id = self.ml_keys[fid]
                try:
                    updated_errors = self.errors_features[original_id][0] + f_errors
                    self.errors_features[original_id] = (updated_errors, self.errors_features[original_id][1])
                except KeyError:
                    self.errors_features[original_id] = (f_errors, self.geometries[fid].exportToWkt())

            if f_errors is None:
                vertices = [0, len(f_geom.asPolyline()) - 1 ]

            if f_errors in ['breakage, overlap', 'breakage', 'overlap', None]:
                for ind, index in enumerate(vertices):
                    if ind != len(vertices) - 1:
                        points = [self.geometries_vertices[fid][i] for i in range(index, vertices[ind + 1] + 1)]
                        p = ''
                        for point in points:
                            p += point[0] + ' ' + point[1] + ', '
                        wkt = 'LINESTRING(' + p[:-2] + ')'
                        self.feat_count += 1
                        new_fid = self.feat_count
                        new_feat = [new_fid, f_attrs, wkt]
                        broken_features.append(new_feat)
                        self.br_keys[new_fid] = fid

        return broken_features

    def kill(self):
        self.br_killed = True

    def find_breakages(self, fid, gids):

        f_geom = self.geometries[fid]

        # errors checks
        must_break = False
        is_closed = False
        if f_geom.asPolyline()[0] == f_geom.asPolyline()[-1]:
            is_closed = True
        is_orphan = True
        is_duplicate = False
        has_overlaps = False

        # get breaking points
        breakages = []

        # is self intersecting
        is_self_intersersecting = False
        for i in f_geom.asPolyline():
            if f_geom.asPolyline().count(i) > 1:
                point = QgsGeometry().fromPoint(QgsPoint(i[0], i[1]))
                breakages.append(point)
                is_self_intersersecting = True
                must_break = True

        for gid in gids:

            g_geom = self.geometries[gid]

            if gid < fid:
                # duplicate geometry
                if f_geom.isGeosEqual(g_geom):
                    is_duplicate = True

                if self.unlinks:
                    if f_geom.crosses(g_geom):
                        crossing_point = f_geom.intersection(g_geom)
                        if crossing_point.wkbType() == 1:
                            self.unlinks_count += 1
                            unlinks_attrs = [[self.unlinks_count], [gid], [fid], [crossing_point.asPoint()[0]],
                                             [crossing_point.asPoint()[1]]]
                            self.unlinked_features.append([self.unlinks_count, unlinks_attrs, crossing_point.exportToWkt()])
                        elif crossing_point.wkbType() == 4:
                            for cr_point in crossing_point.asGeometryCollection():
                                self.unlinks_count += 1
                                unlinks_attrs = [[self.unlinks_count], [gid], [fid], [cr_point.asPoint()[0]],
                                                 [cr_point.asPoint()[1]]]
                                self.unlinked_features.append([self.unlinks_count, unlinks_attrs, cr_point.exportToWkt()])

            if is_duplicate is False:
                intersection = f_geom.intersection(g_geom)
                # intersecting geometries at point
                if intersection.wkbType() == 1 and point_is_vertex(intersection, f_geom):
                    breakages.append(intersection)
                    is_orphan = False
                    must_break = True

                # intersecting geometries at multiple points
                elif intersection.wkbType() == 4:
                    for point in intersection.asGeometryCollection():
                        if point_is_vertex(point, f_geom):
                            breakages.append(point)
                            is_orphan = False
                            must_break = True

                # overalpping geometries
                elif intersection.wkbType() == 2 and intersection.length() != f_geom.length():
                    point1 = QgsGeometry.fromPoint(QgsPoint(intersection.asPolyline()[0]))
                    point2 = QgsGeometry.fromPoint(QgsPoint(intersection.asPolyline()[-1]))
                    if point_is_vertex(point1, f_geom):
                        breakages.append(point1)
                        is_orphan = False
                        must_break = True
                    if point_is_vertex(point2, f_geom):
                        breakages.append(point2)
                        is_orphan = False
                        must_break = True

                # overalpping multi-geometries
                # every feature overlaps with itself as a multilinestring
                elif intersection.wkbType() == 5 and intersection.length() != f_geom.length():
                    point1 = QgsGeometry.fromPoint(QgsPoint(intersection.asGeometryCollection()[0].asPolyline()[0]))
                    point2 = QgsGeometry.fromPoint(QgsPoint(intersection.asGeometryCollection()[-1].asPolyline()[-1]))
                    if point_is_vertex(point1, f_geom):
                        is_orphan = False
                        has_overlaps = True
                        breakages.append(point1)
                    if point_is_vertex(point2, f_geom):
                        is_orphan = False
                        has_overlaps = True
                        breakages.append(point2)

        if is_duplicate is True:
            return 'duplicate', []
        else:
            # add first and last vertex
            vertices = set([vertex for vertex in find_vertex_index(breakages, f_geom)])
            vertices = list(vertices) + [0] + [len(f_geom.asPolyline()) - 1]
            vertices = list(set(vertices))
            vertices.sort()

            if is_orphan:
                if is_closed is True:
                    return 'closed polyline', []
                else:
                    return 'orphan', []

            elif is_self_intersersecting:
                if has_overlaps:
                    return 'breakage, overlap', vertices
                else:
                    return 'breakage', vertices

            elif has_overlaps or must_break:
                if has_overlaps is True and must_break is True:
                    return 'breakage, overlap', vertices
                elif has_overlaps is True and must_break is False:
                    return 'overlap', vertices
                elif has_overlaps is False and must_break is True:
                    if len(vertices) > 2:
                        return 'breakage', vertices
                    else:
                        return None, []
            else:
                return None, []

    def updateErrors(self, errors_dict):

        for k, v in list(errors_dict.items()):

            try:
                original_id = self.br_keys[k]
                try:
                    original_id = self.ml_keys[k]
                except KeyError:
                    pass
            except KeyError:
                original_id = None

            if original_id:
                try:
                    updated_errors = self.errors_features[original_id][0]
                    if ', continuous line' not in self.errors_features[original_id][0]:
                        updated_errors += ', continuous line'
                    self.errors_features[original_id] = (updated_errors, self.errors_features[original_id][1])
                except KeyError:
                    self.errors_features[original_id] = ('continuous line', self.geometries[original_id].exportToWkt())
