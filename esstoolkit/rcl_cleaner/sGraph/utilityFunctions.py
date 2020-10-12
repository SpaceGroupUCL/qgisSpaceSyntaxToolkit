from __future__ import print_function

import collections
import math
import ntpath
from collections import defaultdict

import psycopg2
from psycopg2.extensions import AsIs
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsFields, QgsField, QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, NULL, \
    QgsWkbTypes, QgsCoordinateTransformContext

# FEATURES -----------------------------------------------------------------

# detecting errors:
# (NULL), point, (invalids), multipart geometries, snap (will be added later)
points = []
multiparts = []
error_feat = QgsFeature()
error_flds = QgsFields()
error_flds.append(QgsField('error_type', QVariant.String))
error_feat.setFields(error_flds)


# do not snap - because if self loop needs to break it will not

# FEATURES -----------------------------------------------------------------

def clean_features_iter(feat_iter):
    id = 0
    for f in feat_iter:

        f_geom = f.geometry()  # can be None

        # dropZValue if geometry is 3D
        if f_geom is None:
            pass
        elif f.geometry().constGet().is3D():
            f.geometry().constGet().dropZValue()
            f_geom = f.geometry()

        # point
        if f_geom is None:
            pass
        elif f_geom.length() <= 0:
            ml_error = QgsFeature(error_feat)
            if f_geom.isMultipart():
                ml_error.setGeometry(QgsGeometry.fromPointXY(f_geom.asMultiPolyline()[0][0]))
            else:
                ml_error.setGeometry(QgsGeometry.fromPointXY(f_geom.asPolyline()[0]))
            ml_error.setAttributes(['point'])
            points.append(ml_error)
        # empty geometry
        elif f_geom is NULL:
            # self.empty_geometries.append()
            pass
        # invalid geometry
        elif not f_geom.isGeosValid():
            # self.invalids.append(copy_feature(f, QgsGeometry(), f.id()))
            pass
        elif f_geom.type() == QgsWkbTypes.LineGeometry:
            if not f_geom.isMultipart():
                f.setId(id)
                id += 1
                yield f
            else:
                # multilinestring
                ml_segms = f_geom.asMultiPolyline()
                for ml in ml_segms:
                    ml_geom = QgsGeometry(QgsGeometry.fromPolylineXY(ml))
                    ml_feat = QgsFeature(f)
                    ml_feat.setId(id)
                    id += 1
                    ml_feat.setGeometry(ml_geom)
                    ml_error = QgsFeature(error_feat)
                    ml_error.setGeometry(QgsGeometry.fromPointXY(ml_geom.asPolyline()[0]))
                    ml_error.setAttributes(['multipart'])
                    multiparts.append(ml_error)
                    ml_error = QgsFeature(error_feat)
                    ml_error.setGeometry(QgsGeometry.fromPointXY(ml_geom.asPolyline()[-1]))
                    ml_error.setAttributes(['multipart'])
                    multiparts.append(ml_error)
                    yield ml_feat


# GEOMETRY -----------------------------------------------------------------


def getSelfIntersections(polyline):
    return [item for item, count in list(collections.Counter(polyline).items()) if count > 1]  # points


def find_vertex_indices(polyline, points):
    indices = defaultdict(list)
    for idx, vertex in enumerate(polyline):
        indices[vertex].append(idx)
    break_indices = [indices[v] for v in set(points)] + [[0, (len(polyline) - 1)]]
    break_indices = [item for sublist in break_indices for item in sublist]
    return sorted(list(set(break_indices)))


def angular_change(geom1, geom2):
    pl1 = geom1.asPolyline()
    pl2 = geom2.asPolyline()
    points1 = {pl1[0], pl1[-1]}
    points2 = {pl2[0], pl2[-1]}
    inter_point = points1.intersection(points2)
    point1 = [p for p in points1 if p != inter_point]
    point2 = [p for p in points1 if p != inter_point]

    # find index in geom1
    # if index 0, then get first vertex
    # if index -1, then get the one before last vertex

    # find index in geom2

    return


def angle_3_points(p1, p2, p3):
    inter_vertex1 = math.hypot(abs(float(p2.x()) - float(p1.x())), abs(float(p2.y()) - float(p1.y())))
    inter_vertex2 = math.hypot(abs(float(p2.x()) - float(p3.x())), abs(float(p2.y()) - float(p3.y())))
    vertex1_2 = math.hypot(abs(float(p1.x()) - float(p3.x())), abs(float(p1.y()) - float(p3.y())))
    A = ((inter_vertex1 ** 2) + (inter_vertex2 ** 2) - (vertex1_2 ** 2))
    B = (2 * inter_vertex1 * inter_vertex2)
    if B != 0:
        cos_angle = A / B
    else:
        cos_angle = NULL
    if cos_angle < -1:
        cos_angle = int(-1)
    elif cos_angle > 1:
        cos_angle = int(1)
    return 180 - math.degrees(math.acos(cos_angle))


