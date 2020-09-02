from qgis.core import (QgsApplication, QgsVectorLayer, QgsFeature, QgsLineString, QgsPoint)
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
import unittest

qgs = QgsApplication([], False)
qgs.initQgis()

from gate_transformer import TransformerAnalysis

class TestGateTransformer(unittest.TestCase):

    def test_rotate(self):
        vl = QgsVectorLayer("LineString", "temp", "memory")
        pr = vl.dataProvider()
        f = QgsFeature()
        f.setGeometry( QgsLineString( [ QgsPoint( 210, 41 ), QgsPoint( 301, 55 ) ] ) )
        pr.addFeature(f)
        vl.updateExtents()
        self.assertEqual(vl.featureCount(), 1)
        gt = TransformerAnalysis.GateTransformer
        gt.rotate_line02(gt, vl, 90)
        rotFeat = next(vl.getFeatures()).geometry().asPolyline()
        self.assertAlmostEqual(rotFeat[0][0], 248.5, places=3)
        self.assertAlmostEqual(rotFeat[0][1], 93.5, places=3)
        self.assertAlmostEqual(rotFeat[1][0], 262.5, places=3)
        self.assertAlmostEqual(rotFeat[1][1], 2.5, places=3)

    def test_resize(self):
        vl = QgsVectorLayer("LineString", "temp", "memory")
        pr = vl.dataProvider()
        f = QgsFeature()
        f.setGeometry( QgsLineString( [ QgsPoint( 210, 41 ), QgsPoint( 301, 55 ) ] ) )
        pr.addFeature(f)
        vl.updateExtents()
        self.assertEqual(vl.featureCount(), 1)
        gt = TransformerAnalysis.GateTransformer
        gt.resize_line02(gt, vl, 0.5)
        rotFeat = next(vl.getFeatures()).geometry().asPolyline()
        self.assertAlmostEqual(rotFeat[0][0], 255.7470, places=3)
        self.assertAlmostEqual(rotFeat[0][1], 48.0380, places=3)
        self.assertAlmostEqual(rotFeat[1][0], 255.2529, places=3)
        self.assertAlmostEqual(rotFeat[1][1], 47.9619, places=3)

    def test_rescale(self):
        vl = QgsVectorLayer("LineString", "temp", "memory")
        pr = vl.dataProvider()
        f = QgsFeature()
        f.setGeometry( QgsLineString( [ QgsPoint( 210, 41 ), QgsPoint( 301, 55 ) ] ) )
        pr.addFeature(f)
        vl.updateExtents()
        self.assertEqual(vl.featureCount(), 1)
        gt = TransformerAnalysis.GateTransformer
        gt.rescale_line02(gt, vl, 15)
        rotFeat = next(vl.getFeatures()).geometry().asPolyline()
        self.assertAlmostEqual(rotFeat[0][0], 938.0, places=3)
        self.assertAlmostEqual(rotFeat[0][1], 153.0, places=3)
        self.assertAlmostEqual(rotFeat[1][0], -427.0, places=3)
        self.assertAlmostEqual(rotFeat[1][1], -56.9999, places=3)

if __name__ == '__main__':
    unittest.main()

qgs.exitQgis()
