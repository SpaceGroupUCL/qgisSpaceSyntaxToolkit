from __future__ import print_function
# general imports
from builtins import zip
from builtins import str
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsFeature, QgsGeometry,QgsFields, QgsDataSourceURI
import psycopg2
from psycopg2.extensions import AsIs

# source: ess utility functions


def getLayerByName(name):
    layer = None
    for i in list(QgsProject.instance().mapLayers().values()):
        if i.name() == name:
            layer = i
    return layer


def get_next_vertex(tree, all_con):
    last = tree[-1]
    return tree + [i for i in all_con[last] if i not in tree]


def keep_decimals_string(string, number_decimals):
    integer_part = string.split(".")[0]
    # if the input is an integer there is no decimal part
    if len(string.split("."))== 1:
        decimal_part = str(0)*number_decimals
    else:
        decimal_part = string.split(".")[1][0:number_decimals]
    if len(decimal_part) < number_decimals:
        zeros = str(0) * int((number_decimals - len(decimal_part)))
        decimal_part = decimal_part + zeros
    decimal = integer_part + '.' + decimal_part
    return decimal


def find_vertex_index(points, f_geom):
    for point in points:
        yield f_geom.asPolyline().index(point.asPoint())


def point_is_vertex(point, line):
    #pl_l = line.asPolyline()
    #try:
    #    idx = pl_l.index(point.asPoint())
    #    if idx == 0 or idx == (len(pl_l) - 1):
    #        return True
    #    else:
    #        return False
    #except ValueError:
    #    return False
    if point.asPoint() in line.asPolyline():
        return True


def vertices_from_wkt_2(wkt):
    # the wkt representation may differ in other systems/ QGIS versions
    # TODO: check
    nums = [i for x in wkt[11:-1:].split(', ') for i in x.split(' ')]
    if wkt[0:12] == u'LineString (':
        nums = [i for x in wkt[12:-1:].split(', ') for i in x.split(' ')]
    coords = list(zip(*[iter(nums)] * 2))
    for vertex in coords:
        yield vertex


def make_snapped_wkt(wkt, number_decimals):
    # TODO: check in different system if '(' is included
    snapped_wkt = 'LINESTRING('
    for i in vertices_from_wkt_2(wkt):
        new_vertex = str(keep_decimals_string(i[0], number_decimals)) + ' ' + str(
            keep_decimals_string(i[1], number_decimals))
        snapped_wkt += str(new_vertex) + ', '
    return snapped_wkt[0:-2] + ')'


def to_shp(path, any_features_list, layer_fields, crs, name, encoding, geom_type):
    if path is None:
        if geom_type == 0:
            network = QgsVectorLayer('Point?crs=' + crs.toWkt(), name, "memory")
        else:
            network = QgsVectorLayer('LineString?crs=' + crs.toWkt(), name, "memory")
    else:
        fields = QgsFields()
        for field in layer_fields:
            fields.append(field)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = encoding
        file_writer = QgsVectorFileWriter.create(path, fields, geom_type, crs, QgsCoordinateTransformContext(), options)
        if file_writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ", file_writer.errorMessage())
        del file_writer
        network = QgsVectorLayer(path, name, "ogr")
    pr = network.dataProvider()
    if path is None:
        pr.addAttributes(layer_fields)
    new_features = []
    for i in any_features_list:
        new_feat = QgsFeature()
        new_feat.setId(i[0])
        new_feat.setAttributes([attr[0] for attr in i[1]])
        new_feat.setGeometry(QgsGeometry(QgsGeometry.fromWkt(str(i[2]))))
        #QgsGeometry()
        new_features.append(new_feat)
    network.startEditing()
    pr.addFeatures(new_features)
    network.commitChanges()
    return network

def rmv_parenthesis(my_string):
    idx = my_string.find(',ST_GeomFromText') - 1
    return  my_string[:idx] + my_string[(idx+1):]

def to_dblayer(dbname, user, host, port, password, schema, table_name, qgs_flds, any_features_list, crs):

    crs_id = str(crs.postgisSrid())
    connstring = "dbname=%s user=%s host=%s port=%s password=%s" % (dbname, user, host, port, password)
    try:
        con = psycopg2.connect(connstring)
        cur = con.cursor()
        post_q_flds = {2: 'bigint[]', 6: 'numeric[]', 1: 'bool[]', 'else':'text[]'}
        postgis_flds_q = """"""
        for f in qgs_flds:
            f_name = '\"'  + f.name()  + '\"'
            try: f_type = post_q_flds[f.type()]
            except KeyError: f_type = post_q_flds['else']
            postgis_flds_q += cur.mogrify("""%s %s,""", (AsIs(f_name), AsIs(f_type)))

        query = cur.mogrify("""DROP TABLE IF EXISTS %s.%s; CREATE TABLE %s.%s(%s geom geometry(LINESTRING, %s))""", (AsIs(schema), AsIs(table_name), AsIs(schema), AsIs(table_name), AsIs(postgis_flds_q), AsIs(crs_id)))
        cur.execute(query)
        con.commit()

        data = []

        for (fid, attrs, wkt) in any_features_list:
            for idx, l_attrs in enumerate(attrs):
                if l_attrs:
                    attrs[idx] = [i if i else None for i in l_attrs]
                    if attrs[idx] == [None]:
                        attrs[idx] = None
                    else:
                        attrs[idx] = [a for a in attrs[idx] if a]
            data.append(tuple((attrs, wkt)))

        args_str = ','.join(
            [rmv_parenthesis(cur.mogrify("%s,ST_GeomFromText(%s,%s))", (tuple(attrs), wkt, AsIs(crs_id)))) for
             (attrs, wkt) in tuple(data)])

        ins_str = cur.mogrify("""INSERT INTO %s.%s VALUES """, (AsIs(schema), AsIs(table_name)))
        cur.execute(ins_str + args_str)
        con.commit()
        con.close()
        print("success!")
        uri = QgsDataSourceURI()
        # set host name, port, database name, username and password
        uri.setConnection(host, port, dbname, user, password)
        # set database schema, table name, geometry column and optionally
        uri.setDataSource(schema, table_name, "geom")
        return QgsVectorLayer(uri.uri(), table_name, "postgres")

    except psycopg2.DatabaseError as e:
        return e

# SOURCE: ESS TOOLKIT
def getPostgisSchemas(connstring, commit=False):
    """Execute query (string) with given parameters (tuple)
    (optionally perform commit to save Db)
    :return: result set [header,data] or [error] error
    """

    try:
        connection = psycopg2.connect(connstring)
    except psycopg2.Error as e:
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