def merge_geoms(geoms, simpl_threshold):
    # get attributes from longest
    new_geom = geoms[0]
    for i in geoms[1:]:
        new_geom = new_geom.combine(i)
    if simpl_threshold != 0:
        new_geom = new_geom.simplify(simpl_threshold)
    return new_geom


# ITERATORS -----------------------------------------------------------------

gr = [[29, 27, 26, 28], [31, 11, 10, 3, 30], [71, 51, 52, 69],
      [78, 67, 68, 39, 75], [86, 84, 81, 82, 83, 85], [84, 67, 78, 77, 81],
      [86, 68, 67, 84]]


# WRITE -----------------------------------------------------------------

# geom_type allowed: 'Point', 'Linestring', 'Polygon'
def to_layer(features, crs, encoding, geom_type, layer_type, path):
    first_feat = features[0]
    fields = first_feat.fields()
    layer = None
    if layer_type == 'memory':
        layer = QgsVectorLayer(geom_type + '?crs=' + crs.authid(), path, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields.toList())
        layer.updateFields()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'shapefile':

        wkbTypes = {'Point': QgsWkbTypes.Point, 'Linestring': QgsWkbTypes.LineString, 'Polygon': QgsWkbTypes.Polygon}
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = encoding
        file_writer = QgsVectorFileWriter.create(path, fields, wkbTypes[geom_type], crs,
                                                 QgsCoordinateTransformContext(), options)
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ", file_writer.errorMessage())
        del file_writer
        layer = QgsVectorLayer(path, ntpath.basename(path)[:-4], "ogr")
        pr = layer.dataProvider()
        layer.startEditing()
        pr.addFeatures(features)
        layer.commitChanges()

    elif layer_type == 'postgis':

        # this is needed to load the table later
        # uri = connstring + """ type=""" + geom_types[geom_type] + """ table=\"""" + schema_name + """\".\"""" + table_name + """\" (geom) """

        connstring, schema_name, table_name = path
        uri = connstring + """ type=""" + geom_type + """ table=\"""" + schema_name + """\".\"""" + table_name + """\" (geom) """
        crs_id = crs.postgisSrid()
        try:
            con = psycopg2.connect(connstring)
            cur = con.cursor()
            create_query = cur.mogrify(
                """DROP TABLE IF EXISTS "%s"."%s"; CREATE TABLE "%s"."%s"( geom geometry(%s, %s))""", (
                    AsIs(schema_name), AsIs(table_name), AsIs(schema_name), AsIs(table_name), geom_type, AsIs(crs_id)))
            cur.execute(create_query)
            con.commit()
            post_q_flds = {2: 'bigint', 6: 'numeric', 1: 'bool', 'else': 'text', 4: 'numeric'}
            for f in fields:
                f_type = f.type()
                if f_type not in [2, 6, 1]:
                    f_type = 'else'
                attr_query = cur.mogrify("""ALTER TABLE "%s"."%s" ADD COLUMN "%s" %s""", (
                    AsIs(schema_name), AsIs(table_name), AsIs(f.name()), AsIs(post_q_flds[f_type])))
                cur.execute(attr_query)
                con.commit()
            field_names = ",".join(['"' + f.name() + '"' for f in fields])
            for feature in features:
                attrs = [i if i else None for i in feature.attributes()]
                insert_query = cur.mogrify("""INSERT INTO "%s"."%s" (%s, geom) VALUES %s, ST_GeomFromText(%s,%s))""", (
                    AsIs(schema_name), AsIs(table_name), AsIs(field_names), tuple(attrs), feature.geometry().asWkt(),
                    AsIs(crs_id)))
                idx = insert_query.find(b', ST_GeomFromText') - 1
                insert_query = insert_query[:idx] + insert_query[(idx + 1):]
                # QgsMessageLog.logMessage('sql query %s' % insert_query, level=Qgis.Critical)
                cur.execute(insert_query)
                # con.commit()
            pkey_query = cur.mogrify(
                """ALTER TABLE "%s"."%s" DROP COLUMN IF EXISTS rcl_id; ALTER TABLE "%s"."%s" ADD COLUMN rcl_id serial PRIMARY KEY NOT NULL;""",
                (AsIs(schema_name), AsIs(table_name), AsIs(schema_name), AsIs(table_name)))
            cur.execute(pkey_query)
            con.commit()
            con.close()
            layer = QgsVectorLayer(uri, table_name, 'postgres')
        except psycopg2.DatabaseError as e:
            print(e)
    return layer
