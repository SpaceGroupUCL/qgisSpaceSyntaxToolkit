
# INPUT

from past.builtins import execfile
execfile(u'/Users/i.kolovou/Documents/Github/qgisSpaceSyntaxToolkit/esstoolkit/catchment_analyser/catchment_analysis.py'.encode('utf-8'))
execfile(u'/Users/i.kolovou/Documents/Github/qgisSpaceSyntaxToolkit/esstoolkit/catchment_analyser/utility_functions.py'.encode('utf-8'))

origin_vector = getLayerByName('2595D_pr_tfl_bus_stops')
network = getLayerByName('2595D_spm_pr2_seg2')
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
    if f.geometry().wkbType() == 2:
        attributes_dict [f.id()] = f.attributes()
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
    elif f.geometry().wkbType() == 5:
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
catchment_network, catchment_points = self.graph_analysis(
    graph,
    tied_origins,
    self.settings['distances']
)

# Create output signal
output = {'output network': None,
          'output polygon': None,
          'distances': self.settings['distances']}

network = self.settings['network']

# Write and render the catchment polygons

if self.settings['output polygon check']:
    new_fields = QgsFields()
    new_fields.append(QgsField('id',QVariant.Int))
    new_fields.append(QgsField('origin', QVariant.String))
    new_fields.append(QgsField('distance', QVariant.Int))
    output_polygon = uf.to_layer(new_fields, network.crs(), network.dataProvider().encoding(),
                                 'Polygon', self.settings['layer_type'],
                                 self.settings['output path'][0])


    output_polygon = self.polygon_writer(
        catchment_points,
        self.settings['distances'],
        output_polygon,
        self.settings['polygon tolerance'],
    )
    output['output polygon'] = output_polygon


# get fields

new_fields = self.get_fields(origins, self.settings['name'])

# create layer
output_network = uf.to_layer(new_fields, network.crs(), network.dataProvider().encoding(), 'Linestring', self.settings['layer_type'], self.settings['output path'][0])

# Write and render the catchment network
output_network = self.network_writer(
    output_network,
    catchment_network,
    self.settings['name']
)

output['output network'] = output_network