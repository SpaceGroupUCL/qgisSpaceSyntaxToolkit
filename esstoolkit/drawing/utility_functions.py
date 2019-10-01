from qgis.core import QgsMapLayerRegistry, QgsFields, QgsField, QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, QGis, NULL, QgsDataSourceURI, QgsVectorLayerImport


def getLayerByName(name):
    layer = None
    for i in QgsMapLayerRegistry.instance().mapLayers().values():
        if i.name() == name:
            layer = i
    return layer
