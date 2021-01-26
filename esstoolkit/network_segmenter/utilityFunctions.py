from __future__ import print_function

import ntpath

import psycopg2
from psycopg2.extensions import AsIs
# general imports
from qgis.core import QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QgsWkbTypes, \
    QgsCoordinateTransformContext


# source: ess utility functions

# -------------------------- FEATURE HANDLING

def prototype_feature(attrs, fields):
    feat = QgsFeature()
    feat.initAttributes(1)
    feat.setFields(fields)
    feat.setAttributes(attrs)
    feat.setGeometry(QgsGeometry())
    return feat


# -------------------------- LAYER BUILD

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
                    AsIs(schema_name), AsIs(table_name), AsIs(field_names), tuple(attrs),
                    feature.geometry().asWkt(), AsIs(crs_id)))
                idx = insert_query.find(b', ST_GeomFromText') - 1
                insert_query = insert_query[:idx] + insert_query[(idx + 1):]
                cur.execute(insert_query)
                con.commit()
            pkey_query = cur.mogrify(
                """ALTER TABLE "%s"."%s" DROP COLUMN IF EXISTS seg_id; ALTER TABLE "%s"."%s" ADD COLUMN seg_id serial PRIMARY KEY NOT NULL;""",
                (AsIs(schema_name), AsIs(table_name), AsIs(schema_name), AsIs(table_name)))
            cur.execute(pkey_query)
            con.commit()
            con.close()
            layer = QgsVectorLayer(uri, table_name, 'postgres')
        except psycopg2.DatabaseError as e:
            # fix_print_with_import
            print(e)

    return layer
