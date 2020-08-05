from qgis.core import QgsFields, QgsField, QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, NULL


def getLayerByName(name):
    layer = None
    for i in list(QgsMapLayerRegistry.instance().mapLayers().values()):
        if i.name() == name:
            layer = i
    return layer
