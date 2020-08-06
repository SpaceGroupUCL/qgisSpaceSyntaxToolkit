from qgis.core import QgsFields, QgsField, QgsGeometry, QgsFeature, QgsVectorLayer, QgsVectorFileWriter, NULL, QgsProject


def getLayerByName(name):
    layer = None
    for i in list(QgsProject.instance().mapLayers().values()):
        if i.name() == name:
            layer = i
    return layer
