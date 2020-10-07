# INPUT
from qgis.PyQt.QtCore import QVariant
from qgis.analysis import QgsGraphBuilder
from qgis.core import (QgsSpatialIndex, QgsGeometry, QgsFeature, QgsFields, QgsField, QgsWkbTypes)

import catchment_analyser.catchment_analysis as catchment
import catchment_analyser.utility_functions as uf
from catchment_analyser.analysis_tools import CustomCost
from esstoolkit.utilities import layer_field_helpers as lfh

origin_vector = lfh.getLayerByName('2595D_pr_tfl_bus_stops')
network = lfh.getLayerByName('2595D_spm_pr2_seg2')
origin_name_field = None
cost_field = 'length'
tolerance = 0.01
crs = network.crs()
epsg = network.crs().authid()[5:]

# ANALYSIS

# 1. prepare origins
# Loop through origin and get or create points
origins = []
for i, f in enumerate(origin_vector.getFeatures()):
    # Get origin name
    if origin_name_field:
        origin_name = f[origin_name_field]
    else:
        origin_name = i  # "origin_" + "%s" % (i+1)
    origins.append({'name': origin_name, 'geom': f.geometry().centroid()})

# 2. Build the graph
otf = False
# Get index of cost field
network_fields = network.pendingFields()
network_cost_index = network_fields.indexFromName(cost_field)

# Setting up graph build director
director = QgsLineVectorLayerDirector(network, -1, '', '', '', 3)

# Determining cost calculation
if cost_field != 'length':
    properter = CustomCost(network_cost_index, 0.01)
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

spIndex = QgsSpatialIndex()
indices = {}
attributes_dict = {}
centroids = {}
i = 0
for f in network.getFeatures():
    if f.geometry().type() == QgsWkbTypes.LineGeometry:
    if not f.geometry().isMultipart():
        attributes_dict[f.id()] = f.attributes()
        polyline = f.geometry().asPolyline()
        for idx, p in enumerate(polyline[1:]):
            ml = QgsGeometry.fromPolyline([polyline[idx], p])
            new_f = QgsFeature()
            new_f.setGeometry(ml.centroid())
            new_f.setAttributes([f.id()])
            new_f.setFeatureId(i)
            i += 1
            spIndex.addFeature(new_f)
            centroids[i] = f.id()
    else:
        attributes_dict[f.id()] = f.attributes()
        for pl in f.geometry().asMultiPolyline():
            for idx, p in enumerate(pl[1:]):
                ml = QgsGeometry.fromPolyline([pl[idx], p])
                new_f = QgsFeature()
                new_f.setGeometry(ml.centroid())
                new_f.setAttributes([f.id()])
                new_f.setFeatureId(i)
                spIndex.addFeature(new_f)
                centroids[i] = f.id()
                i += 1

network_fields = network_fields

# Run the analysis
catchment_network, catchment_points = catchment.graph_analysis(
    graph,
    tied_origins,
    catchment.settings['distances']
)

# Create output signal
output = {'output network': None,
          'output polygon': None,
          'distances': catchment.settings['distances']}

network = catchment.settings['network']

# Write and render the catchment polygons

if catchment.settings['output polygon check']:
    new_fields = QgsFields()
    new_fields.append(QgsField('id', QVariant.Int))
    new_fields.append(QgsField('origin', QVariant.String))
    new_fields.append(QgsField('distance', QVariant.Int))
    output_polygon = uf.to_layer(new_fields, network.crs(), network.dataProvider().encoding(),
                                 'Polygon', catchment.settings['layer_type'],
                                 catchment.settings['output path'][0])

    output_polygon = catchment.polygon_writer(
        catchment_points,
        catchment.settings['distances'],
        output_polygon,
        catchment.settings['polygon tolerance'],
    )
    output['output polygon'] = output_polygon

# get fields

new_fields = catchment.get_fields(origins, catchment.settings['name'])

# create layer
output_network = uf.to_layer(new_fields, network.crs(), network.dataProvider().encoding(), 'Linestring',
                             catchment.settings['layer_type'], catchment.settings['output path'][0])

# Write and render the catchment network
output_network = catchment.network_writer(
    output_network,
    catchment_network,
    catchment.settings['name']
)

output['output network'] = output_network
