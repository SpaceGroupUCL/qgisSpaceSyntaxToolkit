from __future__ import print_function
# general imports
from builtins import str
from qgis.core import  QgsMapLayerRegistry, QgsFields, QgsField, QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QGis, NULL, QgsDataSourceURI, QgsVectorLayerImport
import psycopg2
from psycopg2.extensions import AsIs
import ntpath

# source: ess utility functions

# -------------------------- LAYER HANDLING


def getLayerByName(name):
    layer = None
    for i in list(QgsMapLayerRegistry.instance().mapLayers().values()):
        if i.name() == name:
            layer = i
    return layer

# -------------------------- GEOMETRY HANDLING


# -------------------------- FEATURE HANDLING

def prototype_feature(attrs, fields):
    feat = QgsFeature()
    feat.initAttributes(1)
    feat.setFields(fields)
    feat.setAttributes(attrs)
    feat.setGeometry(QgsGeometry())
    return feat

# -------------------------- POSTGIS INFO RETRIEVAL


# SOURCE: ESS TOOLKIT

def getPostgisSchemas(connstring, commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """

    try:
        connection = psycopg2.connect(connstring)
    except psycopg2.Error as e:
        # fix_print_with_import
        print(e.pgerror)
        connection = None

    schemas = []
    data = []
    if connection:
        query = str("""SELECT schema_name from information_schema.schemata;""")
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            if cursor.description is not None:
                data = cursor.fetchall()
            if commit:
                connection.commit()
        except psycopg2.Error as e:
            connection.rollback()
        cursor.close()

    # only extract user schemas
    for schema in data:
        if schema[0] not in ('topology', 'information_schema') and schema[0][:3] != 'pg_':
            schemas.append(schema[0])
    #return the result even if empty
    return sorted(schemas)


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

        wkbTypes = { 'Point': QGis.WKBPoint, 'Linestring': QGis.WKBLineString, 'Polygon': QGis.WKBPolygon }
        file_writer = QgsVectorFileWriter(path, encoding, fields, wkbTypes[geom_type], crs, "ESRI Shapefile")
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            # fix_print_with_import
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
            create_query = cur.mogrify("""DROP TABLE IF EXISTS "%s"."%s"; CREATE TABLE "%s"."%s"( geom geometry(%s, %s))""", (
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
            field_names = ",".join([ '"'+f.name()+'"' for f in fields])
            for feature in features:
                attrs = [i if i else None for i in feature.attributes()]
                insert_query = cur.mogrify("""INSERT INTO "%s"."%s" (%s, geom) VALUES %s, ST_GeomFromText(%s,%s))""", (
                AsIs(schema_name), AsIs(table_name), AsIs(field_names), tuple(attrs),
                feature.geometry().exportToWkt(), AsIs(crs_id)))
                idx = insert_query.find(', ST_GeomFromText') - 1
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



